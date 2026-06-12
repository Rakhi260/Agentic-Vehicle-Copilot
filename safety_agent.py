def assess_risk(query):
    
    query = query.lower()
    
    if "brake" in query:
        return "CRITICAL"
    elif "overheat" in query:
        return "HIGH"
    elif "engine" in query:
        return "HIGH"
    elif "tire" in query:
        return "HIGH"
    elif "battery" in query:
        return "MEDIUM"
    
    return "LOW"