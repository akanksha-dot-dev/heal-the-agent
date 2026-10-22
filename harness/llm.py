"""THE MODEL ADAPTER: one function, `ask(prompt, model) -> str`.

Everything model-specific lives here, so the rest of the harness never cares
whether the brain is a cloud model, a local model, or a recording.

  "gemini-flash-lite-latest"   -> Gemini API (cloud, needs GOOGLE_API_KEY)
  "ollama/gemma4:e4b"          -> Ollama on YOUR laptop (plain HTTP to localhost:11434)
  "replay"                     -> pre-recorded answers (offline stage prop; see cassettes/)

The doctor model only has to turn TEXT into TEXT. No tool-calling needed, which is
exactly what makes small local models usable here.
"""
import json
import os
import time
import urllib.error
import urllib.request


class ModelUnavailable(Exception):
    """The model can't be reached at all (not installed, no key, offline). Skip it, don't retry it."""


def ask(prompt: str, model: str) -> str:
    if model == "replay":
        return _ask_replay(prompt)
    if model.startswith("ollama/"):
        return _ask_ollama(prompt, model.split("/", 1)[1])
    return _ask_gemini(prompt, model)


# ---------- cloud: Gemini ----------
def _ask_gemini(prompt: str, model: str) -> str:
    if not os.getenv("GOOGLE_API_KEY"):
        raise ModelUnavailable("GOOGLE_API_KEY is not set")
    from google import genai  # imported lazily so 'replay' mode needs no network libs

    client = genai.Client()  # reads GOOGLE_API_KEY from the environment
    delay = 2.0
    for attempt in range(4):
        try:
            return client.models.generate_content(model=model, contents=prompt).text or ""
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if isinstance(e, OSError) or type(e).__name__ in {"ConnectError", "ConnectTimeout", "ReadTimeout", "TimeoutException"}:
                raise ModelUnavailable(f"can't reach Gemini ({type(e).__name__}): are you online?") from e
            if "API_KEY_INVALID" in msg or "PERMISSION_DENIED" in msg or "UNAUTHENTICATED" in msg:
                raise ModelUnavailable("Gemini rejected the API key") from e
            if "NOT_FOUND" in msg or "404" in msg:
                raise ModelUnavailable(f"model '{model}' not found for this key (names change often!)") from e
            if ("429" in msg or "RESOURCE_EXHAUSTED" in msg) and attempt < 3:
                print(f"   ⏳ rate-limited by Gemini; waiting {delay:.0f}s and retrying...")
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return ""


# ---------- local: Ollama (it's just an HTTP server!) ----------
def _ask_ollama(prompt: str, model: str) -> str:
    base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    body = json.dumps({"model": model, "stream": False,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(f"{base}/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.load(resp)["message"]["content"]
    except urllib.error.HTTPError as e:
        raise ModelUnavailable(f"Ollama says {e.code} (is '{model}' pulled? try: ollama pull {model})") from e
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ModelUnavailable(f"can't reach Ollama at {base} ({e})") from e


# ---------- offline: replay a recording ----------
_replay_counter = {"n": 0}


def _ask_replay(prompt: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "cassettes", "doctor.json")
    with open(path) as f:
        cassette = json.load(f)
    key = os.getenv("REPLAY_CASSETTE") or os.getenv("VENDOR_API_VERSION", "v1")
    replies = cassette.get(key)
    if not replies:
        raise ModelUnavailable(f"no recording named {key!r}")
    i = min(_replay_counter["n"], len(replies) - 1)
    _replay_counter["n"] += 1
    print("   📼 (REPLAY: this answer is pre-recorded, not a live model)")
    return replies[i]
