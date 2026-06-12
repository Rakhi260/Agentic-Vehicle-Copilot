from dotenv import load_dotenv
load_dotenv()

from supervisor import process_query

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

print("="*50)
print("VEHICLE COPILOT V2")
print("="*50)

query = input("\n Describe your vehicle issue: ")

result = process_query(query)

prompt = f"""
You are an intelligent vehicle copilot.PermissionError
User Query:
{query}

Vehicle Manual Information:
{result['manual']}

Current Weather:
{result['weather']}

Risk Assessment:
{result['risk']}

# Service centre assessment:
# {result['service_centre']}

Provide:

1.Issue Summary
2.Risk Level
3.Weather Impact
4.Recommended Action
5.Safety Advice

Use the manual information whenever possible

"""
response = llm.invoke(prompt)

print("\n")
print("="*50)
print("VEHICLE COPILOT RESPONSE")
print("="*50)

print(response.content)