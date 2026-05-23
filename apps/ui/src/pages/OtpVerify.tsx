import { useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { verifyOtp, resendOtp } from "../api/auth";
import {
  OTP_COOLDOWN_MAX,
  OTP_TIMER_CIRCUMFERENCE,
  OTP_TIMER_RADIUS,
} from "./OtpVerify.consts";
import { OTP_VERIFY_CSS } from "./OtpVerify.styles";

interface Props {
  phone: string;
  countryCode: string;
  onVerified: (token: string) => void;
  onBack: () => void;
}

export function OtpVerify({ phone, countryCode, onVerified, onBack }: Props) {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resendMsg, setResendMsg] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(OTP_COOLDOWN_MAX);
  const [shake, setShake] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => { inputRefs.current[0]?.focus(); }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const updated = [...otp];
    updated[index] = value.slice(-1);
    setOtp(updated);
    setError(null);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const updated = [...otp];
      updated[index - 1] = "";
      setOtp(updated);
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(""));
      inputRefs.current[5]?.focus();
    }
    e.preventDefault();
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length < 6) { triggerShake(); return; }
    setError(null);
    setLoading(true);
    try {
      const token = await verifyOtp(phone, code, countryCode);
      onVerified(token);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Invalid OTP. Please try again.");
      setOtp(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendMsg(null);
    setError(null);
    setResending(true);
    try {
      await resendOtp(phone, countryCode);
      setResendMsg("New OTP sent successfully!");
      setCooldown(OTP_COOLDOWN_MAX);
      setOtp(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to resend OTP");
    } finally {
      setResending(false);
    }
  };

  const maskedPhone = phone.replace(/(\d{2})\d+(\d{3})/, "$1•••••$2");
  const otpFilled = otp.join("").length;
  const timerOffset = OTP_TIMER_CIRCUMFERENCE - (cooldown / OTP_COOLDOWN_MAX) * OTP_TIMER_CIRCUMFERENCE;
  const timerPct = cooldown / OTP_COOLDOWN_MAX;
  const timerColor = timerPct > 0.5 ? "#7068B8" : timerPct > 0.2 ? "#E8A84A" : "#D96070";

  return (
    <div className="ov-page">
      <style>{OTP_VERIFY_CSS}</style>

      {/* Step indicator */}
      <div style={{
        display: "flex", alignItems: "center", gap: "0.375rem",
        marginBottom: "1.5rem", width: "100%", maxWidth: 440,
      }}>
        <div className="ov-step-dot" style={{ background: "#5DAD8A" }} />
        <div className="ov-step-line" style={{ background: "#5DAD8A" }} />
        <div className="ov-step-dot" style={{ background: "#7068B8" }} />
        <div className="ov-step-line" style={{ background: "#E4E0F4" }} />
        <div className="ov-step-dot" style={{ background: "#E4E0F4" }} />
        <span style={{ fontSize: "0.75rem", color: "#7068B8", fontWeight: 600, marginLeft: "0.25rem" }}>
          Step 2 of 3
        </span>
      </div>

      <div className="ov-card">
        {/* Header row */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1.75rem" }}>
          <div>
            {/* Badge */}
            <div style={{
              display: "inline-flex", alignItems: "center", gap: "0.4rem",
              background: "#EDE9FF", padding: "0.3rem 0.875rem",
              borderRadius: 20, marginBottom: "0.875rem",
            }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#7068B8", display: "inline-block" }} />
              <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#7068B8", letterSpacing: "0.07em" }}>
                VERIFICATION
              </span>
            </div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#2D2A50", margin: "0 0 0.375rem", letterSpacing: "-0.02em" }}>
              Enter your code
            </h1>
            <p style={{ color: "#7A788E", fontSize: "0.875rem", lineHeight: 1.6, margin: 0 }}>
              Sent to{" "}
              <strong style={{ color: "#7068B8" }}>{countryCode} {maskedPhone}</strong>
            </p>
          </div>

          {/* Circular countdown timer */}
          <div style={{ flexShrink: 0, marginLeft: "1rem" }}>
            {cooldown > 0 ? (
              <svg width="56" height="56" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r={OTP_TIMER_RADIUS} stroke="#E4E0F4" strokeWidth="3" fill="none" />
                <circle
                  cx="28" cy="28" r={OTP_TIMER_RADIUS}
                  stroke={timerColor}
                  strokeWidth="3" fill="none"
                  strokeDasharray={OTP_TIMER_CIRCUMFERENCE}
                  strokeDashoffset={timerOffset}
                  strokeLinecap="round"
                  transform="rotate(-90 28 28)"
                  style={{ transition: "stroke-dashoffset 1s linear, stroke 0.5s" }}
                />
                <text
                  x="28" y="33"
                  textAnchor="middle"
                  fontSize="13"
                  fontWeight="700"
                  fill={timerColor}
                  fontFamily="Inter, system-ui, sans-serif"
                >
                  {cooldown}s
                </text>
              </svg>
            ) : (
              <div style={{
                width: 56, height: 56, borderRadius: "50%",
                background: "#F0EEFF", border: "3px solid #5DAD8A",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4L19 7" stroke="#5DAD8A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* OTP inputs */}
          <div
            className={`ov-otp-row${shake ? " shake" : ""}`}
            onPaste={handlePaste}
            style={{ marginBottom: "1.5rem", justifyContent: "center" }}
          >
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={loading}
                className={`ov-otp-box${digit ? " filled" : ""}${error ? " error" : ""}`}
              />
            ))}
          </div>

          {/* Progress bar */}
          <div style={{
            height: 4, background: "#F0ECFC", borderRadius: 2,
            marginBottom: "1.25rem", overflow: "hidden",
          }}>
            <div style={{
              height: "100%",
              width: `${(otpFilled / 6) * 100}%`,
              background: error
                ? "linear-gradient(90deg, #D96070, #B84560)"
                : "linear-gradient(90deg, #7068B8, #9078C4)",
              borderRadius: 2,
              transition: "width 0.2s ease, background 0.3s",
            }} />
          </div>

          {/* Feedback messages */}
          {error && (
            <div style={{
              padding: "0.75rem 1rem", background: "#FEF0F2",
              color: "#B84560", borderRadius: 10,
              fontSize: "0.875rem", marginBottom: "1rem",
              display: "flex", alignItems: "center", gap: "0.5rem",
              border: "1px solid #F5C0CC",
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" stroke="#B84560" strokeWidth="1.5"/>
                <path d="M12 8v4M12 16h.01" stroke="#B84560" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              {error}
            </div>
          )}
          {resendMsg && (
            <div style={{
              padding: "0.75rem 1rem", background: "#E8F7F0",
              color: "#3D9E78", borderRadius: 10,
              fontSize: "0.875rem", marginBottom: "1rem",
              display: "flex", alignItems: "center", gap: "0.5rem",
              border: "1px solid #A8DCC8",
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" stroke="#3D9E78" strokeWidth="1.5"/>
                <path d="M8 12l3 3 5-5" stroke="#3D9E78" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {resendMsg}
            </div>
          )}

          {/* Verify button */}
          <button
            type="submit"
            disabled={loading || otpFilled < 6}
            className="ov-btn"
            style={{ marginBottom: "1.25rem" }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.625rem" }}>
                <span style={{
                  width: 17, height: 17,
                  border: "2.5px solid rgba(255,255,255,0.35)",
                  borderTopColor: "#fff", borderRadius: "50%",
                  animation: "ov-spin 0.7s linear infinite",
                  display: "inline-block",
                }} />
                Verifying…
              </span>
            ) : (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
                Verify &amp; Sign In
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
            )}
          </button>

          {/* Footer actions */}
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: "0.5rem", fontSize: "0.875rem",
          }}>
            {cooldown > 0 ? (
              <span style={{ color: "#A09CC4" }}>Resend in <strong style={{ color: "#7A788E" }}>{cooldown}s</strong></span>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="ov-resend-btn"
              >
                {resending ? "Resending…" : "Resend code"}
              </button>
            )}
            <span style={{ color: "#D8D4F0", fontSize: "1rem" }}>·</span>
            <button type="button" onClick={onBack} className="ov-back-btn">
              Change number
            </button>
          </div>
        </form>
      </div>

      <p style={{ marginTop: "1.5rem", color: "#C4C0DC", fontSize: "0.75rem" }}>
        Didn't receive it? Check spam or try a different number.
      </p>
    </div>
  );
}
