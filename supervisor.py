from manual_agent import retrieve_manual_info
from safety_agent import assess_risk
from weather_tool import get_weather
from service_centre import find_service_centre

def process_query(query):
    
    query_lower = query.lower()
    
    result = {}
    
    #manual agent
    if any (word in query_lower for word in [
        "warning","engine","tire","brake","battery","overheat"
    ]):
        result["manual"] = retrieve_manual_info(query)
        
    #weather agent
    if any (word in query_lower for word in[
       "drive","rain","weather","fog","overheat","tire" 
    ]):
        result["weather"] = get_weather()
        
    #safety agent
    if any (word in query_lower for word in[
        "warning","engine","brake","battery","tire","overheat","failure"
    ]):
        result["risk"] = assess_risk(query)
        
    #service centre
    if any (word in query_lower for word in[
        "service","repair","mechanic","garage","dealer","workshop","showroom"
    ]):
        result["service_centre"] = find_service_centre()
        
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

    if "service_center" in result:
        context += f"""
        SERVICE CENTER:
        {result['service_center']}

"""

    return context