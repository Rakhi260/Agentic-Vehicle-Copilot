import { useState, useEffect, useRef, useCallback } from "react";
import { ChatMessage } from "./components/ChatMessage";
import type { ChatMessageData, DiagnosticsData } from "./components/ChatMessage";
import { ChatInputBar } from "./components/ChatInputBar";
import {
  API_BASE,
  ANALYZE_TIMEOUT_MS,
  COLD_START_TIMEOUT_MS,
  HEALTH_INTERVAL_OFFLINE_MS,
  HEALTH_INTERVAL_ONLINE_MS,
  HEALTH_TIMEOUT_MS,
} from "./config";
import {
  Cpu,
  AlertTriangle,
  Wrench,
  CloudRain,
  ShieldAlert,
  FileText,
  Zap,
  Bot,
  Menu,
  X,
} from "lucide-react";

/* ============================================
   Types
   ============================================ */

type LinkState = "connecting" | "online" | "offline";

async function pingBackend(timeoutMs: number): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}/api/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

/* ============================================
   Quick Action Prompts
   ============================================ */

const QUICK_ACTIONS = [
  { icon: <AlertTriangle size={14} />, label: "Engine overheating", query: "My engine is overheating" },
  { icon: <ShieldAlert size={14} />, label: "Brake warning light", query: "Brake warning light is on" },
  { icon: <Zap size={14} />, label: "Battery issues", query: "Battery warning light is flashing" },
  { icon: <CloudRain size={14} />, label: "Driving in rain", query: "Is it safe to drive in heavy rain?" },
  { icon: <Wrench size={14} />, label: "Find service centre", query: "Find nearest service centre for repair" },
  { icon: <FileText size={14} />, label: "Tire pressure low", query: "Tire pressure warning light is on" },
];

/* ============================================
   Unique ID Generator
   ============================================ */

let msgCounter = 0;
function nextMsgId(): string {
  return `msg-${Date.now()}-${++msgCounter}`;
}

/* ============================================
   App Component
   ============================================ */

function App() {
  const [messages, setMessages] = useState<ChatMessageData[]>([
    {
      id: nextMsgId(),
      role: "copilot",
      text: "",
      timestamp: new Date(),
      isWelcome: true,
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [linkState, setLinkState] = useState<LinkState>("connecting");
  const [isWakingBackend, setIsWakingBackend] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceState, setVoiceState] = useState<"idle" | "listening" | "understanding" | "analyzing" | "speaking">("idle");
  const [agentProgress, setAgentProgress] = useState(0);

  const threadRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const isLoadingRef = useRef(false);
  const healthFailuresRef = useRef(0);

  useEffect(() => {
    isLoadingRef.current = isLoading;
  }, [isLoading]);

  const recordHealth = useCallback((ok: boolean) => {
    if (ok) {
      healthFailuresRef.current = 0;
      setLinkState("online");
    } else {
      healthFailuresRef.current += 1;
      // One missed ping is not enough to call the link down.
      if (healthFailuresRef.current >= 2) setLinkState("offline");
    }
  }, []);

  /* ---- Backend Health Check ----
     The backend runs on Render's free plan, which sleeps when idle and needs up to a
     minute to wake. The old check gave up after 1.5 s, so the dot stayed red even
     though the server was only waking up. The first ping now waits long enough for a
     cold start, and later pings run on a relaxed schedule. */
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let first = true;

    const run = async () => {
      let ok: boolean | null = null;
      if (!isLoadingRef.current) {
        ok = await pingBackend(first ? COLD_START_TIMEOUT_MS : HEALTH_TIMEOUT_MS);
        if (cancelled) return;
        if (first && !ok) healthFailuresRef.current = 1; // show OFFLINE right after a failed cold start
        recordHealth(ok);
        first = false;
      }
      const next = ok === false ? HEALTH_INTERVAL_OFFLINE_MS : HEALTH_INTERVAL_ONLINE_MS;
      timer = setTimeout(run, next);
    };

    run();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [recordHealth]);

  /* ---- Auto-Scroll ---- */
  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages, isLoading, voiceState]);

  /* ---- Agent Progress Simulation ---- */
  useEffect(() => {
    let timer: any;
    if (isLoading) {
      setAgentProgress(0);
      timer = setInterval(() => {
        setAgentProgress((prev) => {
          if (prev < 4) return prev + 1;
          return prev;
        });
      }, 700);
    } else {
      setAgentProgress(0);
    }
    return () => clearInterval(timer);
  }, [isLoading]);

  /* ---- Text-to-Speech (TTS) ---- */
  const speakText = (text: string) => {
    window.speechSynthesis.cancel();
    if (!text.trim()) return;

    const utterance = new SpeechSynthesisUtterance(text);
    
    utterance.onstart = () => {
      setVoiceState("speaking");
    };
    utterance.onend = () => {
      setVoiceState("idle");
    };
    utterance.onerror = () => {
      setVoiceState("idle");
    };

    const voices = window.speechSynthesis.getVoices();
    const assistantVoice = voices.find(
      (v) =>
        v.name.includes("Google US English") ||
        v.name.includes("Microsoft Zira") ||
        v.lang === "en-US"
    );
    if (assistantVoice) {
      utterance.voice = assistantVoice;
    }
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    window.speechSynthesis.speak(utterance);
  };

  /* ---- Speech-to-Text (STT) ---- */
  const startVoiceRecognition = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice recognition not supported in this browser.");
      return;
    }

    // Cancel any current TTS
    window.speechSynthesis.cancel();

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setVoiceState("listening");
    };

    recognition.onspeechstart = () => {
      setVoiceState("understanding");
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error);
      setVoiceState("idle");
    };

    recognition.onend = () => {
      setVoiceState((prev) => (prev === "listening" || prev === "understanding" ? "idle" : prev));
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        setVoiceState("analyzing");
        handleSend(transcript);
      }
    };

    recognition.start();
  };

  const handleMicToggle = () => {
    if (voiceState === "speaking") {
      window.speechSynthesis.cancel();
      setVoiceState("idle");
      return;
    }
    if (voiceState === "listening" || voiceState === "understanding") {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      setVoiceState("idle");
      return;
    }
    startVoiceRecognition();
  };

  /* ---- Send Message ---- */
  const handleSend = async (query: string) => {
    // Add user message
    const userMsg: ChatMessageData = {
      id: nextMsgId(),
      role: "user",
      text: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setErrorMessage("");

    let location = null;
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 4000,
          maximumAge: 60000,
        });
      });
      location = {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
      };
    } catch (err) {
      console.warn("Could not get geolocation", err);
    }

    try {
      // If the free Render instance is asleep, wake it before sending the query.
      if (linkState !== "online") {
        setIsWakingBackend(true);
        setLinkState("connecting");
        const awake = await pingBackend(COLD_START_TIMEOUT_MS);
        setIsWakingBackend(false);
        recordHealth(awake);
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT_MS);
      let response: Response;
      try {
        response = await fetch(`${API_BASE}/api/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, location }),
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        throw new Error(`Diagnostics request failed with status ${response.status}`);
      }

      const resData: DiagnosticsData = await response.json();
      recordHealth(true);

      // Finish agent checklist
      setAgentProgress(5);

      // Add copilot response
      const copilotMsg: ChatMessageData = {
        id: nextMsgId(),
        role: "copilot",
        text: "Diagnostic analysis complete. Here are the results:",
        timestamp: new Date(),
        diagnostics: resData,
      };
      setMessages((prev) => [...prev, copilotMsg]);

      // Conversational Voice Readout
      if (voiceEnabled && resData.summary) {
        const sum = resData.summary;
        const raw = resData.raw_agents_data;
        let speechParts: string[] = [];

        if (sum.risk_level) {
          const rl = sum.risk_level.toUpperCase();
          if (rl === "CRITICAL" || rl === "HIGH") {
            speechParts.push(`Warning. Risk level is ${rl.toLowerCase()}.`);
          } else {
            speechParts.push(`Risk level is ${rl.toLowerCase()}.`);
          }
        }
        if (sum.issue_summary) {
          speechParts.push(sum.issue_summary);
        }
        if (sum.recommended_action && sum.recommended_action.length > 0) {
          speechParts.push(...sum.recommended_action.slice(0, 3));
        }
        if (sum.safety_advice && sum.safety_advice.length > 0) {
          speechParts.push(...sum.safety_advice.slice(0, 2));
        }
        if (raw?.service_centre && raw.service_centre.length > 0) {
          speechParts.push("The nearest service centre has been identified.");
        }

        const speechText = speechParts.join(". ");
        speakText(speechText);
      } else {
        setVoiceState("idle");
      }
    } catch (err: any) {
      console.error(err);
      setIsWakingBackend(false);
      const timedOut = err?.name === "AbortError";
      setErrorMessage(
        timedOut
          ? "The diagnostic backend took too long to answer."
          : "System diagnostic connection failed."
      );
      // Add error copilot message
      const errorMsg: ChatMessageData = {
        id: nextMsgId(),
        role: "copilot",
        text: timedOut
          ? "⚠️ The diagnostic backend took too long to respond. The free server may still be starting up. Please send your question again in a few seconds."
          : "⚠️ I couldn't reach the diagnostic backend. The free server may be waking up. Please try again in a few seconds.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setVoiceState("idle");
    } finally {
      setIsLoading(false);
    }
  };

  /* ---- Quick Action Click ---- */
  const handleQuickAction = (query: string) => {
    setSidebarOpen(false);
    handleSend(query);
  };

  return (
    <div className="app-container">
      {/* ======== SIDEBAR ======== */}
      <aside className={`chat-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Cpu
              size={20}
              style={{
                color: "var(--cyber-cyan)",
                filter: "drop-shadow(0 0 5px var(--cyber-cyan))",
              }}
            />
            <div>
              <h1>VEHICLE COPILOT</h1>
              <span className="version-badge">v2.0</span>
            </div>
          </div>

          {/* Close btn for mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            style={{
              display: "none",
              background: "transparent",
              border: "none",
              color: "var(--text-secondary)",
              cursor: "pointer",
              marginLeft: "auto",
            }}
            className="sidebar-close-btn"
          >
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-status" title={linkState === "connecting" ? "The free backend server sleeps when idle and can take up to a minute to wake up." : undefined}>
          <span className={`status-dot ${linkState}`} />
          {linkState === "online" && "TELEMETRY LINK ONLINE"}
          {linkState === "connecting" && "ESTABLISHING TELEMETRY LINK..."}
          {linkState === "offline" && "TELEMETRY LINK OFFLINE"}
        </div>

        <div className="sidebar-section-title">Settings</div>
        <div className="quick-actions" style={{ marginBottom: "1rem" }}>
          <div
            className="quick-action-chip"
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            style={{ justifyContent: "space-between", display: "flex", width: "100%" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span className="chip-icon">🔊</span>
              Voice Responses
            </span>
            <span style={{ color: voiceEnabled ? "var(--cyber-green)" : "var(--text-secondary)", fontWeight: "bold" }}>
              {voiceEnabled ? "ON" : "OFF"}
            </span>
          </div>
        </div>

        <div className="sidebar-section-title">Quick Diagnostics</div>
        <div className="quick-actions">
          {QUICK_ACTIONS.map((action, idx) => (
            <div
              key={idx}
              className="quick-action-chip"
              onClick={() => handleQuickAction(action.query)}
            >
              <span className="chip-icon">{action.icon}</span>
              {action.label}
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          VEHICLE COPILOT HUD v2.0
          <br />
          DEEP INTEGRATION ACTIVE
        </div>
      </aside>

      {/* ======== MAIN CHAT ======== */}
      <div className="chat-main">
        {/* Chat Header */}
        <div className="chat-header">
          <div className="chat-header-title">
            {/* Mobile hamburger */}
            <button
              onClick={() => setSidebarOpen(true)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--cyber-cyan)",
                cursor: "pointer",
                padding: "0.25rem",
                display: "none",
              }}
              className="hamburger-btn"
            >
              <Menu size={20} />
            </button>
            <Bot
              size={20}
              style={{
                color: "var(--cyber-cyan)",
                filter: "drop-shadow(0 0 4px var(--cyber-cyan))",
              }}
            />
            <div>
              <h2>Copilot Chat</h2>
              <span className="subtitle">
                AI-POWERED VEHICLE CO-DRIVER DIAGNOSTIC NET
              </span>
            </div>
          </div>

          <div className="chat-header-actions">
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor:
                    linkState === "online"
                      ? "var(--cyber-green)"
                      : linkState === "connecting"
                        ? "var(--cyber-yellow)"
                        : "var(--cyber-red)",
                  boxShadow:
                    linkState === "online"
                      ? "var(--glow-green)"
                      : linkState === "connecting"
                        ? "var(--glow-yellow)"
                        : "var(--glow-red)",
                  display: "inline-block",
                }}
              />
              {linkState === "online" ? "ONLINE" : linkState === "connecting" ? "CONNECTING" : "OFFLINE"}
            </span>
          </div>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div style={{ padding: "0.5rem 1.5rem 0" }}>
            <div className="chat-error">
              ❌ {errorMessage}
              {import.meta.env.DEV ? (
                <span className="error-hint">
                  Run: <code>uvicorn main:app --reload --port 8000</code>
                </span>
              ) : (
                <span className="error-hint">
                  The backend sleeps when idle and can take up to a minute to wake. Try again shortly.
                </span>
              )}
            </div>
          </div>
        )}

        {/* Chat Thread */}
        <div className="chat-thread" ref={threadRef}>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Voice State HUD Overlay */}
          {voiceState !== "idle" && voiceState !== "analyzing" && (
            <div className="typing-indicator-wrapper" style={{ margin: "0.5rem 0" }}>
              <div className="chat-avatar copilot-avatar">
                <Bot size={18} />
              </div>
              <div className="typing-bubble">
                <span className="typing-label">
                  {voiceState === "listening" && "🎤 Listening..."}
                  {voiceState === "understanding" && "🧠 Understanding..."}
                  {voiceState === "speaking" && "🔊 Speaking..."}
                </span>
                
                {voiceState === "listening" && (
                  <div className="recording-waves" style={{ margin: "0.5rem 0" }}>
                    <div className="recording-wave-bar" />
                    <div className="recording-wave-bar" />
                    <div className="recording-wave-bar" />
                    <div className="recording-wave-bar" />
                    <div className="recording-wave-bar" />
                  </div>
                )}
                
                <div className="scan-line" />
              </div>
            </div>
          )}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="typing-indicator-wrapper">
              <div className="chat-avatar copilot-avatar">
                <Bot size={18} />
              </div>
              <div className="typing-bubble">
                <span className="typing-label">Analyzing</span>
                <div className="typing-dots">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
                <div className="scan-line" />
                <span className="typing-subtext">
                  {isWakingBackend && "WAKING UP BACKEND SERVER (UP TO 1 MIN)..."}
                  {!isWakingBackend && agentProgress === 0 && "RUNNING MANUAL AGENT..."}
                  {!isWakingBackend && agentProgress === 1 && "RUNNING WEATHER AGENT..."}
                  {!isWakingBackend && agentProgress === 2 && "RUNNING SAFETY AGENT..."}
                  {!isWakingBackend && agentProgress === 3 && "RUNNING SERVICE CENTRE AGENT..."}
                  {!isWakingBackend && agentProgress >= 4 && "CORRELATING DATA WITH GEMINI..."}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <ChatInputBar
          onSend={handleSend}
          isLoading={isLoading}
          linkState={linkState}
          voiceState={voiceState}
          onVoiceToggle={handleMicToggle}
        />
      </div>
    </div>
  );
}

export default App;
