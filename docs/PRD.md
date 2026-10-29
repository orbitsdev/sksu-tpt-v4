# SKSU TPT v4: PRD, flows and decisions

Written 28 Oct 2026 for the team discussion. Confidence tags: **[Certain]** = checked in code, data or the server; **[Likely]** = strong inference; **[Guessing]** = needs confirmation from the admission office.

The mockups that go with this document are in `mockups/`. Open `mockups/index.html`, then `ADMIN-JOURNEY-MOCKUP.html` and `APPLICANT-JOURNEY-MOCKUP.html`.

---

## 1. Decisions so far

| # | Decision | Why |
|---|---|---|
| 1 | Keep every function the old TPT performs; how each one works is ours to improve. | The user's mandate. |
| 2 | **A schedule is a day**: campus + date. The applicant picks campus and date, and the system assigns room and seat. Report and start times (for example 7:30 / 8:00 AM) are a guide printed on the permit, not a bookable slot. | It works like the Civil Service exam. It's simpler and matches how SKSU runs test days [Likely]. |
| 3 | Two batches (1st batch 8:00 AM, 2nd batch 1:00 PM) stay as a switch, **off by default**, for a day that overflows. | tptv3 hard-coded times, which split seats in half (`slots / 2`). |
| 4 | **School years and schedules are data, never code.** A school year has one or more exam schedules, each marked Freshmen or Transferees, each with its own registration, exam day(s), seats, scores and release. | tptv3 has year-specific routes, templates and database names. |
| 5 | Two payment paths: the **cashier records** the payment at the counter (approved at once), or the applicant **uploads a receipt** and a reviewer checks it. | From the earlier tpt-recreate-v2 PRD; it removes most of the review queue. |
| 6 | Notifications are a core module: in-app, email and SMS per event. | The user said notifying students is important. |
| 7 | Stack: Laravel 12, Inertia, Vue 3, Tailwind 4, Nuxt UI or shadcn-vue, Pest, MySQL 8, Redis, queue worker. | The same stack as the team's euphoria v2 and the earlier tpt-recreate-v2 attempt. |
| 8 | Look: SKSU deep green, mint and gold, the official seal, light mode. Applicant screens are a native-style mobile app; admin follows euphoria v2 admin patterns. | User feedback in this session. |

---

## 2. Core modules

| Module | What it covers | Mockups |
|---|---|---|
| School years and schedules | School year, one or more schedules (Freshmen or Transferees), registration windows, exam fee, copy from last school year (5-step form with a step rail) | `admin/schedules`, `admin/setup-1…5` |
| Campuses and programs | 7 campuses, programs per campus, offered per school year, board flag, **cut-off score** | `admin/campuses` |
| Rooms | Buildings and rooms per campus with exam seats; reused every school year; added one by one | `admin/rooms` |
| Schedule days | Campus + date + rooms → seats; guide times; optional two batches | `admin/exam-slots` |
| Applicants and applications | Google sign-in; profile, school, 3 program choices (2 for transferees); one status per application (see the status list in section 7) | `applicant/*`, `admin/applications`, `admin/applicant` |
| Uploads | Only what is used: 2×2 ID photo (for the permit) and the payment receipt (online payment only); transferees add their grades for the chairperson. Compressed on the phone; reviewer can ask for a new one | `applicant/apply-*`, `admin/applicant#photo` |
| Payments | Cashier records the OR number (instant), or upload and review; duplicate-reference guard | `admin/cashier`, `admin/payments` |
| Permits | Examinee number from the school-year counter; wallet-style permit and PDF with QR; public verify page | `applicant/permit`, `docs/permit-pdf`, `public/verify` |
| Exam day | Optional, off by default: offline QR check-in on the proctor's phone, information only. Absent is decided by the score import | `proctor/*`, `admin/checkin` |
| Results import | Upload the Testing Center Excel as it is → match columns → checks → preview changes → approve → publish; every file kept unchanged | `admin/scores`, `admin/results` |
| Results and qualification | Standard score, stanine, qualified programs by cut-off; student chooses a program | `applicant/result`, `docs/result-pdf` |
| Notifications | Event → in-app, email, SMS; templates, blasts, send log with resend; student preferences | `applicant/notifications`, `admin/messages`, `docs/sms` |
| Reports and downloads | Funnel, demand, score histogram, every old report; background exports | `admin/reports`, `admin/exports` |
| Staff, roles, audit | Invite-only staff, four roles (Admin, Cashier, Proctor, Program chair), permission matrix; activity log (read-only) | `admin/staff`, `admin/audit` |

---

## 3. Old process → new process

| Old step (tptv3) | What it does | What's wrong | v4 |
|---|---|---|---|
| Google sign-in | Creates the user | Role overwritten on every login; `admin@gmail.com` becomes admin; 4,928 OAuth 400 errors [Certain] | Roles in the DB by invite; Google sign-in only; staff sign-in separate |
| Step middleware (`step_two` … `step_five`) | Gates pages | Progress stored three ways (`users.step`, `applications.status`, row existence) and drifts [Certain] | One status enum with allowed transitions and an event history |
| Personal / school / program forms | Collect data | Strings for dates and age; no autosave; 20 "Data too long" errors [Certain] | Typed fields, autosave, hints and limits shown before saving |
| Photo upload | 2×2 photo | Up to 100 MB, never resized; 26 GB on disk [Certain] | Shrunk on the phone to about 250 KB; face check; reviewer can ask for a new one |
| Payment proof upload | Reference + receipt | Every payment needs a manual review; `store() on null` errors [Certain] | Cashier records at the counter (instant); upload path kept as fallback with duplicate-reference guard |
| Approve payment | Issues examinee number | `max(examinee_number)+1` on a string; two admins collide [Certain] | Per-season counter, locked in the approval transaction |
| Select test center | Picks slot, computes room and seat | Count-then-insert with no lock; `slots / 2` hard-codes AM/PM; 357 "slots on null" errors [Certain] | Pick campus + date; seat assigned under a row lock with a unique key; auto-assign for stragglers |
| Permit PDF | Headless Chrome per request | 19,209 Browsershot errors [Certain] | Built once on the queue, cached; wallet-style permit works offline |
| Exam day | Paper lists | No attendance recorded; 635 registered with no result and no reason [Certain] | The score import marks anyone with a slot but no score as Absent; check-in is optional |
| Results upload (Excel) | Imports scores computed by the Testing Center | Columns read by position; header row saved as a result; no checks; re-upload duplicates; file not kept [Certain] | Same idea, import not compute: Excel as it is, column matching, checks, preview of changes, approval, original file kept |
| Survey + select courses before result | Gate to see the result | Forces a survey; second course pick duplicates choices [Certain] | Survey optional; choice of program happens after results, limited to programs they qualify for |
| Reports (6 Livewire pages) | Lists and exports | Slow full-table queries, missing indexes [Certain] | Same reports plus funnel, attendance and survey; exports queued |
| Emails | Approve/reject via Gmail SMTP | Gmail daily limit, no SMS, no log [Certain] | Mail API + SMS provider; templates; send log with resend |
| Test and debug routes | Left in production | Serious security risk (details kept offline) [Certain] | **Dropped.** Never ship test routes; route list checked in CI |
| One-off PHP scripts in `docs/` | Manual DB fixes | Each school year needs hand fixes [Certain] | **Dropped.** Admin screens cover every fix, with a reason and audit |

---

## 4. Known gaps in tptv3, per module

- **Applicants:** no duplicate detection; no email fallback for students without Google; nothing for students who signed up with the wrong account.
- **Applications:** no "returned for revision"; you can't edit after submitting without a DB edit.
- **Uploads:** no size limit worth the name, no compression, no review or replace flow, files kept forever.
- **Payments:** no cashier path, no duplicate-reference check, no record of who approved.
- **Schedules and rooms:** rooms are a count, not real rooms; no capacity per room; no way to move someone or close a day cleanly; the seat race.
- **Campuses and programs:** campus and program glued in one string in results; no cut-offs in the system.
- **Results import:** columns read by position, header row imported as data, no check against registrations or attendance, re-upload duplicates rows, no record of the file (see RESULTS-IMPORT.md).
- **Results:** labels and stanines stored, not computed; no qualification logic; release is a manual toggle.
- **Notifications:** two emails only; nothing for schedule change, reminders or results.
- **Admin:** admin by email list; no activity log; no roles beyond admin/applicant.
- **Operations:** no backups, 535 MB log, Ubuntu 20.04, root SSH with a password, test routes live.

---

## 5. Scenarios and how v4 handles them

| Scenario | v4 behaviour |
|---|---|
| Applicant wants another date | One self-service change until the schedule's change deadline; after that, staff move them with a reason. |
| No-show | The score import marks anyone with an exam slot but no score as Absent (check-in, if on, is only a note). A setting lets them move to a later schedule without paying again. |
| Room capacity changes | Edit the room's seats; if people already sit above the new capacity, the screen lists them and offers to move them before saving. |
| Exam date moved (typhoon, holiday) | Move the schedule day: everyone on it keeps their room and seat, gets a new permit, and receives SMS + email at once. |
| Walk-in on exam day | Proctor can't add people. The campus admin can seat a walk-in only if they're approved and unscheduled, into an empty seat; it's logged. |
| Duplicate registration | Detector flags same name + birth date or same mobile. A flag only: staff cancel the newer application if it is the same person. No merge. |
| Late payment | Registration close blocks new payments; an admin can extend one applicant with a reason, or roll them to the next schedule. |
| A date overflows | Add rooms or another day; as a last resort, switch on two batches for that day. |
| Wrong room at the door | The scan says which room to send them to. |
| Lost permit | The permit lives in the app and works offline; the proctor can also search by name. |
| Score correction | Upload a fixed Excel file (the screen shows what changes), or correct one score with a reason; the old value is kept. |
| Two cashiers approve the same receipt | The second one is told and moved to the next item. |

**The Civil Service exam as the model** (from general knowledge, not fetched, so confirm the details): applicants file, choose a testing venue, and later get a notice with their school, room and seat. The exam is one fixed date with a reporting time printed on the admission slip. v4 does the same: you choose campus and date, room and seat are assigned, and times are a guide.

---

## 6. Notifications

| Event | In app | Email | SMS |
|---|---|---|---|
| Account created | ✓ | ✓ | |
| Application submitted | ✓ | ✓ | |
| Upload needs redoing (photo, ID, receipt) | ✓ | ✓ | ✓ |
| Receipt received | ✓ | ✓ | |
| Payment approved (examinee no.) | ✓ | ✓ | ✓ |
| Payment rejected (reason) | ✓ | ✓ | ✓ |
| Seat booked, permit ready | ✓ | ✓ | ✓ |
| Schedule changed | ✓ | ✓ | ✓ |
| Exam reminder (day before, 5 PM) | ✓ | ✓ | ✓ |
| Marked absent | ✓ | ✓ | |
| Results released | ✓ | ✓ | ✓ |

Every send is logged with delivery status and can be resent.

---

## 7. Data model

```mermaid
erDiagram
    SEASON ||--o{ ROUND : has
    SEASON ||--o{ PROGRAM_OFFERING : offers
    CAMPUS ||--o{ PROGRAM : has
    CAMPUS ||--o{ ROOM : has
    PROGRAM ||--o{ PROGRAM_OFFERING : "offered as"
    ROUND ||--o{ SCHEDULE_DAY : has
    SCHEDULE_DAY }o--|| CAMPUS : at
    SCHEDULE_DAY ||--o{ SCHEDULE_DAY_ROOM : uses
    ROOM ||--o{ SCHEDULE_DAY_ROOM : "used in"
    USER ||--o{ APPLICATION : files
    APPLICATION }o--|| SEASON : for
    APPLICATION }o--|| ROUND : takes
    APPLICATION ||--o{ PROGRAM_CHOICE : ranks
    APPLICATION ||--o{ UPLOAD : has
    APPLICATION ||--o{ PAYMENT : has
    APPLICATION ||--o| SEAT_ASSIGNMENT : gets
    SEAT_ASSIGNMENT }o--|| SCHEDULE_DAY_ROOM : in
    APPLICATION ||--o| CHECK_IN : "marked at"
    APPLICATION ||--o{ SCORE : has
    ROUND ||--o{ SCORE_IMPORT : has
    SCORE_IMPORT ||--o{ SCORE : loads
    APPLICATION ||--o{ APPLICATION_EVENT : history
    APPLICATION ||--o{ NOTIFICATION : receives
    USER ||--o{ AUDIT_LOG : acts
```

Key rules:

- `applications`: one per (user, schedule), and only one in progress at a time. The account and profile are reused, so a new application is prefilled from the last one. Rejected, absent or past-season applicants can apply again in a later schedule or school year [needs office confirmation: retakes after a result]. `status` enum; `examinee_no` INT, unique per school year, from `seasons.next_examinee_no` locked in the approval transaction.
- `seat_assignments`: unique (schedule_day_room, seat) and unique (application). Assigned under `SELECT … FOR UPDATE`.
- `schedule_days`: campus, date, `report_at` and `starts_at` (guide), `sitting` nullable (only when the two-batches switch is on).
- `scores`: imported exactly as the Testing Center gives them (standard score and stanine per subject and overall). v4 never computes scores. `score_imports` keeps every uploaded file, who and when; a re-import shows what changes before approval.
- `program_offerings`: school year, program, `cutoff` INT, `is_board` bool.
- `payments`: `method` (cashier | upload), `or_no` or `reference_no` unique per school year, `recorded_by`.
- Every FK is indexed; dates are DATE or DATETIME; no year in any table name, route or file name.

---

### Application statuses

One status per application. These exact names are used on every screen, in filters and in emails.

| Status | Means | Next |
|---|---|---|
| Draft | Started, not submitted | Submitted |
| Submitted | The moment of submitting (not a resting state) | Waiting for chairperson (transferees) or Waiting for payment (freshmen) |
| Waiting for chairperson | Transferee; the program chairperson checks grades and slots | Waiting for payment, or Declined |
| Declined | The chairperson said no, with a reason (the 2nd choice gets a turn) | Waiting for chairperson (2nd choice), or Cancelled |
| Waiting for payment | Pay online (upload receipt) or at the cashier | In review (online), or Approved (cashier) |
| In review | The admin checks the whole submission and receipt | Approved, or Sent back |
| Sent back | Remarks say what to fix; the student fixes it and sends again | In review |
| Approved | Paid; examinee number issued | Exam slot picked |
| Exam slot picked | Has a campus and date (or batch), room and seat; permit ready | Scored, or Absent |
| Scored | Score imported from the Testing Center file | Program chosen |
| Absent | Had a slot but no score in the file | Draft in a later schedule (if allowed) |
| Program chosen | Picked one program they qualify for | — |
| Cancelled | Cancelled by the student or an admin, with a reason | — |

## 8. Flows

### Applicant

```mermaid
flowchart LR
    A[Landing] --> B[Sign in with Google]
    B --> C[Apply: about you, school + documents, 3 programs]
    C --> D{Review and submit}
    D --> E{Pay}
    E -->|At the cashier| F[Recorded: approved at once]
    E -->|Upload receipt| G[Review] -->|Approved| F
    G -->|Rejected, reason| E
    F --> H[Pick campus and date; room and seat assigned]
    H --> I[Permit in app + PDF]
    I --> J[Exam day]
    J -->|Present| K[Scored] --> L[Result: qualified programs] --> M[Choose program]
    J -->|Absent| N[Move to next round, if allowed]
```

### Application status

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Waiting_for_chairperson: submitted (transferee)
    Draft --> Waiting_for_payment: submitted (freshman)
    Waiting_for_chairperson --> Waiting_for_payment: chair approves
    Waiting_for_chairperson --> Declined
    Declined --> Waiting_for_chairperson: 2nd choice
    Waiting_for_payment --> In_review: receipt uploaded
    Waiting_for_payment --> Approved: cashier recorded
    In_review --> Approved
    In_review --> Sent_back
    Sent_back --> In_review: fixed and sent again
    Approved --> Exam_slot_picked: picked or assigned
    Exam_slot_picked --> Scored: score imported
    Exam_slot_picked --> Absent: no score in the file
    Scored --> Program_chosen
    Program_chosen --> [*]
```

### Admin school year

```mermaid
flowchart LR
    S1[New season wizard: basics, rounds, campuses, rooms, days] --> S2[Open registration]
    S2 --> S3[Payments: cashier + review queue]
    S3 --> S4[Seats: picked or auto-assigned]
    S4 --> S5[Exam day; check-in optional]
    S5 --> S6[Import Testing Center Excel, check, approve; no score = absent]
    S6 --> S7[Schedule release, notify]
    S7 --> S8[Reports, exports, next round]
```

### Architecture

```mermaid
flowchart TB
    subgraph Clients
      P[Applicant phone app]
      A[Admin laptop]
      R[Proctor phone, offline]
    end
    P & A & R --> N[nginx + PHP-FPM: Laravel 12 + Inertia]
    N --> DB[(MySQL 8)]
    N --> RD[(Redis: cache, sessions, queue)]
    N --> Q[Queue worker: PDFs, image resize, mail, SMS, exports, backups]
    Q --> FS[(File storage)]
    Q --> MAIL[Mail API]
    Q --> SMS[SMS provider]
    Q --> BK[(Off-site backups)]
```

---

## 9. Earlier attempts: what to reuse and why they stalled

| Folder | State | Reuse |
|---|---|---|
| `tpt-recreate` (Feb 2026, 6 commits) | Docs-first: stakeholders, modules, MVP lists, wireframes in Markdown; models and API started | Planning docs, enums, program qualification logic |
| `tpt-recreate-v2` (Feb–Mar 2026, 35 commits) | Laravel 12 + Inertia + Vue; models for Schedule, Room, CampusSlot, ExamSlotAssignment, Payment, Result, ResultScore, SmsLog, Ticket, Faq | Its PRD decisions: date-based schedule with auto room/seat, two payment paths, cut-offs (board 530, nursing/accountancy 600, med tech 650), documents (valid ID, Form 138), roles (super admin, campus admin, cashier) |

[Guessing] Why they stalled: scope grew before the core flow was finished (tickets, FAQs, real-time Reverb, a long SMS guide), there were no clickable mockups to agree on, and the admission school year arrived before a usable end-to-end path existed. To avoid that this time:

1. Agree on these mockups first.
2. Build one thin path end to end (apply → pay → seat → permit) before anything else.
3. Leave tickets, FAQs and real-time features for after the first school year.

---

## 10. Plan

| Phase | Weeks | Done when |
|---|---|---|
| 0 Lock down tptv3 | now | Test routes closed, repo private, backups running |
| 1 Foundation | 1–2 | Schema above, seed from `tpt_october_2025`, CI with Pest |
| 2 Apply and pay | 3–5 | Applicant can apply; cashier and upload paths work |
| 3 Schedule and permit | 6–7 | Days, rooms, locked seats, permit PDF and verify page |
| 4 Exam day and results | 8–9 | Score import (absent from import), release, qualification; optional check-in |
| 5 Notifications, reports, cut-over | 10 | Templates, SMS, reports; load test; switch DNS |

## 11. Open questions for the admission office

1. How many schedules a year, and which are for transferees? (The system allows any number.)
2. Confirm date-only scheduling with guide times. What are the real report and start times?
3. Exam fee, GCash and bank accounts, and whether cashiers will use the system.
4. Official stanine labels and the cut-off list per program for 2027.
5. Which SMS provider and budget?
6. Can absent examinees move to the next schedule for free?

---

## 12. Admin UI rules

1. **One page template**: title, one-line description and the page's primary action top-right; then the filter bar; then the content. Nothing else above the fold.
2. **One focal point per page**: the main task is the biggest thing on the page (the dashboard's "Payments to review"). Everything else is smaller and greyer.
3. **One card**: 12 px radius, 1 px border, white, no shadow, 20 px padding. No mixed card shapes on a page.
4. **One table**: uppercase grey headers, 12 px vertical padding, row hover. Row actions are quiet until you hover (View in green text, ··· menu).
5. **Buttons**: sm 32 px (tables, toolbars), md 40 px (default), lg 48 px (main task); 52 px pills on mobile. One primary per view; secondary is white with a border, ghost is text only, and danger (red) is only for destructive actions. Disabled is 45% opacity. Loading shows a spinner in place of the label.
6. **Labels and positions**: labels sit above fields in plain words ("Official receipt no.", not `or_no`); optional fields say "(optional)". Buttons say what they do ("Record payment", "Approve and issue number"). In forms and dialogs, Cancel sits left of the primary action at the bottom-right; on mobile, actions are full width at the bottom.
7. **Spacing**: 8 px grid (8/16/24/32).
8. **Colour only where it means something**: green for the primary action and the selected item, status colours only on status badges, red only for errors and destructive actions. The sidebar and tables are neutral.
9. **Feedback**: skeletons shaped like the page while loading; an empty state has an icon, one line of reason and one action; toasts say what happened.

## 13. Usability walk-through (28 Oct)

| As… | Friction found | Fixed in the mockups |
|---|---|---|
| A first-time applicant on a phone | Long scrolling form; unclear how to pay; birth date format; mockups looked like a shrunk website | Native app layout (status bar, big titles, floating tab bar, bottom sheets, sticky main button); GCash steps on the payment screen; date hint; autosave toast; wallet-style permit that works offline |
| A first-time applicant | Didn't know when to come or what to bring | Permit and seat screen show "Report by 7:30 AM · exam starts 8:00 AM" and what to bring; reminder text the day before |
| A registrar on a busy day | Too many equal boxes; no single thing to do first; dense rows with boxed buttons | One focal KPI with "Review now"; light sidebar; quiet row actions; global search with `/`; saved views; bulk actions |
| A cashier | Every payment needed a photo and a second person | "Record a payment" at the counter: find the applicant, type the OR number, done |
| A proctor at the door | Paper lists; no signal in some rooms | Optional offline check-in with big Here and Not here buttons (a note only); wrong-room and duplicate warnings |

**Still weak**:

- Tables are wide on small laptops.
- Admin on a phone is usable but not designed screen by screen.
- The filter sheet on mobile is only a placeholder.
- Real content (program names, fees, the cut-off list) still needs the admission office.

## 14. Cashier role

- **Cashier** is its own role with a simple console (`cashier/console.html`). It can't open other admin pages; admins can open the console too.
- **What TPT records** is only that the applicant paid: OR number, amount, payment method, who recorded it, and when. Cash handling and remittance stay in the university's own accounting system, as today.
- **Counter flow:** search (name, application or examinee no.; no QR scanning at the counter) → the fee is fixed → type the OR number (must be unused) → Enter → paid, print an OR copy if needed → next person.
- **Guards:** already paid, OR already used, not found, schedule not open yet, fee waived.
- **Today:** the cashier's list for the day with reprint and an Excel export to match against the OR booklet. The cashier also sees a small info strip (today's count, applicants waiting, seats left per exam day) and an **Info** tab to answer questions at the counter: key dates, fee and requirements, exam days and seats left, rooms (seats, taken, left) and the programs open this school year. All of it is read-only.
- **Void (admin only):** a reason is required. The application goes back to "waiting for payment", and any seat is released if the exam hasn't happened. The applicant gets the reason in the app, by email and by text, and can pay again as normal. The voided payment stays on the lists and in the activity log.
- **Data:** `payments.method = cashier`, `or_no` unique per school year, `recorded_by`, `counter`; voids recorded in the activity log.

## 15. Seats on the dashboard

The dashboard shows the round's seats (total, taken, left, open exam days) and each exam day and campus with a meter. "Nearly full" appears under 60 seats and "Full" at 0. Applicants see seats left per day on the schedule picker.

## 16. Transferee test (2nd semester)

Today the Guidance and Testing Center runs a separate walk-in test for transferees (for example Dec 13, 2026, ₱275, 1st batch 8:00 AM and 2nd batch 1:00 PM, Testing Room, SKSU ACCESS Campus). The paper form asks for personal details, current school, current course and two preferred programs, and the program chairperson or college dean signs it after checking grades and slots.

v4 handles it in the same system:

| Step | Freshmen schedule | Transferee schedule |
|---|---|---|
| Schedule type | Freshmen | Transferees (set when the schedule is created) |
| Apply | Online: 3 program choices | Online or encoded by staff: 2 choices, plus current school and current course, and the transcript or certificate of grades |
| Approval before paying | — | The program chairperson or dean of the 1st-choice program approves (slot available, grades OK) or declines with a reason |
| Pay | Online receipt or cashier | Cashier only |
| Exam | Exam slots by campus and date | One venue, 1st or 2nd batch |
| Examinee no., permit, results, choosing a program | Same | Same |

New role: **Program chair**. Sees only the transferee applicants for their own program, with the uploaded grades, and approves or declines. Every decision goes in the activity log.

If the 1st-choice chairperson declines, the 2nd-choice chairperson gets a turn (the mockups show this). **Confirm with the office.**
