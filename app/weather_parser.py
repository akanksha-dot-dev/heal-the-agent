def parse_weather(raw: dict) -> dict:
    """Turn a vendor payload into {"city": str, "temp_c": float, "condition": str}.

    temp_c is ALWAYS degrees Celsius.
    """
    # Handle NEW payload format
    if "location" in raw or "current" in raw:
        location = raw.get("location", {})
        current = raw.get("current", {})
        
        city = location.get("name") or location.get("city", "Unknown")
        
        # Determine temperature and convert if Fahrenheit
        temp_val = current.get("temp")
        if temp_val is None:
            temp_val = current.get("temp_c", 0.0)
            temp_c = float(temp_val)
        else:
            temp_val = float(temp_val)
            unit = current.get("unit", "C").upper()
            if unit == "F":
                temp_c = (temp_val - 32.0) * 5.0 / 9.0
            else:
                temp_c = temp_val

        condition = current.get("text") or current.get("condition", "Unknown")
        
        return {
            "city": city,
            "temp_c": temp_c,
            "condition": condition,
        }

    # Handle OLD payload format
    return {
        "city": raw["city"],
        "temp_c": float(raw["temp_c"]),
        "condition": raw["condition"],
    }
