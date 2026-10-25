def parse_weather(raw: dict) -> dict:
    """Turn a vendor payload into {"city": str, "temp_c": float, "condition": str}.

    temp_c is ALWAYS degrees Celsius. Supports both old and new payload formats.
    """
    # Support new format (location/current) with fallback to old format (flat keys)
    location = raw.get("location", {})
    current = raw.get("current", {})

    city = location.get("name") or raw.get("city")
    temp_c = current.get("temp") if "temp" in current else raw.get("temp_c")
    condition = current.get("text") or raw.get("condition")

    return {
        "city": str(city),
        "temp_c": float(temp_c),
        "condition": str(condition),
    }
