"""🩺 LIVE DASHBOARD — watch the agent heal itself in your browser.

    python dashboard.py                    # default: localhost:8765
    python dashboard.py --port 9000        # custom port

Opens automatically. Click [BREAK IT] → [HEAL IT] and watch.
"""
import http.server
import json
import os
import io
import re
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ── bootstrap ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from app.vendor_api import fetch_weather
from app.contract import contract_violations, KNOWN_GOOD
from harness.guardrails import run_sandboxed, static_check
from harness.llm import ask, ModelUnavailable
from harness.prompts import DOCTOR_PROMPT, history_block

PARSER_FILE = ROOT / "app" / "weather_parser.py"
ORIGINAL    = ROOT / "app" / "weather_parser.ORIGINAL.py"
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "3"))
CASCADE = [m.strip() for m in os.getenv("DOCTOR_CASCADE", "gemini-flash-lite-latest").split(",") if m.strip()]

# ── healing engine (produces step-by-step events) ────────────────
def run_healing(api_version: str):
    """Generator that yields JSON-serialisable step dicts."""
    os.environ["VENDOR_API_VERSION"] = api_version

    # Reset parser
    import shutil
    shutil.copy(ORIGINAL, PARSER_FILE)
    PARSER_FILE.with_suffix(".py.bak").unlink(missing_ok=True)

    code_before = PARSER_FILE.read_text(encoding="utf-8")
    yield {"step": "init", "code_before": code_before, "api_version": api_version}

    # Fetch
    raw = fetch_weather("Lisbon")
    yield {"step": "fetch", "payload": raw}

    # Sense
    outcome = _sense(code_before, raw)
    yield {"step": "sense", "outcome": outcome}
    if outcome["ok"]:
        yield {"step": "done", "result": outcome["result"], "healed": False, "code_after": code_before}
        return

    # Heal loop
    failures = []
    cascade = list(CASCADE)
    attempt = 0
    code_after = None

    while attempt < MAX_ATTEMPTS and cascade:
        model = cascade[0]
        yield {"step": "diagnose_start", "model": model, "attempt": attempt + 1, "max": MAX_ATTEMPTS}

        prompt = DOCTOR_PROMPT.format(
            code=code_before, kind=outcome["kind"],
            detail=outcome["detail"].strip(),
            payload=json.dumps(raw, indent=2),
            history=history_block(failures),
        )

        try:
            reply = ask(prompt, model)
        except ModelUnavailable as e:
            yield {"step": "model_skip", "model": model, "reason": str(e)}
            cascade.pop(0)
            continue

        attempt += 1
        diagnosis = reply.split("```")[0].strip() or "(no diagnosis)"
        match = re.search(r"```(?:python|py)?\s*\n(.*?)```", reply, re.DOTALL)
        candidate = match.group(1).strip() + "\n" if match else None

        yield {"step": "diagnose_done", "diagnosis": diagnosis, "has_code": candidate is not None}

        if candidate is None:
            problems = ["no ```python block in reply"]
        else:
            problems = _verify(candidate, raw)

        if problems:
            yield {"step": "verify_fail", "problems": problems, "attempt": attempt}
            failures.append(f"attempt {attempt} ({model}): {' | '.join(problems)}")
            if len(cascade) > 1:
                cascade.pop(0)
            continue

        code_after = candidate
        yield {"step": "verify_pass", "attempt": attempt}
        break

    if code_after is None:
        yield {"step": "give_up"}
        return

    # Apply patch
    PARSER_FILE.with_suffix(".py.bak").write_text(code_before, encoding="utf-8")
    PARSER_FILE.write_text(code_after, encoding="utf-8")

    # Compute diff lines
    import difflib
    diff_lines = list(difflib.unified_diff(
        code_before.splitlines(), code_after.splitlines(),
        "before", "after", lineterm="", n=2
    ))
    yield {"step": "done", "healed": True, "code_before": code_before,
           "code_after": code_after, "diff": diff_lines,
           "result": _sense(code_after, raw).get("result", {})}


def _sense(code, raw):
    out = run_sandboxed(code, [raw])
    if "timeout" in out:
        return {"ok": False, "kind": "timeout", "detail": "parser timed out"}
    if "load_error" in out:
        return {"ok": False, "kind": "exception", "detail": out["load_error"]}
    first = out["results"][0]
    if not first["ok"]:
        return {"ok": False, "kind": "exception", "detail": first["traceback"]}
    problems = contract_violations(first["result"])
    if problems:
        return {"ok": False, "kind": "contract violation", "detail": "; ".join(problems)}
    return {"ok": True, "result": first["result"]}


def _verify(candidate, raw):
    problems = static_check(candidate)
    if problems:
        return problems
    payloads = [raw] + [old for old, _ in KNOWN_GOOD]
    out = run_sandboxed(candidate, payloads)
    if "timeout" in out:
        return ["patched code timed out"]
    if "load_error" in out:
        return [f"load error: {out['load_error'].strip().splitlines()[-1]}"]
    new, *old_results = out["results"]
    if not new["ok"]:
        return [f"still crashes: {new['traceback'].strip().splitlines()[-1]}"]
    problems += contract_violations(new["result"])
    for (old_raw, expected), r in zip(KNOWN_GOOD, old_results):
        if not r["ok"] or r["result"] != expected:
            problems.append(f"regression on {old_raw['city']}")
    return problems


# ── HTTP server ──────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🩺 Heal the Agent — Live Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:        #0d1117;
    --surface:   #161b22;
    --surface2:  #1c2333;
    --border:    #30363d;
    --text:      #e6edf3;
    --text-dim:  #8b949e;
    --accent:    #58a6ff;
    --green:     #3fb950;
    --red:       #f85149;
    --orange:    #d29922;
    --purple:    #bc8cff;
    --cyan:      #39d353;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Header ── */
  .header {
    background: linear-gradient(135deg, #161b22 0%, #1a1f2e 100%);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header h1 {
    font-size: 20px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .header h1 span { font-size: 26px; }
  .header .tagline {
    color: var(--text-dim);
    font-size: 13px;
    font-weight: 400;
  }
  .equation {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: var(--accent);
  }

  /* ── Main layout ── */
  .main {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 0;
    height: calc(100vh - 65px);
  }

  /* ── Sidebar ── */
  .sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  .sidebar h2 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    margin-bottom: 8px;
  }
  .version-btns {
    display: flex;
    gap: 8px;
  }
  .version-btns button {
    flex: 1;
    padding: 10px 0;
    border: 2px solid var(--border);
    border-radius: 8px;
    background: var(--surface2);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .version-btns button:hover { border-color: var(--accent); background: #1c2940; }
  .version-btns button.active { border-color: var(--accent); background: #1c2940; color: var(--accent); }
  .version-btns button.v2 { border-color: var(--orange); color: var(--orange); }
  .version-btns button.v3 { border-color: var(--red); color: var(--red); }

  .action-btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  .action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .break-btn { background: linear-gradient(135deg, #da3633, #f85149); color: white; }
  .break-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(248,81,73,0.3); }
  .heal-btn { background: linear-gradient(135deg, #238636, #3fb950); color: white; }
  .heal-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(63,185,80,0.3); }
  .reset-btn { background: var(--surface2); color: var(--text-dim); border: 1px solid var(--border); }
  .reset-btn:hover:not(:disabled) { color: var(--text); border-color: var(--accent); }

  /* ── Pipeline ── */
  .content { padding: 24px 32px; overflow-y: auto; }

  .pipeline {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 24px;
  }
  .pipe-step {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    font-size: 13px;
    font-weight: 600;
    transition: all 0.4s;
    white-space: nowrap;
  }
  .pipe-step .icon { font-size: 18px; }
  .pipe-arrow { color: var(--text-dim); font-size: 18px; padding: 0 2px; }
  .pipe-step.active { border-color: var(--accent); background: #1c2940; box-shadow: 0 0 20px rgba(88,166,255,0.15); }
  .pipe-step.pass { border-color: var(--green); background: #0d2818; }
  .pipe-step.fail { border-color: var(--red); background: #2d1215; }

  /* ── Log ── */
  .log-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 24px;
    overflow: hidden;
  }
  .log-panel h3 {
    padding: 12px 18px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-dim);
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
  }
  .log-content {
    padding: 16px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.7;
    max-height: 200px;
    overflow-y: auto;
  }
  .log-entry { padding: 3px 0; display: flex; align-items: flex-start; gap: 8px; }
  .log-entry .ts { color: var(--text-dim); min-width: 52px; }
  .log-entry.sense { color: var(--red); }
  .log-entry.diagnose { color: var(--orange); }
  .log-entry.verify-pass { color: var(--green); }
  .log-entry.verify-fail { color: var(--red); }
  .log-entry.healed { color: var(--green); font-weight: 600; }
  .log-entry.info { color: var(--text-dim); }
  .log-entry.skip { color: var(--text-dim); font-style: italic; }

  /* ── Code panels ── */
  .code-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .code-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }
  .code-panel h3 {
    padding: 10px 18px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-dim);
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .code-panel h3 .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .dot-red { background: var(--red); }
  .dot-green { background: var(--green); }
  .code-panel pre {
    padding: 16px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    line-height: 1.65;
    overflow-x: auto;
    white-space: pre;
    color: var(--text);
    max-height: 300px;
    overflow-y: auto;
  }

  /* ── Diff ── */
  .diff-panel pre .add { color: var(--green); background: rgba(63,185,80,0.1); display: block; }
  .diff-panel pre .del { color: var(--red); background: rgba(248,81,73,0.1); display: block; }
  .diff-panel pre .hdr { color: var(--purple); display: block; }
  .diff-panel pre .ctx { color: var(--text-dim); display: block; }

  /* ── Result banner ── */
  .result-banner {
    padding: 20px 24px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    display: none;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    animation: slideIn 0.4s ease;
  }
  @keyframes slideIn { from { opacity:0; transform:translateY(-10px); } to { opacity:1; transform:translateY(0); } }
  .result-banner.healed {
    display: flex;
    background: linear-gradient(135deg, #0d2818, #132f1e);
    border: 1px solid var(--green);
    color: var(--green);
  }
  .result-banner.failed {
    display: flex;
    background: linear-gradient(135deg, #2d1215, #3d1519);
    border: 1px solid var(--red);
    color: var(--red);
  }
  .result-banner.ok {
    display: flex;
    background: linear-gradient(135deg, #0c2d48, #133a57);
    border: 1px solid var(--accent);
    color: var(--accent);
  }
  .result-banner .icon { font-size: 28px; }
  .result-banner .time { color: var(--text-dim); font-weight: 400; font-size: 13px; margin-left: auto; }

  /* ── Payload display ── */
  .payload-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
  }
  .payload-panel pre {
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--orange);
  }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1><span>🩺</span> Heal the Agent <span style="font-weight:400;color:var(--text-dim);font-size:14px;">— Live Dashboard</span></h1>
  </div>
  <div class="equation">Agent = Model + Harness</div>
</div>

<div class="main">
  <div class="sidebar">
    <div>
      <h2>Vendor API Version</h2>
      <div class="version-btns">
        <button id="btn-v1" onclick="setVersion('v1')" class="active">v1</button>
        <button id="btn-v2" onclick="setVersion('v2')">v2</button>
        <button id="btn-v3" onclick="setVersion('v3')">v3</button>
      </div>
    </div>
    <div>
      <h2>Actions</h2>
      <button class="action-btn break-btn" id="btn-break" onclick="doBreak()">💥 Break It</button>
      <div style="height:10px"></div>
      <button class="action-btn heal-btn" id="btn-heal" onclick="doHeal()" disabled>🩺 Heal It</button>
      <div style="height:10px"></div>
      <button class="action-btn reset-btn" onclick="doReset()">↺ Reset</button>
    </div>
    <div>
      <h2>Status</h2>
      <div id="status-text" style="font-size:13px;color:var(--text-dim);">Ready. Pick a version and click Break It.</div>
    </div>
    <div style="margin-top:auto; border-top:1px solid var(--border); padding-top:16px;">
      <div style="font-size:11px; color:var(--text-dim); line-height:1.6;">
        <strong style="color:var(--text);">Tip for workshop:</strong><br>
        Also open <code>app/weather_parser.py</code> in your editor to watch the code change on disk!
      </div>
    </div>
  </div>

  <div class="content">
    <!-- Pipeline -->
    <div class="pipeline">
      <div class="pipe-step" id="ps-sense"><span class="icon">🔍</span> Sense</div>
      <span class="pipe-arrow">→</span>
      <div class="pipe-step" id="ps-diagnose"><span class="icon">🩺</span> Diagnose</div>
      <span class="pipe-arrow">→</span>
      <div class="pipe-step" id="ps-verify"><span class="icon">🧪</span> Verify</div>
      <span class="pipe-arrow">→</span>
      <div class="pipe-step" id="ps-patch"><span class="icon">💊</span> Patch</div>
    </div>

    <!-- Result banner -->
    <div class="result-banner" id="result-banner">
      <span class="icon" id="result-icon"></span>
      <span id="result-text"></span>
      <span class="time" id="result-time"></span>
    </div>

    <!-- Log -->
    <div class="log-panel">
      <h3>Healing Log</h3>
      <div class="log-content" id="log"></div>
    </div>

    <!-- Code -->
    <div class="code-grid" id="code-grid" style="display:none;">
      <div class="code-panel">
        <h3><span class="dot dot-red"></span> Before (broken)</h3>
        <pre id="code-before"></pre>
      </div>
      <div class="code-panel diff-panel">
        <h3><span class="dot dot-green"></span> After (healed)</h3>
        <pre id="code-after"></pre>
      </div>
    </div>
  </div>
</div>

<script>
let currentVersion = 'v1';
let running = false;

function setVersion(v) {
  currentVersion = v;
  document.querySelectorAll('.version-btns button').forEach(b => {
    b.className = b.id === 'btn-' + v ? 'active' : '';
    if (v === 'v2' && b.id === 'btn-v2') b.classList.add('v2');
    if (v === 'v3' && b.id === 'btn-v3') b.classList.add('v3');
  });
}

function log(msg, cls = '') {
  const el = document.getElementById('log');
  const ts = new Date().toLocaleTimeString('en', {hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit'});
  el.innerHTML += `<div class="log-entry ${cls}"><span class="ts">${ts}</span><span>${msg}</span></div>`;
  el.scrollTop = el.scrollHeight;
}

function resetPipeline() {
  ['sense','diagnose','verify','patch'].forEach(s => {
    const el = document.getElementById('ps-' + s);
    el.className = 'pipe-step';
  });
  const b = document.getElementById('result-banner');
  b.className = 'result-banner';
  b.style.display = 'none';
  document.getElementById('code-grid').style.display = 'none';
}

function setPipeStep(name, state) {
  document.getElementById('ps-' + name).className = 'pipe-step ' + state;
}

async function doBreak() {
  if (running) return;
  resetPipeline();
  document.getElementById('log').innerHTML = '';
  log(`💥 Breaking with vendor API ${currentVersion}...`, 'sense');

  const res = await fetch('/api/break?v=' + currentVersion);
  const data = await res.json();

  if (data.ok) {
    log(`✅ v${currentVersion}: parser works fine — nothing to heal!`, 'verify-pass');
    setPipeStep('sense', 'pass');
    showBanner('ok', '🟢', `v${currentVersion}: Parser works correctly — no healing needed`, '');
    document.getElementById('btn-heal').disabled = true;
    document.getElementById('status-text').textContent = 'Parser is healthy. Try v2 or v3 to break it.';
  } else {
    log(`🔴 ${data.kind}: ${data.detail}`, 'sense');
    setPipeStep('sense', 'fail');
    document.getElementById('btn-heal').disabled = false;
    document.getElementById('status-text').textContent = 'Parser is BROKEN. Click Heal It!';
    showBanner('failed', '💥', `BROKEN — ${data.kind}`, '');
  }
}

async function doHeal() {
  if (running) return;
  running = true;
  document.getElementById('btn-heal').disabled = true;
  document.getElementById('btn-break').disabled = true;
  document.getElementById('status-text').textContent = 'Healing in progress...';

  resetPipeline();
  document.getElementById('log').innerHTML = '';
  log('🔄 Starting self-healing pipeline...', 'info');
  const start = performance.now();

  try {
    const res = await fetch('/api/heal?v=' + currentVersion);
    const data = await res.json();

    for (const step of data.steps) {
      await sleep(200); // pace the visual updates
      processStep(step);
    }

    const elapsed = ((performance.now() - start) / 1000).toFixed(1);
    const lastStep = data.steps[data.steps.length - 1];

    if (lastStep.step === 'done' && lastStep.healed) {
      showBanner('healed', '✅', `HEALED — ${JSON.stringify(lastStep.result)}`, `${elapsed}s`);
      document.getElementById('status-text').textContent = `Healed in ${elapsed}s!`;
      // Show code
      document.getElementById('code-grid').style.display = 'grid';
      document.getElementById('code-before').textContent = lastStep.code_before;
      if (lastStep.diff) {
        document.getElementById('code-after').innerHTML = lastStep.diff.map(line => {
          if (line.startsWith('+') && !line.startsWith('+++'))
            return `<span class="add">${esc(line)}</span>`;
          if (line.startsWith('-') && !line.startsWith('---'))
            return `<span class="del">${esc(line)}</span>`;
          if (line.startsWith('@@'))
            return `<span class="hdr">${esc(line)}</span>`;
          return `<span class="ctx">${esc(line)}</span>`;
        }).join('');
      }
    } else if (lastStep.step === 'done' && !lastStep.healed) {
      showBanner('ok', '🟢', 'Parser was already healthy', '');
      document.getElementById('status-text').textContent = 'No healing needed.';
    } else {
      showBanner('failed', '🛑', 'Could not produce a verified fix', `${elapsed}s`);
      document.getElementById('status-text').textContent = 'Healing failed. Try resetting and healing again.';
    }
  } catch (e) {
    log('❌ Error: ' + e.message, 'sense');
    document.getElementById('status-text').textContent = 'Error: ' + e.message;
  }

  running = false;
  document.getElementById('btn-break').disabled = false;
}

function processStep(s) {
  switch (s.step) {
    case 'init':
      log(`📄 Parser loaded (${s.api_version})`, 'info');
      break;
    case 'fetch':
      log(`📡 Vendor payload: ${JSON.stringify(s.payload)}`, 'info');
      break;
    case 'sense':
      setPipeStep('sense', s.outcome.ok ? 'pass' : 'fail');
      if (!s.outcome.ok) log(`🔴 SENSE: ${s.outcome.kind} — ${s.outcome.detail}`, 'sense');
      else log('🟢 SENSE: parser is healthy', 'verify-pass');
      break;
    case 'diagnose_start':
      setPipeStep('diagnose', 'active');
      log(`🩺 DIAGNOSE: asking ${s.model} (attempt ${s.attempt}/${s.max})`, 'diagnose');
      break;
    case 'model_skip':
      log(`⏭️ SKIP: ${s.model} — ${s.reason}`, 'skip');
      break;
    case 'diagnose_done':
      log(`💬 DIAGNOSIS: ${s.diagnosis}`, 'diagnose');
      setPipeStep('diagnose', 'pass');
      setPipeStep('verify', 'active');
      break;
    case 'verify_fail':
      setPipeStep('verify', 'fail');
      log(`🧪 VERIFY ✗ rejected: ${s.problems.join(' | ')}`, 'verify-fail');
      setPipeStep('diagnose', '');
      setPipeStep('verify', '');
      break;
    case 'verify_pass':
      setPipeStep('verify', 'pass');
      setPipeStep('patch', 'pass');
      log('🧪 VERIFY ✓ new payload passes · old payloads still work', 'verify-pass');
      log('💊 PATCH applied — parser file rewritten on disk', 'healed');
      break;
    case 'give_up':
      log('🛑 GIVE UP: could not produce a verified fix', 'sense');
      break;
  }
}

function showBanner(cls, icon, text, time) {
  const b = document.getElementById('result-banner');
  b.className = 'result-banner ' + cls;
  b.style.display = 'flex';
  document.getElementById('result-icon').textContent = icon;
  document.getElementById('result-text').textContent = text;
  document.getElementById('result-time').textContent = time;
}

async function doReset() {
  await fetch('/api/reset');
  resetPipeline();
  document.getElementById('log').innerHTML = '';
  document.getElementById('btn-heal').disabled = true;
  document.getElementById('status-text').textContent = 'Reset. Pick a version and break it.';
  log('↺ Parser reset to original', 'info');
  setVersion('v1');
}

function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
</script>
</body>
</html>
"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html(HTML_PAGE)
        elif parsed.path == "/api/break":
            self._api_break(parse_qs(parsed.query))
        elif parsed.path == "/api/heal":
            self._api_heal(parse_qs(parsed.query))
        elif parsed.path == "/api/reset":
            self._api_reset()
        else:
            self.send_error(404)

    def _html(self, content):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _api_break(self, qs):
        v = qs.get("v", ["v1"])[0]
        os.environ["VENDOR_API_VERSION"] = v
        import shutil
        shutil.copy(ORIGINAL, PARSER_FILE)
        PARSER_FILE.with_suffix(".py.bak").unlink(missing_ok=True)
        code = PARSER_FILE.read_text(encoding="utf-8")
        raw = fetch_weather("Lisbon")
        result = _sense(code, raw)
        self._json(result)

    def _api_heal(self, qs):
        v = qs.get("v", ["v2"])[0]
        steps = list(run_healing(v))
        self._json({"steps": steps})

    def _api_reset(self):
        import shutil
        shutil.copy(ORIGINAL, PARSER_FILE)
        PARSER_FILE.with_suffix(".py.bak").unlink(missing_ok=True)
        os.environ["VENDOR_API_VERSION"] = "v1"
        self._json({"ok": True})

    def log_message(self, fmt, *args):
        pass  # suppress noisy access logs


def main():
    port = 8765
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"🩺 Dashboard running at {url}")
    print(f"   Press Ctrl+C to stop.\n")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
