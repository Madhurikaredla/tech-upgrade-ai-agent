import { useEffect, useRef, useState } from "react";
import { STAGE_COLORS, STAGE_INDEX, STAGES } from "../../constants/stages";
import type { Stage } from "../../types/chat";
import type { UserInfo } from "../../utils/tokenUtils";
import { avatarColor } from "../../utils/tokenUtils";
import styles from "./ChatHeader.module.css";

interface ChatHeaderProps {
  userInfo: UserInfo;
  currentStage: Stage;
  showHistory: boolean;
  showHelpModal: boolean;
  onToggleHistory: () => void;
  onNewChat: () => void;
  onOpenHelp: () => void;
  onLogout: () => void;
}

export function ChatHeader({
  userInfo,
  currentStage,
  showHistory,
  showHelpModal,
  onToggleHistory,
  onNewChat,
  onOpenHelp,
  onLogout,
}: ChatHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const userBg = avatarColor(userInfo.name);
  const currentStageIdx = STAGE_INDEX[currentStage] ?? 0;
  const stageColor = STAGE_COLORS[currentStage] ?? "#7068B8";
  const stageLabel = STAGES[currentStageIdx]?.label ?? currentStage;

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  const handleOpenHelp = () => {
    onOpenHelp();
    setMenuOpen(false);
  };

  const handleLogout = () => {
    setMenuOpen(false);
    onLogout();
  };

  const dotColor = stageColor === "#7068B8" ? "#C8C4F0" : stageColor;
  const dotShadow = stageColor === "#7068B8" ? "rgba(200,196,240,0.8)" : stageColor;

  return (
    <header className={styles.header}>
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
          <div className={styles.brandSubtitle}>Admin Portal</div>
        </div>
      </div>

      <div className={styles.center}>
        <button
          type="button"
          className={styles.histIconBtn}
          onClick={onToggleHistory}
          title="Chat history"
          aria-pressed={showHistory}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.75" />
            <path
              d="M12 7v5l3 3"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        <button
          type="button"
          className={styles.newChatBtn}
          onClick={onNewChat}
          title="Start a new chat"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 5v14M5 12h14"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
          New Chat
        </button>

        <div className={styles.stageBadge}>
          <span
            className={currentStage !== "PUBLISHED" ? styles.stageDotPulsing : styles.stageDot}
            style={{
              background: dotColor,
              boxShadow: `0 0 6px ${dotShadow}`,
            }}
          />
          {stageLabel}
        </div>

        <button
          type="button"
          className={`${styles.helpBtn}${showHelpModal ? ` ${styles.helpBtnActive}` : ""}`}
          onClick={onOpenHelp}
          title="Prompting Guide"
        >
          ?
        </button>
      </div>

      <div className={styles.userMenuWrapper} ref={menuRef}>
        <button
          type="button"
          className={styles.userBtn}
          onClick={() => setMenuOpen((o) => !o)}
          aria-expanded={menuOpen}
        >
          <div className={styles.userAvatar} style={{ background: userBg }}>
            {userInfo.initials}
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
            <span className={styles.userName}>{userInfo.name.split(" ")[0]}</span>
            <span className={styles.userRole}>{userInfo.displayRole}</span>
          </div>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            className={styles.userChevron}
          >
            <path
              d="M6 9l6 6 6-6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {menuOpen && (
          <div className={styles.userMenu}>
            <div className={styles.menuProfile}>
              <div className={styles.menuProfileAvatar} style={{ background: userBg }}>
                {userInfo.initials}
              </div>
              <div>
                <div className={styles.menuProfileName}>{userInfo.name}</div>
                <div className={styles.menuProfileRole}>{userInfo.displayRole}</div>
              </div>
            </div>
            <button type="button" className={styles.menuItem} onClick={handleOpenHelp}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#7A788E" strokeWidth="1.5" />
                <path
                  d="M12 8v4M12 16h.01"
                  stroke="#7A788E"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              Prompting Guide
            </button>
            <button
              type="button"
              className={`${styles.menuItem} ${styles.menuItemDanger}`}
              onClick={handleLogout}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <path
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  stroke="#B84560"
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
    </header>
  );
}
