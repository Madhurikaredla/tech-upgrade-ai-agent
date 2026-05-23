import { useEffect } from "react";
import type { MouseEvent } from "react";
import { EXAMPLE_PROMPTS, HOW_IT_WORKS, KEY_FIELDS, QUICK_COMMANDS } from "./HelpModal.consts";
import styles from "./HelpModal.module.css";

interface HelpModalProps {
  onClose: () => void;
  onUsePrompt: (text: string) => void;
}

export function HelpModal({ onClose, onUsePrompt }: HelpModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleOverlayClick = () => onClose();
  const handleCardClick = (e: MouseEvent) => e.stopPropagation();

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.card} onClick={handleCardClick}>
        <div className={styles.header}>
          <div className={styles.headerIcon}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="#fff" strokeWidth="1.5" />
              <path
                d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"
                stroke="#fff"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <div className={styles.headerTitle}>Prompting Guide</div>
            <div className={styles.headerSubtitle}>How to describe your program to the AI</div>
          </div>
          <button type="button" className={styles.closeBtn} onClick={onClose} title="Close (Esc)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <div className={styles.body}>
          <div>
            <div className={styles.sectionTitle}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                <path
                  d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"
                  stroke="#7068B8"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              How it works
            </div>
            <div className={styles.stepsCol}>
              {HOW_IT_WORKS.map((s) => (
                <div key={s.n} className={styles.stepCard} style={{ background: s.bg }}>
                  <div className={styles.stepNum} style={{ background: s.color }}>
                    {s.n}
                  </div>
                  <div>
                    <div className={styles.stepTitle}>{s.title}</div>
                    <div className={styles.stepDesc}>{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className={styles.sectionTitle}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  stroke="#4A4770"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Key fields to mention
            </div>
            <div className={styles.chipsWrap}>
              {KEY_FIELDS.map(([label, bg, text, border]) => (
                <span
                  key={label}
                  className={styles.chip}
                  style={{ background: bg, color: text, border: `1px solid ${border}` }}
                >
                  {label}
                </span>
              ))}
            </div>
            <p className={styles.chipsNote}>
              You don&apos;t need every field — the AI will ask for what&apos;s missing.
            </p>
          </div>

          <div>
            <div className={styles.sectionTitle}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                <path
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  stroke="#4A4770"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Example prompts — click &ldquo;Use&rdquo; to try one
            </div>
            <div className={styles.examplesCol}>
              {EXAMPLE_PROMPTS.map((ex) => (
                <div key={ex.tag} className={styles.exampleRow}>
                  <div className={styles.exampleBody}>
                    <span
                      className={styles.exampleTag}
                      style={{
                        background: ex.tagBg,
                        color: ex.tagColor,
                        border: `1px solid ${ex.tagColor}40`,
                      }}
                    >
                      {ex.tag}
                    </span>
                    <p className={styles.exampleText}>{ex.text}</p>
                  </div>
                  <button
                    type="button"
                    className={styles.useBtn}
                    onClick={() => onUsePrompt(ex.text)}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 12h14M12 5l7 7-7 7"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    Use this prompt
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.quickCmds}>
            <div className={styles.quickCmdsTitle}>Quick reply commands</div>
            <div className={styles.quickCmdsCol}>
              {QUICK_COMMANDS.map((kw) => (
                <div key={kw.word} className={styles.quickCmdRow}>
                  <code className={styles.quickCmdCode}>{kw.word}</code>
                  <span className={styles.quickCmdDesc}>{kw.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <p className={styles.footer}>
            Press <kbd className={styles.footerKbd}>Esc</kbd> or click outside to close
          </p>
        </div>
      </div>
    </div>
  );
}
