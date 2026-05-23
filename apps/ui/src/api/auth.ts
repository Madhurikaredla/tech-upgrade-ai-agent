import { ApiError } from "./client";
import { clearAuthToken, getAuthToken, setAuthToken } from "../utils/authToken";

export function getToken(): string | null {
  return getAuthToken();
}

export function saveToken(token: string): void {
  setAuthToken(token);
}

export function clearToken(): void {
  clearAuthToken();
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    // JWT uses base64url (- and _ instead of + and /). atob() needs standard base64.
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(b64));
  } catch {
    return null;
  }
}

export function isLoggedIn(): boolean {
  const token = getToken();
  if (!token) return false;
  const payload = decodeJwtPayload(token);
  if (!payload) return false;
  // If no exp claim, trust the token is valid
  if (!payload.exp) return true;
  return (payload.exp as number) * 1000 > Date.now();
}

/** Extract the token string from whatever NestJS returns. */
function extractToken(data: Record<string, unknown>): string {
  // Top-level token fields
  const top = data["accessToken"] ?? data["access_token"] ?? data["token"];
  if (typeof top === "string") return top;

  // NestJS wraps payload under data.data.token
  const nested = data["data"];
  if (nested && typeof nested === "object") {
    const inner = nested as Record<string, unknown>;
    const t = inner["token"] ?? inner["accessToken"] ?? inner["access_token"];
    if (typeof t === "string") return t;
  }

  throw new Error("No token found in auth response");
}

// ---------------------------------------------------------------------------
// Send OTP  →  POST api.portal.dev.divami.com/auth/login
// ---------------------------------------------------------------------------

export async function sendOtp(phone: string, countryCode = "+91"): Promise<void> {
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login_type: "phone", phone_number: phone, country_code: countryCode }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Failed to send OTP" }));
    throw new ApiError(res.status, data.detail ?? "Failed to send OTP");
  }
}

// ---------------------------------------------------------------------------
// Verify OTP  →  POST api.portal.dev.divami.com/auth/validate-otp
// Returns NestJS token directly
// ---------------------------------------------------------------------------

export async function verifyOtp(phone: string, otp: string, countryCode = "+91"): Promise<string> {
  const res = await fetch("/api/v1/auth/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login_type: "phone", phone_number: phone, country_code: countryCode, otp }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Invalid OTP" }));
    throw new ApiError(res.status, data.detail ?? "Invalid OTP");
  }
  const data = await res.json();
  return extractToken(data);
}

// ---------------------------------------------------------------------------
// Resend OTP  →  POST api.portal.dev.divami.com/auth/resend-otp
// ---------------------------------------------------------------------------

export async function resendOtp(phone: string, countryCode = "+91"): Promise<void> {
  const res = await fetch("/api/v1/auth/resend-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login_type: "phone", phone_number: phone, country_code: countryCode }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Failed to resend OTP" }));
    throw new ApiError(res.status, data.detail ?? "Failed to resend OTP");
  }
}
