export const HOW_IT_WORKS = [
  {
    n: "1",
    color: "#7068B8",
    bg: "#F0EEFF",
    title: "Describe",
    desc: "Send a plain-language message with your program details. The more you include upfront, the faster it goes.",
  },
  {
    n: "2",
    color: "#C9943A",
    bg: "#FEF7E8",
    title: "Review & confirm",
    desc: 'Preview shows all details. Click Yes to confirm, or type any change inline — e.g. "reg opens June 1".',
  },
  {
    n: "3",
    color: "#5DAD8A",
    bg: "#E8F7F0",
    title: "Publish",
    desc: "A registration form is auto-attached. Click Publish to go live or save as draft.",
  },
] as const;

export const KEY_FIELDS: Array<[string, string, string, string]> = [
  ["Program name", "#F0EEFF", "#6560A8", "#D8D4F0"],
  ["Program type", "#FEF3E8", "#B85C20", "#FAD8B0"],
  ["Start & end dates", "#E8F7F0", "#3D8A60", "#B0DCC8"],
  ["Venue / city", "#FEF7E8", "#A06820", "#F8DCA0"],
  ["Target audience", "#E8F4FF", "#2068A0", "#B0D4F0"],
  ["Seats / capacity", "#F0EEFF", "#7068B8", "#D8D4F0"],
  ["Fee (if any)", "#FEF0F4", "#A04060", "#F5C4D4"],
  ["Online / offline", "#E8F7F0", "#3D7860", "#B0D4C4"],
  ["Registration deadline", "#F0EEFF", "#5858A0", "#D4D0EC"],
];

export const EXAMPLE_PROMPTS = [
  {
    tag: "HDB",
    tagColor: "#6560A8",
    tagBg: "#F0EEFF",
    text: "HDBMSD 26-27\n\nVenue: Leonia, Hyderabad\nNo seat limit, no waitlist\nBed count: 120\nHDB fee: 200000, MSD fee: 200000\nRegistration opens: 21 May 2026, 9:00 AM\nRegistration closes: 25 Sep 2026, 9:00 AM\n\n5 sub-programs, same venue (Leonia, Hyderabad) for all:\n\nHDB 1 — 10 Jan 2026, check-in 10 Jan 2026 9:00 AM, check-out 10 Jan 2026 5:00 PM\nHDB 2 — 14 Feb 2026, check-in 14 Feb 2026 9:00 AM, check-out 14 Feb 2026 5:00 PM\nHDB 3 — 21 Mar 2026, check-in 21 Mar 2026 9:00 AM, check-out 21 Mar 2026 5:00 PM\nMSD 1 — 18 Jul 2026, check-in 18 Jul 2026 9:00 AM, check-out 18 Jul 2026 5:00 PM\nMSD 2 — 22 Aug 2026, check-in 22 Aug 2026 9:00 AM, check-out 22 Aug 2026 5:00 PM",
  },
  {
    tag: "TAT",
    tagColor: "#3D9E78",
    tagBg: "#E8F7F0",
    text: "Create a TAT program called Mindfulness Fundamentals. 8 online sessions via Zoom starting July 5 2025, every Saturday 7–9 AM. Program fee ₹2,500. Registration opens June 15, closes July 3. Max 100 participants.",
  },
  {
    tag: "ENT",
    tagColor: "#A06820",
    tagBg: "#FEF7E8",
    text: "Create an ENT event called Sound Healing Concert on August 15 2025, online via live stream. Fee ₹500. Limited to 200 seats with waitlist. Registration closes August 12.",
  },
] as const;

export const QUICK_COMMANDS = [
  { word: "yes", desc: "Approve the current preview and move forward" },
  { word: "edit [changes]", desc: 'Modify — e.g. "edit change venue to Mumbai"' },
  { word: "publish", desc: "Publish the program live" },
] as const;

