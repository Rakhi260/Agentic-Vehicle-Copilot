import contextlib
import time

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

load_dotenv()

from supervisor import process_query, build_context  # noqa: E402
from ai_summary import summarize, gemini_configured  # noqa: E402
from manual_agent import get_index  # noqa: E402
import weather_tool  # noqa: E402

MAX_QUERY_LENGTH = 500


async def health(request):
    """Lightweight status endpoint polled by the frontend's telemetry indicator."""
    return JSONResponse({
        "status": "ok",
        "gemini": gemini_configured(),
        "weather_provider": "OpenWeather" if weather_tool.API_KEY else "Open-Meteo",
    })


async def analyze_issue(request):
    if request.method == "OPTIONS":
        return JSONResponse({"status": "ok"})

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    query = str(body.get("query") or "").strip()[:MAX_QUERY_LENGTH]
    location = body.get("location")
    if not isinstance(location, dict):
        location = None
    if not query:
        return JSONResponse({"error": "Query string cannot be empty"}, status_code=400)

    start_time = time.time()

    # The agents and Gemini make blocking network calls. Running them in a worker thread
    # keeps the event loop free, so /api/health keeps answering while a query is processed.
    # (Before this, one slow query froze the whole server and the UI showed OFFLINE.)
    result = await run_in_threadpool(process_query, query, location)
    context = build_context(result)
    summary, source = await run_in_threadpool(summarize, query, result, context)

    return JSONResponse({
        "query": query,
        "processing_time": f"{time.time() - start_time:.2f}",
        "summary_source": source,
        "raw_agents_data": {
            "risk": result.get("risk", "LOW"),
            "weather": result.get("weather", {}),
            "manual": result.get("manual", "Not Available"),
            "service_centre": result.get("service_centre", []),
            "service_search_url": result.get("service_search_url"),
        },
        "summary": summary,
    })


async def root(request):
    return JSONResponse({"service": "Agentic Vehicle Copilot API", "health": "/api/health", "analyze": "POST /api/analyze"})


@contextlib.asynccontextmanager
async def lifespan(app):
    # Build the manual index at boot so the first user query is fast.
    await run_in_threadpool(get_index)
    yield


routes = [
    Route("/", root, methods=["GET", "HEAD"]),
    Route("/api/health", health, methods=["GET", "HEAD"]),
    Route("/api/analyze", analyze_issue, methods=["POST", "OPTIONS"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=False,
        max_age=86400,
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware, lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
