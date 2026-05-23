import { useState } from "react";
import { ApiError, sendPrompt } from "../api/client";
import type { AnalyzedPayload } from "../api/client";

interface PromptInputProps {
  userId: string;
  sessionId?: string;
  onResult?: (result: AnalyzedPayload) => void;
}

const RISK_COLOR: Record<string, string> = {
  low: "#16a34a",
  medium: "#d97706",
  high: "#ea580c",
  critical: "#dc2626",
};

export function PromptInput({ userId, sessionId, onResult }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzedPayload | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await sendPrompt({ prompt, user_id: userId, session_id: sessionId });
      if (response.success && response.data) {
        setResult(response.data);
        onResult?.(response.data);
      } else {
        setError(response.message || "Analysis failed");
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? `Error ${err.status}: ${err.message}` : "Unexpected error"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "1.5rem" }}>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt…"
          disabled={loading}
          rows={6}
          style={{
            width: "100%",
            padding: "0.75rem",
            fontSize: "1rem",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            resize: "vertical",
            fontFamily: "inherit",
            boxSizing: "border-box",
          }}
        />
        <button
          type="submit"
          disabled={loading || !prompt.trim()}
          style={{
            marginTop: "0.75rem",
            padding: "0.6rem 1.5rem",
            fontSize: "1rem",
            background: loading ? "#6b7280" : "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {error && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem",
            background: "#fef2f2",
            color: "#dc2626",
            borderRadius: 6,
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1rem",
            background: "#f9fafb",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
          }}
        >
          <div
            style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}
          >
            <span style={{ fontWeight: 600 }}>Risk Level:</span>
            <span
              style={{
                padding: "0.2rem 0.6rem",
                borderRadius: 4,
                background: (RISK_COLOR[result.risk_level] ?? "#6b7280") + "22",
                color: RISK_COLOR[result.risk_level] ?? "#6b7280",
                fontWeight: 700,
                fontSize: "0.875rem",
                textTransform: "uppercase",
              }}
            >
              {result.risk_level}
            </span>
          </div>

          <p style={{ margin: 0, lineHeight: 1.6 }}>{result.summary}</p>

          {Object.keys(result.details).length > 0 && (
            <pre
              style={{
                marginTop: "0.75rem",
                fontSize: "0.8rem",
                overflow: "auto",
                background: "#fff",
                padding: "0.75rem",
                borderRadius: 4,
                border: "1px solid #e5e7eb",
              }}
            >
              {JSON.stringify(result.details, null, 2)}
            </pre>
          )}

          <p style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#9ca3af" }}>
            Payload ID: {result.payload_id} · Tokens: {result.tokens_used}
          </p>
        </div>
      )}
    </div>
  );
}
