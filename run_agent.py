"""Run the ADK agent from a script:   python run_agent.py "What's the weather in Lisbon?"
(Works on Windows too: --api v2 instead of VENDOR_API_VERSION=v2.  In a notebook, replace asyncio.run(...) with `await ...`.)"""
import asyncio
import os
import sys

from dotenv import load_dotenv

if "--api" in sys.argv:  # e.g. python run_agent.py --api v2 "What is the weather in Lisbon?"
    i = sys.argv.index("--api"); os.environ["VENDOR_API_VERSION"] = sys.argv[i + 1]; del sys.argv[i:i + 2]

from google.adk.runners import InMemoryRunner  # noqa: E402

from weather_desk.agent import root_agent  # noqa: E402


async def main(question: str) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="weather_desk")
    await runner.run_debug(question)  # prints the conversation, tool calls and all


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What's the weather in Lisbon?"))
