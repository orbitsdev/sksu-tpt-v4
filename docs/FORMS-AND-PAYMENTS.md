# Forms, records and the payment flow

Checked against tptv3's Livewire validation rules and migrations, and the live schema (`tpt_october_2025`). Tags: **[Certain]**, **[Likely]**, **[Guessing]**.

## 1. Forms in tptv3 and what v4 keeps

### Personal information (`PersonalInfo.php`)

| tptv3 field | Rule today | Problem | v4 |
|---|---|---|---|
| type_id (freshman/transferee) | required, in:1,2 | Fine | Keep: "I am a…" (Senior high graduate, Transferee, ALS passer) |
| first, middle, last name, extension | required / nullable | No length limit; extension free text | Keep; extension as a dropdown (Jr., Sr., III…) |
| present_address, permanent_address | required, free text | Can't report by province or town | Province → city → barangay dropdowns (PSGC), street optional; "Same as present" tick |
| phone_number | required, any text | Texts fail on bad numbers [Likely] | PH mobile format check (09xx xxx xxxx) |
| date_of_birth | required, **string column** | Wrong sorting, typos like 2018 | DATE, age check (15–60) |
| age | required, gte:16, **stored** | Goes stale | Computed, not stored |
| place_of_birth | required | Fine | Keep |
| tribe, religion | required | Required personal data with no stated use (Data Privacy Act) [Likely] | Optional; ask only if the office needs it for reports (IP and Muslim admission quotas [Guessing]) |
| nationality, citizenship | required / nullable | Two fields for one fact | One: citizenship |
| sex | required | Fine | Keep |
| photo | required, max:100000 (100 MB) | 26 GB of uploads [Certain] | Shrunk on the phone to about 250 KB, face check |

### School (`SchoolInfo.php`)

| tptv3 field | Problem | v4 |
|---|---|---|
| school_graduated / school_last_attended | Two fields switched by type | One "Last school attended" |
| year_graduated / year_last_attended | Strings | One year dropdown |
| previous_school_address | Free text | Town only (dropdown) |
| track_and_strand_taken | Free text | Dropdown (STEM, ABM, HUMSS, GAS, TVL, Arts and Design, Sports, ALS) |
| honor_or_awards_received | 20 "Data too long" errors [Certain] | Optional, 200-character limit shown |
| (missing) | — | GWA (number, 60–100); Form 138 upload; valid ID upload |

### Program choices (`ProgramInfo.php`, plus `select_courses` after the survey)

- **Today:** 3 choices before the exam, then picked again after the survey. That's two tables (`program_choices`, `selected_courses`) for one decision [Certain].
- **v4:** 3 ranked choices once. After results, the student picks one program they qualify for.

### Payment (`PaymentSection.php`)

- **Today:** a reference number (unique) and 1+ proof files (jpeg/png/pdf, no size limit). `paid_at = now()` is the upload time, not the payment time [Certain].
- **v4:** payment method, reference or OR number (unique per season and method), amount, date paid, one proof image (shrunk). Or no form at all when the cashier records it.

## 2. Records each step creates

| Step | Records | Application status |
|---|---|---|
| Sign in | users | — |
| Start | applications (season, round) | draft |
| Forms | applicant_profiles, schools, program_choices, uploads (photo, Form 138, ID) | draft |
| Submit | application_events | submitted |
| Pay (upload) | payments (method, ref, amount, paid_on), uploads (receipt) | payment_review |
| Pay (cashier) or approve | payments (recorded_by, or_no) + examinee_no from the season counter | approved |
| Reject payment | payments.status = rejected, reason; notification | payment_rejected |
| Pick a day | seat_assignments (day, room, seat) | scheduled |
| Exam day | check_ins | present / absent |
| Import | scores (raw) + norms | scored |
| Release | result snapshot; notification | released |
| Choose program | program_selection | released |

Every status change also writes an `application_events` row (who, when, why).

## 3. Payment flow that fits a Philippine state university

**How people actually pay** [Likely]:

- At a campus cashier (cash, official receipt).
- Landbank (LinkBiz online or an over-the-counter deposit).
- GCash or Maya to a university merchant account.
- Rarely, other banks.

Scholars and indigent applicants may be exempt.

**Recommended, simplest that works:**

1. **The cashier records it in the system** (preferred). The applicant shows the application code, the cashier types the OR number, and the payment is approved at once. Nothing to review.
2. **Online or bank payment with a proof upload.** The applicant enters method, reference no., date and amount, and adds a screenshot or slip. A reviewer checks it against the bank or GCash statement.
3. **Waiver.** An admin waives the fee with a reason (indigent, scholar). The applicant is approved, and it's counted separately in reports.

**Checks built in:**

- Reference and OR numbers are unique per season, so the same receipt can't be used twice.
- Amount must equal the fee; underpaid payments go to review with a flag.
- Two reviewers can't decide the same payment (row lock).
- **Reconciliation:** the reviewer can import the day's GCash or Landbank statement (CSV). Matching references are approved in bulk, and the rest stay for manual review. [Guessing] Whether SKSU can export these statements needs the accounting office.

**Rejection and resubmission:** the reason comes from a fixed list plus a note. The applicant gets a text and email and can resend from the same screen. Nothing else is lost.

**Refunds:** recorded by an admin with a reason (paid twice, round cancelled); the money goes back through the cashier. The status stays correct and the Payments report shows it.

**Trade-offs:**

| Option | Good | Bad |
|---|---|---|
| Cashier records it | Instant, no fake receipts | Needs cashiers to use the system; queues at campuses |
| Proof upload | Works from anywhere | Manual review; fake screenshots possible (reconciliation fixes this) |
| Payment gateway (PayMongo, Landbank ePayment) | Fully automatic | Fees, accreditation and procurement for a state university take time [Likely]. Phase 2 |

## 4. Gaps filled in this pass

- Payment method choice and a "show this code at the cashier" screen for applicants.
- Fee waiver and refund actions in the admin.
- A form field list with types and checks (above), ready to turn into migrations.
- Records per step, so every report can be answered from the data.

## 5. Still open

- Exact fee, merchant accounts, and whether cashiers will log in.
- Which personal fields the office really needs (tribe, religion) under the Data Privacy Act.
- Can the accounting office export GCash or Landbank statements for reconciliation?
- Whether a payment gateway is allowed this year.
