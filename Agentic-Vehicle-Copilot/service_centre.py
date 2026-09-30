import math
import threading
import time
from urllib.parse import quote_plus

import requests

NOMINATIM = "https://nominatim.openstreetmap.org"
# Nominatim's usage policy asks for an identifying User-Agent and at most 1 request/second.
HEADERS = {"User-Agent": "AgenticVehicleCopilot/2.0 (https://agentic-vehicle-copilot.vercel.app)"}
TIMEOUT = 8

_rate_lock = threading.Lock()
_last_call = [0.0]
_cache = {}
CACHE_SECONDS = 600


def _nominatim(path, params):
    with _rate_lock:
        wait = 1.05 - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
    resp = requests.get(f"{NOMINATIM}/{path}", params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * math.asin(math.sqrt(a)) * 6371


def maps_search_url(city=None, lat=None, lon=None):
    """Google Maps search for workshops, shown as a fallback because OpenStreetMap coverage is thin in many towns."""
    if lat is not None and lon is not None:
        return f"https://www.google.com/maps/search/car+repair/@{lat},{lon},13z"
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus('car repair near ' + (city or 'me'))}"


def _geocode(city):
    data = _nominatim("search", {"q": city, "format": "jsonv2", "limit": 1})
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None


def _place_name(place):
    if place.get("name"):
        return place["name"]
    return "Car repair workshop"


def _phone(place):
    tags = place.get("extratags") or {}
    # Only real numbers published in OpenStreetMap. Never generate one: a driver may call it.
    return tags.get("phone") or tags.get("contact:phone")


def find_service_centre(user_city="Mumbai", location=None, limit=3):
    lat = lon = None
    if location and isinstance(location, dict):
        lat, lon = location.get("latitude"), location.get("longitude")

    cache_key = (round(lat, 2), round(lon, 2)) if lat is not None and lon is not None else (user_city or "").lower()
    cached = _cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]

    try:
        if lat is None or lon is None:
            centre = _geocode(user_city or "Mumbai")
            if not centre:
                return []
            lat, lon = centre
        lat, lon = float(lat), float(lon)

        found = {}
        # Look close by first, widen the box if the area has few mapped workshops.
        for delta in (0.15, 0.6):
            viewbox = f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}"
            data = _nominatim("search", {
                "q": "car repair", "format": "jsonv2", "limit": 15, "extratags": 1,
                "bounded": 1, "viewbox": viewbox,
            })
            for place in data:
                found[place.get("place_id")] = place
            if len(found) >= limit:
                break
    except Exception as e:
        print(f"Service Centre lookup failed: {e}")
        return []

    centres = []
    for place in found.values():
        try:
            p_lat, p_lon = float(place["lat"]), float(place["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        dist = haversine(lat, lon, p_lat, p_lon)
        centres.append({
            "name": _place_name(place),
            "address": place.get("display_name", "Unknown"),
            "latitude": place["lat"],
            "longitude": place["lon"],
            "distance": f"{dist:.1f} km",
            "phone": _phone(place),
            "_d": dist,
        })

    centres.sort(key=lambda c: c["_d"])
    for c in centres:
        c.pop("_d", None)
    centres = centres[:limit]
    _cache[cache_key] = (time.time(), centres)
    return centres
