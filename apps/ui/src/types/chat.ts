export type MessageRole = "user" | "assistant";

export type Stage =
  | "COLLECTING"
  | "PROGRAM_PREVIEW"
  | "PROGRAM_CREATED"
  | "FORM_PREVIEW"
  | "FORM_ATTACHED"
  | "READY_TO_PUBLISH"
  | "PUBLISHED";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  stage?: string;
  ts: Date;
  dtoPreview?: Record<string, unknown>;
}

export interface ChatApiResponse {
  session_id: string;
  reply: string;
  stage: Stage;
  requires_confirmation: boolean;
  program_id?: number;
  success: boolean;
  dto_preview?: Record<string, unknown>;
}

export interface StoredSession {
  session_id: string;
  title: string;
  stage: Stage;
  updated_at: string;
}

export interface DisplayMessage {
  id: string;
  role: MessageRole;
  content: string;
  stage?: string;
  ts: string;
  dto_preview?: Record<string, unknown>;
}

export interface ConfirmButton {
  label: string;
  value: string;
  primary: boolean;
}
