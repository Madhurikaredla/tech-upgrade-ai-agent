# AI Agent — Program Configuration API Reference

## 15. Add Program Wizard — APIs Consumed

> All API calls the existing wizard makes during the program creation/edit flow. The AI agent interacts with the same backend context (program types, workflows, codes) — this table documents the full call surface so the agent can be designed without gaps.

| # | Method | Endpoint | When Called | Purpose |
| --- | --- | --- | --- | --- |
| 1 | GET | `program-type/:id` | Page mount — create mode | Fetch program type metadata (name, key, default field values) to initialise the form |
| 2 | GET | `program/:id` | Page mount — edit mode | Fetch existing program data including nested grouped programs and sessions; drives `reset()` pre-fill |
| 3 | GET | `program-type/:typeId` | Page mount — edit mode only, after call #2 | Fetch program type metadata using the `typeId` from the loaded program; merged with program data to initialise the form |
| 4 | GET | `workflow/program-type/:programTypeKey` | After program type loads | Resolve the `workflowId` for the selected program type; stored in state and injected into the submit payload |
| 5 | GET | `program/check-code?code=:code&excludeId=:id` | On every change to the program code field (600 ms debounce) | Real-time uniqueness check; `excludeId` is set in edit mode so the program's own code does not fail validation |
| 6 | GET | `v1/program-templates/program-type/:programTypeId` | On program type load | Fetch available saved templates for the program type; used to pre-populate the form from a template if selected |
| 7 | POST | `aws/file-upload` | On banner image/animation selection and on logo image selection | Upload file to AWS S3; response URL is written into the form field (`bannerImageUrl`, `bannerAnimationUrl`, or `logoUrl`) |
| 8 | POST | `program` | Final step submit — create mode | Create root program + child records (grouped programs / sessions) in one call |
| 9 | PUT | `program/:id` | Final step submit — edit mode | Update existing program and replace child records |
| 10 | GET | `question?filters={"createdBy":"-2"}&limit=100` | After successful POST/PUT response | Fetch default registration questions to pass to the form-builder page the wizard navigates to post-creation |

### Call Sequence — Create Mode

```text
1. GET program-type/:id          → initialise form
2. GET workflow/program-type/:key → resolve workflowId
3. GET v1/program-templates/...  → load templates (if any)
   [user fills form]
4. GET program/check-code?...    → debounced on code field
5. POST aws/file-upload          → on banner / logo upload
6. POST program                  → on final submit
7. GET question?...              → navigate to form builder
```

### Call Sequence — Edit Mode

```text
1. GET program/:id               → load existing program
2. GET program-type/:typeId      → load type metadata, merge
3. GET workflow/program-type/:key → resolve workflowId
   [user edits form]
4. GET program/check-code?...&excludeId=:id  → on code change
5. POST aws/file-upload          → if banner / logo changed
6. PUT program/:id               → on save submit
7. GET question?...              → navigate to form builder
```

---

## API Payloads

All responses are wrapped in the standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Error responses use the same envelope with `success: false`, `data: null`, and `error` populated.

---

### API 1 & 3 — GET `program-type/:id`

**Path param:** `id` (number) — the program type's numeric ID.

**Response `data`:**

```json
{
  "id": 1,
  "name": "HDB MSD",
  "key": "PT_HDBMSD",
  "description": "Himalayan Boundary program type",
  "modeOfOperation": "offline",
  "onlineType": "NA",
  "maxSessionDurationDays": 8,
  "hasMultipleSessions": true,
  "frequency": "YEARLY",
  "defaultStartTime": "09:00:00",
  "defaultEndTime": "18:00:00",
  "defaultDuration": "8 hours",
  "requiresResidence": false,
  "involvesTravel": false,
  "hasGoodies": false,
  "hasCheckinCheckout": false,
  "requiresPayment": true,
  "requiresAttendanceAllSessions": true,
  "allowsMinors": false,
  "allowsProxyRegistration": false,
  "requiresApproval": false,
  "registrationLevel": "SESSION",
  "isActive": true,
  "noOfSession": 0,
  "waitlistApplicable": false,
  "maxCapacity": 0,
  "limitedSeats": false,
  "isGroupedProgram": false,
  "venue": null,
  "meta": {},
  "logoUrl": null,
  "bannerUrl": null,
  "subProgramType": null,
  "allowSaveAsDraft": false,
  "currency": "INR",
  "maxProxyRegistrations": 0,
  "seekerCanShareExperience": false,
  "igst": 0,
  "cgst": 0,
  "sgst": 0,
  "gstPercentage": 18.0,
  "tdsPercent": 0,
  "gstNumber": null,
  "tdsApplicability": null,
  "invoiceSenderName": null,
  "invoiceSenderPan": null,
  "invoiceSenderCin": null,
  "invoiceSenderAddress": null,
  "helplineNumber": null,
  "emailSenderName": null,
  "emailSenderAddress": null,
  "emailBccAddress": null,
  "emailBccName": null,
  "venueNameInEmails": null,
  "createdAt": "2024-01-01T00:00:00.000Z",
  "updatedAt": "2024-01-01T00:00:00.000Z",
  "deletedAt": null,
  "createdBy": 1,
  "updatedBy": 1
}
```

**Enum values:**

| Field | Values |
| --- | --- |
| `modeOfOperation` | `online`, `offline`, `hybrid` |
| `onlineType` | `NA`, `meeting`, `webinar`, `live_stream` |
| `frequency` | `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`, `ONE_TIME` |
| `registrationLevel` | `PROGRAM`, `SESSION` |
| `tdsApplicability` | `APPLICABLE`, `NOT_APPLICABLE`, `EXEMPTED` |

---

### API 2 — GET `program/:id`

**Path param:** `id` (number) — the program's numeric ID.

**Response `data`:**

```json
{
  "id": 101,
  "typeId": 1,
  "workflowId": 13,
  "programTemplateId": null,
  "name": "HDB MSD 2025",
  "code": "HDB_MSD_2025",
  "description": "Annual HDB MSD program",
  "modeOfOperation": "offline",
  "onlineType": "NA",
  "maxSessionDurationDays": 8,
  "hasMultipleSessions": true,
  "frequency": "YEARLY",
  "defaultStartTime": "09:00:00",
  "defaultEndTime": "18:00:00",
  "startsAt": "2025-03-01T00:00:00.000Z",
  "endsAt": "2025-03-08T00:00:00.000Z",
  "blessEndsAt": null,
  "canRegisterTill": "2025-02-28T23:59:59.000Z",
  "duration": "8 days",
  "requiresResidence": true,
  "requiresPayment": true,
  "requiresAttendanceAllSessions": true,
  "allowsMinors": false,
  "allowsProxyRegistration": false,
  "requiresApproval": false,
  "allowSaveAsDraft": false,
  "registrationLevel": "SESSION",
  "limitedSeats": true,
  "isGroupedProgram": false,
  "totalSeats": 500,
  "waitlistTriggerCount": 50,
  "availableSeats": 450,
  "filledSeats": 50,
  "waitlistApplicable": true,
  "maxCapacity": 500,
  "registrationStartsAt": "2025-01-01T00:00:00.000Z",
  "registrationEndsAt": "2025-02-28T23:59:59.000Z",
  "basePrice": 15000,
  "programFee": 15000,
  "gstPercentage": 18,
  "cgst": 9,
  "sgst": 9,
  "igst": 0,
  "tdsPercent": 0,
  "gstNumber": "27AAACG1234R1Z5",
  "tdsApplicability": null,
  "allocateSeatIfOfflinePending": false,
  "invoiceSenderName": "Infinitheism",
  "invoiceSenderPan": null,
  "invoiceSenderCin": null,
  "invoiceSenderAddress": null,
  "helplineNumber": null,
  "emailSenderName": null,
  "emailSenderAddress": null,
  "emailBccAddress": null,
  "emailBccName": null,
  "venueNameInEmails": null,
  "seekerCanShareExperience": false,
  "totalBedCount": 0,
  "launchDate": null,
  "currency": "INR",
  "status": "DRAFT",
  "isActive": true,
  "noOfSession": 8,
  "venue": "Coimbatore",
  "isTravelInvolved": false,
  "hasGoodies": false,
  "hasCheckinCheckout": true,
  "checkinAt": "2025-03-01T06:00:00.000Z",
  "checkoutAt": "2025-03-08T12:00:00.000Z",
  "checkinEndsAt": null,
  "checkoutEndsAt": null,
  "bannerImageUrl": "https://bucket.s3.region.amazonaws.com/assets/program/banner/ts_filename.jpg",
  "bannerAnimationUrl": null,
  "logoUrl": null,
  "subProgramType": null,
  "groupId": null,
  "isPrimaryProgram": false,
  "primaryProgramId": null,
  "groupDisplayOrder": 1,
  "elderMinAge": null,
  "childMaxAge": null,
  "meta": {},
  "meetingDetails": null,
  "webinarDetails": null,
  "streamDetails": null,
  "venueAddressId": null,
  "venueAddress": null,
  "groupedPrograms": [],
  "programSessions": [
    {
      "id": 201,
      "programId": 101,
      "name": "Day 1",
      "code": "HDB_MSD_2025_D1",
      "displayOrder": 1,
      "startsAt": "2025-03-01T09:00:00.000Z",
      "endsAt": "2025-03-01T18:00:00.000Z",
      "status": "scheduled",
      "isActive": true,
      "totalSeats": 500,
      "availableSeats": 450,
      "venue": "Main Hall"
    }
  ],
  "type": {
    "id": 1,
    "name": "HDB MSD",
    "key": "PT_HDBMSD"
  },
  "createdAt": "2024-12-01T00:00:00.000Z",
  "updatedAt": "2024-12-15T00:00:00.000Z",
  "deletedAt": null,
  "createdBy": 1,
  "updatedBy": 1
}
```

**Enum values:**

| Field | Values |
| --- | --- |
| `status` | `DRAFT`, `PUBLISHED`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `ARCHIVED` |

---

### API 4 — GET `workflow/program-type/:programTypeKey`

**Path param:** `programTypeKey` (string) — e.g. `PT_HDBMSD`.

**Response `data`:**

```json
{
  "workflowId": 13,
  "workflowKey": "WF_HDBMSD_V1",
  "workflowName": "HDB MSD Workflow",
  "programTypeKey": "PT_HDBMSD"
}
```

> The `workflowId` from this response must be injected into the `workflowId` field of the POST/PUT program payload.

---

### API 5 — GET `program/check-code`

**Query params:**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | string (max 50) | Yes | Program code to check, e.g. `HDB_2026` |
| `excludeId` | number | No | Exclude this program ID from the check (use in edit mode) |

**Response `data` (code available):**

```json
{
  "isAvailable": true
}
```

**Response `data` (code taken):**

```json
{
  "isAvailable": false,
  "conflictingProgram": {
    "id": 55,
    "name": "HDB 2026 Batch A",
    "code": "HDB_2026"
  }
}
```

---

### API 6 — GET `v1/program-templates/program-type/:programTypeId`

**Path param:** `programTypeId` (number) — numeric ID of the program type.

**Response `data`** (array of templates):

```json
[
  {
    "id": 10,
    "programTypeId": 1,
    "name": "HDB MSD 2025 Template",
    "description": "Standard template for HDB MSD programs",
    "version": 1,
    "status": "ACTIVE",
    "isActive": true,
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z",
    "createdBy": 1
  }
]
```

**Enum values:**

| Field | Values |
| --- | --- |
| `status` | `DRAFT`, `ACTIVE`, `ARCHIVED` |

---

### API 7 — POST `aws/file-upload`

**Request body:**

```json
{
  "fileName": "banner.jpg",
  "contentType": "image/jpeg",
  "imageType": "BANNER",
  "programCode": "HDB_MSD_2025",
  "userId": 1
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fileName` | string | Yes | Name of the file to upload |
| `contentType` | string | Yes | MIME type, e.g. `image/jpeg`, `image/png`, `image/gif` |
| `imageType` | enum | No | See enum values below |
| `programCode` | string | No | Program code — used to scope the S3 path |
| `userId` | number | No | Overrides the authenticated user for the S3 path |

**Enum values for `imageType`:**

| Value | Usage |
| --- | --- |
| `BANNER` | Program banner image / animation |
| `PROFILE` | User profile photo |
| `FACE` | Face login image |

**Response `data`:**

```json
{
  "putUrl": "https://bucket.s3.region.amazonaws.com/assets/program/banner/1700000000000_banner.jpg?X-Amz-...",
  "accessUrl": "https://bucket.s3.region.amazonaws.com/assets/program/banner/1700000000000_banner.jpg"
}
```

> The wizard PUTs the file binary directly to `putUrl` and then writes `accessUrl` into `bannerImageUrl`, `bannerAnimationUrl`, or `logoUrl` on the program form.

---

### API 8 — POST `program`

**Request body:**

```json
{
  "typeId": 1,
  "workflowId": 13,
  "programTemplateId": 10,
  "name": "HDB MSD 2025",
  "code": "HDB_MSD_2025",
  "description": "Annual HDB MSD program",
  "modeOfOperation": "offline",
  "onlineType": "NA",
  "maxSessionDurationDays": 8,
  "hasMultipleSessions": true,
  "frequency": "YEARLY",
  "defaultStartTime": "09:00:00",
  "defaultEndTime": "18:00:00",
  "startsAt": "2025-03-01T00:00:00.000Z",
  "endsAt": "2025-03-08T00:00:00.000Z",
  "blessEndsAt": null,
  "canRegisterTill": "2025-02-28T23:59:59.000Z",
  "duration": "8 days",
  "requiresResidence": true,
  "requiresPayment": true,
  "requiresAttendanceAllSessions": true,
  "allowsMinors": false,
  "allowsProxyRegistration": false,
  "requiresApproval": false,
  "allowSaveAsDraft": false,
  "registrationLevel": "SESSION",
  "limitedSeats": true,
  "isGroupedProgram": false,
  "totalSeats": 500,
  "waitlistTriggerCount": 50,
  "availableSeats": 500,
  "waitlistApplicable": true,
  "maxCapacity": 500,
  "registrationStartsAt": "2025-01-01T00:00:00.000Z",
  "registrationEndsAt": "2025-02-28T23:59:59.000Z",
  "basePrice": 15000,
  "programFee": 15000,
  "gstPercentage": 18,
  "cgst": 9,
  "sgst": 9,
  "igst": 0,
  "tdsPercent": 0,
  "gstNumber": "27AAACG1234R1Z5",
  "tdsApplicability": null,
  "allocateSeatIfOfflinePending": false,
  "invoiceSenderName": "Infinitheism",
  "invoiceSenderPan": null,
  "invoiceSenderCin": null,
  "invoiceSenderAddress": null,
  "helplineNumber": null,
  "emailSenderName": null,
  "emailSenderAddress": null,
  "emailBccAddress": null,
  "emailBccName": null,
  "venueNameInEmails": null,
  "seekerCanShareExperience": false,
  "totalBedCount": 0,
  "launchDate": null,
  "currency": "INR",
  "status": "DRAFT",
  "isActive": true,
  "noOfSession": 8,
  "venue": "Coimbatore",
  "isTravelInvolved": false,
  "hasGoodies": false,
  "hasCheckinCheckout": true,
  "checkinAt": "2025-03-01T06:00:00.000Z",
  "checkoutAt": "2025-03-08T12:00:00.000Z",
  "checkinEndsAt": null,
  "checkoutEndsAt": null,
  "bannerImageUrl": "https://bucket.s3.region.amazonaws.com/assets/program/banner/ts_banner.jpg",
  "bannerAnimationUrl": null,
  "logoUrl": null,
  "subProgramType": null,
  "elderMinAge": null,
  "childMaxAge": null,
  "meta": {},
  "venueAddress": {
    "addressLine1": "123 Main Road",
    "addressLine2": null,
    "city": "Coimbatore",
    "state": "Tamil Nadu",
    "country": "India",
    "pincode": "641001"
  },
  "meetingDetails": null,
  "webinarDetails": null,
  "streamDetails": null,
  "groupedPrograms": [
    {
      "name": "Group A",
      "code": "HDB_MSD_2025_GA",
      "groupDisplayOrder": 1,
      "startsAt": "2025-03-01T00:00:00.000Z",
      "endsAt": "2025-03-08T00:00:00.000Z",
      "totalSeats": 250,
      "basePrice": 15000,
      "programFee": 15000,
      "description": null
    }
  ],
  "programSessions": [
    {
      "programId": 0,
      "name": "Day 1",
      "code": "HDB_MSD_2025_D1",
      "displayOrder": 1,
      "startsAt": "2025-03-01T09:00:00.000Z",
      "endsAt": "2025-03-01T18:00:00.000Z",
      "venue": "Main Hall",
      "modeOfOperation": "offline",
      "totalSeats": 500,
      "registrationStartsAt": "2025-01-01T00:00:00.000Z",
      "registrationEndsAt": "2025-02-28T23:59:59.000Z",
      "status": "scheduled",
      "isActive": true,
      "createdBy": 1,
      "updatedBy": 1
    }
  ],
  "createdBy": 1,
  "updatedBy": 1
}
```

**Required fields:** `typeId`, `workflowId`, `name`, `createdBy`, `updatedBy`

**Response `data`:** Full program object (same shape as GET `program/:id`).

#### `venueAddress` object

| Field | Type | Required |
| --- | --- | --- |
| `addressLine1` | string | No |
| `addressLine2` | string | No |
| `city` | string | No |
| `state` | string | No |
| `country` | string | No |
| `pincode` | string | No |

#### `groupedPrograms` items

Each item inherits all optional fields from the root program payload. Additional required field:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | number | No (omit on create, include on update) | Program ID of the grouped sub-program |
| `name` | string | Yes | Name of the sub-program |
| `groupDisplayOrder` | number | Yes (min 1) | Display order within the group |

#### `programSessions` items

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | number | No (omit on create, include on update) | Session ID |
| `programId` | number | Yes | Parent program ID (use `0` on create; server assigns) |
| `name` | string | Yes | Session name |
| `code` | string | No | Session code |
| `displayOrder` | number | No | Sort order (min 1) |
| `startsAt` | ISO date | No | Session start datetime |
| `endsAt` | ISO date | No | Session end datetime |
| `blessEndsAt` | ISO date | No | Bless end datetime |
| `canRegisterTill` | ISO date | No | Registration cut-off |
| `venue` | string | No | Session venue |
| `modeOfOperation` | enum | No | `online`, `offline`, `hybrid` |
| `meetingLink` | string | No | Online meeting link |
| `meetingId` | string | No | Online meeting ID |
| `meetingPassword` | string | No | Online meeting password |
| `totalSeats` | number | No | Total seats for session |
| `availableSeats` | number | No | Available seats |
| `waitlistTriggerCount` | number | No | Seat count that triggers waitlist |
| `waitlistApplicable` | boolean | No | Whether waitlist is active |
| `reservedSeats` | number | No | Reserved / hold seats |
| `registrationStartsAt` | ISO date | No | Session registration open |
| `registrationEndsAt` | ISO date | No | Session registration close |
| `checkinAt` | ISO date | No | Check-in datetime |
| `checkoutAt` | ISO date | No | Check-out datetime |
| `checkinEndsAt` | ISO date | No | Check-in window close |
| `checkoutEndsAt` | ISO date | No | Check-out window close |
| `status` | enum | No | `scheduled`, `active`, `completed`, `cancelled`, `postponed` |
| `isActive` | boolean | No | Whether session is active |
| `limitedSeats` | boolean | No | Whether seat limit is enforced |
| `allowsProxyRegistration` | boolean | No | Whether proxy registration is allowed |
| `maxProxyRegistrations` | number | No | Max proxy registrations per user (0 = unlimited) |
| `basePrice` | decimal | No | Base price for session |
| `programFee` | decimal | No | Fee charged to registrant |
| `gstPercentage` | decimal | No | GST % (0–100) |
| `cgst` | decimal | No | CGST rate |
| `sgst` | decimal | No | SGST rate |
| `igst` | decimal | No | IGST rate |
| `tdsPercent` | decimal | No | TDS % |
| `tdsApplicability` | enum | No | `APPLICABLE`, `NOT_APPLICABLE`, `EXEMPTED` |
| `gstNumber` | string | No | GST number |
| `currency` | string | No | ISO currency code, e.g. `INR` |
| `invoiceSenderName` | string | No | Invoice entity name |
| `invoiceSenderPan` | string | No | PAN of invoice entity |
| `invoiceSenderCin` | string | No | CIN of invoice entity |
| `invoiceSenderAddress` | string | No | Invoice entity address |
| `helplineNumber` | string | No | Support number shown in emails |
| `emailSenderName` | string | No | From-name for outgoing emails |
| `emailSenderAddress` | string | No | From-address for outgoing emails |
| `emailBccAddress` | string | No | BCC address for outgoing emails |
| `emailBccName` | string | No | BCC display name |
| `venueNameInEmails` | string | No | Venue name shown in emails |
| `bannerImageUrl` | string | No | Session banner image URL |
| `bannerAnimationUrl` | string | No | Session banner animation URL |
| `logoUrl` | string | No | Session logo URL |
| `launchDate` | ISO date | No | Public launch date |
| `description` | string | No | Session description |
| `meta` | object | No | Arbitrary key-value metadata |
| `isTravelRequired` | boolean | No | Whether travel is required |
| `meetingDetails` | object | No | For `onlineType: meeting` |
| `webinarDetails` | object | No | For `onlineType: webinar` |
| `streamDetails` | object | No | For `onlineType: live_stream` |
| `venueAddress` | object | No | Nested address (same shape as root `venueAddress`) |
| `createdBy` | number | Yes | User ID |
| `updatedBy` | number | Yes | User ID |

#### Online details objects

These are passed when `onlineType` is `meeting`, `webinar`, or `live_stream`.

```json
"meetingDetails": {
  "meetingLink": "https://zoom.us/j/123456789",
  "meetingId": "123456789",
  "meetingPassword": "pass123",
  "platform": "zoom"
}
```

```json
"webinarDetails": {
  "webinarLink": "https://zoom.us/w/987654321",
  "webinarId": "987654321",
  "platform": "zoom"
}
```

```json
"streamDetails": {
  "streamUrl": "https://youtube.com/live/abc123",
  "platform": "youtube"
}
```

---

### API 9 — PUT `program/:id`

**Path param:** `id` (number) — program ID to update.

**Request body:** Same shape as POST `program` above, with these differences:

- `createdBy` is **omitted** (not allowed in update).
- `updatedBy` is **required**.
- `groupedPrograms` items that already exist **must include `id`**.
- `programSessions` items that already exist **must include `id`** inside the session object.
- Two additional top-level fields for explicit deletion:

```json
{
  "updatedBy": 1,
  "name": "HDB MSD 2025 — Updated",
  "groupedPrograms": [
    {
      "id": 201,
      "name": "Group A — Updated",
      "groupDisplayOrder": 1
    }
  ],
  "deletedProgramIds": [202, 203],
  "deletedSessionIds": [301, 302]
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `updatedBy` | number | Yes | ID of user making the update |
| `deletedProgramIds` | number[] | No | IDs of grouped sub-programs to hard-delete |
| `deletedSessionIds` | number[] | No | IDs of sessions to hard-delete |

**Response `data`:** Updated full program object (same shape as GET `program/:id`).

---

### API 10 — GET `question`

**Query params:**

| Param | Type | Description |
| --- | --- | --- |
| `filters` | JSON string | `{"createdBy":"-2"}` — fetches system default questions |
| `limit` | number | Maximum results to return, e.g. `100` |

Example: `GET /question?filters={"createdBy":"-2"}&limit=100`

**Response `data`** (array of questions):

```json
[
  {
    "id": 1,
    "label": "First Name",
    "type": "text",
    "answerType": "SHORT_TEXT",
    "status": "ACTIVE",
    "config": {
      "is_required": true,
      "placeholder": "Enter your first name"
    },
    "formSectionId": null,
    "createdBy": -2,
    "updatedBy": -2,
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
]
```

| Field | Type | Description |
| --- | --- | --- |
| `id` | number | Question ID |
| `label` | string | Display label shown to the registrant |
| `type` | string | Input type, e.g. `text`, `select`, `radio`, `checkbox` |
| `answerType` | enum | `SHORT_TEXT`, `LONG_TEXT`, `SINGLE_SELECT`, `MULTI_SELECT`, `DATE`, `NUMBER`, `BOOLEAN` |
| `status` | enum | `ACTIVE`, `INACTIVE` |
| `config` | object | Validation and display config (e.g. `is_required`, `placeholder`, `options`) |
| `formSectionId` | number \| null | Section grouping ID, null for ungrouped |
| `createdBy` | number | `-2` = system default question |

---

## Add Program Page — API Payloads Reference

All endpoints use the PORTAL base URL. Auth token required in headers.

---

### API 1 — `GET /program/{programId}` — Load existing program (edit mode)

**Request:** No body. Path param: `programId` (number)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "TAT TA26",
    "code": "TA26",
    "description": "TAT 2026 online webinar",
    "typeId": 3,
    "workflowId": 7,
    "programTemplateId": 2,
    "modeOfOperation": "ONLINE",
    "onlineType": "WEBINAR",
    "registrationLevel": "PROGRAM",
    "status": "DRAFT",
    "accessType": "PUBLIC",
    "isActive": true,
    "isGroupedProgram": false,
    "startsAt": "2026-05-01T00:00:00Z",
    "endsAt": "2026-07-17T00:00:00Z",
    "blessEndsAt": null,
    "canRegisterTill": "2026-04-30T00:00:00Z",
    "registrationStartsAt": "2026-02-01T00:00:00Z",
    "registrationEndsAt": "2026-04-30T00:00:00Z",
    "checkinAt": null,
    "checkoutAt": null,
    "checkinEndsAt": null,
    "checkoutEndsAt": null,
    "launchDate": null,
    "duration": "12 weeks",
    "noOfSession": 12,
    "frequency": "YEARLY",
    "hasMultipleSessions": true,
    "maxSessionDurationDays": 8,
    "defaultStartTime": "19:00:00",
    "defaultEndTime": "21:00:00",
    "venue": null,
    "requiresResidence": false,
    "involvesTravel": false,
    "hasGoodies": false,
    "hasCheckinCheckout": false,
    "requiresPayment": true,
    "requiresAttendanceAllSessions": true,
    "allowsMinors": false,
    "allowsProxyRegistration": false,
    "maxProxyRegistrations": 0,
    "requiresApproval": false,
    "allowSaveAsDraft": false,
    "limitedSeats": true,
    "waitlistApplicable": true,
    "totalSeats": 200,
    "waitlistTriggerCount": 20,
    "availableSeats": 200,
    "filledSeats": 0,
    "maxCapacity": null,
    "allocateSeatIfOfflinePending": false,
    "programFee": 5000.00,
    "basePrice": 4237.29,
    "gstPercentage": 18.00,
    "cgst": 9.00,
    "sgst": 9.00,
    "igst": 0.00,
    "tdsPercent": 0.00,
    "tdsApplicability": null,
    "gstNumber": "29ABCDE1234F1Z5",
    "currency": "INR",
    "invoiceSenderName": "Infinitheism",
    "invoiceSenderPan": "ABCDE1234F",
    "invoiceSenderCin": null,
    "invoiceSenderAddress": "123 Main St, Chennai",
    "helplineNumber": "+91 9876543210",
    "emailSenderName": "Infinitheism Team",
    "emailSenderAddress": "noreply@infinitheism.com",
    "emailBccAddress": null,
    "emailBccName": null,
    "venueNameInEmails": null,
    "bannerImageUrl": null,
    "bannerAnimationUrl": null,
    "logoUrl": null,
    "seekerCanShareExperience": false,
    "totalBedCount": 0,
    "elderMinAge": null,
    "childMaxAge": null,
    "meta": {},
    "meetingDetails": null,
    "webinarDetails": {
      "platform": "Zoom",
      "link": "https://zoom.us/j/123456789"
    },
    "streamDetails": null,
    "venueAddress": null,
    "subProgramType": null,
    "groupId": null,
    "isPrimaryProgram": false,
    "primaryProgramId": null,
    "groupDisplayOrder": 1,
    "createdAt": "2026-02-23T00:00:00Z",
    "updatedAt": "2026-02-23T00:00:00Z",
    "createdBy": 1,
    "updatedBy": 1,
    "type": {
      "id": 3,
      "key": "PT_TAT",
      "name": "Transcendence Achievement Training"
    }
  },
  "error": null
}
```

---

### API 2 — `GET /program-type/{typeId}` — Fetch program type details

**Request:** No body. Path param: `typeId` (number)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 3,
    "key": "PT_TAT",
    "name": "Transcendence Achievement Training",
    "description": "12-week online program",
    "modeOfOperation": "ONLINE",
    "registrationLevel": "PROGRAM",
    "defaultWorkflowId": 7,
    "gstPercentage": 18.00,
    "cgst": 9.00,
    "sgst": 9.00,
    "igst": 0.00,
    "tdsPercent": 0.00,
    "tdsApplicability": null,
    "requiresPayment": true,
    "requiresApproval": false,
    "allowsMinors": false,
    "allowsProxyRegistration": false,
    "involvesTravel": false,
    "hasGoodies": false,
    "requiresResidence": false,
    "isActive": true,
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-01T00:00:00Z"
  },
  "error": null
}
```

---

### API 3 — `GET /program/check-code` — Code uniqueness check

**Query params:**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | string | Yes | Program code to check (max 50 chars) |
| `excludeId` | number | No | Program ID to exclude (edit mode) |

**Example:** `GET /program/check-code?code=TA26&excludeId=42`

**Response (available):**

```json
{
  "success": true,
  "data": { "isAvailable": true },
  "error": null
}
```

**Response (taken):**

```json
{
  "success": true,
  "data": { "isAvailable": false },
  "error": null
}
```

---

### API 4 — `POST /program` — Create new program

**Required fields:** `typeId`, `workflowId`, `name`, `createdBy`, `updatedBy`

**Request body:**

```json
{
  "typeId": 3,
  "workflowId": 7,
  "programTemplateId": 2,
  "name": "TAT TA26",
  "code": "TA26",
  "description": "TAT 2026 online webinar program",
  "modeOfOperation": "ONLINE",
  "onlineType": "WEBINAR",
  "registrationLevel": "PROGRAM",
  "startsAt": "2026-05-01T00:00:00Z",
  "endsAt": "2026-07-17T00:00:00Z",
  "canRegisterTill": "2026-04-30T00:00:00Z",
  "registrationStartsAt": "2026-02-01T00:00:00Z",
  "registrationEndsAt": "2026-04-30T00:00:00Z",
  "duration": "12 weeks",
  "noOfSession": 12,
  "hasMultipleSessions": true,
  "frequency": "YEARLY",
  "defaultStartTime": "19:00:00",
  "defaultEndTime": "21:00:00",
  "requiresPayment": true,
  "requiresApproval": false,
  "allowsMinors": false,
  "allowsProxyRegistration": false,
  "allowSaveAsDraft": false,
  "requiresResidence": false,
  "involvesTravel": false,
  "hasGoodies": false,
  "hasCheckinCheckout": false,
  "limitedSeats": true,
  "waitlistApplicable": true,
  "totalSeats": 200,
  "waitlistTriggerCount": 20,
  "programFee": 5000.00,
  "basePrice": 4237.29,
  "gstPercentage": 18.00,
  "cgst": 9.00,
  "sgst": 9.00,
  "igst": 0.00,
  "currency": "INR",
  "invoiceSenderName": "Infinitheism",
  "invoiceSenderPan": "ABCDE1234F",
  "invoiceSenderAddress": "123 Main St, Chennai",
  "helplineNumber": "+91 9876543210",
  "emailSenderName": "Infinitheism Team",
  "emailSenderAddress": "noreply@infinitheism.com",
  "status": "DRAFT",
  "isActive": true,
  "webinarDetails": {
    "platform": "Zoom",
    "link": "https://zoom.us/j/123456789"
  },
  "meta": {},
  "createdBy": 1,
  "updatedBy": 1
}
```

**For grouped programs**, add:

```json
{
  "isGroupedProgram": true,
  "groupedPrograms": [
    {
      "name": "TAT TA26 - Batch A",
      "code": "TA26-A",
      "startsAt": "2026-05-01T00:00:00Z",
      "endsAt": "2026-07-17T00:00:00Z",
      "groupDisplayOrder": 1,
      "totalSeats": 100,
      "programFee": 5000.00
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "TAT TA26",
    "code": "TA26",
    "status": "DRAFT"
  },
  "error": null
}
```

---

### API 5 — `PUT /program/{id}` — Update existing program

**Request:** Path param `id` (number). Body is partial — send only fields to update.

```json
{
  "name": "TAT TA26 (Updated)",
  "totalSeats": 250,
  "programFee": 5500.00,
  "basePrice": 4661.02,
  "registrationEndsAt": "2026-05-15T00:00:00Z",
  "webinarDetails": {
    "platform": "Zoom",
    "link": "https://zoom.us/j/987654321"
  },
  "updatedBy": 1,
  "deletedSessionIds": [],
  "deletedProgramIds": []
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "TAT TA26 (Updated)",
    "updatedAt": "2026-05-20T10:00:00Z"
  },
  "error": null
}
```

---

### API 6 — `GET /question` — Fetch questions (form builder)

**Query params:**

| Param | Type | Description |
| --- | --- | --- |
| `limit` | number | Page size (e.g. 100) |
| `offset` | number | Pagination offset |
| `searchText` | string | Search by label |
| `filters` | JSON string | e.g. `{"status":"ACTIVE","formSectionId":5}` |

**Example:** `GET /question?limit=100&offset=0&filters={"createdBy":"-2"}`

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 10,
        "label": "Full Name",
        "type": "TEXT",
        "answerType": "STRING",
        "status": "ACTIVE",
        "bindingKey": "fullName",
        "config": {
          "isRequired": true,
          "maxLength": 255
        },
        "optionConfig": null,
        "conditionalConfig": null,
        "formSectionId": 5,
        "createdAt": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  },
  "error": null
}
```

---

### API 7 — `POST /program/form` — Save form (new program, form builder)

**Request body:**

```json
{
  "programId": 42,
  "programTemplateId": 2,
  "cloneFromTemplate": true,
  "sections": [
    {
      "templateFormSectionId": 15,
      "displayOrder": 1,
      "questions": [
        { "masterQuestionId": 101, "displayOrder": 1 },
        { "masterQuestionId": 102, "displayOrder": 2 }
      ]
    },
    {
      "sectionName": "Additional Info",
      "sectionKey": "FS_ADDITIONAL",
      "sectionDescription": "Extra questions",
      "displayOrder": 2,
      "questions": [
        {
          "label": "T-shirt size",
          "type": "DROPDOWN",
          "displayOrder": 1,
          "optionConfig": [
            { "label": "S", "value": "S" },
            { "label": "M", "value": "M" },
            { "label": "L", "value": "L" }
          ],
          "config": { "isRequired": false }
        }
      ]
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "programId": 42,
    "sectionsCreated": 2,
    "questionsCreated": 3
  },
  "error": null
}
```

---

### API 8 — `PATCH /program/{programId}/form` — Update form (existing program)

**Request:** Path param `programId`. Body is delta — only changed items.

```json
{
  "deleteSectionIds": [23],
  "updateSections": [
    {
      "formSectionId": 20,
      "sectionName": "Basic Details (Updated)",
      "displayOrder": 1,
      "updateQuestions": [
        {
          "programQuestionId": 55,
          "displayOrder": 3,
          "config": { "isRequired": true }
        }
      ],
      "addQuestions": [
        { "masterQuestionId": 110, "displayOrder": 5 }
      ],
      "deleteQuestionIds": [48]
    }
  ],
  "addSections": [
    {
      "sectionName": "Travel Preferences",
      "sectionKey": "FS_TRAVEL_PREF",
      "displayOrder": 3,
      "questions": [
        {
          "label": "Mode of transport",
          "type": "RADIO",
          "displayOrder": 1,
          "optionConfig": [
            { "label": "Flight", "value": "flight" },
            { "label": "Train", "value": "train" }
          ]
        }
      ]
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "programId": 42,
    "sectionsDeleted": 1,
    "sectionsUpdated": 1,
    "sectionsAdded": 1
  },
  "error": null
}
```

---

### API 9 — `DELETE /program-question/{questionId}` — Remove a question

**Request:** Path param `questionId` (number). No body.

**Response:**

```json
{
  "success": true,
  "data": { "deleted": true, "id": 55 },
  "error": null
}
```

---

### API 10 — `POST /program-question` — Add questions to program (publish step)

**Request body:**

```json
{
  "programId": 42,
  "registrationLevel": "PROGRAM",
  "sections": [
    {
      "sectionName": "Basic Details",
      "sectionDisplayOrder": 1,
      "questions": [
        { "questionId": 101, "displayOrder": 1 },
        { "questionId": 102, "displayOrder": 2 }
      ],
      "customQuestions": [
        {
          "question": {
            "label": "Dietary preference",
            "type": "RADIO",
            "bindingKey": "dietaryPreference"
          },
          "options": [
            { "name": "Vegetarian", "type": "OPTION" },
            { "name": "Non-Vegetarian", "type": "OPTION" }
          ],
          "displayOrder": 3
        }
      ]
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "programId": 42,
    "questionsAdded": 3
  },
  "error": null
}
```

---

### API 11 — `PUT /program/{programId}/status` — Publish program

**Request:** Path param `programId`.

**Public access:**

```json
{
  "status": "PUBLISHED",
  "updatedBy": 1,
  "accessType": "PUBLIC",
  "clearExistingRegistrations": false
}
```

**Restricted access:**

```json
{
  "status": "PUBLISHED",
  "updatedBy": 1,
  "accessType": "RESTRICTED",
  "programAccess": {
    "addUserIds": [101, 102, 103],
    "removeUserIds": [],
    "accessScope": "VIEW_AND_REGISTER",
    "effectiveFrom": "2026-02-01T00:00:00Z",
    "effectiveTill": "2026-04-30T00:00:00Z"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 42,
    "status": "PUBLISHED",
    "accessType": "PUBLIC",
    "updatedAt": "2026-05-20T10:00:00Z"
  },
  "error": null
}
```

---

### API 12 — `GET /user` — Paginated user list (access control)

**Query params:**

| Param | Type | Description |
| --- | --- | --- |
| `limit` | number | Page size |
| `offset` | number | Pagination offset |
| `searchText` | string | Search by name / email / phone |
| `filters` | JSON string | e.g. `{"role":"ROLE_VIEWER","userApprovalStatus":"APPROVED"}` |

**Example:** `GET /user?limit=20&offset=0&searchText=john&filters={"role":"ROLE_VIEWER"}`

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 101,
        "fullName": "John Doe",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "phoneNumber": "9876543210",
        "countryCode": "+91",
        "role": "ROLE_VIEWER",
        "gender": "MALE",
        "dob": "1990-01-15",
        "userApprovalStatus": "APPROVED",
        "profileUrl": null,
        "userType": "SEEKER",
        "createdAt": "2025-06-01T00:00:00Z"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  },
  "error": null
}
```

---

### Add Program Page — Endpoint Summary

| # | Method | Endpoint | Page / Component | Purpose |
| --- | --- | --- | --- | --- |
| 1 | GET | `program/{programId}` | AddProgramPage | Load existing program (edit mode) |
| 2 | GET | `program-type/{typeId}` | AddProgramPage | Fetch program type details |
| 3 | GET | `program/check-code?code=&excludeId=` | AddProgramPage, DynamicSubProgramCard | Real-time code uniqueness check |
| 4 | POST | `program` | AddProgramPage | Create new program |
| 5 | PUT | `program/{id}` | AddProgramPage | Update existing program |
| 6 | GET | `question?filters=...&limit=100` | AddProgramPage, FormBuilderEdit | Fetch questions for form builder |
| 7 | POST | `program/form` | FormBuilderEdit | Save form for new program |
| 8 | PATCH | `program/{programId}/form` | FormBuilderEdit | Update form for existing program |
| 9 | DELETE | `program-question/{questionId}` | FormBuilderEdit | Remove a question |
| 10 | POST | `program-question` | PreviewForm / PublishModal | Add questions at publish step |
| 11 | PUT | `program/{programId}/status` | PreviewForm / PublishModal | Publish program |
| 12 | GET | `user?limit=&offset=&searchText=&filters=` | PublishModal | Paginated user list for access control |

---

### Enum Reference

| Enum | Values |
| --- | --- |
| `modeOfOperation` | `ONLINE`, `OFFLINE`, `HYBRID` |
| `onlineType` | `WEBINAR`, `LIVE_STREAM`, `RECORDED`, `NA` |
| `registrationLevel` | `PROGRAM`, `SESSION` |
| `frequency` | `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`, `ONE_TIME` |
| `status` (program) | `DRAFT`, `PUBLISHED`, `ARCHIVED`, `CANCELLED` |
| `accessType` | `PUBLIC`, `INTERNAL`, `RESTRICTED` |
| `tdsApplicability` | `APPLICABLE`, `NOT_APPLICABLE`, `CONDITIONAL` |
| `accessScope` | `VIEW_ONLY`, `VIEW_AND_REGISTER` |

---

## Standard Response Envelope

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**Error envelope:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PROGRAM_NOT_FOUND",
    "message": "The requested program could not be found."
  }
}
```

---
