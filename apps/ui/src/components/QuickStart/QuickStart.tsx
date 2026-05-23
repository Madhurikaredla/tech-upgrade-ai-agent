import styles from "./QuickStart.module.css";

interface Step {
  n: string;
  title: string;
  desc: string;
}

const STEPS: Step[] = [
  {
    n: "1",
    title: "Describe",
    desc: "Tell me the program type (HDB / TAT / ENT / CUSTOM) and key details — name, dates, fees, venue",
  },
  {
    n: "2",
    title: "Review",
    desc: "I'll extract the details and show a preview. Update anything inline or click Yes to confirm",
  },
  {
    n: "3",
    title: "Publish",
    desc: "Registration form is auto-attached. Publish live or save as draft with one click",
  },
];

interface QuickStartProps {
  voiceSupported: boolean;
}

export function QuickStart({ voiceSupported }: QuickStartProps) {
  return (
    <div className={styles.quickStart}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707M12 21a9 9 0 110-18 9 9 0 010 18z"
              stroke="#7068B8"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span className={styles.cardTitle}>How it works — 3 simple steps</span>
        </div>

        <div className={styles.stepsRow}>
          {STEPS.map((step, i) => (
            <div key={step.n} className={styles.stepItem}>
              <div className={styles.stepIconCol}>
                <div className={styles.stepNumber}>{step.n}</div>
                {i < 2 && <div className={styles.stepConnectorLine} />}
              </div>
              <div className={styles.stepContent}>
                <div className={styles.stepTitle}>{step.title}</div>
                <div className={styles.stepDesc}>{step.desc}</div>
              </div>
            </div>
          ))}
        </div>

        {voiceSupported && (
          <div className={styles.voiceTip}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
                stroke="#7068B8"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"
                stroke="#7068B8"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <span>
              <strong>Pro tip:</strong> Click the mic button to describe your program by voice —
              hands-free!
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
