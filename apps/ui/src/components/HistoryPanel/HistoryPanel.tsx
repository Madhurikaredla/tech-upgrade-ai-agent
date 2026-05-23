import type { MouseEvent } from "react";
import { STAGE_COLORS, STAGES } from "../../constants/stages";
import type { StoredSession } from "../../types/chat";
import styles from "./HistoryPanel.module.css";

interface HistoryPanelProps {
  storedSessions: StoredSession[];
  currentSessionId: string;
  onClose: () => void;
  onNewChat: () => void;
  onLoadSession: (s: StoredSession) => void;
  onDeleteSession: (e: MouseEvent, id: string) => void;
}

export function HistoryPanel({
  storedSessions,
  currentSessionId,
  onClose,
  onNewChat,
  onLoadSession,
  onDeleteSession,
}: HistoryPanelProps) {
  const handleOverlayClick = () => onClose();
  const handlePanelClick = (e: MouseEvent) => e.stopPropagation();

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.panel} onClick={handlePanelClick}>
        <div className={styles.panelHeader}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="9" stroke="rgba(255,255,255,0.8)" strokeWidth="1.75" />
            <path
              d="M12 7v5l3 3"
              stroke="rgba(255,255,255,0.8)"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className={styles.panelTitle}>Chat History</span>
          <button type="button" className={styles.newChatBtn} onClick={onNewChat}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 5v14M5 12h14"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
            New Chat
          </button>
          <button type="button" className={styles.closeBtn} onClick={onClose} title="Close">
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

        <div className={styles.sessionList}>
          {storedSessions.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>💬</div>
              <div className={styles.emptyText}>
                No chat history yet.
                <br />
                Start a conversation to see it here.
              </div>
            </div>
          ) : (
            storedSessions.map((s) => {
              const isActive = s.session_id === currentSessionId;
              const color = STAGE_COLORS[s.stage] ?? "#7068B8";
              const stageInfo = STAGES.find((st) => st.key === s.stage);
              const date = new Date(s.updated_at);
              const dateStr = date.toLocaleDateString([], { month: "short", day: "numeric" });

              return (
                <button
                  key={s.session_id}
                  type="button"
                  className={`${styles.sessionItem}${isActive ? ` ${styles.sessionItemActive}` : ""}`}
                  onClick={() => onLoadSession(s)}
                >
                  <div className={styles.sessionInfo}>
                    <div
                      className={styles.sessionTitle}
                      style={{ color: isActive ? "#4A4770" : "#2D2A50" }}
                    >
                      {s.title}
                    </div>
                    <div className={styles.sessionMeta}>
                      <span
                        className={styles.stagePill}
                        style={{
                          background: `${color}18`,
                          color,
                        }}
                      >
                        {stageInfo?.short ?? s.stage}
                      </span>
                      <span className={styles.sessionDate}>{dateStr}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className={styles.deleteBtn}
                    onClick={(e) => onDeleteSession(e, s.session_id)}
                    title="Delete"
                  >
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"
                        stroke="currentColor"
                        strokeWidth="1.75"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
