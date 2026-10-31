# Feature settings: start like the old TPT, switch the extras on when the office is ready

Nov 1, 2026. Owner's direction after testing:

- Applicants **must upload their receipt when they apply** (as in the old TPT); "I will pay at an SKSU cashier" is hidden.
- The **cashier counter** is **off by default**; receipts are still checked and approved by staff (the approver page).
- Students should **not change their exam slot or program choices** themselves (10,000 applicants; changes cause mix-ups).
- **Survey before the result** (students skip it once they have seen their result).
- **Old-curriculum high school graduates** (no senior high) must be able to apply.
- Deans/program chairs keep their **transferee approval** page, as staff did before.
- One organized **Settings** page (like Euphoria), so the office can turn features on later without a developer.

## Settings page (Admin → System → Settings)

| Group | Setting | Default (old TPT) | When on / changed |
|---|---|---|---|
| Applying | Transferee applications | Off | Transferee schedules, chair approval, grades upload |
| Applying | Old-curriculum high school graduates (before senior high) | **On** | "High school graduate (old curriculum)" in the school step; no strand needed |
| Paying | How students pay | **Upload the receipt when applying** | Or: pay at an SKSU cashier counter; or both (student picks) |
| Paying | Cashier counters | **Off** | Counter screen, shifts, OR booklets, cashier accounts; walk-ins at the counter |
| Paying | Walk-in applications (staff fill in the form) | **Off** | "New walk-in application" for staff |
| Exam slot | Students may change their exam slot | **Off** | They can move it until the schedule's "change slot until" day |
| Results | Survey before the result | **On** | The short survey comes first, then the scores |

Switches that already exist stay where they are (System → Pause: student app, new applications, payments).

## What "off" means

- **Cashier counters off:** the Cashier counters page, the cashier area and the cashier role are hidden; payments
  come only from uploaded receipts (approved by staff with "check uploaded receipts", and admins). The office's
  emergency "Record payment here" stays for admins.
- **Upload required:** the Payment step shows only "I already paid" (receipt photo, reference no., day paid); the
  home page, student Home and emails say "upload your receipt", never "pay at the cashier".
- **Slot change off:** the student sees their slot and permit, with "Ask the office through Support to change it";
  staff can still move a student.
- **Survey first:** after results are released, Home shows "Answer a short survey to see your result"; the result,
  the result PDF and choosing a program open after it.

## Not changed

Receipts to check (approver page), program chair/dean approval, results release, check-in, reports.

## Approved Nov 1, 2026 (mockup `mockups/admin/settings-v2.html`)

- **Settings page** with sections on the left and a search box (like Euphoria and Claude settings): Applying, Paying,
  Exam slot and results, Staff work, Emails and alerts, Website, Pause.
- **Admin menu** in groups: Overview · Daily work (Receipts to check, Result lookup, Support tickets) · Applicants ·
  Exam · Results · Payments · People · System. Switched-off features show "Off".
- **Staff jobs** (one person may hold several): Admin, Receipt checker, Support desk, Proctor, Program chair,
  College dean (Cashier only when counters are on).
- **Receipts to check** for admins and receipt checkers: search (name, code, reference, OR no.), campus / paid-by /
  order filters, tabs Mine · All campuses · Sent back · Approved today, the 2×2 photo beside the receipt, checks
  (reference, photo, same person), a 10-minute hold so two people never approve the same receipt. "Mine" = the
  checker's campus (1st choice) by default; Settings can make it one shared list.
- **Result lookup** (office) for admins and receipt checkers: all campuses, search or permit QR, "Is this the
  student?" (type the birth date the student says, then compare ID and face with the 2×2 photo) before the result
  shows; print, show on screen, or share (Messenger, email). Read-only and logged. At the office the slip may be
  printed before the survey; the student is asked to answer it in the app.
- **Support tickets**: tabs Mine · Not assigned · All open; new tickets given out in turn to Support desk staff;
  Reply / Take it. Program or slot changes are done by staff from the ticket.
