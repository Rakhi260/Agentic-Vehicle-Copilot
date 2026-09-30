// Backend base URL. Override it in Vercel -> Project -> Settings -> Environment Variables
// with VITE_API_URL (e.g. when the Render service is renamed), or in frontend/.env.local
// as VITE_API_URL=http://localhost:8000 for local development.
export const API_BASE: string = (
  import.meta.env.VITE_API_URL || "https://agentic-vehicle-copilot.onrender.com"
).replace(/\/+$/, "");

// Render's free plan puts the service to sleep after ~15 minutes without traffic.
// The first request wakes it up, which can take up to a minute.
export const COLD_START_TIMEOUT_MS = 75_000;
export const HEALTH_TIMEOUT_MS = 20_000;
export const ANALYZE_TIMEOUT_MS = 90_000;
export const HEALTH_INTERVAL_ONLINE_MS = 20_000;
export const HEALTH_INTERVAL_OFFLINE_MS = 8_000;
