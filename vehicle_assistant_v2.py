from dotenv import load_dotenv
load_dotenv()

from supervisor import process_query, build_context
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

print("="*50)
print("VEHICLE COPILOT V2")
print("="*50)

query = input("\nDescribe your vehicle issue: ")

#Run all agents
result = process_query(query)

#Build context for gemini
context = build_context(result)

#format weather
weather = result.get("weather", {})

weather_text = f"""
Condition: {weather.get('condition', 'N/A')}
Temperature: {weather.get('temperature', 'N/A')} °C
Humidity: {weather.get('humidity', 'N/A')} %
Wind Speed: {weather.get('wind_speed', 'N/A')} m/s
"""

manual_text = result.get("manual", "Not Available")

prompt = f"""
You are an intelligent vehicle copilot.
User Query:
{query}

Context:
{context}

Provide:

1.Issue Summary
2.Risk Level
3.Weather Impact
4.Recommended Action
5.Safety Advice

Use the manual information whenever possible
"""

#manual response 
print("\n")
print("=" * 50)
print("VEHICLE COPILOT RESPONSE")
print("=" * 50)

#Primary mode that is gemini
try:
    
    response = llm.invoke(prompt)
    print(response.content)
    
#fallback mode that is template response
except Exception as e:

    print(f"""
    Issue Summary:
    {query}

    Risk Level:
    {result.get('risk','Unknown')}

    Weather Information:
    {weather_text}

    Manual Information:
    {manual_text[:400]}...

    Recommended Action:
    1. Stop vehicle safely.
    2. Follow the vehicle manual instructions.
    3. If risk level is CRITICAL, stop driving immediately.
    4. Contact a service centre if necessary.

    System Note:
    Gemini response unavailable.
    Using fallback response mode.
    """)
    print(f"\n[Debug] {str(e)}")