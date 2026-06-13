def assess_risk(query):
    
    print("RULE BASED SAFETY AGENT ACTIVE")

    query = query.lower()

    critical = [
        "brake failure",
        "engine overheating",
        "engine heating",
        "accident",
        "fire",
        "steering failure"
    ]

    high = [
        "flat tire",
        "battery issue",
        "engine problem",
        "coolant leak"
    ]

    medium = [
        "wiper failure",
        "headlight issue"
    ]

    for item in critical:
        if item in query:
            return "CRITICAL"

    for item in high:
        if item in query:
            return "HIGH"

    for item in medium:
        if item in query:
            return "MEDIUM"

    return "LOW"