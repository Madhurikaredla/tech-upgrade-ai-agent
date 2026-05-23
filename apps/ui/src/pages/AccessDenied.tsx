import { ACCESS_DENIED_CSS } from "./AccessDenied.styles";

interface Props {
  onLogout: () => void;
  userName?: string;
}

export function AccessDenied({ onLogout, userName }: Props) {
  const initials = userName
    ? userName.split(/\s+/).filter(Boolean).map((p) => p[0].toUpperCase()).slice(0, 2).join("")
    : "?";

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(145deg, #FFF5F5 0%, #FEF2F2 40%, #F9FAFB 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
      fontFamily: "'Inter', system-ui, sans-serif",
    }}>
      <style>{ACCESS_DENIED_CSS}</style>

      <div className="ad-card">
        {/* Shield icon */}
        <div className="ad-shield-wrap">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
              fill="#FEE2E2"
              stroke="#DC2626"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <path d="M12 9v4" stroke="#DC2626" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="12" cy="16" r="1.25" fill="#DC2626" />
          </svg>
        </div>

        {/* Badge */}
        <div style={{
          display: "inline-flex", alignItems: "center", gap: "0.4rem",
          background: "#FEF2F2", border: "1px solid #FECACA",
          padding: "0.3rem 0.875rem", borderRadius: 20, marginBottom: "1rem",
        }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#EF4444", display: "inline-block" }} />
          <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#DC2626", letterSpacing: "0.07em" }}>
            ACCESS RESTRICTED
          </span>
        </div>

        <h1 style={{
          fontSize: "1.625rem", fontWeight: 800, color: "#111827",
          margin: "0 0 1rem", letterSpacing: "-0.02em",
        }}>
          Admin Access Required
        </h1>

        {/* User chip */}
        {userName && (
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "0.5rem",
            background: "#F9FAFB", border: "1px solid #E5E7EB",
            padding: "0.4rem 0.875rem 0.4rem 0.5rem",
            borderRadius: 20, marginBottom: "1.25rem",
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              background: "#E5E7EB", display: "flex",
              alignItems: "center", justifyContent: "center",
              fontSize: "0.6875rem", fontWeight: 700, color: "#374151",
            }}>
              {initials}
            </div>
            <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 500 }}>
              {userName}
            </span>
          </div>
        )}

        <p style={{ color: "#6B7280", lineHeight: 1.7, fontSize: "0.9375rem", margin: "0 0 0.75rem" }}>
          Your account does not have the administrator privileges needed to access this portal.
        </p>

        <p style={{ color: "#9CA3AF", fontSize: "0.875rem", lineHeight: 1.7, margin: "0 0 1.75rem" }}>
          Please contact your system administrator to request access, or sign in with an authorised account.
        </p>

        {/* Info box */}
        <div style={{
          background: "#FFFBEB", border: "1px solid #FDE68A",
          borderRadius: 12, padding: "0.875rem 1.25rem",
          marginBottom: "1.75rem", textAlign: "left",
          display: "flex", gap: "0.75rem", alignItems: "flex-start",
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 1 }}>
            <circle cx="12" cy="12" r="10" stroke="#D97706" strokeWidth="1.5" />
            <path d="M12 8v4M12 16h.01" stroke="#D97706" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <p style={{ margin: 0, fontSize: "0.8125rem", color: "#92400E", lineHeight: 1.6 }}>
            If you believe this is a mistake, reach out to your administrator and ask them to grant you access to the portal.
          </p>
        </div>

        <div style={{ borderTop: "1px solid #F3F4F6", paddingTop: "1.5rem", display: "flex", gap: "0.75rem" }}>
          <button className="ad-btn-secondary" onClick={onLogout}>
            Sign Out
          </button>
          <button
            className="ad-btn-primary"
            onClick={() =>
              (window.location.href =
                "mailto:admin@divami.com?subject=Portal%20Access%20Request&body=Hi%2C%20I%20would%20like%20to%20request%20access%20to%20the%20Program%20Config%20portal.%20Please%20grant%20me%20the%20necessary%20permissions.")
            }
          >
            Request Access
          </button>
        </div>
      </div>

      <p style={{ marginTop: "1.5rem", color: "#D1D5DB", fontSize: "0.8125rem" }}>
        Program Config AI · Admin Portal
      </p>
    </div>
  );
}
