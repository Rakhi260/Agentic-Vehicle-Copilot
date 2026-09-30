"""
AI summary for the diagnostic response.

Calls the Gemini REST API directly (no LangChain / google SDK needed, which keeps the
Render free instance light). If no key is configured, the model is unavailable, or the
quota is exhausted, a rule-based summary built from the agents' data is returned instead,
so the site always answers.

Environment variables (set them in Render -> your service -> Environment):
  GEMINI_API_KEY (or GOOGLE_API_KEY)  required for AI summaries
  GEMINI_MODEL                        optional, overrides the model list below
"""

import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
# Tried in order until one answers. Older models (e.g. gemini-2.5-flash) are only open to
# keys that already used them, so newer ones come first.
MODELS = [m.strip() for m in os.getenv("GEMINI_MODEL", "").split(",") if m.strip()] or [
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT = 30

_working_model = [None]


def gemini_configured():
    return bool(API_KEY)


def _call_gemini(prompt):
    models = [_working_model[0]] if _working_model[0] else MODELS
    for model in models:
        try:
            resp = requests.post(
                ENDPOINT.format(model=model),
                headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
                timeout=TIMEOUT,
            )
        except requests.Timeout:
            print(f"Gemini {model} timed out")
            return None
        except requests.RequestException as e:
            print(f"Gemini {model} request error: {e}")
            continue

        if resp.status_code != 200:
            print(f"Gemini {model} returned {resp.status_code}: {' '.join(resp.text.split())[:300]}")
            if "API_KEY_INVALID" in resp.text or "API key not valid" in resp.text or resp.status_code == 401:
                return None  # bad key, other models won't help
            continue

        try:
            parts = resp.json()["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        except (KeyError, IndexError, ValueError):
            print(f"Gemini {model} returned an unexpected payload")
            continue

        _working_model[0] = model
        return text
    _working_model[0] = None
    return None


def _parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).rstrip("`").strip()
    try:
        return json.loads(text)
    except ValueError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else None


# --------------------------------------------------------------------------
# Rule-based fallback
# --------------------------------------------------------------------------

PLAYBOOK = {
    "overheat": {
        "match": r"overheat|too hot|temperature gauge|coolant|steam|boil",
        "summary": "The engine is running too hot. Continuing to drive can seriously damage it.",
        "actions": [
            "Pull over at a safe place as soon as possible and shift to P or N.",
            "Turn off the A/C. If steam is coming from under the hood or the gauge stays in the red, switch the engine off.",
            "After the engine has cooled down, check the coolant level in the reservoir and look for leaks under the vehicle.",
            "Have the cooling system (coolant, fan, radiator hoses) inspected before driving further.",
        ],
        "safety": [
            "Never open the radiator or coolant reservoir cap while the engine is hot. Scalding coolant can spray out.",
            "Keep hands and clothing away from the cooling fan and drive belts.",
        ],
        "tips": ["Check the coolant level regularly when the engine is cold.", "Replace coolant at the interval given in the maintenance schedule."],
    },
    "brake": {
        "match": r"brake",
        "summary": "A brake warning can mean the parking brake is on, the brake fluid is low, or the brake system has a fault.",
        "actions": [
            "Check that the parking brake is fully released.",
            "If the light stays on, slow down gradually and stop in a safe place.",
            "With the vehicle parked, check the brake fluid level in the reservoir.",
            "Have the brake system inspected before continuing your trip.",
        ],
        "safety": [
            "Stopping distances may be longer. Keep a larger gap to the vehicle ahead.",
            "If the pedal feels soft or sinks to the floor, do not drive. Call for towing.",
        ],
        "tips": ["Have brake pads and fluid checked at every service.", "Replace brake fluid at the interval in the maintenance schedule."],
    },
    "battery": {
        "match": r"battery|charging|alternator|won'?t start|dead",
        "summary": "A battery or charging warning usually means the charging system is not keeping the battery charged.",
        "actions": [
            "Switch off electrical loads you do not need (A/C, audio, seat or window heaters).",
            "Drive directly to the nearest workshop. Avoid turning the engine off, as it may not restart.",
            "Have the battery, alternator and drive belt tested.",
        ],
        "safety": [
            "If the engine stalls, stop in a safe place and switch on the hazard lights.",
            "Do not touch corroded or leaking battery terminals with bare hands.",
        ],
        "tips": ["Keep battery terminals clean and tight.", "Have the battery tested before long trips or when it is more than 3 years old."],
    },
    "tire": {
        "match": r"tyre|tire|puncture|flat",
        "summary": "Low tyre pressure affects braking, handling and fuel economy, and can lead to tyre failure.",
        "actions": [
            "Reduce speed and avoid sudden steering or braking.",
            "At the next fuel station, check all tyre pressures and inflate to the values on the driver's door label.",
            "Inspect the tyres for nails, cuts or bulges.",
            "If a tyre is flat, stop on firm level ground and fit the spare or call roadside assistance.",
        ],
        "safety": [
            "Driving on an under-inflated tyre can overheat it and cause a blowout.",
            "Change a wheel only well away from traffic, with the hazard lights on.",
        ],
        "tips": ["Check tyre pressures once a month when the tyres are cold.", "Rotate tyres and check alignment at the recommended intervals."],
    },
    "weather": {
        "match": r"rain|fog|snow|storm|weather|wet|flood|visibility",
        "summary": "Driving conditions depend on the current weather. Adjust speed and spacing to the road surface and visibility.",
        "actions": [
            "Turn on the headlights and wipers, and use the defogger to keep the windscreen clear.",
            "Reduce speed and keep at least twice the usual following distance.",
            "Avoid driving through standing or flowing water.",
        ],
        "safety": [
            "Brake gently and early. Wet roads increase stopping distance.",
            "If visibility becomes very poor, stop in a safe place with the hazard lights on.",
        ],
        "tips": ["Replace worn wiper blades before the rainy season.", "Keep tyre tread depth well above the legal minimum."],
    },
    "service": {
        "match": r"service|repair|mechanic|garage|workshop|dealer",
        "summary": "Here are workshops near the selected location.",
        "actions": [
            "Choose a workshop below, or open the map search for more options.",
            "Call ahead to confirm they can handle your vehicle and the issue.",
            "Describe the symptoms clearly and bring your service records.",
        ],
        "safety": ["If the vehicle is not safe to drive, arrange towing instead of driving it to the workshop."],
        "tips": ["Follow the maintenance schedule in the owner's manual."],
    },
}

GENERIC = {
    "summary": "The issue was checked against the vehicle manual and the other agents.",
    "actions": [
        "If the vehicle behaves abnormally, stop in a safe place and switch on the hazard lights.",
        "Review the matching manual sections below.",
        "Have the vehicle inspected at a workshop if the problem continues.",
    ],
    "safety": ["Do not drive if a red warning light stays on or the vehicle is hard to control."],
    "tips": ["Follow the maintenance schedule in the owner's manual."],
}


def _weather_impact(weather):
    if not weather or weather.get("error"):
        return "Weather data was not needed or not available for this query."
    text = (
        f"Current conditions in {weather.get('city', 'your area')}: {weather.get('condition', 'unknown')}, "
        f"{weather.get('temperature', 'N/A')}°C."
    )
    advice = weather.get("advice") or []
    return text + (" " + " ".join(advice) if advice else "")


def fallback_summary(query, result):
    q = query.lower()
    entry = next((v for v in PLAYBOOK.values() if re.search(v["match"], q)), GENERIC)
    risk = result.get("risk", "LOW")
    actions = list(entry["actions"])
    if result.get("service_centre"):
        actions.append("Nearby workshops are listed below.")
    return {
        "issue_summary": entry["summary"],
        "risk_level": risk,
        "weather_impact": _weather_impact(result.get("weather")),
        "recommended_action": actions,
        "safety_advice": [f"Risk is classified as {risk}."] + entry["safety"],
        "manual_summary": {
            "immediate_actions": entry["actions"][:2],
            "warnings": entry["safety"],
            "recommended_steps": entry["actions"][2:],
            "preventive_tips": entry["tips"],
        },
    }


def _normalise(ai, fallback, risk):
    """Make sure every field the frontend reads exists and has the right type."""
    out = dict(fallback)
    if not isinstance(ai, dict):
        return out
    for key in ("issue_summary", "weather_impact"):
        if isinstance(ai.get(key), str) and ai[key].strip():
            out[key] = ai[key].strip()
    for key in ("recommended_action", "safety_advice"):
        if isinstance(ai.get(key), list) and ai[key]:
            out[key] = [str(x) for x in ai[key] if str(x).strip()]
    ms = ai.get("manual_summary")
    if isinstance(ms, dict):
        merged = dict(fallback["manual_summary"])
        for key in merged:
            if isinstance(ms.get(key), list) and ms[key]:
                merged[key] = [str(x) for x in ms[key] if str(x).strip()]
        out["manual_summary"] = merged
    out["risk_level"] = risk  # the safety agent decides the risk level
    return out


def summarize(query, result, context):
    """Returns (summary_dict, source) where source is 'gemini' or 'rule-based'."""
    risk = result.get("risk", "LOW")
    fallback = fallback_summary(query, result)
    if not API_KEY:
        return fallback, "rule-based"

    prompt = f"""
You are an intelligent vehicle copilot assistant.
User Query: "{query}"

Context:
{context}

Analyze the user's issue and return a JSON object EXACTLY in the following format:
{{
  "issue_summary": "Short 1-2 sentence description of the vehicle issue.",
  "risk_level": "{risk}",
  "weather_impact": "Assess if the weather conditions impact this issue (e.g. wet road risk, poor visibility, high engine temps).",
  "recommended_action": ["Action step 1", "Action step 2"],
  "safety_advice": ["Safety warning 1", "Safety warning 2"],
  "manual_summary": {{
    "immediate_actions": ["Action 1", "Action 2"],
    "warnings": ["Warning 1", "Warning 2"],
    "recommended_steps": ["Step 1", "Step 2"],
    "preventive_tips": ["Tip 1", "Tip 2"]
  }}
}}

Return ONLY the raw JSON. Keep every sentence short and clear.
If manual information is provided in the Context, base manual_summary on it. If not, use standard
vehicle manual best practices for the reported issue. If no weather information is in the Context,
say that weather data was not needed for this query.
"""
    text = _call_gemini(prompt)
    if not text:
        return fallback, "rule-based"
    try:
        ai = _parse_json(text)
    except ValueError:
        ai = None
    if not isinstance(ai, dict):
        print("Gemini returned non-JSON output, using rule-based summary")
        return fallback, "rule-based"
    return _normalise(ai, fallback, risk), "gemini"
