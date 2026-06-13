import requests

def find_service_centre(user_city="Mumbai"):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": "Toyota Nashik",
        "format": "json",
        "limit": 5
    }

    headers = {
        "User-Agent": "VehicleCopilot/1.0"
    }

    response = requests.get(url, params=params, headers=headers)

    print("STATUS:", response.status_code)

    data = response.json()

    centres = []

    for place in data[:3]:

        centres.append({
            "name": place.get("name", "Unknown"),
            "address": place.get("display_name", "Unknown"),
            "latitude": place.get("lat"),
            "longitude": place.get("lon")
        })

    return centres