import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { ProgramPreviewCard } from "../ProgramPreviewCard";
import type { Message } from "../../types/chat";
import type { UserInfo } from "../../utils/tokenUtils";
import { avatarColor } from "../../utils/tokenUtils";
import styles from "./MessageList.module.css";

function formatTime(d: Date): string {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

interface MessageListProps {
  messages: Message[];
  loading: boolean;
  error: string | null;
  lastUserText: string | null;
  userInfo: UserInfo;
  onClearError: () => void;
  onRetry: (text: string) => void;
  quickStartSlot?: ReactNode;
}

export function MessageList({
  messages,
  loading,
  error,
  lastUserText,
  userInfo,
  onClearError,
  onRetry,
  quickStartSlot,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const userBg = avatarColor(userInfo.name);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text).catch(() => {
      // best-effort copy
    });
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleRetry = () => {
    if (!lastUserText) return;
    onClearError();
    onRetry(lastUserText);
  };

  return (
    <div className={styles.messages}>
      <div className={styles.messagesInner}>
        {messages.map((msg) => (
          <div key={msg.id} className={styles.msgGroup}>
            <div
              className={styles.msgRow}
              style={{ justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}
            >
              {msg.role === "assistant" && (
                <div
                  className={styles.avatar}
                  style={{ background: "linear-gradient(135deg, #7068B8, #8578C4)" }}
                >
                  AI
                </div>
              )}
              {msg.role === "user" && (
                <button
                  type="button"
                  className={`${styles.copyBtn}${copiedId === msg.id ? ` ${styles.copyBtnCopied}` : ""}`}
                  onClick={() => handleCopy(msg.id, msg.content)}
                  title="Copy message"
                >
                  {copiedId === msg.id ? (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 13l4 4L19 7"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                      <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="1.75" />
                      <path
                        d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"
                        stroke="currentColor"
                        strokeWidth="1.75"
                      />
                    </svg>
                  )}
                </button>
              )}
              {msg.role === "assistant" && msg.dtoPreview ? (
                <ProgramPreviewCard dto={msg.dtoPreview} />
              ) : (
                <div
                  className={`${styles.bubble} ${msg.role === "user" ? styles.bubbleUser : styles.bubbleAi}`}
                  style={msg.role === "user" ? { background: userBg } : undefined}
                >
                  {msg.content.split("\n").map((line, i, arr) => (
                    <span key={`${msg.id}-line-${i}`}>
                      {line}
                      {i < arr.length - 1 && <br />}
                    </span>
                  ))}
                </div>
              )}
              {msg.role === "assistant" && (
                <button
                  type="button"
                  className={`${styles.copyBtn}${copiedId === msg.id ? ` ${styles.copyBtnCopied}` : ""}`}
                  onClick={() => handleCopy(msg.id, msg.content)}
                  title="Copy message"
                >
                  {copiedId === msg.id ? (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 13l4 4L19 7"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                      <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="1.75" />
                      <path
                        d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"
                        stroke="currentColor"
                        strokeWidth="1.75"
                      />
                    </svg>
                  )}
                </button>
              )}
              {msg.role === "user" && (
                <div className={styles.avatar} style={{ background: userBg }}>
                  {userInfo.initials}
                </div>
              )}
            </div>
            <div
              className={styles.timestampRow}
              style={{
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                paddingLeft: msg.role === "assistant" ? "2.5rem" : 0,
                paddingRight: msg.role === "user" ? "2.5rem" : 0,
              }}
            >
              <span className={styles.timestamp}>{formatTime(msg.ts)}</span>
            </div>
          </div>
        ))}

        {quickStartSlot}

        {loading && (
          <div className={styles.msgGroup}>
            <div className={styles.msgRow} style={{ justifyContent: "flex-start" }}>
              <div
                className={styles.avatar}
                style={{ background: "linear-gradient(135deg, #7068B8, #8578C4)" }}
              >
                AI
              </div>
              <div className={`${styles.bubble} ${styles.bubbleAi} ${styles.typingBubble}`}>
                <span className={styles.dot} style={{ animationDelay: "0s" }} />
                <span className={styles.dot} style={{ animationDelay: "0.18s" }} />
                <span className={styles.dot} style={{ animationDelay: "0.36s" }} />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className={styles.errorCard}>
            <div className={styles.errorRow}>
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                style={{ flexShrink: 0, marginTop: 1 }}
              >
                <circle cx="12" cy="12" r="10" stroke="#B84560" strokeWidth="1.5" />
                <path
                  d="M12 8v4M12 16h.01"
                  stroke="#B84560"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <div style={{ flex: 1 }}>
                <div className={styles.errorTitle}>Something went wrong</div>
                <div className={styles.errorBody}>{error}</div>
              </div>
              <button
                type="button"
                className={styles.errorDismiss}
                onClick={onClearError}
                title="Dismiss"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M18 6L6 18M6 6l12 12"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
            {lastUserText && (
              <button type="button" className={styles.retryBtn} onClick={handleRetry}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M1 4v6h6M23 20v-6h-6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Retry
              </button>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
