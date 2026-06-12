from manual_agent import retrieve_manual_info
from safety_agent import assess_risk
from weather_tool import get_weather

def process_query(query):
    
    manual_context = retrieve_manual_info(query)
    
    weather = get_weather()
    
    risk = assess_risk(query)
    
    return{
        "manual":manual_context,
        "weather":weather,
        "risk":risk
    }