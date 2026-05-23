# Custom Program Type — Field Spec

**Version:** v1.1 | **Last Updated:** 2026-05-15

## What it is
A form for creating/editing a program of type **CUSTOM**. Fields are shown or hidden based on the admin's choices in the form. On submit → `POST /api/programs` (create) or `PATCH /api/programs/:id` (edit) with `CreateProgramDto`.

---

## Supported Field Types

| Field Type | Description |
|---|---|
| `text` | Single-line text input |
| `textarea` | Multi-line text input |
| `number` | Numeric input |
| `radio` | Radio button group |
| `select` | Dropdown (single-select) |
| `creatableSelect` | Multi-select with tag-style input; user can type and create new entries (backed by `CreatableSelectField` component) |
| `imageUpload` | File picker that uploads an image and returns a URL in the DTO payload (backed by `ImageUploadField` component) |
| `date` | Standalone date picker (no time) |
| `time` | Standalone time picker (HH:MM:SS) |
| `daterange` | Dual date-time picker for start/end ranges |
| `datetime` | Combined date and time picker |
| `email` | Email format input |

---

## Conditional Logic — Quick Reference

| When this field is... | ...set to | Show / Hide |
|---|---|---|
| `modeOfProgram` | `online` or `hybrid` | Show `onlineType` |
| `modeOfProgram` | `offline` or `hybrid` | Show `venue`, `venueAddress`, `venueNameInEmail`, `isResidenceRequired` |
| `modeOfProgram` | `online` | **Disable*isTravelInvolved` — field is rendered but interactions are blocked and value is forced `false` (`disabledWhen` condition) |
| `programStructure` | `grouped` | Show grouped sub-programs list (`GroupedProgramDto`) |
| `programStructure` | `multiple` | Show sessions list (`CreateProgramSessionDto`) |
| `programStructure` | `multiple` (Sessions) | Show `noOfSession` |
| `approvalRequired` | `yes` | Show `blessEndsAt` |
| `hasSeatLimit` | `yes` | Show `totalSeats`, `waitlistApplicable` |
| `waitlistApplicable` | `yes` | Show `waitlistTriggerCount` |
| `requiresPayment` | `yes` | Show Payment & Billing section |
| `hasCheckinCheckout` | `yes` | Show `checkinAt`, `checkinEndsAt`, `checkoutAt`, `checkoutEndsAt` (in Schedule & Dates) |
| `isResidenceRequired` | `yes` | Show `totalBedCount` (in Venue & Location) |

### Conditional Logic Notes

- **`visibleWhen`** — field is shown when a single named field equals a specific value.
- **`visibleWhenAll`** — field is shown only when *all* listed conditions are simultaneously true (AND logic). Used when a field requires multiple parent conditions to be met before appearing.
- **`disabledWhen`** — field is visible but rendered as disabled (interactions blocked) when the condition is met. The value is forced to its default. Currently used for `isTravelInvolved` when `modeOfProgram = online`.

---

## Section 1 — Basic Info

| Form Field | DTO Field | Type | Required |
|---|---|---|---|
| `programName` | `name` | text | Yes |
| `programCode` | `code` | text | No |
| `description` | `description` | textarea | No |
| `launchDate` | `launchDate` | date | No |
| `logoUrl` | `logoUrl` | imageUpload (file upload → URL in payload) | No |
| `subProgramType` | `subProgramType` | select (SubProgramTypeEnum) — label: "Program Type" | No |

---

## Section 2 — Mode & Structure

| Form Field | DTO Field | Type | Required | Condition |
|---|---|---|---|---|
| `modeOfProgram` | `modeOfOperation` | radio: ONLINE / OFFLINE / HYBRID | Yes | Always |
| `onlineType` | `onlineType` | select: MEETING / WEBINAR / LIVE_STREAM | Yes (if online/hybrid) | visible when `modeOfProgram` = online or hybrid |
| `programStructure` | maps to `isGroupedProgram` + `hasMultipleSessions` | radio: Single / Sessions / Programs | Yes | Always |

> `programStructure` mapping: Single → both false and no of sessions also 0, Sessions → `hasMultipleSessions=true`, Programs → `isGroupedProgram=true`

---

## Section 3 — Registration Rules

| Form Field | DTO Field | Type |
|---|---|---|
| `approvalRequired` | `requiresApproval` | radio: Yes / No |
| `allowsProxyRegistration` | `allowsProxyRegistration` | radio: Yes / No |
| `allowSaveAsDraft` | `allowSaveAsDraft` | radio: Yes / No |
| `elderMinAge` | `elderMinAge` | number (0–150) |
| `childMaxAge` | `childMaxAge` | number (0–150) |
| `seekerCanShareExperience` | `seekerCanShareExperience` | radio: Yes / No |

---

## Section 4 — Schedule & Dates

| Form Field | DTO Field | Type | Required | Condition |
|---|---|---|---|---|
| Program Dates | `startsAt` / `endsAt` | daterange | No | Always |
| `blessEndsAt` | `blessEndsAt` | datetime | No | visible when `approvalRequired` = yes |
| Registration Start | `registrationStartsAt` | datetime | No | Always |
| Registration End | `registrationEndsAt` | datetime | No | Always |
| `defaultStartTime` | `defaultStartTime` | time (HH:MM:SS) | No | Always |
| `defaultEndTime` | `defaultEndTime` | time (HH:MM:SS) | No | Always |
| `noOfSession` | `noOfSession` | number (min 0) | No | visible when `programStructure` = Sessions |
| `hasCheckinCheckout` | `hasCheckinCheckout` | radio: Yes / No | No | Always |
| `checkinAt` | `checkinAt` | datetime | No | visible when `hasCheckinCheckout` = yes |
| `checkinEndsAt` | `checkinEndsAt` | datetime | No | visible when `hasCheckinCheckout` = yes |
| `checkoutAt` | `checkoutAt` | datetime | No | visible when `hasCheckinCheckout` = yes |
| `checkoutEndsAt` | `checkoutEndsAt` | datetime | No | visible when `hasCheckinCheckout` = yes |

---

## Section 5 — Venue & Location

Core venue fields visible only when `modeOfProgram` = `offline` or `hybrid`.

| Form Field | DTO Field | Type | Condition |
|---|---|---|---|
| `venue` | `venue` | text | offline/hybrid only |
| `venueNameInEmail` | `venueNameInEmails` | text | offline/hybrid only |
| `isResidenceRequired` | `isResidenceRequired` | radio: Yes / No | offline/hybrid only |
| `totalBedCount` | `totalBedCount` | number (min 0) | visible when `isResidenceRequired` = yes |

---

## Section 6 — Seats & Capacity

| Form Field | DTO Field | Type | Condition |
|---|---|---|---|
| `hasSeatLimit` | `limitedSeats` | radio: Yes / No | Always |
| `totalSeats` | `totalSeats` | number (min 0) | visible when `hasSeatLimit` = yes |
| `waitlistApplicable` | `waitlistApplicable` | radio: Yes / No | visible when `hasSeatLimit` = yes |
| `waitlistTriggerCount` | `waitlistTriggerCount` | number (min 0) | visible when `waitlistApplicable` = yes |

---

## Section 7 — Program Features (Stage Flags)

| Form Field | DTO Field | Type | Notes |
|---|---|---|---|
| `requiresPayment` | `requiresPayment` | radio: Yes / No | Shows Payment & Billing section |
| `isTravelInvolved` | `isTravelInvolved` | radio: Yes / No | Disabled + forced No when mode = ONLINE |

---

## Section 8 — Payment & Billing

Visible only when `requiresPayment` = `yes`.

| Form Field | DTO Field | Type | Notes |
|---|---|---|---|
| `currency` | `currency` | text (default "INR", disabled) | |
| `basePrice` | `basePrice` | number (min 0, ₹) | |
| `programFee` | `programFee` | number (min 0, ₹) | |
| `gstPercentage` | `gstPercentage` | number (0–100) | disabled — auto-calculated from CGST + SGST |
| `cgst` | `cgst` | number (0–100) | |
| `sgst` | `sgst` | number (0–100) | |
| `igst` | `igst` | number (0–100) | |
| `gstNumber` | `gstNumber` | text (max 15 chars) | |
| `tdsPercent` | `tdsPercent` | number (0–100) | |
| `tdsApplicability` | `tdsApplicability` | select (TdsApplicabilityEnum) | |
| `invoiceSenderName` | `invoiceSenderName` | text | |
| `invoiceSenderPan` | `invoiceSenderPan` | text (10 chars, PAN format) | |
| `invoiceSenderCin` | `invoiceSenderCin` | text (max 21 chars) | |
| `invoiceSenderAddress` | `invoiceSenderAddress` | textarea | |

---

## Section 9 — Email & Communication

| Form Field | DTO Field | Type |
|---|---|---|
| `emailSenderName` | `emailSenderName` | text |
| `emailSenderAddress` | `emailSenderAddress` | email |
| `emailBccName` | `emailBccName` | text |
| `emailBccAddress` | `emailBccAddress` | email |
| `helplineNumber` | `helplineNumber` | text |

---

## Section 10 — Grouped Sub-Programs

Visible only when `programStructure` = `Programs`. Admin adds one or more sub-programs using `GroupedProgramDto`.

**Minimum required per sub-program:*name` + `groupDisplayOrder` (unique, min 1)

| Form Field | DTO Field | Type | Condition |
|---|---|---|---|
| `name` | `name` | text (required) | Always |
| `groupDisplayOrder` | `groupDisplayOrder` | number (min 1, required) | Always |
| `code` | `code` | text | Always |
| `description` | `description` | textarea | Always |
| Dates | `startsAt` / `endsAt` | daterange | Always |
| `modeOfOperation` | `modeOfOperation` | radio: ONLINE/OFFLINE/HYBRID | Always |
| `venueAddress` | `venueAddress` | creatableSelect | offline/hybrid only |
| Check-in Start | `checkinAt` | datetime | offline/hybrid only |
| Check-in End | `checkinEndsAt` | datetime | offline/hybrid only |
| Check-out Start | `checkoutAt` | datetime | offline/hybrid only |
| Check-out End | `checkoutEndsAt` | datetime | offline/hybrid only |
| `hasSeatLimit` | `limitedSeats` | radio | Always |
| `totalSeats` | `totalSeats` | number | when `hasSeatLimit` = yes |
| `waitlistApplicable` | `waitlistApplicable` | radio | when `hasSeatLimit` = yes |
| `waitlistTriggerCount` | `waitlistTriggerCount` | number | when `waitlistApplicable` = yes |

---

## Section 11 — Sessions

Visible only when `programStructure` = `Sessions`. Admin adds one or more sessions using `CreateProgramSessionDto`.

**Minimum required per session:*name`

| Form Field | DTO Field | Type | Condition |
|---|---|---|---|
| `name` | `name` | text (required) | Always |
| `code` | `code` | text | Always |
| `displayOrder` | `displayOrder` | number (min 1) | Always |
| Session Dates | `startsAt` / `endsAt` | daterange | Always |
| `modeOfOperation` | `modeOfOperation` | radio: ONLINE/OFFLINE/HYBRID | Always |
| `meetingLink` | `meetingLink` | text (URL) | online/hybrid only |
| `meetingId` | `meetingId` | text | online/hybrid only |
| `meetingPassword` | `meetingPassword` | text | online/hybrid only |
| `venueAddress` | `venueAddress` | creatableSelect | offline/hybrid only |
| Check-in Start | `checkinAt` | datetime | offline/hybrid only |
| Check-out Start | `checkoutAt` | datetime | offline/hybrid only |
| `limitedSeats` | `limitedSeats` | radio | Always |
| `totalSeats` | `totalSeats` | number | when `limitedSeats` = yes |
| `waitlistApplicable` | `waitlistApplicable` | radio | when `limitedSeats` = yes |
| `waitlistTriggerCount` | `waitlistTriggerCount` | number | when `waitlistApplicable` = yes |
| `description` | `description` | textarea | Always |

---

## Section 12 — Advanced

| Form Field | DTO Field       | Type            |
|------------|-----------------|-----------------|
| `meta`     | `meta`          | textarea (JSON) |

---

## Validation Rules

| Rule | Applies To | Message / Behaviour |
| --- | --- | --- |
| Required fields | `programName`, `modeOfProgram`, `programStructure` | Always required for CUSTOM type |
| At least 1 session | Sessions list when `programStructure` = Sessions | `NO_SESSIONS` — at least 1 session must be added before submission |
| At least 1 sub-program | Grouped sub-programs list when `programStructure` = Programs | `NO_SUB_PROGRAMS` — at least 1 sub-program must be added before submission |
| Declared session count matches actual | `noOfSession` vs. actual count of session entries | `SESSION_COUNT_MISMATCH(declared, actual)` — the number entered in `noOfSession` must equal the number of session entries |
| Declared sub-program count matches actual | `noOfSubPrograms` vs. actual count of sub-program entries | `SUB_PROGRAM_COUNT_MISMATCH(declared, actual)` — the declared count must equal the number of sub-program entries |

---

## API Mapping

| Action         | Endpoint                  | Payload                                                          |
|----------------|---------------------------|------------------------------------------------------------------|
| Create         | `POST /api/programs`      | `CreateProgramDto` + `createdBy` + `updatedBy` from localStorage |
| Edit           | `PATCH /api/programs/:id` | `CreateProgramDto` + `updatedBy` from localStorage               |
| Fetch for edit | `GET /api/programs/:id`   | Pre-fills all sections                                           |


## Summary 

programStructure` determines program type flow:

 `single` → root program only
 `multiple` → enables `programSessions[]`
 `grouped` → enables `groupedPrograms[]`

modeOfProgram` controls operational flow:

 `ONLINE` → online fields enabled, venue/travel fields hidden
 `OFFLINE` → venue fields enabled
 `HYBRID` → both online + venue fields enabled

ONLINE` mode forces:

 `isTravelInvolved = false`
 disables travel interaction
 clears venue-related data

approvalRequired = yes` enables approval timeline flow using `blessEndsAt`.

requiresPayment = yes` enables:

 payment section
 GST/TDS fields
 invoice configuration
 fee configuration

requiresPayment = no` clears all payment/billing fields automatically.

hasSeatLimit = yes` enables:

 `totalSeats`
 `waitlistApplicable`

waitlistApplicable = yes` enables:

 `waitlistTriggerCount`

hasCheckinCheckout = yes` enables:

 check-in/check-out scheduling fields

isResidenceRequired = yes` enables:

 `totalBedCount`

Session mode requires:

 at least 1 session
 `noOfSession` count must match actual session entries

Grouped mode requires:

 at least 1 grouped sub-program
 declared count must match actual entries

Child entities (`programSessions[]`, `groupedPrograms[]`) inherit/sync parent values:

 mode
 venue details
 online details
 seat configuration
 waitlist configuration
 codes

Parent program code auto-generates child codes:

 `<parent>_S1`
 `<parent>_S2`

Changing session/sub-program count replaces and re-scaffolds child arrays.

Hidden conditional fields are auto-cleared before submission to avoid stale data.

visibleWhen`, `visibleWhenAll`, and `disabledWhen` drive conditional rendering and interaction behavior.

prefillFrom` copies parent values into newly created child entities.

dynamicPrefill` derives child values dynamically from parent mappings.

AI-generated configurations must obey all:

 visibility rules
 dependency rules
 validation rules
 cleanup rules
 parent-child sync rules

Wizard submission is always human-reviewed:

 AI only pre-fills
 admin confirms before create/update

Form configuration is fully JSON-driven:

 rendering
 validation
 dependencies
 scaffolding
 conditional visibility
 sync behavior
