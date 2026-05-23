import { STAGE_COLORS, STAGE_INDEX, STAGES } from "../../constants/stages";
import type { Stage } from "../../types/chat";
import styles from "./ChatStepper.module.css";

interface ChatStepperProps {
  currentStage: Stage;
}

export function ChatStepper({ currentStage }: ChatStepperProps) {
  const currentStageIdx = STAGE_INDEX[currentStage] ?? 0;
  const stageColor = STAGE_COLORS[currentStage] ?? "#7068B8";

  return (
    <div className={styles.stepper}>
      {STAGES.map((stage, i) => {
        const done = i < currentStageIdx;
        const active = i === currentStageIdx;
        const pending = i > currentStageIdx;

        return (
          <div className={styles.step} key={stage.key}>
            <div className={styles.stepNode}>
              <div
                className={styles.stepCircle}
                style={{
                  background: done ? stageColor : active ? `${stageColor}20` : "#F5F3FF",
                  border: `2px solid ${done || active ? stageColor : "#E4E0F4"}`,
                  color: done ? "#fff" : active ? stageColor : "#C4C0DC",
                  boxShadow: active ? `0 0 0 3px ${stageColor}28` : "none",
                }}
              >
                {done ? (
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 13l4 4L19 7"
                      stroke="#fff"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={styles.stepLabel}
                style={{ color: pending ? "#D8D4F0" : active ? stageColor : "#8880CC" }}
              >
                {stage.short}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div
                className={styles.stepConnector}
                style={{ background: done ? stageColor : "#EDE9FF" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
