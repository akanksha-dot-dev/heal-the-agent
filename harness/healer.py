"""THE HARNESS  (Agent = Model + Harness).

The model never touches your files and never runs anything. It only writes text.
Everything that makes this an *agent that heals itself* is the code in this file:

    SENSE  -> notice something is wrong          (exceptions AND contract violations)
    DIAGNOSE -> show the model the evidence      (traceback + payload + current code)
    PATCH  -> pull a fix out of the model's reply
    VERIFY -> don't trust it: test it in a sandbox, incl. old payloads
    LOOP   -> retry with memory, escalate to a stronger model, give up gracefully
"""
import difflib
import json
import os
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.contract import KNOWN_GOOD, contract_violations
from app.vendor_api import fetch_weather
from harness.guardrails import run_sandboxed, static_check
from harness.llm import ModelUnavailable, ask
from harness.prompts import DOCTOR_PROMPT, history_block

PARSER_FILE = Path(__file__).resolve().parent.parent / "app" / "weather_parser.py"
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "3"))
# Models to try, in order. A failed attempt escalates to the next one.
# e.g. DOCTOR_CASCADE="ollama/gemma4:e4b,gemini-flash-lite-latest"
CASCADE = [m.strip() for m in os.getenv("DOCTOR_CASCADE", "gemini-flash-lite-latest").split(",") if m.strip()]
AUTO_APPLY = os.getenv("AUTO_APPLY", "1") == "1"
ANTI_CHEAT = os.getenv("ANTI_CHEAT", "0") == "1"  # BONUS: see verify_fresh_sample()

C = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "dim": "\033[2m", "end": "\033[0m"}


def say(icon: str, label: str, text: str = "", color: str = "") -> None:
    print(f"{C.get(color, '')}{icon} {label:<9}{C['end']} {text}")


# ───────────────────────── STEP 1 · SENSE ─────────────────────────
def sense(code: str, raw: dict) -> dict:
    """Run the parser on `raw` (in the sandbox). Report what happened.

    Return {"ok": True, "result": {...}}                      when healthy, or
           {"ok": False, "kind": "...", "detail": "...", ...} when something is wrong.
    """
    outcome = run_sandboxed(code, [raw])
    if "timeout" in outcome:
        return {"ok": False, "kind": "timeout", "detail": "the parser ran for more than 5 seconds"}
    if "load_error" in outcome:
        return {"ok": False, "kind": "exception", "detail": outcome["load_error"]}
    first = outcome["results"][0]
    if not first["ok"]:
        return {"ok": False, "kind": "exception", "detail": first["traceback"]}
    problems = contract_violations(first["result"])
    if problems:  # no crash, but the ANSWER is wrong. Exceptions alone would have missed this.
        return {"ok": False, "kind": "contract violation", "detail": "; ".join(problems)}
    return {"ok": True, "result": first["result"]}


# ───────────────────── STEP 2 · DIAGNOSE & PATCH ─────────────────────
def build_prompt(code: str, raw: dict, incident: dict, failures: list[str]) -> str:
    return DOCTOR_PROMPT.format(
        code=code,
        kind=incident["kind"],
        detail=incident["detail"].strip(),
        payload=json.dumps(raw, indent=2),
        history=history_block(failures),
    )


def extract_code(reply: str) -> str | None:
    """Models are chatty. Pull the python code block out of the reply (None if there isn't one)."""
    match = re.search(r"```(?:python|py)?\s*\n(.*?)```", reply, re.DOTALL)
    return match.group(1).strip() + "\n" if match else None


def extract_diagnosis(reply: str) -> str:
    return reply.split("```")[0].strip() or "(the model gave no diagnosis)"


# ───────────────────────── STEP 3 · VERIFY ─────────────────────────
def verify(candidate: str, raw: dict) -> list[str]:
    """Never trust a patch. Return the reasons to REJECT it ([] means accept)."""
    problems = static_check(candidate)
    if problems:
        return problems
    payloads = [raw] + [old_raw for old_raw, _ in KNOWN_GOOD]
    out = run_sandboxed(candidate, payloads)
    if "timeout" in out:
        return ["the patched code timed out"]
    if "load_error" in out:
        return [f"the patched code failed to load: {out['load_error'].strip().splitlines()[-1]}"]
    new, *old = out["results"]
    if not new["ok"]:
        return [f"still crashes on the new payload: {new['traceback'].strip().splitlines()[-1]}"]
    problems += contract_violations(new["result"])
    for (old_raw, expected), r in zip(KNOWN_GOOD, old):  # REGRESSION: old payloads must still work
        if not r["ok"] or r["result"] != expected:
            problems.append(f"regression: the OLD payload for {old_raw['city']} no longer gives {expected}")
    return problems


# ───────────────────────── STEP 4 · THE LOOP ─────────────────────────
def heal(code: str, raw: dict, incident: dict) -> str | None:
    """Try to produce a verified fix. Returns new source code, or None if we give up."""
    failures: list[str] = []
    cascade = list(CASCADE)
    attempt = 0
    while attempt < MAX_ATTEMPTS and cascade:
        model = cascade[0]
        say("🩺", "DIAGNOSE", f"asking {model} (attempt {attempt + 1}/{MAX_ATTEMPTS})", "yellow")
        try:
            reply = ask(build_prompt(code, raw, incident, failures), model)
        except ModelUnavailable as why:
            say("⏭️ ", "SKIP", f"{model}: {why}", "dim")
            cascade.pop(0)  # can't reach this brain: try the next one, no attempt used
            continue
        attempt += 1
        say("💬", "MODEL", extract_diagnosis(reply))
        candidate = extract_code(reply)
        problems = ["the reply contained no ```python block"] if candidate is None else verify(candidate, raw)
        if not problems and ANTI_CHEAT:
            problems = verify_fresh_sample(candidate)
        if not problems:
            return candidate
        say("🧪", "VERIFY", "✗ rejected: " + " | ".join(problems), "red")
        failures.append(f"attempt {attempt} ({model}) was rejected: {' | '.join(problems)}")
        if len(cascade) > 1:  # escalate: a failed attempt hands the baton to the next (stronger) model
            cascade.pop(0)
    if attempt == 0:
        say("🛑", "NO BRAIN", "none of the models in DOCTOR_CASCADE could be reached", "red")
    return None


def verify_fresh_sample(candidate: str) -> list[str]:
    """BONUS anti-cheat. A patch that merely *looks* valid can hard-code the answer.
    So test it on a DIFFERENT city, fetched right now, that the model has never seen."""
    twin = fetch_weather("Zanzibar")
    out = run_sandboxed(candidate, [twin])
    if "results" not in out or not out["results"][0]["ok"]:
        return ["anti-cheat: the patch fails on a fresh sample"]
    result = out["results"][0]["result"]
    if result.get("city") != "Zanzibar":
        return [f"anti-cheat: I asked about Zanzibar but the patch answered {result.get('city')!r} (hard-coded?)"]
    return contract_violations(result)


def show_diff(old: str, new: str) -> None:
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), "before", "after", lineterm="", n=1):
        color = "green" if line.startswith("+") and not line.startswith("+++") else \
                "red" if line.startswith("-") and not line.startswith("---") else "dim"
        print(f"   {C[color]}{line}{C['end']}")


def get_weather_with_healing(city: str) -> dict:
    """The tool the agent calls. From the agent's point of view it just... works."""
    raw = fetch_weather(city)
    code = PARSER_FILE.read_text()
    outcome = sense(code, raw)
    if outcome["ok"]:
        say("🟢", "OK", f"{outcome['result']}", "green")
        return outcome["result"]

    say("🔴", "SENSE", f"{outcome['kind']}", "red")
    for line in outcome["detail"].strip().splitlines()[-3:]:
        print(f"   {C['dim']}{line}{C['end']}")
    started = time.time()
    fixed = heal(code, raw, outcome)
    if fixed is None:
        say("🛑", "GIVE UP", "could not produce a verified fix. Escalating to a human.", "red")
        return {"status": "error", "message": "The weather parser broke and automatic repair failed. A human must look at it.",
                "incident": outcome["kind"]}

    say("🧪", "VERIFY", "✓ new payload passes the contract · ✓ old payloads still work", "green")
    say("💊", "PATCH", "proposed change:")
    show_diff(code, fixed)
    if not AUTO_APPLY and input("   Apply this patch? [y/N] ").strip().lower() != "y":
        return {"status": "error", "message": "A repair was proposed but a human declined it."}
    PARSER_FILE.with_suffix(".py.bak").write_text(code)  # always keep a way back
    PARSER_FILE.write_text(fixed)

    again = sense(fixed, raw)
    if not again["ok"]:  # paranoia: re-run the real thing after applying
        PARSER_FILE.write_text(code)
        return {"status": "error", "message": "Patch failed on re-check and was rolled back."}
    say("✅", "HEALED", f"in {time.time() - started:.1f}s → {again['result']}", "green")
    return again["result"]
