import time
import re

from manual_agent import retrieve_manual_info
from safety_agent import assess_risk
from weather_tool import get_weather
from service_centre import find_service_centre

def extract_city(query):
    # Regex match for common location prepositions followed by a word
    match = re.search(r"\b(?:in|at|near|for|of)\s+([a-zA-Z\s]+)\b", query, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        # Clean up trailing/leading spaces or extra words
        city_first_word = city.split()[0]
        non_cities = {"the", "a", "my", "your", "heavy", "rain", "fog", "snow", "hot", "cold", "wet", "dry", "car", "suv", "truck", "here", "warning", "service", "centre", "me", "us", "him", "her", "them", "it", "repair", "nearest", "closest", "mechanic"}
        if city_first_word.lower() not in non_cities:
            return city_first_word.capitalize()

    # Predefined popular cities fallback
    cities = ["mumbai", "pune", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "london", "new york", "paris", "tokyo", "berlin", "san francisco", "seattle", "nashik", "goa"]
    query_lower = query.lower()
    for c in cities:
        if c in query_lower:
            return c.capitalize()
    return None

def process_query(query, location=None):
    query_lower = query.lower()
    result = {}

    # Extract coordinates if location is provided
    lat, lon = None, None
    if location and isinstance(location, dict):
        lat = location.get("latitude")
        lon = location.get("longitude")

    # City name extraction
    extracted_city = extract_city(query)
    
    # Determine parameters for tools
    tool_city = "Mumbai"
    tool_lat, tool_lon = None, None
    tool_location = None
    
    if extracted_city:
        tool_city = extracted_city
        # Query contains a city, so override/ignore GPS coordinates
        print(f"Supervisor: Extracted city name '{extracted_city}' from query. Ignoring GPS.")
    else:
        if lat is not None and lon is not None:
            tool_lat, tool_lon = lat, lon
            tool_location = location
            tool_city = None
            print(f"Supervisor: Using GPS coordinates ({lat}, {lon})")
        else:
            print(f"Supervisor: No city found and no GPS. Defaulting to city '{tool_city}'")

    # ----------------------------
    # Manual Agent
    # ----------------------------
    if any(word in query_lower for word in [
        "warning", "engine", "tire", "brake",
        "battery", "overheat", "battery issue"
    ]):
        start = time.time()
        result["manual"] = retrieve_manual_info(query)
        print(f"Manual Agent: {time.time() - start:.2f} sec")

    # ----------------------------
    # Weather Agent
    # ----------------------------
    if any(word in query_lower for word in [
        "drive", "rain", "weather", "fog",
        "overheat", "tire"
    ]):
        start = time.time()
        result["weather"] = get_weather(city=tool_city, lat=tool_lat, lon=tool_lon)
        print(f"Weather Agent: {time.time() - start:.2f} sec")

    # ----------------------------
    # Safety Agent
    # ----------------------------
    if any(word in query_lower for word in [
        "warning", "engine", "brake",
        "battery", "tire", "overheat", "failure"
    ]):
        start = time.time()
        result["risk"] = assess_risk(query)
        print(f"Safety Agent: {time.time() - start:.2f} sec")

    # ----------------------------
    # Service Centre Agent
    # ----------------------------
    if any(word in query_lower for word in [
        "service", "repair", "mechanic",
        "garage", "dealer", "workshop",
        "showroom"
    ]):
        start = time.time()
        result["service_centre"] = find_service_centre(user_city=tool_city, location=tool_location)
        print(f"Service Centre Agent: {time.time() - start:.2f} sec")

    return result


def build_context(result):

    context = ""

    if "manual" in result:
        context += f"""
MANUAL INFORMATION:
{result['manual']}

"""

    if "weather" in result:
        context += f"""
WEATHER INFORMATION:
Condition: {result['weather']['condition']}
Temperature: {result['weather']['temperature']} °C
Humidity: {result['weather']['humidity']} %
Wind Speed: {result['weather']['wind_speed']} m/s

"""

    if "risk" in result:
        context += f"""
RISK LEVEL:
{result['risk']}

"""

    # Fixed spelling
    if "service_centre" in result:
        context += f"""
SERVICE CENTRE:
{result['service_centre']}

"""

    return context