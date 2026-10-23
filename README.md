# 🩺 Heal the Agent — a 60-minute workshop starter

An AI agent whose *tool* breaks when a vendor API changes, and a **harness** that
**detects → diagnoses → patches → verifies** the fix on its own.

> **Agent = Model + Harness.** The model only writes text. Everything else is `harness/healer.py`.

## Pick ONE setup path (A is the safest)

**A · Colab (zero install).** Open a new notebook at colab.research.google.com, then:
```python
# cell 1
!git clone https://github.com/akanksha-dot-dev/heal-the-agent && cd heal-the-agent && pip -q install -r requirements.txt
# cell 2  (add GOOGLE_API_KEY in the 🔑 Secrets panel and enable notebook access)
import os, sys; from google.colab import userdata
os.chdir("heal-the-agent"); sys.path.insert(0, ".")
os.environ["GOOGLE_API_KEY"] = userdata.get("GOOGLE_API_KEY")
# cell 3
!python check_setup.py
```
*(These cells are untested in Colab from where this was written: rehearse them once.)*

**B · Your laptop with `uv`** (handles the Python-version problem for you; ADK needs 3.11+):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # Windows: see docs.astral.sh/uv
git clone https://github.com/akanksha-dot-dev/heal-the-agent && cd heal-the-agent
uv sync && cp .env.example .env                         # then paste your key into .env
uv run python check_setup.py
```

**C · pip:** `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## The 60-second tour
```bash
python reset.py                                  # parser back to its original v1-only state
python run_demo.py                               # v1: everything works (needs Exercises 1-3 done, or the solution)
python run_unprotected.py --api v2               # ACT 1: no harness, just the crash 💥
python run_demo.py --api v2                      # the vendor changed its format → watch it heal
python run_demo.py --api v3                      # trickier: first fix looks right but is WRONG
python dashboard.py                              # 🖥️ live web dashboard — break & heal in your browser
adk web .                                        # (local only) chat UI with traces → pick "weather_desk"
python run_agent.py --api v2 "What's the weather in Lisbon?"
```

## Files
| File | Role |
|---|---|
| `app/vendor_api.py` | the pretend vendor (v1/v2/v3 formats, offline on purpose) |
| `app/weather_parser.py` | **the patient**. This is the file the agent rewrites |
| `app/contract.py` | what a *correct* result looks like (+ known-good regression cases) |
| `harness/healer.py` | **the harness. Students complete 4 TODOs here** (skeleton) |
| `solutions/healer.py` | the finished harness (`cp solutions/healer.py harness/healer.py` to catch up) |
| `harness/llm.py` | model adapter: Gemini · Ollama (plain HTTP) · `replay` (recording) |
| `harness/guardrails.py` | AST allow-list + subprocess sandbox for model-written code |
| `weather_desk/agent.py` | the ADK agent (an agent = a model that chooses to call tools) |
| `cassettes/doctor.json` | pre-recorded doctor answers for offline mode |
| `dashboard.py` | 🖥️ live web dashboard — visual Break It → Heal It pipeline |
| `check_setup.py` | pre-flight check for participants · `selftest.py` for the presenter |
| `slides/` | workshop delivery guide with slide content + presenter script |

## Model cascade (local + cloud in one run)
`DOCTOR_CASCADE=ollama/gemma4:e4b,gemini-flash-lite-latest` tries the local model first; a failed
verification (or an unreachable Ollama) hands the job to the cloud model. No Ollama? It is skipped automatically.

## 🖥️ Live Dashboard
```bash
python dashboard.py                 # opens localhost:8765 automatically
```
A visual web UI where you pick a vendor version (v1/v2/v3), click **Break It** to crash the parser,
then **Heal It** to watch the full pipeline — Sense → Diagnose → Verify → Patch — with real-time logs,
a success banner, and a side-by-side before/after code diff. Great for presenting to an audience.

**Tip:** Also open `app/weather_parser.py` in a split pane to watch the file change on disk.

## ⚠️ Safety
The harness runs model-written code. The guardrails are a **speed bump, not a security boundary**.
Run workshops on throwaway environments (Colab is one). Never commit `.env`.
