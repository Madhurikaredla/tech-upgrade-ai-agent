import { getAuthToken } from "../utils/authToken";

export interface PromptRequestBody {
  prompt: string;
  user_id: string;
  session_id?: string;
}

export interface AnalyzedPayload {
  payload_id: string;
  summary: string;
  risk_level: "low" | "medium" | "high" | "critical";
  details: Record<string, unknown>;
  tokens_used: number;
}

export interface AgentResponse {
  success: boolean;
  data: AnalyzedPayload | null;
  message: string;
  request_id: string;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function authHeader(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function sendPrompt(body: PromptRequestBody): Promise<AgentResponse> {
  const res = await fetch("/api/v1/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }

  return res.json() as Promise<AgentResponse>;
}
