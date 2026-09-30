import re

# Rule-based safety agent.
# The earlier version only matched exact phrases, so "My engine is overheating"
# (the first quick action) did not match "engine overheating" and came back LOW.
# Patterns below match the usual ways people describe the same problem.

CRITICAL_PATTERNS = [
    r"brakes?\s*(have\s*|has\s*|are\s*|is\s*)?(fail|not\s*work|gone|stopped\s*work)",
    r"no\s*brakes?", r"overheat", r"engine\s*(is\s*)?(heating|too\s*hot|boiling)",
    r"\bfire\b", r"\bflames?\b", r"smok(e|ing)\s*(from|under|out)",
    r"steering\s*(has\s*|is\s*)?(fail|lock|not\s*work)", r"accident", r"crash",
    r"(fuel|petrol|diesel|gas)\s*(leak|smell)", r"smell\s*of\s*(fuel|petrol|diesel|gas)",
    r"tyre\s*burst|tire\s*burst|blow\s*-?out",
]

HIGH_PATTERNS = [
    r"brake.*(warning|light|indicator)", r"(warning|light|indicator).*brake",
    r"brake\s*fluid", r"oil\s*pressure", r"battery", r"charging\s*system",
    r"flat\s*(tyre|tire)", r"puncture", r"coolant\s*leak", r"engine\s*problem",
    r"check\s*engine.*flash", r"engine.*(knock|stall|shut\s*down)", r"srs|airbag",
]

MEDIUM_PATTERNS = [
    r"tyre|tire", r"wiper", r"headlight|head\s*lamp", r"check\s*engine",
    r"malfunction\s*indicator", r"heavy\s*rain|fog|snow|storm|flood|waterlog",
    r"noise|vibration|rattle", r"\bwarning\b",
]


def _matches(patterns, text):
    return any(re.search(p, text) for p in patterns)


def assess_risk(query):
    print("RULE BASED SAFETY AGENT ACTIVE")
    text = query.lower()

    if _matches(CRITICAL_PATTERNS, text):
        return "CRITICAL"
    if _matches(HIGH_PATTERNS, text):
        return "HIGH"
    if _matches(MEDIUM_PATTERNS, text):
        return "MEDIUM"
    return "LOW"


RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def max_risk(*levels):
    valid = [lvl for lvl in levels if lvl in RISK_ORDER]
    if not valid:
        return "LOW"
    return max(valid, key=RISK_ORDER.index)
