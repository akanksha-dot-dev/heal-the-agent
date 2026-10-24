"""PRE-FLIGHT CHECK. Run this the day before:   python check_setup.py
Prints ✅ / ⚠️ / ❌ for each thing the workshop needs. Only the first four are REQUIRED."""
import importlib.metadata as md
import json
import os
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

required_ok = True


def show(ok, label, hint="", required=True):
    global required_ok
    icon = "✅" if ok else ("❌" if required else "⚠️ ")
    print(f"{icon} {label}" + (f"\n     → {hint}" if hint and not ok else ""))
    if required and not ok:
        required_ok = False


show(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (need 3.11+)",
     "Install uv (https://docs.astral.sh/uv/) and run `uv sync`, or use the Colab link in the README")
try:
    show(True, f"google-adk {md.version('google-adk')} installed")
except md.PackageNotFoundError:
    show(False, "google-adk installed", "pip install -r requirements.txt")
key = os.getenv("GOOGLE_API_KEY", "")
show(bool(key), "GOOGLE_API_KEY found", "copy .env.example to .env and paste your key from https://aistudio.google.com/apikey")

working_model = None
if key:
    try:
        from google import genai
        client = genai.Client()
        for name in [os.getenv("AGENT_MODEL", ""), "gemini-flash-lite-latest", "gemini-flash-latest"]:
            if not name:
                continue
            try:
                text = client.models.generate_content(model=name, contents="Reply with the single word: pong").text
                working_model = name
                print(f"✅ Gemini answered from '{name}': {text.strip()[:20]!r}")
                break
            except Exception as e:  # noqa: BLE001
                print(f"   (model '{name}' failed: {str(e)[:90]})")
    except Exception as e:  # noqa: BLE001
        print(f"   (could not start Gemini client: {e})")
show(working_model is not None, "A Gemini model works with your key",
     "Check the key, your network, or the model name (names change!). Ask in the chat with this output.")

# ---- optional ----
try:
    with urllib.request.urlopen(os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/api/tags", timeout=2) as r:
        names = [m["name"] for m in json.load(r)["models"]]
    show(True, f"Ollama is running; models: {', '.join(names) or '(none pulled yet)'}")
    show(any("gemma4" in n for n in names), "a local model is pulled (optional)",
         "ollama pull gemma4:e4b   (several GB! do it on home wifi)", required=False)
except Exception:
    show(False, "Ollama is running (OPTIONAL: the workshop works without it)", "install from https://ollama.com", required=False)

print("\n" + ("🎉 You're ready. See you at the workshop!" if required_ok else "🛠  Fix the ❌ items (or just use the Colab path in the README)."))
sys.exit(0 if required_ok else 1)
