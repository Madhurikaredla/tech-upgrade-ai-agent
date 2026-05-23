import { useEffect, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { STAGE_COLORS, STAGES } from "../../constants/stages";
import type { StoredSession } from "../../types/chat";
import type { UserInfo } from "../../utils/tokenUtils";
import { avatarColor } from "../../utils/tokenUtils";
import styles from "./Sidebar.module.css";

interface SidebarProps {
  userInfo: UserInfo;
  storedSessions: StoredSession[];
  currentSessionId: string;
  onNewChat: () => void;
  onLoadSession: (s: StoredSession) => void;
  onDeleteSession: (e: MouseEvent, id: string) => void;
  onOpenHelp: () => void;
  onLogout: () => void;
}

export function Sidebar({
  userInfo,
  storedSessions,
  currentSessionId,
  onNewChat,
  onLoadSession,
  onDeleteSession,
  onOpenHelp,
  onLogout,
}: SidebarProps) {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const userBg = avatarColor(userInfo.name);

  useEffect(() => {
    const handler = (e: globalThis.MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    if (userMenuOpen) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [userMenuOpen]);

  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.brandLogo}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5z" fill="#fff" />
            <path
              d="M2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="#fff"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div>
          <div className={styles.brandTitle}>Program Config AI</div>
          <div className={styles.brandSub}>Admin Portal</div>
        </div>
      </div>

      {/* New Chat */}
      <div className={styles.newChatWrap}>
        <button type="button" className={styles.newChatBtn} onClick={onNewChat}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
          New Chat
        </button>
      </div>

      {/* History */}
      <div className={styles.historySection}>
        <div className={styles.historyLabel}>Recent Chats</div>
        <div className={styles.sessionList}>
          {storedSessions.length === 0 ? (
            <div className={styles.emptyState}>
              <span>No previous chats yet.</span>
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
                    <div className={styles.sessionTitle}>{s.title}</div>
                    <div className={styles.sessionMeta}>
                      <span
                        className={styles.stagePill}
                        style={{ background: `${color}20`, color }}
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

      {/* Bottom actions */}
      <div className={styles.bottomSection}>
        <button type="button" className={styles.helpBtn} onClick={onOpenHelp}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.75" />
            <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          Prompting Guide
        </button>

        <div className={styles.userRow} ref={menuRef}>
          <button
            type="button"
            className={styles.userBtn}
            onClick={() => setUserMenuOpen((o) => !o)}
          >
            <div className={styles.userAvatar} style={{ background: userBg }}>
              {userInfo.initials}
            </div>
            <div className={styles.userInfo}>
              <span className={styles.userName}>{userInfo.name}</span>
              <span className={styles.userRole}>{userInfo.displayRole}</span>
            </div>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" className={styles.userChevron}>
              <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {userMenuOpen && (
            <div className={styles.userMenu}>
              <button
                type="button"
                className={`${styles.menuItem} ${styles.menuItemDanger}`}
                onClick={() => { setUserMenuOpen(false); onLogout(); }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
