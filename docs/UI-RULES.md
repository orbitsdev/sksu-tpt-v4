# UI rules

How every screen in SKSU TPT v4 is built, so the system stays the same as it grows. The people using it are admission staff, cashiers and Grade 12 students, not IT people. When a rule here and a mockup disagree, the rule wins and the mockup gets fixed.

## 1. Page, dialog, drawer or step form

| Use | When | Examples |
|---|---|---|
| **Page** | A list or a record people come back to | Applications, one applicant, Results, Reports |
| **Dialog** | A short form (up to about 6 fields) or a yes/no question | Add program, Invite staff, Add exam slot, Reject with remarks, Publish |
| **Drawer** (slides from the right) | A quick look at one row without leaving the list | Quick look at an applicant from Applications |
| **Step form** with the vertical step rail | A long job with 3+ parts that happens rarely | New school year (5 steps), Import scores (5 steps) |
| **Toast** (small note, bottom corner) | Telling the user something worked | "Saved", "Reply sent" |

Never a dialog on top of a dialog. Never a step form for something done every day.

## 2. Buttons

- **One main (green) button per screen or dialog**: the thing the user most likely wants next. Everything else is a plain button or a link.
- The main button sits **top right** on a page, **bottom right** in a dialog or form. **Cancel/Back** sits to its left.
- Buttons say what happens: "Approve payment", "Publish results", "Send reply". Never "OK" or "Submit" alone.
- **Red buttons** only for things that remove or undo: Void payment, Cancel application, Unpublish. They always ask first and say what will happen.
- A button that is not allowed right now is hidden or explained ("Opens Jan 3"), not just greyed out with no reason.

## 3. What happens after a click

| Action | Then |
|---|---|
| Save, add, edit | Dialog closes, toast "Saved", the list shows the change |
| Approve, reject, publish, void | Confirm dialog that says who is affected and whether it can be undone → toast → the change is in the record's history and the activity log |
| Anything sent to students (reject remarks, reply, announcement) | Confirm shows how many people and which channels (app, email, SMS) |
| Long jobs (import, sending 600 messages, big exports) | Progress bar, "Run in background", the bell tells you when it's done |
| Something two staff could do at once (approve the same payment) | The second person gets "Already approved by Ana at 9:02" and nothing is saved twice |

## 4. What a screen shows

- **Title** says what the page is. **No description line** unless the page would be confusing without it.
- **Stat cards** only on pages where the numbers drive work (Dashboard, Results, Import scores, Cashier). White card, grey label, dark number. Red only for a real problem.
- **Lists** show the few columns needed to decide, newest or oldest-waiting first. Click a row to open it.
- **Selected things** (tab, sidebar item, filter) are shown with dark bold text, an underline, or a grey chip. Never a light green box with a border.
- Words are the old system's: **School year → Schedule → Exam slot**. Examinee no., OR no., cut-off score.

## 5. Form fields and lists

- **The right field for the data:** a date picker with a calendar for dates (birth date, registration dates, exam days), time picker for times, `tel` with +63 for mobile, `email` for email, numeric keypad for scores, GWA, OR and reference numbers, radio buttons for 2–4 choices, a select for 5–15, a search-as-you-type picker for long lists (schools, programs, applicants), a camera/file picker for photos.
- Labels above the field, help or error text under it. Required fields are not marked with stars; optional ones say "(optional)".
- **Every list that can grow** has search, the filters people actually use (schedule, campus, status), sorting on the columns that matter (name, date, oldest waiting), and pages of 25. Short fixed lists (under about 10 rows) don't need them.

## 6. Every screen has these states

Loading (grey placeholders), empty (what to do first), error (what went wrong and what to do), success (toast), no permission (who to ask). The mockups show them in the yellow "States on this page" bar.

## 7. Errors

- Say **what is wrong and how to fix it**, next to the field: "Not a real date", "This OR no. was already used on Jan 12 for Maria Dela Cruz".
- Never lose what the user typed. Forms save drafts.
- No connection: "You're offline. We'll send it when you're back." Nothing is lost.
- Server problems show a plain message and a reference number for IT, never a code dump.

## 8. Built for the long term

- Every school year, schedule, campus, program and room is **data**, created on screen. No code change for a new year.
- Nothing is deleted that already has applicants. It is switched off instead, and old years stay readable.
- Every change by staff goes in the **activity log**: who, what, when, old and new value.
- Technical pages (Email and SMS, System status, Activity logs) sit in the **System** group at the bottom of the sidebar, for the super admin only.
- Fast by design: lists load 25 rows at a time, search answers as you type (name, examinee no., OR no., reference), heavy work runs in the background.
