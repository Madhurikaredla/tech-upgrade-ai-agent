import { useEffect, useState } from "react";
import {
  deleteSession,
  fetchSessions,
} from "../services/programConfig.service";
import type { StoredSession } from "../types/chat";

export interface UseSessionsReturn {
  storedSessions: StoredSession[];
  showHistory: boolean;
  openHistory: () => void;
  closeHistory: () => void;
  toggleHistory: () => void;
  removeSession: (e: React.MouseEvent, id: string) => Promise<void>;
  refreshSessions: () => void;
}

export function useSessions(userId: string): UseSessionsReturn {
  const [storedSessions, setStoredSessions] = useState<StoredSession[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchSessions(userId)
      .then(setStoredSessions)
      .catch(() => setStoredSessions([]));
  }, [userId]);

  const refreshSessions = () => {
    fetchSessions(userId)
      .then(setStoredSessions)
      .catch(() => {});
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowHistory(false);
    };
    if (showHistory) document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [showHistory]);

  const openHistory = () => setShowHistory(true);
  const closeHistory = () => setShowHistory(false);
  const toggleHistory = () => setShowHistory((v) => !v);

  const removeSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    setStoredSessions((prev) => prev.filter((s) => s.session_id !== id));
  };

  return {
    storedSessions,
    showHistory,
    openHistory,
    closeHistory,
    toggleHistory,
    removeSession,
    refreshSessions,
  };
}
