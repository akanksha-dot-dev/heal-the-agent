"""The ADK agent. This is the part that makes it an AGENT and not a chatbot:
it decides on its own to call a tool, reads the result, and answers.

Notice what the agent does NOT know: that the tool is wrapped in a self-healing harness.
When the vendor API changes, the repair happens INSIDE the tool call, and the agent
just gets a correct answer a few seconds later.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from harness.healer import get_weather_with_healing  # noqa: E402  (after .env so keys are visible)


def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: The city name, for example "Lisbon".

    Returns:
        A dict with city, temp_c (degrees Celsius) and condition.
        If it contains "status": "error", the tool is broken and could not be repaired.
    """
    return get_weather_with_healing(city)


root_agent = Agent(
    name="weather_desk",
    model=os.getenv("AGENT_MODEL", "gemini-flash-lite-latest"),
    description="Answers weather questions by calling a weather tool.",
    instruction=(
        "You are a concise weather assistant. ALWAYS call the get_weather tool; never guess. "
        "Answer in one friendly sentence with the temperature in Celsius. "
        "If the tool reports an error, say honestly that the weather service is broken right now."
    ),
    tools=[get_weather],
)
