# Vehicle Copilot
An AI-powered Multi-Agent Vehicle Assistant that helps drivers diagnose vehicle issues using RAG,
weather intelligence, safety analysis, nearby service center recommendations, and voice interaction.

## Features

- RAG-based Vehicle Manual Retrieval
- AI Safety Risk Assessment
- Real-time Weather Information
- Nearby Service Centre Finder
- Voice Input (Speech-to-Text)
- Text-to-Speech Response
- Multi-Agent Architecture
- FAISS Vector Database
- Gemini Integration

## Tech Stack

### Frontend (v2, deployed on Vercel)
- React + TypeScript + Vite (`frontend/`)
- Browser Speech Recognition and Speech Synthesis for voice

### Backend (v2 API, deployed on Render)
- Python + Starlette (`main.py`)
- Multi-agent supervisor (`supervisor.py`): manual, weather, safety and service-centre agents run in parallel

### AI
- Gemini API (called over REST in `ai_summary.py`, with a rule-based fallback)
- Manual retrieval: BM25 keyword search over the Toyota manual chunks in `data/manual_chunks.json`
  (the same chunks as the original FAISS store; the embedding model was too heavy for Render's free instance)

### APIs
- OpenWeather API (optional) with Open-Meteo / wttr.in as key-free fallbacks
- OpenStreetMap Nominatim for nearby workshops

### v1 prototype
- Streamlit app (`app.py`), LangChain, FAISS, Sentence Transformers, SpeechRecognition, pyttsx3

## Deployment

| Part | Host | Config |
|------|------|--------|
| Frontend (`frontend/`) | Vercel | Root directory `frontend`, build `npm run build`, output `dist` |
| Backend (`main.py`) | Render (free) | `render.yaml`: `pip install -r requirement.txt`, `uvicorn main:app --host 0.0.0.0 --port $PORT` |

Environment variables on **Render** (Dashboard → service → Environment):

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | Recommended | AI summaries. Without it the app answers with a rule-based summary. |
| `GEMINI_MODEL` | Optional | Force a model, e.g. `gemini-3.5-flash`. By default a list of Flash models is tried. |
| `OPENWEATHER_API_KEY` | Optional | Uses OpenWeather; otherwise Open-Meteo is used (no key needed). |

Environment variable on **Vercel** (optional): `VITE_API_URL`, the backend URL. Defaults to
`https://agentic-vehicle-copilot.onrender.com`.

Render's free plan sleeps after about 15 minutes without traffic. The first visit wakes it (up to a
minute); the sidebar shows **ESTABLISHING TELEMETRY LINK** meanwhile and switches to **ONLINE** when it is up.

### Run locally

```bash
# backend
pip install -r requirement.txt
uvicorn main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Future Improvements

- Intelligent Response Agent
- Vehicle Diagnosis Agent
- Predictive Maintenance
- OBD-II Integration
