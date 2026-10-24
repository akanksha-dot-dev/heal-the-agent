def parse_weather(raw: dict) -> dict:
    """Turn a vendor payload into {"city": str, "temp_c": float, "condition": str}.

    temp_c is ALWAYS degrees Celsius.
    """
    # Support OLD payload format (flat dict with 'city', 'temp_c', 'condition')
    # and NEW payload format (nested 'location' and 'current' dicts).
    
    # Resolve city
    city = raw.get("city")
    if city is None and "location" in raw:
        city = raw["location"].get("name")

    # Resolve temp_c
    temp_c = raw.get("temp_c")
    if temp_c is None and "current" in raw:
        temp_c = raw["current"].get("temp")

    # Resolve condition
    condition = raw.get("condition")
    if condition is None and "current" in raw:
        condition = raw["current"].get("text")

    return {
        "city": str(city) if city is not None else "",
        "temp_c": float(temp_c) if temp_c is not None else 0.0,
        "condition": str(condition) if condition is not None else "",
    }
