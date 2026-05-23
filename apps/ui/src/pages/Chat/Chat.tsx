import { useState } from "react";
import { ChatStepper } from "../../components/ChatStepper";
import { HelpModal } from "../../components/HelpModal";
import { InputBar } from "../../components/InputBar";
import { MessageList } from "../../components/MessageList";
import { QuickStart } from "../../components/QuickStart";
import { Sidebar } from "../../components/Sidebar";
import { useChat } from "../../hooks/useChat";
import { useSessions } from "../../hooks/useSessions";
import { useVoiceInput } from "../../hooks/useVoiceInput";
import type { UserInfo } from "../../utils/tokenUtils";
import styles from "./Chat.module.css";

interface ChatProps {
  onLogout: () => void;
  userInfo: UserInfo;
}

export function Chat({ onLogout, userInfo }: ChatProps) {
  const [showHelpModal, setShowHelpModal] = useState(false);

  const chat = useChat(userInfo);
  const sessions = useSessions(userInfo.userId);
  const voice = useVoiceInput();

  const handleNewChat = () => {
    chat.newChat();
    sessions.refreshSessions();
  };

  const handleLoadSession = async (s: Parameters<typeof chat.loadSession>[0]) => {
    await chat.loadSession(s);
  };

  const handleSend = async (text: string) => {
    await chat.send(text);
    sessions.refreshSessions();
  };

  const handleUsePrompt = (text: string) => {
    setShowHelpModal(false);
    if (chat.textareaRef.current) chat.textareaRef.current.focus();
    void handleSend(text);
  };

  return (
    <div className={styles.layout}>
      <Sidebar
        userInfo={userInfo}
        storedSessions={sessions.storedSessions}
        currentSessionId={chat.sessionId}
        onNewChat={handleNewChat}
        onLoadSession={handleLoadSession}
        onDeleteSession={sessions.removeSession}
        onOpenHelp={() => setShowHelpModal(true)}
        onLogout={onLogout}
      />

      <div className={styles.main}>
        <ChatStepper currentStage={chat.currentStage} />

        <MessageList
          messages={chat.messages}
          loading={chat.loading}
          error={chat.error}
          lastUserText={chat.lastUserText}
          userInfo={userInfo}
          onClearError={chat.clearError}
          onRetry={chat.send}
          quickStartSlot={
            chat.showQuickStart && !chat.hasUserMessages ? (
              <QuickStart voiceSupported={voice.voiceSupported} />
            ) : undefined
          }
        />

        <InputBar
          currentStage={chat.currentStage}
          requiresConfirmation={chat.requiresConfirmation}
          loading={chat.loading}
          isListening={voice.isListening}
          voiceSupported={voice.voiceSupported}
          textareaRef={chat.textareaRef}
          onSend={handleSend}
          onStartListening={voice.startListening}
          onStopListening={voice.stopListening}
        />
      </div>

      {showHelpModal && (
        <HelpModal
          onClose={() => setShowHelpModal(false)}
          onUsePrompt={handleUsePrompt}
        />
      )}
    </div>
  );
}
