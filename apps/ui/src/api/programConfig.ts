import { ApiError } from "./client";
import { getAuthToken } from "../utils/authToken";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  stage?: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  stage: string;
  requires_confirmation: boolean;
  program_id?: number;
  success: boolean;
}

export interface StoredSession {
  session_id: string;
  title: string;
  stage: string;
  updated_at: string;
}

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  stage?: string;
  ts: string;
}

function authHeader(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  userId: string
): Promise<ChatResponse> {
  const res = await fetch("/api/v1/program-config/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }

  return res.json() as Promise<ChatResponse>;
}

export async function fetchSessions(userId: string): Promise<StoredSession[]> {
  try {
    const res = await fetch(
      `/api/v1/program-config/sessions?userId=${encodeURIComponent(userId)}`,
      { headers: authHeader() }
    );
    if (!res.ok) return [];
    return res.json() as Promise<StoredSession[]>;
  } catch {
    return [];
  }
}

export async function fetchSessionMessages(sessionId: string): Promise<DisplayMessage[]> {
  try {
    const res = await fetch(
      `/api/v1/program-config/sessions/${encodeURIComponent(sessionId)}/messages`,
      { headers: authHeader() }
    );
    if (!res.ok) return [];
    return res.json() as Promise<DisplayMessage[]>;
  } catch {
    return [];
  }
}

export async function deleteSessionApi(sessionId: string): Promise<void> {
  try {
    await fetch(
      `/api/v1/program-config/sessions/${encodeURIComponent(sessionId)}`,
      { method: "DELETE", headers: authHeader() }
    );
  } catch {
    // best-effort delete
  }
}
