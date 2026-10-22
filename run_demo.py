"""Simplest demo (no ADK, no chat): call the self-healing tool once.

    python reset.py
    python run_demo.py --api v2                         # break it, watch it heal
    python run_demo.py --api v3                         # a trickier break
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # must happen BEFORE importing the harness
if "--api" in sys.argv:  # cross-platform: `python run_demo.py --api v2` (no env-var syntax needed)
    os.environ["VENDOR_API_VERSION"] = sys.argv[sys.argv.index("--api") + 1]

from harness.healer import get_weather_with_healing  # noqa: E402

print(get_weather_with_healing("Lisbon"))
