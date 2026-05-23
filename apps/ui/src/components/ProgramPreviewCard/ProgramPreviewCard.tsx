import styles from "./ProgramPreviewCard.module.css";

interface GroupedProgram {
  name?: string;
  starts_at?: string;
  ends_at?: string;
  venue_address?: string;
  checkin_at?: string;
  checkin_ends_at?: string;
  checkout_at?: string;
  checkout_ends_at?: string;
  limited_seats?: boolean;
  total_seats?: number;
}

interface ProgramSession {
  name?: string;
  starts_at?: string;
  ends_at?: string;
  mode_of_operation?: string;
  meeting_link?: string;
}

interface ProgramPreviewCardProps {
  dto: Record<string, unknown>;
}

function fmtDate(iso: unknown): string {
  if (!iso || typeof iso !== "string") return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      ...(iso.includes("T") ? { hour: "2-digit", minute: "2-digit" } : {}),
    });
  } catch {
    return String(iso);
  }
}

function fmtFee(amount: unknown): string {
  if (amount == null || amount === "") return "—";
  const n = Number(amount);
  return isNaN(n) ? "—" : `₹${n.toLocaleString("en-IN")}`;
}

function badge(text: string, variant: "type" | "mode" | "status") {
  return (
    <span className={`${styles.badge} ${styles[`badge_${variant}`]}`}>{text}</span>
  );
}

export function ProgramPreviewCard({ dto }: ProgramPreviewCardProps) {
  const subType = (dto.sub_program_type as string) || "CUSTOM";
  const mode = (dto.mode_of_operation as string) || "";
  const isGrouped = Boolean(dto.is_grouped_program);
  const hasSessions = Boolean(dto.has_multiple_sessions);
  const isPaid = Boolean(dto.requires_payment);
  const isResidential = Boolean(dto.is_residence_required);
  const groupedPrograms = (dto.grouped_programs as GroupedProgram[]) || [];
  const sessions = (dto.program_sessions as ProgramSession[]) || [];

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardHeaderLeft}>
          <span className={styles.cardTitle}>{(dto.name as string) || "Program Preview"}</span>
          {dto.code && <span className={styles.cardCode}>{dto.code as string}</span>}
        </div>
        <div className={styles.cardHeaderBadges}>
          {badge(subType, "type")}
          {mode && badge(mode, "mode")}
          {badge("DRAFT", "status")}
        </div>
      </div>

      <div className={styles.sections}>
        {/* Basic Info */}
        <section className={styles.section}>
          <h4 className={styles.sectionTitle}>Basic Information</h4>
          <div className={styles.grid}>
            {dto.description && (
              <div className={styles.fieldFull}>
                <span className={styles.label}>Description</span>
                <span className={styles.value}>{dto.description as string}</span>
              </div>
            )}
            <div className={styles.field}>
              <span className={styles.label}>Structure</span>
              <span className={styles.value}>
                {isGrouped ? "Grouped sub-programs" : hasSessions ? "Multiple sessions" : "Single"}
              </span>
            </div>
            {dto.no_of_session != null && (
              <div className={styles.field}>
                <span className={styles.label}>{isGrouped ? "Sub-programs" : "Sessions"}</span>
                <span className={styles.value}>{String(dto.no_of_session)}</span>
              </div>
            )}
            <div className={styles.field}>
              <span className={styles.label}>Approval required</span>
              <span className={styles.value}>{dto.requires_approval ? "Yes" : "No"}</span>
            </div>
            {dto.banner_image_url && (
              <div className={styles.fieldFull}>
                <span className={styles.label}>Banner</span>
                <a
                  href={dto.banner_image_url as string}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.link}
                >
                  {dto.banner_image_url as string}
                </a>
              </div>
            )}
          </div>
        </section>

        {/* Schedule */}
        <section className={styles.section}>
          <h4 className={styles.sectionTitle}>Schedule</h4>
          <div className={styles.grid}>
            <div className={styles.field}>
              <span className={styles.label}>Starts</span>
              <span className={styles.value}>{fmtDate(dto.starts_at)}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Ends</span>
              <span className={styles.value}>{fmtDate(dto.ends_at)}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Registration opens</span>
              <span className={styles.value}>{fmtDate(dto.registration_starts_at)}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Registration closes</span>
              <span className={styles.value}>{fmtDate(dto.registration_ends_at)}</span>
            </div>
            {dto.checkin_at && (
              <div className={styles.field}>
                <span className={styles.label}>Check-in starts</span>
                <span className={styles.value}>{fmtDate(dto.checkin_at)}</span>
              </div>
            )}
            {dto.checkin_ends_at && (
              <div className={styles.field}>
                <span className={styles.label}>Check-in ends</span>
                <span className={styles.value}>{fmtDate(dto.checkin_ends_at)}</span>
              </div>
            )}
            {dto.checkout_at && (
              <div className={styles.field}>
                <span className={styles.label}>Check-out starts</span>
                <span className={styles.value}>{fmtDate(dto.checkout_at)}</span>
              </div>
            )}
            {dto.checkout_ends_at && (
              <div className={styles.field}>
                <span className={styles.label}>Check-out ends</span>
                <span className={styles.value}>{fmtDate(dto.checkout_ends_at)}</span>
              </div>
            )}
          </div>
        </section>

        {/* Capacity */}
        <section className={styles.section}>
          <h4 className={styles.sectionTitle}>Capacity &amp; Registration</h4>
          <div className={styles.grid}>
            <div className={styles.field}>
              <span className={styles.label}>Seats</span>
              <span className={styles.value}>
                {dto.limited_seats ? `${dto.total_seats ?? "—"} (limited)` : "Unlimited"}
              </span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Waitlist</span>
              <span className={styles.value}>
                {dto.waitlist_applicable
                  ? `Yes${dto.waitlist_trigger_count ? ` (trigger: ${dto.waitlist_trigger_count})` : ""}`
                  : "No"}
              </span>
            </div>
          </div>
        </section>

        {/* Venue */}
        {(dto.venue || isResidential) && (
          <section className={styles.section}>
            <h4 className={styles.sectionTitle}>Venue</h4>
            <div className={styles.grid}>
              {dto.venue && (
                <div className={styles.field}>
                  <span className={styles.label}>Venue</span>
                  <span className={styles.value}>{dto.venue as string}</span>
                </div>
              )}
              {dto.venue_name_in_emails && (
                <div className={styles.field}>
                  <span className={styles.label}>Venue name in emails</span>
                  <span className={styles.value}>{dto.venue_name_in_emails as string}</span>
                </div>
              )}
              {isResidential && (
                <div className={styles.field}>
                  <span className={styles.label}>Bed count</span>
                  <span className={styles.value}>{String(dto.total_bed_count ?? "—")}</span>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Payment */}
        {isPaid && (
          <section className={styles.section}>
            <h4 className={styles.sectionTitle}>Payment</h4>
            <div className={styles.grid}>
              {subType === "HDB" ? (
                <>
                  <div className={styles.field}>
                    <span className={styles.label}>HDB fee</span>
                    <span className={`${styles.value} ${styles.fee}`}>{fmtFee(dto.base_price)}</span>
                  </div>
                  <div className={styles.field}>
                    <span className={styles.label}>MSD fee</span>
                    <span className={`${styles.value} ${styles.fee}`}>{fmtFee(dto.program_fee)}</span>
                  </div>
                </>
              ) : (
                <div className={styles.field}>
                  <span className={styles.label}>Program fee</span>
                  <span className={`${styles.value} ${styles.fee}`}>{fmtFee(dto.program_fee)}</span>
                </div>
              )}
              {dto.gst_number && (
                <div className={styles.field}>
                  <span className={styles.label}>GST number</span>
                  <span className={styles.value}>{dto.gst_number as string}</span>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Sub-programs */}
        {isGrouped && groupedPrograms.length > 0 && (
          <section className={styles.section}>
            <h4 className={styles.sectionTitle}>Sub-programs ({groupedPrograms.length})</h4>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Dates</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Seats</th>
                  </tr>
                </thead>
                <tbody>
                  {groupedPrograms.map((g, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>{g.name || "—"}</td>
                      <td>
                        {g.starts_at || g.ends_at
                          ? `${fmtDate(g.starts_at)} → ${fmtDate(g.ends_at)}`
                          : "—"}
                      </td>
                      <td>
                        {g.checkin_at
                          ? `${fmtDate(g.checkin_at)}${g.checkin_ends_at ? ` → ${fmtDate(g.checkin_ends_at)}` : ""}`
                          : "—"}
                      </td>
                      <td>
                        {g.checkout_at
                          ? `${fmtDate(g.checkout_at)}${g.checkout_ends_at ? ` → ${fmtDate(g.checkout_ends_at)}` : ""}`
                          : "—"}
                      </td>
                      <td>{g.limited_seats ? String(g.total_seats ?? "—") : "Unlimited"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Sessions */}
        {hasSessions && sessions.length > 0 && (
          <section className={styles.section}>
            <h4 className={styles.sectionTitle}>Sessions ({sessions.length})</h4>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Dates</th>
                    <th>Mode</th>
                    <th>Link</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>{s.name || "—"}</td>
                      <td>
                        {s.starts_at || s.ends_at
                          ? `${fmtDate(s.starts_at)} → ${fmtDate(s.ends_at)}`
                          : "—"}
                      </td>
                      <td>{s.mode_of_operation || "—"}</td>
                      <td>
                        {s.meeting_link ? (
                          <a
                            href={s.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.link}
                          >
                            Link
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>

      <div className={styles.cardFooter}>
        <span className={styles.footerHint}>
          Reply <strong>yes</strong> to create · <strong>edit</strong> to change something
        </span>
      </div>
    </div>
  );
}
