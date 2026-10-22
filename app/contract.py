"""The CONTRACT: what a healthy parser result looks like.

A sensor that only watches for exceptions misses the worst bugs (v3: no crash,
just a wrong number). So we also check *invariants* on the output.
"""

# Payloads the parser has handled correctly in the past, with the answer we expect.
# A fix must not break these (a "regression suite").
KNOWN_GOOD = [
    (
        {"city": "Lisbon", "temp_c": 31.2, "condition": "Humid"},
        {"city": "Lisbon", "temp_c": 31.2, "condition": "Humid"},
    ),
]


def contract_violations(result) -> list[str]:
    problems = []
    if not isinstance(result, dict):
        return [f"result must be a dict, got {type(result).__name__}"]
    for key, typ in (("city", str), ("temp_c", (int, float)), ("condition", str)):
        if key not in result:
            problems.append(f"missing key '{key}'")
        elif not isinstance(result[key], typ):
            problems.append(f"'{key}' has wrong type {type(result[key]).__name__}")
    t = result.get("temp_c")
    if isinstance(t, (int, float)) and not (-90 <= t <= 60):
        problems.append(f"temp_c={t} is outside the plausible Celsius range -90..60 (wrong unit?)")
    return problems
