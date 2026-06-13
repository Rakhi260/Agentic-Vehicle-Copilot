import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city="Mumbai"):
    
    try:
        
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={API_KEY}&units=metric" 
        )
        
        response = requests.get(url)
        
        data = response.json()
        
        
        return  {
            "condition": data["weather"][0]["description"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
        
    except Exception as e:
        
        return {
            "error": str(e)
        }
    
    
    
