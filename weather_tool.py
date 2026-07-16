import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city="Mumbai", lat=None, lon=None):
    
    try:
        
        if lat is not None and lon is not None:
            url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}"
                f"&appid={API_KEY}"
                "&units=metric"
            )
        else:
            url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}"
                f"&appid={API_KEY}"
                "&units=metric"
            )
        
        response = requests.get(url)
        
        if response.status_code != 200:
            return{
                "error":"Unable to fetch weather."
            }
        data = response.json()
        
        if "weather" not in data or "main" not in data or "wind" not in data:
            return {
                "error": "Invalid weather response structure"
            }
        
        weather = {
            "city": city,
            "condition": data["weather"][0].get("description", "unknown"),
            "temperature": data["main"].get("temp"),
            "feels_like": data["main"].get("feels_like"),
            "humidity": data["main"].get("humidity"),
            "pressure": data["main"].get("pressure"),
            "visibility": data.get("visibility", 0) / 1000 if data.get("visibility") is not None else 0,
            "wind_speed": data["wind"].get("speed", 0)
        }

        weather["driving_risk"] = get_weather_risk(weather)
        weather["advice"] = get_weather_advice(weather)

        return weather

    except Exception as e:

        return {
            "error": str(e)
        }


def get_weather_risk(weather):

    condition = weather["condition"].lower()

    if "thunderstorm" in condition:
        return "CRITICAL"

    elif "fog" in condition:
        return "HIGH"

    elif "rain" in condition:
        return "HIGH"

    elif weather["temperature"] > 40:
        return "HIGH"

    elif weather["visibility"] < 2:
        return "HIGH"

    else:
        return "LOW"


def get_weather_advice(weather):

    advice = []

    condition = weather["condition"].lower()

    if "rain" in condition:
        advice.append("Roads may be slippery.")
        advice.append("Maintain a safe distance from other vehicles.")

    if "fog" in condition:
        advice.append("Use fog lamps.")
        advice.append("Drive at a reduced speed.")

    if weather["temperature"] > 40:
        advice.append("High temperature may increase engine overheating risk.")

    if weather["wind_speed"] > 10:
        advice.append("Strong crosswinds may affect vehicle stability.")

    if weather["visibility"] < 2:
        advice.append("Poor visibility. Avoid high-speed driving.")

    if not advice:
        advice.append("Weather conditions are suitable for driving.")

    return advice
    
    
