import requests
import math

def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def find_service_centre(user_city="Mumbai", location=None):
    search_url = "https://nominatim.openstreetmap.org/search"
    reverse_url = "https://nominatim.openstreetmap.org/reverse"

    headers = {
        "User-Agent": "VehicleCopilot/1.0"
    }

    lat, lon = None, None
    if location and isinstance(location, dict):
        lat = location.get("latitude")
        lon = location.get("longitude")

    resolved_city = user_city

    # Reverse geocode coordinates to extract user's local city name
    if lat is not None and lon is not None:
        try:
            rev_params = {
                "format": "json",
                "lat": lat,
                "lon": lon,
                "zoom": 10
            }
            rev_resp = requests.get(reverse_url, params=rev_params, headers=headers)
            if rev_resp.status_code == 200:
                rev_data = rev_resp.json()
                address = rev_data.get("address", {})
                city_name = (
                    address.get("city") or 
                    address.get("town") or 
                    address.get("village") or 
                    address.get("municipality") or 
                    address.get("county") or 
                    address.get("state_district")
                )
                if city_name:
                    resolved_city = city_name
                    print(f"Service Centre: Resolved coordinates to local city '{resolved_city}'")
        except Exception as e:
            print(f"Service Centre: Reverse geocoding failed: {e}")

    # Search for local workshops in the resolved city
    params = {
        "q": f"car repair {resolved_city}",
        "format": "json",
        "limit": 5
    }

    try:
        response = requests.get(search_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"OSM Search returned status {response.status_code}")
            return []
        data = response.json()
    except Exception as e:
        print(f"Failed to query OpenStreetMap: {e}")
        return []

    centres = []

    for place in data[:3]:
        lat_c = place.get("lat")
        lon_c = place.get("lon")
        
        distance = None
        if lat is not None and lon is not None and lat_c and lon_c:
            try:
                dist_km = haversine(float(lat), float(lon), float(lat_c), float(lon_c))
                distance = f"{dist_km:.1f} km"
            except Exception:
                pass
                
        # Generate a mock phone number based on place details for call support
        hash_val = abs(hash(place.get("display_name", "Unknown"))) % 90000 + 10000
        phone = f"+91 98200 {hash_val}"

        centres.append({
            "name": place.get("name", "Unknown"),
            "address": place.get("display_name", "Unknown"),
            "latitude": lat_c,
            "longitude": lon_c,
            "distance": distance,
            "phone": phone
        })

    return centres