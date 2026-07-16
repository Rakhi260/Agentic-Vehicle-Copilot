import { useState } from "react";
import type React from "react";
import {
  AlertOctagon,
  CheckCircle2,
  ShieldAlert,
  ShieldCheck,
  Thermometer,
  Wind,
  Droplets,
  Eye,
  Compass,
  CloudRain,
  Terminal,
  FileText,
  Wrench,
  Navigation,
  AlertTriangle,
  Zap,
  Bot,
  User,
  Phone,
  ExternalLink,
} from "lucide-react";

/* ============================================
   Types
   ============================================ */

interface DiagnosticsData {
  query: string;
  processing_time: string;
  raw_agents_data: {
    risk: string;
    weather: any;
    manual: string;
    service_centre: any[];
  };
  summary: {
    issue_summary: string;
    risk_level: string;
    weather_impact: string;
    recommended_action: string[];
    safety_advice: string[];
    manual_summary?: any;
  };
}

export interface ChatMessageData {
  id: string;
  role: "user" | "copilot";
  text: string;
  timestamp: Date;
  diagnostics?: DiagnosticsData;
  isWelcome?: boolean;
}

interface ChatMessageProps {
  message: ChatMessageData;
}

/* ============================================
   Helper: Format Time
   ============================================ */

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ============================================
   Risk Details
   ============================================ */

function getRiskDetails(level: string) {
  const l = level.toUpperCase();
  if (l === "CRITICAL") {
    return {
      color: "var(--cyber-red)",
      percentage: 100,
      icon: <AlertOctagon size={14} color="var(--cyber-red)" />,
      borderClass: "risk-border-critical",
    };
  } else if (l === "HIGH") {
    return {
      color: "var(--cyber-orange)",
      percentage: 75,
      icon: <ShieldAlert size={14} color="var(--cyber-orange)" />,
      borderClass: "risk-border-high",
    };
  } else if (l === "MEDIUM") {
    return {
      color: "var(--cyber-yellow)",
      percentage: 50,
      icon: <ShieldAlert size={14} color="var(--cyber-yellow)" />,
      borderClass: "risk-border-medium",
    };
  } else {
    return {
      color: "var(--cyber-green)",
      percentage: 25,
      icon: <CheckCircle2 size={14} color="var(--cyber-green)" />,
      borderClass: "risk-border-low",
    };
  }
}

/* ============================================
   Sub-Components for Copilot Bubbles
   ============================================ */

const RiskSection: React.FC<{
  riskLevel: string;
  issueSummary: string;
}> = ({ riskLevel, issueSummary }) => {
  const details = getRiskDetails(riskLevel);
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (details.percentage / 100) * circumference;

  return (
    <div className={`risk-section ${details.borderClass}`}>
      <div className="risk-gauge-mini">
        <svg viewBox="0 0 72 72">
          <circle className="gauge-bg" cx="36" cy="36" r={radius} />
          <circle
            className="gauge-fill"
            cx="36"
            cy="36"
            r={radius}
            stroke={details.color}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ filter: `drop-shadow(0 0 3px ${details.color})` }}
          />
        </svg>
        <div className="risk-gauge-label">
          <div className="risk-text" style={{ color: details.color }}>
            {riskLevel}
          </div>
          <div className="risk-sub">RISK</div>
        </div>
      </div>
      <div className="risk-info">
        <div className="risk-title">Issue Analysis</div>
        <p className="risk-summary">{issueSummary}</p>
      </div>
    </div>
  );
};

const WeatherSection: React.FC<{
  weather: any;
  weatherImpact?: string;
}> = ({ weather, weatherImpact }) => {
  if (!weather || weather.error) return null;

  return (
    <div className="weather-section">
      <div className="weather-section-header">
        <h4>
          <CloudRain size={13} />
          Cabin Telemetry
        </h4>
        {weather.condition && (
          <span className="condition-tag">{weather.condition}</span>
        )}
      </div>

      <div className="weather-metrics">
        {weather.temperature !== undefined && (
          <div className="weather-metric">
            <Thermometer size={14} className="metric-icon" />
            <div className="wm-val">{weather.temperature}°C</div>
            <div className="wm-label">Temp</div>
          </div>
        )}
        {weather.feels_like !== undefined && (
          <div className="weather-metric">
            <Thermometer size={14} className="metric-icon" style={{ color: "var(--cyber-blue)" }} />
            <div className="wm-val">{weather.feels_like}°C</div>
            <div className="wm-label">Feels</div>
          </div>
        )}
        {weather.humidity !== undefined && (
          <div className="weather-metric">
            <Droplets size={14} className="metric-icon" />
            <div className="wm-val">{weather.humidity}%</div>
            <div className="wm-label">Humid</div>
          </div>
        )}
        {weather.wind_speed !== undefined && (
          <div className="weather-metric">
            <Wind size={14} className="metric-icon" />
            <div className="wm-val">{weather.wind_speed}</div>
            <div className="wm-label">Wind m/s</div>
          </div>
        )}
        {weather.visibility !== undefined && (
          <div className="weather-metric">
            <Eye size={14} className="metric-icon" />
            <div className="wm-val">{weather.visibility}</div>
            <div className="wm-label">Vis km</div>
          </div>
        )}
        {weather.pressure !== undefined && (
          <div className="weather-metric">
            <Compass size={14} className="metric-icon" />
            <div className="wm-val">{weather.pressure}</div>
            <div className="wm-label">hPa</div>
          </div>
        )}
      </div>

      {weatherImpact && (
        <div className="weather-impact-note">
          <span className="weather-impact-label">Environmental Impact</span>
          {weatherImpact}
        </div>
      )}
    </div>
  );
};

const ActionsSection: React.FC<{ actions: string[] }> = ({ actions }) => {
  if (!actions || actions.length === 0) return null;
  return (
    <div className="actions-section">
      <h4>
        <Zap size={13} style={{ color: "var(--cyber-cyan)" }} /> Recommended
        Actions
      </h4>
      {actions.map((act, idx) => (
        <div key={idx} className="action-item">
          <span className="action-bullet">›</span>
          <span>{act}</span>
        </div>
      ))}
    </div>
  );
};

const SafetySection: React.FC<{ advice: string[] }> = ({ advice }) => {
  if (!advice || advice.length === 0) return null;
  return (
    <div className="safety-section">
      <h4>
        <AlertTriangle size={12} /> Safety Warnings
      </h4>
      {advice.map((adv, idx) => (
        <div key={idx} className="safety-item">
          <span className="safety-bullet">•</span>
          <span>{adv}</span>
        </div>
      ))}
    </div>
  );
};

const ManualSection: React.FC<{ manualText?: string; manualSummary?: any }> = ({ manualText, manualSummary }) => {
  const [isOpen, setIsOpen] = useState(false);

  const hasSummary = manualSummary && (
    (manualSummary.immediate_actions && manualSummary.immediate_actions.length > 0) ||
    (manualSummary.warnings && manualSummary.warnings.length > 0) ||
    (manualSummary.recommended_steps && manualSummary.recommended_steps.length > 0) ||
    (manualSummary.preventive_tips && manualSummary.preventive_tips.length > 0)
  );

  const hasRaw = manualText && manualText !== "Not Available";

  if (!hasSummary && !hasRaw) return null;

  const lines = hasRaw
    ? manualText!
        .split("\n")
        .filter((line) => line.trim().length > 0)
    : [];

  return (
    <div className="manual-section" style={{ padding: "0.75rem", background: "rgba(8, 15, 26, 0.4)", border: "1px solid rgba(0, 242, 254, 0.06)", borderRadius: "8px" }}>
      <h4 style={{ margin: "0 0 0.5rem", fontFamily: "Orbitron, sans-serif", fontSize: "0.7rem", color: "var(--cyber-cyan)", textTransform: "uppercase", letterSpacing: "1px", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        <FileText size={12} /> Vehicle Manual Summary
      </h4>
      
      {hasSummary && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {manualSummary.immediate_actions && manualSummary.immediate_actions.length > 0 && (
            <div>
              <span style={{ fontSize: "0.65rem", color: "var(--cyber-red)", fontWeight: "bold", textTransform: "uppercase", fontFamily: "Orbitron" }}>⚠️ Immediate Actions</span>
              {manualSummary.immediate_actions.map((act: string, idx: number) => (
                <div key={idx} style={{ fontSize: "0.82rem", color: "var(--text-primary)", display: "flex", gap: "0.3rem", padding: "1px 0" }}>
                  <span style={{ color: "var(--cyber-red)" }}>•</span>
                  <span>{act}</span>
                </div>
              ))}
            </div>
          )}

          {manualSummary.warnings && manualSummary.warnings.length > 0 && (
            <div>
              <span style={{ fontSize: "0.65rem", color: "var(--cyber-orange)", fontWeight: "bold", textTransform: "uppercase", fontFamily: "Orbitron" }}>⚡ Warnings</span>
              {manualSummary.warnings.map((warn: string, idx: number) => (
                <div key={idx} style={{ fontSize: "0.82rem", color: "var(--text-primary)", display: "flex", gap: "0.3rem", padding: "1px 0" }}>
                  <span style={{ color: "var(--cyber-orange)" }}>•</span>
                  <span>{warn}</span>
                </div>
              ))}
            </div>
          )}

          {manualSummary.recommended_steps && manualSummary.recommended_steps.length > 0 && (
            <div>
              <span style={{ fontSize: "0.65rem", color: "var(--cyber-cyan)", fontWeight: "bold", textTransform: "uppercase", fontFamily: "Orbitron" }}>✓ Recommended Steps</span>
              {manualSummary.recommended_steps.map((step: string, idx: number) => (
                <div key={idx} style={{ fontSize: "0.82rem", color: "var(--text-primary)", display: "flex", gap: "0.3rem", padding: "1px 0" }}>
                  <span style={{ color: "var(--cyber-cyan)" }}>•</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          )}

          {manualSummary.preventive_tips && manualSummary.preventive_tips.length > 0 && (
            <div>
              <span style={{ fontSize: "0.65rem", color: "var(--cyber-green)", fontWeight: "bold", textTransform: "uppercase", fontFamily: "Orbitron" }}>🌱 Preventive Tips</span>
              {manualSummary.preventive_tips.map((tip: string, idx: number) => (
                <div key={idx} style={{ fontSize: "0.82rem", color: "var(--text-primary)", display: "flex", gap: "0.3rem", padding: "1px 0" }}>
                  <span style={{ color: "var(--cyber-green)" }}>•</span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {hasRaw && (
        <div style={{ marginTop: "0.75rem" }}>
          <button 
            className="map-link" 
            style={{ width: "100%", justifyContent: "center", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.3rem" }}
            onClick={() => setIsOpen(!isOpen)}
          >
            <Terminal size={10} />
            {isOpen ? "Hide Complete Manual" : "View Complete Manual"}
          </button>

          {isOpen && (
            <div className="manual-content" style={{ marginTop: "0.5rem" }}>
              {lines.map((line, idx) => (
                <div key={idx} className="manual-line">
                  <span className="line-num">
                    [{String(idx + 1).padStart(3, "0")}]
                  </span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const ServiceSection: React.FC<{ centres?: any[] }> = ({ centres }) => {
  if (!centres || centres.length === 0) return null;
  return (
    <div className="service-section">
      <h4>
        <Wrench size={13} /> Nearby Workshops
      </h4>
      {centres.map((centre: any, idx: number) => {
        const navigateUrl = `https://www.google.com/maps/dir/?api=1&destination=${centre.latitude},${centre.longitude}`;
        const mapsUrl = `https://www.google.com/maps?q=${centre.latitude},${centre.longitude}`;
        return (
          <div key={idx} className="service-card">
            <div className="service-name" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <span className="svc-dot" />
                {centre.name}
              </span>
              {centre.distance && (
                <span style={{ fontFamily: "Share Tech Mono, monospace", fontSize: "0.75rem", color: "var(--cyber-cyan)" }}>
                  {centre.distance}
                </span>
              )}
            </div>
            <div className="service-address">{centre.address}</div>
            {centre.latitude && centre.longitude && (
              <div className="service-footer" style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.25rem", justifyContent: "space-between", width: "100%" }}>
                <span className="service-coords" style={{ alignSelf: "center" }}>
                  GPS: {parseFloat(centre.latitude).toFixed(4)}°N,{" "}
                  {parseFloat(centre.longitude).toFixed(4)}°E
                </span>
                <div style={{ display: "flex", gap: "0.4rem" }}>
                  {centre.phone && (
                    <a
                      href={`tel:${centre.phone}`}
                      className="map-link"
                      title="Call workshop"
                      style={{ padding: "0.3rem 0.5rem" }}
                    >
                      <Phone size={10} />
                      Call
                    </a>
                  )}
                  <a
                    href={navigateUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="map-link"
                    title="Navigate driving directions"
                    style={{ padding: "0.3rem 0.5rem" }}
                  >
                    <Navigation size={10} />
                    Navigate
                  </a>
                  <a
                    href={mapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="map-link"
                    title="Open place location in Google Maps"
                    style={{ padding: "0.3rem 0.5rem" }}
                  >
                    <ExternalLink size={10} />
                    Maps
                  </a>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

/* ============================================
   Welcome Message Content
   ============================================ */

const WelcomeContent: React.FC = () => (
  <div className="welcome-content">
    <h3>
      Welcome to Vehicle Copilot
    </h3>
    <p>
      I'm your AI-powered vehicle co-driver. Describe any vehicle issue,
      warning light, or driving concern and I'll run a comprehensive diagnostic
      analysis with real-time data.
    </p>
    <div className="welcome-features">
      <span className="welcome-feature-tag">
        <ShieldCheck size={12} className="feat-icon" /> Risk Assessment
      </span>
      <span className="welcome-feature-tag">
        <CloudRain size={12} className="feat-icon" /> Weather Telemetry
      </span>
      <span className="welcome-feature-tag">
        <FileText size={12} className="feat-icon" /> Manual Lookup
      </span>
      <span className="welcome-feature-tag">
        <Wrench size={12} className="feat-icon" /> Service Locator
      </span>
    </div>
  </div>
);

/* ============================================
   Main ChatMessage Component
   ============================================ */

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { role, text, timestamp, diagnostics, isWelcome } = message;

  /* ---- User Message ---- */
  if (role === "user") {
    return (
      <div className="chat-message user">
        <div className="chat-avatar user-avatar">
          <User size={18} />
        </div>
        <div>
          <div className="chat-bubble user-bubble">
            <p>{text}</p>
          </div>
          <div className="chat-timestamp">{formatTime(timestamp)}</div>
        </div>
      </div>
    );
  }

  /* ---- Copilot Welcome ---- */
  if (isWelcome) {
    return (
      <div className="chat-message copilot">
        <div className="chat-avatar copilot-avatar">
          <Bot size={18} />
        </div>
        <div>
          <div className="chat-bubble copilot-bubble">
            <WelcomeContent />
          </div>
          <div className="chat-timestamp">{formatTime(timestamp)}</div>
        </div>
      </div>
    );
  }

  /* ---- Copilot Diagnostic Response ---- */
  const summary = diagnostics?.summary;
  const raw = diagnostics?.raw_agents_data;
  const riskBorderClass = summary
    ? getRiskDetails(summary.risk_level).borderClass
    : "";

  return (
    <div className="chat-message copilot">
      <div className="chat-avatar copilot-avatar">
        <Bot size={18} />
      </div>
      <div>
        <div className={`chat-bubble copilot-bubble ${riskBorderClass}`}>
          {/* Intro text */}
          {text && <p className="copilot-text">{text}</p>}

          {/* Risk + Summary */}
          {summary && (
            <RiskSection
              riskLevel={summary.risk_level}
              issueSummary={summary.issue_summary}
            />
          )}

          {/* Weather */}
          {raw?.weather && (
            <WeatherSection
              weather={raw.weather}
              weatherImpact={summary?.weather_impact}
            />
          )}

          {/* Recommended Actions */}
          {summary?.recommended_action && (
            <ActionsSection actions={summary.recommended_action} />
          )}

          {/* Safety Warnings */}
          {summary?.safety_advice && (
            <SafetySection advice={summary.safety_advice} />
          )}

          {/* Manual Viewer */}
          {raw?.manual && <ManualSection manualText={raw.manual} manualSummary={summary?.manual_summary} />}

          {/* Service Centre */}
          {raw?.service_centre && (
            <ServiceSection centres={raw.service_centre} />
          )}

          {/* Processing Time */}
          {diagnostics?.processing_time && (
            <div className="processing-time">
              ⚡ {diagnostics.processing_time}s
            </div>
          )}
        </div>
        <div className="chat-timestamp">{formatTime(timestamp)}</div>
      </div>
    </div>
  );
};
