import type { ConfirmButton, Stage } from "../types/chat";

export interface StageInfo {
  key: string;
  short: string;
  label: string;
}

export const STAGES: StageInfo[] = [
  { key: "COLLECTING",         short: "Collect",   label: "Gathering Info" },
  { key: "TEMPLATE_SELECTION", short: "Template",  label: "Choose Template" },
  { key: "PROGRAM_PREVIEW",    short: "Preview",   label: "Review Program" },
  { key: "PROGRAM_CREATED",  short: "Created",  label: "Program Created" },
  { key: "FORM_PREVIEW",     short: "Form",     label: "Review Form" },
  { key: "FORM_ATTACHED",    short: "Attached", label: "Form Attached" },
  { key: "READY_TO_PUBLISH", short: "Ready",    label: "Ready to Publish" },
  { key: "PUBLISHED",        short: "Live",     label: "Published ✓" },
];

export const STAGE_INDEX: Record<string, number> = Object.fromEntries(
  STAGES.map((s, i) => [s.key, i])
);

export const STAGE_COLORS: Record<string, string> = {
  COLLECTING:         "#E2CCFF",
  TEMPLATE_SELECTION: "#93C5FD",
  PROGRAM_PREVIEW:    "#FCD34D",
  PROGRAM_CREATED:  "#6EE7B7",
  FORM_PREVIEW:     "#FB923C",
  FORM_ATTACHED:    "#65afab",
  READY_TO_PUBLISH: "#F472B6",
  PUBLISHED:        "#91e95e",
};

export const CONFIRM_BUTTONS: Partial<Record<Stage, ConfirmButton[]>> = {
  PROGRAM_PREVIEW: [
    { label: "✓  Yes, create it",   value: "yes",           primary: true  },
    { label: "✏  Edit details",     value: "edit",          primary: false },
  ],
  FORM_PREVIEW: [
    { label: "✓  Yes, attach form", value: "ok",            primary: true  },
    { label: "✏  Edit questions",   value: "edit",          primary: false },
  ],
  READY_TO_PUBLISH: [
    { label: "🚀  Publish now",     value: "publish",       primary: true  },
    { label: "💾  Keep as draft",   value: "keep as draft", primary: false },
  ],
};
