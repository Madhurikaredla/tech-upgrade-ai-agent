import { useRef, useState } from "react";
import type { RefObject } from "react";
import { ApiError } from "../api/client";
import { CONFIRM_BUTTONS } from "../constants/stages";
import {
  fetchSessionMessages,
  sendChatMessage,
} from "../services/programConfig.service";
import type { Message, Stage, StoredSession } from "../types/chat";
import type { UserInfo } from "../utils/tokenUtils";

function generateSessionId(): string {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

function makeWelcome(name: string): Message {
  return {
    id: "welcome",
    role: "assistant",
    content: `Hello${name !== "Admin User" ? ` ${name.split(" ")[0]}` : ""}! I am your Program Configuration Assistant.\n\nDescribe the program you would like to create and I will guide you through the setup step by step. Or pick a quick example below to get started.`,
    stage: "COLLECTING",
    ts: new Date(),
  };
}

export interface UseChatReturn {
  sessionId: string;
  messages: Message[];
  loading: boolean;
  error: string | null;
  currentStage: Stage;
  requiresConfirmation: boolean;
  lastUserText: string | null;
  showQuickStart: boolean;
  hasUserMessages: boolean;
  send: (text: string) => Promise<void>;
  newChat: () => void;
  loadSession: (s: StoredSession) => Promise<void>;
  clearError: () => void;
  setShowQuickStart: (v: boolean) => void;
  textareaRef: RefObject<HTMLTextAreaElement>;
}

export function useChat(userInfo: UserInfo): UseChatReturn {
  const [sessionId, setSessionId] = useState(generateSessionId);
  const [messages, setMessages] = useState<Message[]>(() => [makeWelcome(userInfo.name)]);
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<Stage>("COLLECTING");
  const [error, setError] = useState<string | null>(null);
  const [requiresConfirmation, setRequiresConfirmation] = useState(false);
  const [lastUserText, setLastUserText] = useState<string | null>(null);
  const [showQuickStart, setShowQuickStart] = useState(true);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const hasUserMessages = messages.some((m) => m.role === "user");

  const newChat = () => {
    setSessionId(generateSessionId());
    setMessages([makeWelcome(userInfo.name)]);
    setCurrentStage("COLLECTING");
    setRequiresConfirmation(false);
    setShowQuickStart(true);
    setError(null);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const loadSession = async (s: StoredSession) => {
    const raw = await fetchSessionMessages(s.session_id);
    const msgs: Message[] = raw.map((m) => ({
      ...m,
      ts: new Date(m.ts as string),
      dtoPreview: m.dto_preview,
    }));
    if (!msgs.length) return;
    setSessionId(s.session_id);
    setMessages([makeWelcome(userInfo.name), ...msgs]);
    setCurrentStage(s.stage);
    setRequiresConfirmation(s.stage in CONFIRM_BUTTONS);
    setShowQuickStart(false);
    setError(null);
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setShowQuickStart(false);
    setLastUserText(trimmed);
    setRequiresConfirmation(false);

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: "user",
      content: trimmed,
      ts: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setError(null);
    setLoading(true);

    try {
      const res = await sendChatMessage(trimmed, sessionId, userInfo.userId);
      setCurrentStage(res.stage);
      setRequiresConfirmation(res.requires_confirmation ?? false);
      setMessages((prev) => [
        ...prev,
        {
          id: `a_${Date.now()}`,
          role: "assistant",
          content: res.reply,
          stage: res.stage,
          ts: new Date(),
          dtoPreview: res.dto_preview,
        },
      ]);
    } catch (err) {
      const raw = err instanceof ApiError ? err.message : "";
      let friendly: string;
      if (raw.startsWith("infra:timeout")) {
        friendly =
          "The request timed out — the server took too long to respond. Please try again in a moment.";
      } else if (raw.startsWith("infra:network") || raw === "") {
        friendly =
          "Cannot reach the server. Please check that the backend is running and try again.";
      } else if (raw.startsWith("validation:")) {
        friendly = raw.replace("validation:", "").trim() || "Please review the request and try again.";
      } else if (raw.startsWith("domain:")) {
        friendly = "The request could not be completed in the current workflow state.";
      } else if (raw.toLowerCase().includes("agent error") || raw.toLowerCase().includes("see logs")) {
        friendly =
          "The AI assistant hit an unexpected error. Please try rephrasing your message or try again.";
      } else {
        friendly = raw || "Something went wrong. Please try again.";
      }
      setError(friendly);
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return {
    sessionId,
    messages,
    loading,
    error,
    currentStage,
    requiresConfirmation,
    lastUserText,
    showQuickStart,
    hasUserMessages,
    send,
    newChat,
    loadSession,
    clearError,
    setShowQuickStart,
    textareaRef,
  };
}
