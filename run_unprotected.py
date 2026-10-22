"""ACT 1 · BREAK IT. No harness, no model: just the plain pipeline everyone has shipped.

    python run_unprotected.py                 # v1: works
    python run_unprotected.py --api v2        # the vendor changed its format → 💥
"""
import os
import sys

if "--api" in sys.argv:  # cross-platform way to pick the vendor version (works in PowerShell/cmd too)
    os.environ["VENDOR_API_VERSION"] = sys.argv[sys.argv.index("--api") + 1]

from app.vendor_api import fetch_weather
from app.weather_parser import parse_weather

print(parse_weather(fetch_weather("Lisbon")))
