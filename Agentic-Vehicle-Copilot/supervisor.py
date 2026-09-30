import re
import time
from concurrent.futures import ThreadPoolExecutor

from manual_agent import retrieve_manual_info
from safety_agent import assess_risk, max_risk
from weather_tool import get_weather
from service_centre import find_service_centre, maps_search_url

DEFAULT_CITY = "Mumbai"

NON_CITIES = {
    "the", "a", "an", "my", "your", "our", "heavy", "rain", "fog", "snow", "hot", "cold", "wet", "dry",
    "car", "suv", "truck", "bike", "here", "there", "warning", "service", "centre", "center", "me", "us",
    "him", "her", "them", "it", "repair", "nearest", "closest", "mechanic", "night", "morning", "evening",
    "afternoon", "traffic", "highway", "city", "town", "idle", "low", "high", "speed", "first", "all",
    "least", "once", "some", "any", "front", "back", "rear", "gear", "neutral", "reverse", "park",
    "winter", "summer", "monsoon", "general", "case", "order", "time", "times", "while", "road", "roads",
}

POPULAR_CITIES = [
    "mumbai", "pune", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "london",
    "new york", "paris", "tokyo", "berlin", "san francisco", "seattle", "nashik", "goa", "kolhapur",
    "ichalkaranji", "sangli", "nagpur", "ahmedabad", "jaipur",
]

MANUAL_WORDS = ["warning", "engine", "tire", "tyre", "brake", "battery", "overheat", "light", "oil",
                "coolant", "leak", "start", "noise", "steer", "fuel", "wiper", "airbag", "gear", "clutch"]
WEATHER_WORDS = ["drive", "driving", "rain", "weather", "fog", "overheat", "tire", "tyre", "snow",
                 "storm", "wet", "hot", "temperature", "visibility", "road"]
SERVICE_WORDS = ["service", "repair", "mechanic", "garage", "dealer", "workshop", "showroom", "centre",
                 "center", "tow", "fix"]


def extract_city(query):
    for match in re.finditer(r"\b(?:in|at|near|around)\s+([a-zA-Z]+)", query, re.IGNORECASE):
        word = match.group(1).strip()
        if word.lower() not in NON_CITIES:
            return word.capitalize()

    query_lower = query.lower()
    for c in POPULAR_CITIES:
        if re.search(rf"\b{re.escape(c)}\b", query_lower):
            return c.title()
    return None


def process_query(query, location=None):
    query_lower = query.lower()
    result = {}

    lat = lon = None
    if location and isinstance(location, dict):
        lat, lon = location.get("latitude"), location.get("longitude")
    has_gps = lat is not None and lon is not None

    extracted_city = extract_city(query)
    if extracted_city:
        print(f"Supervisor: city '{extracted_city}' found in query, using it for location tools.")
    elif has_gps:
        print(f"Supervisor: using GPS coordinates ({lat}, {lon})")
    else:
        print(f"Supervisor: no city and no GPS, defaulting to '{DEFAULT_CITY}'")

    # Safety agent is rule based and instant, so it runs first and helps decide the rest.
    result["risk"] = assess_risk(query)

    wants_manual = any(w in query_lower for w in MANUAL_WORDS)
    wants_weather = any(w in query_lower for w in WEATHER_WORDS)
    wants_service = any(w in query_lower for w in SERVICE_WORDS) or result["risk"] in ("HIGH", "CRITICAL")
    if not (wants_manual or wants_weather or wants_service):
        # Unrecognised question: still look it up in the manual rather than returning nothing.
        wants_manual = True

    tasks = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        if wants_manual:
            tasks["manual"] = pool.submit(retrieve_manual_info, query)
        if wants_weather:
            tasks["weather"] = pool.submit(
                get_weather,
                city=extracted_city if extracted_city else (None if has_gps else DEFAULT_CITY),
                lat=lat, lon=lon,
            )
        if wants_service:
            tasks["service_centre"] = pool.submit(
                find_service_centre,
                user_city=extracted_city or DEFAULT_CITY,
                location=None if extracted_city else location,
            )

        for name, future in tasks.items():
            start = time.time()
            try:
                result[name] = future.result(timeout=25)
            except Exception as e:
                print(f"{name} agent failed: {e}")
                result[name] = [] if name == "service_centre" else (
                    {"error": str(e)} if name == "weather" else "Unable to retrieve information from the vehicle manual."
                )
            print(f"{name} agent: {time.time() - start:.2f} sec")

    if wants_service:
        if extracted_city or not has_gps:
            result["service_search_url"] = maps_search_url(city=extracted_city or DEFAULT_CITY)
        else:
            result["service_search_url"] = maps_search_url(lat=lat, lon=lon)

    # Bad weather raises the risk for driving-related questions.
    weather = result.get("weather") or {}
    if wants_weather and not weather.get("error"):
        result["risk"] = max_risk(result["risk"], weather.get("driving_risk"))

    return result


def build_context(result):
    context = ""

    if result.get("manual"):
        context += f"\nMANUAL INFORMATION:\n{result['manual']}\n"

    weather = result.get("weather")
    if weather and not weather.get("error"):
        context += (
            "\nWEATHER INFORMATION:\n"
            f"Location: {weather.get('city', 'N/A')}\n"
            f"Condition: {weather.get('condition', 'N/A')}\n"
            f"Temperature: {weather.get('temperature', 'N/A')} °C\n"
            f"Humidity: {weather.get('humidity', 'N/A')} %\n"
            f"Wind Speed: {weather.get('wind_speed', 'N/A')} m/s\n"
            f"Visibility: {weather.get('visibility', 'N/A')} km\n"
        )

    if result.get("risk"):
        context += f"\nRISK LEVEL:\n{result['risk']}\n"

    if result.get("service_centre"):
        lines = [f"- {c['name']} ({c.get('distance') or 'distance unknown'}): {c['address']}" for c in result["service_centre"]]
        context += "\nNEARBY SERVICE CENTRES:\n" + "\n".join(lines) + "\n"

    return context
