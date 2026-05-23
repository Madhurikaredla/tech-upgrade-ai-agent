import { ApiError } from "../api/client";
import { requestJson } from "../api/http";
import {
  PROGRAM_CONFIG_API_BASE,
  PROGRAM_CONFIG_CHAT_TIMEOUT_MS,
} from "../constants/programConfig";
import type { ChatApiResponse, DisplayMessage, Stage, StoredSession } from "../types/chat";
import { getAuthToken } from "../utils/authToken";
import { getActiveRole } from "../utils/tokenUtils";

function authHeader(): Record<string, string> {
  const token = getAuthToken();
  const role = getActiveRole();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (role) headers["active-role"] = role;
  return headers;
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  userId: string
): Promise<ChatApiResponse> {
  const data = await requestJson<{
    session_id: string;
    reply: string;
    stage: Stage;
    requires_confirmation: boolean;
    program_id?: number;
    success: boolean;
    dto_preview?: Record<string, unknown>;
  }>(`${PROGRAM_CONFIG_API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
    timeoutMs: PROGRAM_CONFIG_CHAT_TIMEOUT_MS,
    retries: 1,
  });
  return data;
}

export async function fetchSessions(userId: string, signal?: AbortSignal): Promise<StoredSession[]> {
  return requestJson<StoredSession[]>(
    `${PROGRAM_CONFIG_API_BASE}/sessions?userId=${encodeURIComponent(userId)}`,
    { headers: authHeader(), signal, retries: 1 }
  );
}

export async function fetchSessionMessages(sessionId: string, signal?: AbortSignal): Promise<DisplayMessage[]> {
  return requestJson<DisplayMessage[]>(
    `${PROGRAM_CONFIG_API_BASE}/sessions/${encodeURIComponent(sessionId)}/messages`,
    { headers: authHeader(), signal, retries: 1 }
  );
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${PROGRAM_CONFIG_API_BASE}/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
    headers: authHeader(),
  });
  if (!res.ok) throw new ApiError(res.status, `domain:delete-failed-${res.status}`);
}
