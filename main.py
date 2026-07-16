import os
import json
import time
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents and supervisor
from supervisor import process_query, build_context
from voice_agent import listen_to_driver
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize Gemini LLM
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    llm = None

async def analyze_issue(request):
    # Handle CORS preflight options request manually if needed, 
    # though CORSMiddleware usually handles it automatically.
    if request.method == "OPTIONS":
        return JSONResponse({"status": "ok"})
        
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
    query = body.get("query")
    location = body.get("location")
    if not query:
        return JSONResponse({"error": "Query string cannot be empty"}, status_code=400)
    
    start_time = time.time()
    
    # Run the supervisor query processor
    result = process_query(query, location=location)
    
    # Gather weather and manual data
    weather = result.get("weather", {})
    manual_text = result.get("manual", "Not Available")
    service_centre = result.get("service_centre", [])
    risk = result.get("risk", "LOW")
    
    # Context for Gemini
    context = build_context(result)
    
    # Construct structured prompt for JSON output
    prompt = f"""
    You are an intelligent vehicle copilot assistant.
    User Query: "{query}"

    Context:
    {context}

    Analyze the user's issue and return a JSON object EXACTLY in the following format:
    {{
      "issue_summary": "Short 1-2 sentence description of the vehicle issue.",
      "risk_level": "{risk}",
      "weather_impact": "Assess if the weather conditions impacts this issue (e.g. wet road risk, poor visibility, high engine temps).",
      "recommended_action": [
        "Action step 1",
        "Action step 2"
      ],
      "safety_advice": [
        "Safety warning 1",
        "Safety warning 2"
      ],
      "manual_summary": {{
        "immediate_actions": [
          "Action 1",
          "Action 2"
        ],
        "warnings": [
          "Warning 1",
          "Warning 2"
        ],
        "recommended_steps": [
          "Step 1",
          "Step 2"
        ],
        "preventive_tips": [
          "Tip 1",
          "Tip 2"
        ]
      }}
    }}

    IMPORTANT: Do not wrap the JSON in markdown code blocks. Return ONLY the raw JSON string.
    If manual information is provided in the Context, summarize it into the manual_summary object with immediate_actions, warnings, recommended_steps, and preventive_tips. Each array should contain short, clear sentences. If no manual context is available, populate these arrays using standard vehicle manual best practices for the reported issue.
    """
    
    ai_summary = None
    if llm:
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            # Clean possible markdown JSON wrappers if LLM still returned them
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            ai_summary = json.loads(content)
        except Exception as e:
            print(f"Gemini processing failed, falling back. Error: {e}")
    
    # If Gemini fails or was not initialized, build a high-quality manual fallback response
    if not ai_summary:
        ai_summary = {
            "issue_summary": f"Reported issue: {query}",
            "risk_level": risk,
            "weather_impact": f"Weather is {weather.get('condition', 'unknown')} with temp {weather.get('temperature', 'N/A')}°C. {'' if 'rain' not in weather.get('condition', '').lower() else 'Rain may cause slippery road conditions.'}",
            "recommended_action": [
                "Stop the vehicle safely on the side of the road if driving is compromised.",
                "Review the retrieved vehicle manual instructions below.",
                "Contact a local service center if the hazard persists."
            ],
            "safety_advice": [
                f"Risk is classified as {risk}.",
                "Avoid driving if warning lights remain red or flashing.",
                "Keep emergency contact numbers handy."
            ],
            "manual_summary": {
                "immediate_actions": ["Stop the vehicle safely on the side of the road if driving is compromised."],
                "warnings": ["Avoid driving if warning lights remain red or flashing."],
                "recommended_steps": ["Review the retrieved vehicle manual instructions.", "Contact a local service center if the hazard persists."],
                "preventive_tips": ["Perform regular vehicle inspections.", "Keep emergency contact numbers handy."]
            }
        }

    processing_time = time.time() - start_time
    
    return JSONResponse({
        "query": query,
        "processing_time": f"{processing_time:.2f}",
        "raw_agents_data": {
            "risk": risk,
            "weather": weather,
            "manual": manual_text,
            "service_centre": service_centre
        },
        "summary": ai_summary
    })

async def get_voice_input(request):
    if request.method == "OPTIONS":
        return JSONResponse({"status": "ok"})
        
    print("Starting backend voice recognition...")
    try:
        spoken_text = listen_to_driver()
        return JSONResponse({"text": spoken_text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

routes = [
    Route("/api/analyze", analyze_issue, methods=["POST", "OPTIONS"]),
    Route("/api/voice", get_voice_input, methods=["POST", "OPTIONS"]),
]

# Configure CORS Middleware using Starlette's CORSMiddleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
