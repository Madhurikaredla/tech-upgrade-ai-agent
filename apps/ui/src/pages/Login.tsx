import { useEffect, useRef, useState } from "react";
import PhoneInput, {
  isValidPhoneNumber,
  parsePhoneNumber,
  getCountryCallingCode,
} from "react-phone-number-input";
import type { Country } from "react-phone-number-input";
import "react-phone-number-input/style.css";
import { ApiError } from "../api/client";
import { sendOtp } from "../api/auth";
import { LOGIN_CSS } from "./Login.styles";

interface Props {
  onOtpSent: (phone: string, countryCode: string) => void;
}

interface CountryOption {
  value?: Country;
  label: string;
}
interface FlagProps {
  country: Country;
  label: string;
}
interface CountrySelectProps {
  value?: Country;
  onChange: (v?: Country) => void;
  options: CountryOption[];
  iconComponent: React.ComponentType<FlagProps>;
  disabled?: boolean;
}

function CountrySelect({ value, onChange, options, iconComponent: Flag, disabled }: CountrySelectProps) {
  const [open, setOpen]       = useState(false);
  const [search, setSearch]   = useState("");
  const containerRef          = useRef<HTMLDivElement>(null);
  const searchRef             = useRef<HTMLInputElement>(null);
  const listRef               = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (open) setTimeout(() => searchRef.current?.focus(), 50);
  }, [open]);

  useEffect(() => {
    if (!open || !listRef.current) return;
    const active = listRef.current.querySelector("[data-selected='true']") as HTMLElement | null;
    active?.scrollIntoView({ block: "center" });
  }, [open]);

  const callingCode = value ? `+${getCountryCallingCode(value)}` : "";

  const filtered = options.filter((o) => {
    if (!o.value) return false;
    const q = search.toLowerCase();
    return (
      o.label.toLowerCase().includes(q) ||
      getCountryCallingCode(o.value).includes(q.replace("+", ""))
    );
  });

  const handleSelect = (country?: Country) => {
    onChange(country);
    setOpen(false);
    setSearch("");
  };

  return (
    <div ref={containerRef} style={{ position: "relative", flexShrink: 0, alignSelf: "stretch", display: "flex", alignItems: "stretch" }}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0 0.875rem",
          flex: 1,
          background: "#F5F3FF",
          border: "none",
          borderRight: "1.5px solid #E4E0F4",
          cursor: disabled ? "not-allowed" : "pointer",
          outline: "none",
          whiteSpace: "nowrap",
          minWidth: 92,
        }}
      >
        {value ? (
          <Flag country={value} label={value} />
        ) : (
          <span style={{ fontSize: "1.25rem", lineHeight: 1 }}>🌐</span>
        )}
        <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#2D2A50" }}>
          {callingCode || "—"}
        </span>
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none"
          style={{ transition: "transform 0.2s", transform: open ? "rotate(180deg)" : "rotate(0)" }}
        >
          <path d="M6 9l6 6 6-6" stroke="#A09CC4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            zIndex: 200,
            background: "#fff",
            border: "1.5px solid #E4E0F4",
            borderRadius: 14,
            boxShadow: "0 12px 40px rgba(107,101,168,0.14), 0 2px 8px rgba(0,0,0,0.05)",
            width: 270,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div style={{ padding: "0.625rem 0.75rem", borderBottom: "1px solid #F0ECFC", flexShrink: 0 }}>
            <div style={{
              display: "flex", alignItems: "center", gap: "0.5rem",
              background: "#FAF8FF", border: "1.5px solid #E4E0F4",
              borderRadius: 8, padding: "0.4rem 0.75rem",
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, color: "#A09CC4" }}>
                <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
                <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              <input
                ref={searchRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search country or code…"
                style={{
                  border: "none", outline: "none", background: "transparent",
                  fontSize: "0.875rem", color: "#2D2A50", width: "100%",
                  fontFamily: "inherit",
                }}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "#A09CC4", lineHeight: 1 }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </button>
              )}
            </div>
          </div>

          <div ref={listRef} style={{ overflowY: "auto", maxHeight: 340, flex: 1 }}>
            {filtered.length === 0 ? (
              <div style={{ padding: "1.5rem 1rem", textAlign: "center", color: "#A09CC4", fontSize: "0.875rem" }}>
                No country found
              </div>
            ) : (
              filtered.map((opt) => {
                const isSelected = opt.value === value;
                const code = opt.value ? `+${getCountryCallingCode(opt.value)}` : "";
                return (
                  <button
                    key={opt.value}
                    type="button"
                    data-selected={isSelected}
                    onClick={() => handleSelect(opt.value)}
                    style={{
                      width: "100%", display: "flex", alignItems: "center",
                      gap: "0.625rem", padding: "0.5rem 0.875rem",
                      background: isSelected ? "#EDE9FF" : "transparent",
                      border: "none", cursor: "pointer", textAlign: "left",
                      fontFamily: "inherit", transition: "background 0.1s",
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) (e.currentTarget as HTMLButtonElement).style.background = "#F5F3FF";
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                    }}
                  >
                    {opt.value && <Flag country={opt.value} label={opt.label} />}
                    <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#7068B8", minWidth: 36 }}>
                      {code}
                    </span>
                    <span style={{ fontSize: "0.875rem", color: "#2D2A50", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {opt.label}
                    </span>
                    {isSelected && (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                        <path d="M5 13l4 4L19 7" stroke="#7068B8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   Login page
   ───────────────────────────────────────────── */
export function Login({ onOtpSent }: Props) {
  const [phone, setPhone]             = useState<string>("");
  const [loading, setLoading]         = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [phoneError, setPhoneError]   = useState<string | null>(null);
  const [touched, setTouched]         = useState(false);

  const validate = (val: string): string | null => {
    if (!val) return "Phone number is required";
    if (!isValidPhoneNumber(val)) return "Enter a valid phone number for the selected country";
    return null;
  };

  const handleBlur = () => {
    setTouched(true);
    setPhoneError(validate(phone));
  };

  const handlePhoneChange = (val: string | undefined) => {
    const v = val ?? "";
    setPhone(v);
    setSubmitError(null);
    if (touched) setPhoneError(validate(v));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    const err = validate(phone);
    if (err) { setPhoneError(err); return; }

    setSubmitError(null);
    setLoading(true);
    try {
      const parsed      = parsePhoneNumber(phone);
      const countryCode = "+" + (parsed?.countryCallingCode ?? "91");
      const nationalNum = parsed?.nationalNumber ?? phone;
      await sendOtp(nationalNum, countryCode);
      onOtpSent(nationalNum, countryCode);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const isValid = phone ? isValidPhoneNumber(phone) : false;

  return (
    <div className="lr-root">
      <style>{LOGIN_CSS}</style>

      {/* ── Left brand panel — light pastel lavender ── */}
      <div className="lr-left">
        <div className="lr-blob lr-blob-1" />
        <div className="lr-blob lr-blob-2" />
        <div className="lr-blob lr-blob-3" />

        <div className="lr-left-content">
          {/* Brand */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "3.5rem" }}>
            <div className="lr-brand-logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7l10 5 10-5-10-5z" fill="#fff" />
                <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <span style={{ color: "#2D2A50", fontWeight: 700, fontSize: "1.125rem", letterSpacing: "-0.01em" }}>
              Program Config AI
            </span>
          </div>

          <div style={{ flex: 1 }}>
            <h2 style={{ color: "#2D2A50", fontSize: "2.1rem", fontWeight: 800, lineHeight: 1.2, marginBottom: "1rem", letterSpacing: "-0.03em" }}>
              The intelligent way to configure programs
            </h2>
            <p style={{ color: "#625E88", fontSize: "0.9875rem", lineHeight: 1.75, marginBottom: "3rem" }}>
              Describe your program in plain language. Our AI extracts every detail and guides you through to publishing — no complex forms, no friction.
            </p>

            {[
              {
                icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707M12 21a9 9 0 110-18 9 9 0 010 18z" stroke="#7068B8" strokeWidth="1.5" strokeLinecap="round"/></svg>,
                title: "AI-Powered Extraction",
                desc: "Natural language → structured program data, automatically",
              },
              {
                icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" stroke="#7068B8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>,
                title: "Guided Multi-Stage Workflow",
                desc: "From collection to publish — every step AI-assisted",
              },
              {
                icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="5" y="11" width="14" height="10" rx="2" stroke="#7068B8" strokeWidth="1.5"/><path d="M8 11V7a4 4 0 018 0v4" stroke="#7068B8" strokeWidth="1.5" strokeLinecap="round"/></svg>,
                title: "Secure Access",
                desc: "Enterprise access control — only authorised admins can configure",
              },
            ].map((f, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "1rem", marginBottom: "1.5rem" }}>
                <div className="lr-feature-icon">{f.icon}</div>
                <div>
                  <div style={{ color: "#2D2A50", fontWeight: 600, fontSize: "0.9375rem", marginBottom: 3 }}>{f.title}</div>
                  <div style={{ color: "#7A788E", fontSize: "0.8125rem", lineHeight: 1.55 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ borderTop: "1px solid #D8D4F0", paddingTop: "1.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <rect x="5" y="11" width="14" height="10" rx="2" stroke="#A09CC4" strokeWidth="1.5"/>
              <path d="M8 11V7a4 4 0 018 0v4" stroke="#A09CC4" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span style={{ color: "#A09CC4", fontSize: "0.8125rem" }}>
              Built for InfiniPath program administrators
            </span>
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="lr-right">
        <div className="lr-form-wrap">

          {/* Step indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.375rem", marginBottom: "2rem" }}>
            <div className="lr-step-dot" style={{ background: "#7068B8" }} />
            <div className="lr-step-line" style={{ background: "#7068B8" }} />
            <div className="lr-step-dot" style={{ background: "#E4E0F4" }} />
            <div className="lr-step-line" style={{ background: "#E4E0F4" }} />
            <div className="lr-step-dot" style={{ background: "#E4E0F4" }} />
            <span style={{ fontSize: "0.75rem", color: "#7068B8", fontWeight: 600, marginLeft: "0.25rem" }}>Step 1 of 3</span>
          </div>

          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", background: "#EDE9FF", padding: "0.3rem 0.875rem", borderRadius: 20, marginBottom: "1rem" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#7068B8", display: "inline-block" }} />
            <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#7068B8", letterSpacing: "0.07em" }}>ADMIN PORTAL</span>
          </div>

          <h1 style={{ fontSize: "1.875rem", fontWeight: 800, color: "#2D2A50", margin: "0 0 0.5rem", letterSpacing: "-0.025em" }}>
            Welcome back
          </h1>
          <p style={{ color: "#7A788E", fontSize: "0.9rem", margin: "0 0 2rem", lineHeight: 1.6 }}>
            Sign in with your registered phone number to continue
          </p>

          <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "#4A4770", marginBottom: "0.4rem" }}>
                Phone Number
              </label>

              <div className={`lr-phone-field${touched && phoneError ? " has-error" : ""}`}>
                <PhoneInput
                  international
                  defaultCountry="IN"
                  value={phone}
                  onChange={handlePhoneChange}
                  onBlur={handleBlur}
                  disabled={loading}
                  placeholder="Enter phone number"
                  countrySelectComponent={CountrySelect}
                />
              </div>

              {touched && phoneError && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.375rem", marginTop: "0.4rem" }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="#D96070" strokeWidth="1.5"/>
                    <path d="M12 8v4M12 16h.01" stroke="#D96070" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  <span style={{ fontSize: "0.8rem", color: "#D96070" }}>{phoneError}</span>
                </div>
              )}
              {touched && !phoneError && phone && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.375rem", marginTop: "0.4rem" }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="#5DAD8A" strokeWidth="1.5"/>
                    <path d="M8 12l3 3 5-5" stroke="#5DAD8A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span style={{ fontSize: "0.8rem", color: "#5DAD8A" }}>Looks good</span>
                </div>
              )}
            </div>

            {submitError && (
              <div style={{ padding: "0.75rem 1rem", background: "#FEF0F2", color: "#B84560", borderRadius: 10, fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.625rem", border: "1px solid #F5C0CC" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10" stroke="#B84560" strokeWidth="1.5"/>
                  <path d="M12 8v4M12 16h.01" stroke="#B84560" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                {submitError}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !isValid}
              className="lr-btn"
              style={{ marginTop: "0.25rem" }}
            >
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.625rem" }}>
                  <span style={{ width: 17, height: 17, border: "2.5px solid rgba(255,255,255,0.35)", borderTopColor: "#fff", borderRadius: "50%", animation: "lr-spin 0.7s linear infinite", display: "inline-block", flexShrink: 0 }} />
                  Sending OTP…
                </span>
              ) : (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
                  Send OTP
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12h14M13 6l6 6-6 6" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
              )}
            </button>
          </form>

          <div style={{ marginTop: "1.75rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", padding: "0.75rem 1rem", background: "#FAF8FF", borderRadius: 10, border: "1px solid #EDE9FF" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <rect x="5" y="11" width="14" height="10" rx="2" stroke="#A09CC4" strokeWidth="1.5"/>
              <path d="M8 11V7a4 4 0 018 0v4" stroke="#A09CC4" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <span style={{ fontSize: "0.75rem", color: "#A09CC4" }}>
              OTP verified · End-to-end encrypted · Secure access
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
