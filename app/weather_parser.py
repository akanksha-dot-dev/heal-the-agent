def parse_weather(raw: dict) -> dict:
    """Turn a vendor payload into {"city": str, "temp_c": float, "condition": str}.

    temp_c is ALWAYS degrees Celsius.
    """
    return {
        "city": raw["city"],
        "temp_c": float(raw["temp_c"]),
        "condition": raw["condition"],
    }
