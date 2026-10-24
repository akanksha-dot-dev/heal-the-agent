"""PRESENTER'S REHEARSAL TEST (offline, no API key, uses recordings).
Run it the morning of the workshop:   python selftest.py     -> must end with ALL GREEN.
It tests the COMPLETE solution (solutions/healer.py), not the student skeleton."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LOAD = ("import importlib.util as u; s=u.spec_from_file_location('h','solutions/healer.py'); "
        "m=u.module_from_spec(s); s.loader.exec_module(m); ")


def scenario(name, env, code, must_contain, must_not_contain=()):
    subprocess.run([sys.executable, "reset.py"], cwd=ROOT, capture_output=True)
    e = {**os.environ, "DOCTOR_CASCADE": "replay", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", **env}
    e.pop("GOOGLE_API_KEY", None)
    out = subprocess.run([sys.executable, "-c", LOAD + code], cwd=ROOT, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace")
    text = (out.stdout + out.stderr)
    ok = all(s in text for s in must_contain) and not any(s in text for s in must_not_contain)
    print(("✅" if ok else "❌"), name)
    if not ok:
        print(text[-1200:])
    return ok


def skeleton_is_really_a_skeleton():
    sk = open(os.path.join(ROOT, "harness", "healer.py"), encoding="utf-8").read()
    ok = sk.count("NotImplementedError") == 3 and "STARTER: ONE attempt" in sk
    print(("✅" if ok else "❌"), "student skeleton (harness/healer.py) still has its TODOs (Ex1-3 stubs + Ex4 one-shot starter)")
    return ok


results = [
    skeleton_is_really_a_skeleton(),
    scenario("v1: healthy, no repair needed", {"VENDOR_API_VERSION": "v1"},
             "print(m.get_weather_with_healing('Lisbon'))", ["OK", "'temp_c': 31.2"], ["SENSE"]),
    scenario("v2: crash is detected, diagnosed, patched, verified", {"VENDOR_API_VERSION": "v2"},
             "print(m.get_weather_with_healing('Lisbon'))", ["SENSE", "HEALED", "'temp_c': 31.2"]),
    scenario("v3: first patch is wrong-but-plausible, verifier rejects, 2nd attempt heals", {"VENDOR_API_VERSION": "v3"},
             "print(m.get_weather_with_healing('Lisbon'))", ["rejected", "HEALED", "'temp_c': 31.2"]),
    scenario("give-up path: leaves the file untouched and says so", {"VENDOR_API_VERSION": "v3", "MAX_ATTEMPTS": "1"},
             "print(m.get_weather_with_healing('Lisbon'))", ["GIVE UP", "'status': 'error'"], ["HEALED"]),
    scenario("hole: a hard-coded 'cheat' patch FOOLS the weak verifier", {"VENDOR_API_VERSION": "v2", "REPLAY_CASSETTE": "v2-cheat"},
             "m.get_weather_with_healing('Lisbon'); print(m.get_weather_with_healing('Oslo'))", ["'city': 'Lisbon'"]),
    scenario("fix: ANTI_CHEAT=1 rejects the cheat and heals properly", {"VENDOR_API_VERSION": "v2", "REPLAY_CASSETTE": "v2-cheat", "ANTI_CHEAT": "1"},
             "print(m.get_weather_with_healing('Oslo'))", ["anti-cheat", "'city': 'Oslo'"]),
    scenario("guardrail: malicious patch (import os) is blocked", {"VENDOR_API_VERSION": "v2"},
             "print(m.verify('import os\\ndef parse_weather(raw):\\n    return {}', {}))", ["not allowed"]),
]
subprocess.run([sys.executable, "reset.py"], cwd=ROOT, capture_output=True)
print("\n" + ("🎉 ALL GREEN" if all(results) else "🛑 SOMETHING IS BROKEN. Don't go on stage until this is green."))
sys.exit(0 if all(results) else 1)
