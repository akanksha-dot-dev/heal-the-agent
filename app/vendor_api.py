"""A PRETEND third-party weather vendor.

It is offline and deterministic on purpose: a live demo must never depend on
someone else's API being up. Flip the version with an environment variable:

    VENDOR_API_VERSION=v1   the format our parser was written for
    VENDOR_API_VERSION=v2   vendor renamed + nested the fields      -> crash
    VENDOR_API_VERSION=v3   ...and switched to Fahrenheit            -> a naive fix gives a plausible but WRONG number
"""
import os


def fetch_weather(city: str) -> dict:
    version = os.environ.get("VENDOR_API_VERSION", "v1")
    if version == "v1":
        return {"city": city, "temp_c": 31.2, "condition": "Humid"}
    if version == "v2":
        return {"location": {"name": city}, "current": {"temp": 31.2, "unit": "C", "text": "Humid"}}
    if version == "v3":
        return {"location": {"name": city}, "current": {"temp": 88.2, "unit": "F", "text": "Humid"}}
    raise ValueError(f"unknown VENDOR_API_VERSION: {version}")
