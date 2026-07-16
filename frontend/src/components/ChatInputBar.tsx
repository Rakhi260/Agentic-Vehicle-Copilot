import { useState } from "react";
import type React from "react";
import { Mic, MicOff, Send, Volume2 } from "lucide-react";

interface ChatInputBarProps {
  onSend: (query: string) => void;
  isLoading: boolean;
  isBackendConnected: boolean;
  voiceState: "idle" | "listening" | "understanding" | "analyzing" | "speaking";
  onVoiceToggle: () => void;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onSend,
  isLoading,
  isBackendConnected,
  voiceState,
  onVoiceToggle,
}) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading || voiceState === "listening" || voiceState === "understanding") return;
    onSend(query.trim());
    setQuery("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isListening = voiceState === "listening" || voiceState === "understanding";

  return (
    <div className="chat-input-bar">
      {/* Recording indicator overlay inside the input bar */}
      {isListening && (
        <div className="recording-indicator" style={{ marginBottom: "0.25rem" }}>
          <div className="recording-waves">
            <div className="recording-wave-bar" />
            <div className="recording-wave-bar" />
            <div className="recording-wave-bar" />
            <div className="recording-wave-bar" />
            <div className="recording-wave-bar" />
          </div>
          <span>
            {voiceState === "listening" ? "SPEAKING DIAGNOSTIC SYMPTOMS..." : "PROCESSING AUDIO NET..."}
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-inner">
        <div className="chat-input-field">
          <input
            type="text"
            placeholder={
              isListening
                ? "Listening..."
                : voiceState === "speaking"
                  ? "Speaking response..."
                  : isBackendConnected
                    ? "Describe your vehicle issue..."
                    : "Backend offline — type a query anyway..."
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isListening}
          />

          <button
            type="button"
            className={`voice-btn ${isListening ? "recording" : ""} ${voiceState === "speaking" ? "speaking-glowing" : ""}`}
            onClick={onVoiceToggle}
            disabled={isLoading && !isListening}
            title={
              voiceState === "speaking"
                ? "Stop speech"
                : isListening
                  ? "Stop listening"
                  : "Speak issue"
            }
            style={{
              borderColor: voiceState === "speaking" ? "var(--cyber-cyan)" : undefined,
              boxShadow: voiceState === "speaking" ? "var(--glow-cyan)" : undefined,
            }}
          >
            {voiceState === "speaking" ? (
              <Volume2 size={18} className="animate-pulse" />
            ) : isListening ? (
              <Mic size={18} />
            ) : (
              <MicOff size={18} />
            )}
          </button>
        </div>

        <button
          type="submit"
          className="send-btn"
          disabled={isLoading || isListening || !query.trim()}
          title="Send"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};
