"""Put the parser back to its original (v1-only) state. Run before every demo/rehearsal."""
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

here = Path(__file__).parent / "app"
shutil.copy(here / "weather_parser.ORIGINAL.py", here / "weather_parser.py")
(here / "weather_parser.py.bak").unlink(missing_ok=True)
print("↺ parser reset to original. Now run with VENDOR_API_VERSION=v2 to break it.")
