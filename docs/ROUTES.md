# Pages, routes and permissions

Every screen's address, who may open it, and what it sends. Built for **Option A** (one Laravel system: student app under `/app`, staff under `/admin` and `/cashier`). Option A is the recommended choice; it is assumed here until the owner confirms it.

## In short (for the office)

- **Four doors, one system.** The public website, the **student app** (`/app`, installable on phones), the **admin** (`/admin`) and the **cashier counter** (`/cashier`). Program chairs and deans use a small part of the admin.
- **Everyone sees only what their job needs.** A cashier sees name, code and payment, not grades or addresses. A program chair sees only their own program's transferees. A student sees only their own application.
- **Risky actions are protected.** Recording a payment can't happen twice by accident. Voiding, hiding results or publishing without PDFs need the right role, a reason, and they are logged.
- **Busy days stay fast.** Each screen sends only its own small data; lists come 25 at a time; slow parts load after the page shows.

## 1. Areas and who uses them

| Area | Address | Who | Signs in with |
|---|---|---|---|
| Public website | `/` | Anyone | (no sign-in) |
| Student app (PWA) | `/app` | Applicants | Google |
| Admin | `/admin` | Admin, super admin, program chair, college dean, proctor | Google (staff invited only) |
| Cashier counter | `/cashier` | Cashiers | Google (invited only) |
| Proctor check-in | `/admin/checkin` | Proctors | Only when a schedule has check-in turned on |

Staff accounts exist only by invite. A Google account that wasn't invited lands in the student app, never in `/admin` or `/cashier`.

## 2. Roles and permissions

Roles and permissions use **spatie/laravel-permission**. A permission is one action. A role is a set of permissions. Scope (campus, program, college) narrows what a role can see.

### Roles

| Role | Who | Scope |
|---|---|---|
| **Admin** | Guidance and Testing Center staff | Everything except the super admin actions |
| Admin + **Super admin** switch | One or two senior staff | Adds system, staff, maintenance and emergency actions |
| **Cashier** | Cashier at a counter | Their counter and campus. Optional switch: **can create walk-in applications** (off by default) |
| **Proctor** | Room proctor | Their exam slot and room, only when check-in is on |
| **Program chair** | One program | Transferee applicants of that program only |
| **College dean** | A college | Transferee applicants of the programs in that college |
| **Student** | Applicant | Their own application only |

### Permissions

| Permission | Admin | Super admin | Cashier | Proctor | Chair / Dean |
|---|---|---|---|---|---|
| `dashboard.view` | ✓ | ✓ | | | |
| `applications.view` | ✓ | ✓ | name, code, payment only | own room list | own program / college transferees |
| `applications.create_walkin` | ✓ | ✓ | only with the switch | | |
| `applications.edit` (with a reason) | ✓ | ✓ | | | |
| `applications.send_back` | ✓ | ✓ | | | |
| `applications.cancel` | ✓ | ✓ | | | |
| `applications.change_signin_email` | ✓ | ✓ | | | |
| `transferees.decide` (approve / decline) | ✓ | ✓ | | | ✓ (scoped) |
| `payments.record` | | | ✓ | | |
| `payments.record_late` (paper OR after a brownout) | | | ✓ | | |
| `payments.void` / `payments.correct_or` | ✓ | ✓ | | | |
| `payments.extend` (pay-by for one applicant) | ✓ | ✓ | | | |
| `cashier.manage` (counters, booklets, shifts) | ✓ | ✓ | own shift only | | |
| `online_payments.review` (when the switch is on) | ✓ | ✓ | | | |
| `schedules.manage` (school years, schedules, publish, postpone) | ✓ | ✓ | | | |
| `exam_slots.manage` (add, rooms, move or cancel) | ✓ | ✓ | | | |
| `campuses.manage` (campuses, programs, rooms) | ✓ | ✓ | | | |
| `checkin.record` | | | | ✓ (scoped) | |
| `scores.import` | ✓ | ✓ | | | |
| `scores.approve` / `scores.correct` | ✓ | ✓ | | | |
| `results.prepare_pdfs` | ✓ | ✓ | | | |
| `results.publish` / `results.hide` / `results.hide_one` | ✓ | ✓ | | | |
| `results.publish_without_pdfs` (emergency) | | ✓ | | | |
| `survey.manage` / `survey.view_results` | ✓ | ✓ | | | |
| `support.reply` / `support.pause_student` | ✓ | ✓ | | | |
| `announcements.send` | ✓ | ✓ | | | |
| `reports.view` / `exports.create` | ✓ | ✓ | own shift report | | |
| `content.manage` (student app editor, landing) | ✓ | ✓ | | | |
| `settings.manage` (email sender, limits) | | ✓ | | | |
| `staff.manage` | | ✓ | | | |
| `system.maintenance` (pause, schedule maintenance) | | ✓ | | | |
| `activity.view` | ✓ | ✓ | | | |

**Student rules** are not permissions: a student can only read and change their **own** application, and only while it isn't locked (locked after approval, except through Support → "Request a change").

### Scope rules (checked on every request, not only hidden in the screen)

- **Cashier:** the applicant search returns name, code, program, campus, photo and payment state only. No birth date, address, grades or scores.
- **Program chair / dean:** queries are filtered to `application_choices` of their program (chair) or college (dean), for transferee schedules only.
- **Proctor:** only the applicants seated in their exam slot and room, only on exam day, only if check-in is on.
- **Student:** every query is filtered by the signed-in user. Codes in URLs are checked against the owner.

## 3. Routes

How to read the tables:
- **Sends:** the data the page receives. *Small* = only what the screen shows. *Deferred* = loads right after the page appears (slow parts like charts). *Paged* = 25 at a time.
- **Limit:** rate limit (see section 5).
- Pages are `GET`. Actions are `POST` / `PATCH` / `DELETE` and return to the page with a message.

### Public

| Method | URL | Page / action | Who | Sends | Limit |
|---|---|---|---|---|---|
| GET | `/` | Landing (schedules, fee, how it works, install guide) | anyone | small, cached | |
| GET | `/sign-in` | Sign in with Google (consent tick) | anyone | small | |
| GET | `/auth/google/redirect`, `/auth/google/callback` | Google sign-in | anyone | | sign-in |
| GET | `/verify/{token}` | Permit or result check from a QR | anyone | name, examinee no., valid/not valid, photo for permits; **no scores** | verify |
| GET | `/privacy` | Privacy notice and terms | anyone | static | |
| GET | `/maintenance` | Maintenance screen (when paused) | anyone | small | |

### Student app (`/app`)

| Method | URL | Page / action | Sends | Limit |
|---|---|---|---|---|
| GET | `/app` | Home (status, next step, announcement) | small, cached per student | |
| GET | `/app/apply/{step}` | About you · School · Programs · Review | that step's fields; school and program pickers search on demand | |
| PATCH | `/app/apply/{step}` | Save a step (autosave) | | apply |
| POST | `/app/apply/photo` | Upload the 2×2 photo (already shrunk on the phone) | | apply |
| POST | `/app/apply/submit` | Submit (consent required) | | apply |
| GET | `/app/pay` | Pay at the cashier (code, offices, pay-by) | small | |
| GET / POST | `/app/pay/online` | Upload receipt + reference *(only when online payment is on)* | | apply |
| GET | `/app/exam-slot` | Pick an exam slot | slots of the student's schedule with seats left (cached, short) | |
| POST | `/app/exam-slot` | Book (locks the seat) | | apply |
| GET | `/app/permit` | Permit (works offline once opened) | small | |
| GET | `/app/result` | Result summary | small, cached | |
| GET | `/app/result/pdf` | Full result PDF (ready file) | signed, short-lived link | pdf |
| POST | `/app/result/share-link` | Make a proof link (no scores) | | pdf |
| GET / POST | `/app/survey` | The survey (once) | the school year's questions | apply |
| POST | `/app/program` | Choose a program (from those qualified) | | apply |
| GET | `/app/support` | My requests | small | |
| POST | `/app/support` | New request (one open, 5 per school year) | | support-new |
| GET | `/app/support/{ticket}` | A request's thread | small | |
| POST | `/app/support/{ticket}/reply` | Reply | | support-reply |
| POST | `/app/support/{ticket}/solved` | Mark as solved | | |
| GET | `/app/notifications` | Notifications | paged | |
| GET | `/app/account` | Account (details read-only after approval) | small | |
| POST | `/app/account/request-change` | Opens a "Change my details" support request | | support-new |
| GET | `/app/transferee/...` | Transferee school and programs steps, waiting for chairperson | same pattern as apply | apply |

### Admin (`/admin`)

| Method | URL | Page / action | Who | Sends |
|---|---|---|---|---|
| GET | `/admin` | Dashboard | `dashboard.view` | numbers small; charts **deferred** |
| GET | `/admin/setup` | Setup checklist | `schedules.manage` | small |
| GET | `/admin/applications` | Applications (status tabs, search, filters) | `applications.view` | **paged**; tab counts cached |
| GET | `/admin/applications/{code}` | Applicant record | `applications.view` | small; history **deferred** |
| PATCH | `/admin/applications/{code}` | Edit details (reason required) | `applications.edit` | |
| POST | `/admin/applications/{code}/send-back` · `/cancel` · `/move-slot` · `/seat-now` · `/extend-payment` · `/change-email` | Record actions | matching permission | |
| POST | `/admin/applications/walk-in` | New application for someone | `applications.create_walkin` | |
| GET | `/admin/payments` | Online payment review *(only when the switch is on)* | `online_payments.review` | paged |
| POST | `/admin/payments/{id}/void` · `/correct-or` | Void or correct an OR (reason) | `payments.void` / `payments.correct_or` | |
| GET | `/admin/cashier` | Counters · Shifts · Recorded late · booklets | `cashier.manage` | paged |
| POST | `/admin/cashier/booklets` | Add an OR booklet (range, counter) | `cashier.manage` | |
| GET | `/admin/support` · `/admin/support/{ticket}` | Support list and thread | `support.reply` | paged · small |
| POST | `/admin/support/{ticket}/reply` · `/assign` · `/close` · `/pause-student` | Ticket actions | `support.reply` / `support.pause_student` | |
| GET / POST | `/admin/announcements` | Send an announcement (in app + email, waves) | `announcements.send` | |
| GET | `/admin/schedules` | Exam schedules (this year · all years) | `schedules.manage` | small |
| POST | `/admin/school-years` · `/admin/schedules` | New school year (step rail) · add schedule | `schedules.manage` | |
| PATCH | `/admin/schedules/{id}` · POST `/publish` · `/unpublish` · `/postpone` | Edit, publish, unpublish, postpone | `schedules.manage` | |
| GET | `/admin/exam-slots` | Exam slots (picker per schedule) | `exam_slots.manage` | small |
| POST | `/admin/exam-slots` · `/{id}/rooms` · `/{id}/move` · `/{id}/close` · `/assign-seats` | Add, add rooms, move or cancel, close, assign seats | `exam_slots.manage` | |
| GET | `/admin/checkin` | Live check-in monitor (when on) | `checkin.record` or admin | small, polled |
| GET | `/admin/scores` | Import scores (step rail) | `scores.import` | small |
| POST | `/admin/scores/upload` · `/map` · `/approve` | Upload Excel, match columns, approve | `scores.import` / `scores.approve` | upload runs in the queue |
| GET | `/admin/results` | Results (schedule picker, tabs, PDF status) | `scores.approve` | **paged**; PDF progress polled |
| POST | `/admin/results/prepare` · `/prepare/{code}` | Prepare all PDFs · one student now | `results.prepare_pdfs` | queued |
| POST | `/admin/results/publish` · `/visibility` · `/{code}/hide` | Publish (or prepare-then-publish) · show/hide all · hide one | `results.publish` / `results.hide` / `results.hide_one` | |
| POST | `/admin/results/publish-without-pdfs` | Emergency publish (reason + PUBLISH) | `results.publish_without_pdfs` | |
| PATCH | `/admin/results/{code}/score` | Correct a score (reason) | `scores.correct` | |
| GET | `/admin/reports` · `/admin/reports/{report}` | Reports (office summary, home town, survey results…) | `reports.view` | **deferred** charts, paged tables |
| POST | `/admin/exports` · GET `/admin/downloads` | Start an export · Downloads list | `exports.create` | queued; files kept 7 days |
| GET / POST | `/admin/campuses` · `/admin/rooms` | Campuses, programs (cut-off, ESM/overall, offered), rooms | `campuses.manage` | small |
| GET / POST | `/admin/staff` | Staff (invite, role, scope, deactivate) · Roles tab | `staff.manage` | small |
| GET / POST | `/admin/survey` | Survey questions per school year | `survey.manage` | small |
| GET / POST | `/admin/student-app` | Student app editor with phone preview | `content.manage` | small |
| GET / POST | `/admin/email` | Official sender, templates, send log | `settings.manage` | send log paged |
| GET | `/admin/system` | System status | `system.maintenance` | health checks cached |
| POST | `/admin/system/pause` · `/resume` · `/maintenance-window` | Pause app / applications / payments, schedule maintenance | `system.maintenance` | |
| GET | `/admin/activity` | Activity logs | `activity.view` | paged |
| GET | `/admin/chair` | Program chair / dean: transferee applicants | `transferees.decide` | **paged**, scoped |
| POST | `/admin/chair/{code}/approve` · `/decline` · `/in-person` | Decide (reason on decline) | `transferees.decide` | |
| GET / POST | `/admin/account` | My account, guide switches | any staff | small |

### Cashier (`/cashier`)

| Method | URL | Page / action | Who | Sends | Limit |
|---|---|---|---|---|---|
| GET | `/cashier/shift/start` · POST | Start of shift (first OR, starting cash) | cashier | small | |
| GET | `/cashier` | Counter (search, waiting list, payment panel) | cashier | search results small; list **paged** | |
| POST | `/cashier/payments` | Record payment | `payments.record` | | cashier-record |
| POST | `/cashier/payments/late` | Record a paper payment (after a brownout) | `payments.record_late` | | cashier-record |
| POST | `/cashier/or/spoiled` | Mark OR numbers as spoiled (reason) | cashier | | |
| GET | `/cashier/paid` | Paid (today · this schedule), reprint slip, resend confirmation | cashier | paged | |
| GET | `/cashier/slip/{payment}` | Print slip | cashier | small | |
| GET | `/cashier/info` | Info for applicants | cashier | cached | |
| GET / POST | `/cashier/shift/end` | End of shift (count cash, difference note) | cashier | small | |

**About 120 routes** in all: roughly 6 public, 25 student, 75 admin and 12 cashier.

## 4. Key actions and their safety

| Action | Protection |
|---|---|
| **Record payment** | An **idempotency key** made when the payment panel opens: pressing Record twice, or a slow network retry, returns the first result ("Already recorded by you at 10:02"). One transaction with a row lock on the school year's examinee counter: checks the OR (unused, in this counter's booklet, right format), saves the payment, gives the next examinee number, approves. |
| **Record a paper payment** | Same as above, plus the real paid time and reason; flagged "recorded late" for admin review. |
| **Book an exam slot** | Row lock on the exam slot; seat count checked and updated in the same transaction ("just taken" if full). |
| **Approve scores** | One transaction for the whole file; refused if most rows aren't in this schedule; the file and approver are kept. |
| **Publish results** | If PDFs aren't all ready, it becomes "prepare, then publish". Emergency publish needs super admin + reason + typing PUBLISH. |
| **Void / correct OR, hide one result, edit details, cancel** | Reason required; written to the activity log; voided examinee numbers are retired, never reused. |
| **Postpone a schedule / move a slot** | Preview of who is affected first; one job updates everyone, rebuilds permits, sends notices in waves. |

**Validation (summary):** dates as real dates (birth date: at least 15 on exam day); mobile +63 and 10 digits; general average 60–100; OR no. 7 digits; scores 200–800, stanine 1–9 and matching; files: photo JPG/PNG ≤ 2 MB, Excel .xlsx/.csv ≤ 20 MB; support message 10–1,000 characters.

**Who can undo:** voids, hides, extensions and edits are undone by an admin through the opposite action (show again, correct again), each logged. Nothing is deleted once it has applicants or payments.

## 5. Rate limits

| Limit | Applies to | Allowed |
|---|---|---|
| sign-in | Google sign-in attempts | 10 a minute per address |
| apply | saving steps, photo, booking, survey, choosing | 30 a minute per student |
| pdf | result PDF downloads and share links | 10 a minute per student |
| verify | QR check page | 30 a minute per address |
| support-new | new support requests | 1 open at a time, 5 a school year |
| support-reply | replies | 1 a minute, 20 a day per ticket |
| cashier-record | record payment | 20 a minute per cashier (stops runaway double-submits) |
| everything else | any signed-in user | 120 a minute |

## 6. Security notes

- **Laravel 13's PreventRequestForgery** (the renamed CSRF protection) is on for every form, and it also checks where a request comes from.
- **Policies per model:** every route checks the signed-in user's permission **and** scope on the server; hiding a button is never the protection.
- **No guessable IDs in URLs:** applicants by code (APP-27-10422), tickets by a random token, PDFs and share links by **signed, short-lived URLs**.
- **Uploads:** checked type and size, stored outside the public folder, served through signed links.
- **Activity log** on every staff change (who, what, when, old and new value).
- **Sessions:** staff sessions expire after inactivity; students stay signed in on their own phone.

## 7. Typed routes (Wayfinder)

All links and form actions in the Vue screens come from **Laravel Wayfinder**, which turns the route list into typed functions. No hand-written URLs: rename a route and the code shows every place to fix.

## 8. To confirm

1. **Option A** (one system, `/app` + `/admin` + `/cashier`). Assumed here.
2. Who gets the **super admin** switch (recommended: one or two people).
3. Should **cashiers** ever see the applicant's birth date (to tell two people with the same name apart)? Assumed **no**: photo and code are enough.
