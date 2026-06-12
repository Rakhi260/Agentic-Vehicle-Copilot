from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

def assess_risk(query):

    prompt = f"""
You are a vehicle safety classifier.

Issue:
{query}

Classify the severity.

Rules:

CRITICAL:
- Brake failure
- Engine overheating
- Steering failure
- Airbag failure

HIGH:
- Tire puncture
- Battery failure
- Coolant leak

MEDIUM:
- Wiper failure
- Headlight failure
- Tire pressure warning

LOW:
- Washer fluid low
- Minor maintenance reminders
- Service center requests

Output ONLY one word:

LOW
MEDIUM
HIGH
CRITICAL
"""
    print("Classifying risk...")
    
    response = llm.invoke(prompt)
    
    print("Gemini responded.")
    
    risk = response.content.strip().upper()

    if "CRITICAL" in risk:
        return "CRITICAL"

    elif "HIGH" in risk:
        return "HIGH"

    elif "MEDIUM" in risk:
        return "MEDIUM"

    return "LOW"