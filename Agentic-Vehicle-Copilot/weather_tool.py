import os
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

# Optional. If OPENWEATHER_API_KEY is set (Render -> Environment), OpenWeather is used.
# Without a key the agent falls back to Open-Meteo (and wttr.in), which are free and
# need no key, so the weather card keeps working either way.
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
DEFAULT_CITY = "Mumbai"
TIMEOUT = 5
HEADERS = {"User-Agent": "AgenticVehicleCopilot/2.0 (https://agentic-vehicle-copilot.vercel.app)"}

# WMO weather interpretation codes used by Open-Meteo
WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


def _openweather(city=None, lat=None, lon=None):
    params = {"appid": API_KEY, "units": "metric"}
    if city:
        params["q"] = city
    else:
        params["lat"], params["lon"] = lat, lon
    resp = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=TIMEOUT)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if "weather" not in data or "main" not in data or "wind" not in data:
        return None
    return {
        "city": data.get("name") or city or "Current location",
        "condition": data["weather"][0].get("description", "unknown"),
        "temperature": data["main"].get("temp"),
        "feels_like": data["main"].get("feels_like"),
        "humidity": data["main"].get("humidity"),
        "pressure": data["main"].get("pressure"),
        "visibility": round(data["visibility"] / 1000, 1) if data.get("visibility") is not None else None,
        "wind_speed": data["wind"].get("speed", 0),
        "source": "OpenWeather",
    }


def _geocode_city(city):
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    results = resp.json().get("results") if resp.status_code == 200 else None
    if not results:
        return None
    r = results[0]
    return r["latitude"], r["longitude"], r.get("name", city)


def _open_meteo(city=None, lat=None, lon=None):
    name = "Current location"
    if city:
        geo = _geocode_city(city)
        if not geo:
            return None
        lat, lon, name = geo
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,"
                       "wind_speed_10m,surface_pressure,visibility",
            "wind_speed_unit": "ms",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        return None
    cur = resp.json().get("current") or {}
    if "temperature_2m" not in cur:
        return None
    visibility = cur.get("visibility")
    return {
        "city": name,
        "condition": WMO_CODES.get(cur.get("weather_code"), "unknown"),
        "temperature": cur.get("temperature_2m"),
        "feels_like": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"),
        "pressure": round(cur["surface_pressure"]) if cur.get("surface_pressure") is not None else None,
        "visibility": round(visibility / 1000, 1) if visibility is not None else None,
        "wind_speed": cur.get("wind_speed_10m", 0),
        "source": "Open-Meteo",
    }


def _wttr(city=None, lat=None, lon=None):
    """Second no-key provider, used when Open-Meteo does not answer in time."""
    place = city if city else f"{lat},{lon}"
    resp = requests.get(f"https://wttr.in/{quote(place)}", params={"format": "j1"}, headers=HEADERS, timeout=TIMEOUT)
    if resp.status_code != 200:
        return None
    cur = (resp.json().get("current_condition") or [None])[0]
    if not cur:
        return None
    desc = ((cur.get("weatherDesc") or [{}])[0].get("value") or "unknown").strip().lower()
    return {
        "city": city or "Current location",
        "condition": desc,
        "temperature": float(cur["temp_C"]),
        "feels_like": float(cur["FeelsLikeC"]),
        "humidity": int(cur["humidity"]),
        "pressure": int(cur["pressure"]),
        "visibility": float(cur["visibility"]),
        "wind_speed": round(float(cur["windspeedKmph"]) / 3.6, 1),
        "source": "wttr.in",
    }


def get_weather(city=DEFAULT_CITY, lat=None, lon=None, budget=15):
    """Weather for a city name or GPS coordinates. Tries the city first, then GPS, then the default city."""
    attempts = []
    if city:
        attempts.append({"city": city})
    if lat is not None and lon is not None:
        attempts.append({"lat": lat, "lon": lon})
    if not city or city != DEFAULT_CITY:
        attempts.append({"city": DEFAULT_CITY})

    providers = ([_openweather] if API_KEY else []) + [_open_meteo, _wttr]
    last_error = "Unable to fetch weather."
    deadline = time.time() + budget

    for kwargs in attempts:
        for provider in providers:
            if time.time() > deadline:
                return {"error": "Weather service timed out."}
            try:
                weather = provider(**kwargs)
            except Exception as e:  # network error, timeout, bad JSON
                last_error = str(e)
                print(f"Weather provider {provider.__name__} failed: {e}")
                continue
            if weather:
                weather["driving_risk"] = get_weather_risk(weather)
                weather["advice"] = get_weather_advice(weather)
                return weather

    return {"error": last_error}


def get_weather_risk(weather):
    condition = (weather.get("condition") or "").lower()
    temperature = weather.get("temperature")
    visibility = weather.get("visibility")

    if "thunderstorm" in condition or "violent" in condition:
        return "CRITICAL"
    if "fog" in condition or "heavy rain" in condition or "snow" in condition or "freezing" in condition:
        return "HIGH"
    if "rain" in condition or "drizzle" in condition or "shower" in condition:
        return "MEDIUM"
    if temperature is not None and temperature > 40:
        return "HIGH"
    if visibility is not None and visibility < 2:
        return "HIGH"
    return "LOW"


def get_weather_advice(weather):
    advice = []
    condition = (weather.get("condition") or "").lower()
    temperature = weather.get("temperature")
    visibility = weather.get("visibility")
    wind = weather.get("wind_speed") or 0

    if "rain" in condition or "drizzle" in condition or "shower" in condition:
        advice.append("Roads may be slippery.")
        advice.append("Maintain a safe distance from other vehicles.")
    if "fog" in condition:
        advice.append("Use fog lamps.")
        advice.append("Drive at a reduced speed.")
    if "thunderstorm" in condition:
        advice.append("Avoid driving during the storm if possible.")
    if temperature is not None and temperature > 40:
        advice.append("High temperature may increase engine overheating risk.")
    if wind > 10:
        advice.append("Strong crosswinds may affect vehicle stability.")
    if visibility is not None and visibility < 2:
        advice.append("Poor visibility. Avoid high-speed driving.")
    if not advice:
        advice.append("Weather conditions are suitable for driving.")
    return advice
