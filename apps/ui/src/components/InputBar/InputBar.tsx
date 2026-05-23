import { useCallback, useState } from "react";
import type { ChangeEvent, KeyboardEvent, RefObject } from "react";
import { CONFIRM_BUTTONS } from "../../constants/stages";
import type { Stage } from "../../types/chat";
import styles from "./InputBar.module.css";

interface InputBarProps {
  currentStage: Stage;
  requiresConfirmation: boolean;
  loading: boolean;
  isListening: boolean;
  voiceSupported: boolean;
  textareaRef: RefObject<HTMLTextAreaElement>;
  onSend: (text: string) => void;
  onStartListening: (onTranscript: (text: string) => void) => void;
  onStopListening: () => void;
}

export function InputBar({
  currentStage,
  requiresConfirmation,
  loading,
  isListening,
  voiceSupported,
  textareaRef,
  onSend,
  onStartListening,
  onStopListening,
}: InputBarProps) {
  const [input, setInput] = useState("");

  const confirmBtns = CONFIRM_BUTTONS[currentStage];

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [textareaRef]);

  const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        onSend(input.trim());
        setInput("");
        if (textareaRef.current) textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim());
      setInput("");
      if (textareaRef.current) textareaRef.current.style.height = "auto";
    }
  };

  const handleConfirm = (value: string) => {
    onSend(value);
  };

  const handleVoiceTranscript = useCallback(
    (text: string) => {
      setInput(text);
      if (textareaRef.current) {
        textareaRef.current.value = text;
        resizeTextarea();
      }
    },
    [textareaRef, resizeTextarea]
  );

  const handleMicClick = () => {
    if (isListening) {
      onStopListening();
    } else {
      onStartListening(handleVoiceTranscript);
    }
  };

  return (
    <div className={styles.inputArea}>
      {requiresConfirmation && confirmBtns && (
        <div className={styles.confirmBar}>
          {confirmBtns.map((btn) => (
            <button
              key={btn.value}
              type="button"
              disabled={loading}
              className={`${styles.confirmBtn} ${btn.primary ? styles.confirmBtnPrimary : styles.confirmBtnSecondary}`}
              onClick={() => handleConfirm(btn.value)}
            >
              {btn.label}
            </button>
          ))}
        </div>
      )}

      {isListening && (
        <div className={styles.listeningIndicator}>
          <span className={styles.listeningDot} />
          Listening… speak your program description. Release mic to auto-send.
        </div>
      )}

      <div className={`${styles.inputBox}${isListening ? ` ${styles.inputBoxListening}` : ""}`}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? "Speaking…"
              : loading
              ? "Generating response… (you can keep typing)"
              : "Describe the program you want to create… (Enter to send)"
          }
          rows={1}
          className={styles.textarea}
        />

        {voiceSupported && (
          <button
            type="button"
            onClick={handleMicClick}
            disabled={loading}
            className={`${styles.micBtn}${isListening ? ` ${styles.micBtnListening}` : ""}`}
            title={isListening ? "Stop recording" : "Voice input (click to speak)"}
          >
            {isListening && <div className={styles.micRing} />}
            {isListening && <div className={`${styles.micRing} ${styles.micRing2}`} />}
            {isListening ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="6" width="12" height="12" rx="2" fill="#D96070" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                />
                <path
                  d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </button>
        )}

        <button
          type="button"
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className={styles.sendBtn}
          title="Send (Enter)"
        >
          {loading ? (
            <span className={styles.spinner} />
          ) : (
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <path
                d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>
      </div>

      <p className={styles.hint}>
        Press <kbd className={styles.hintKbd}>Enter</kbd> to send ·{" "}
        <kbd className={styles.hintKbd}>Shift+Enter</kbd> for new line
        {voiceSupported && " · 🎙 mic for voice"}
      </p>
    </div>
  );
}
