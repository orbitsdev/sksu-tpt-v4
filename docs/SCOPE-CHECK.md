# Scope check: what v4 adds beyond tptv3

The rule: **keep the old process**, and make it work better. Everything below is either new or bigger than what tptv3 does. Mark each one keep or cut when you discuss it. The remittance in the cashier console is already removed; cash handling stays in the university's own accounting.

**Legend:**

- **Old**: tptv3 does this today.
- **Asked**: you asked for it in this session.
- **New**: neither of the above.

| # | Feature | Old / Asked / New | Recommendation |
|---|---|---|---|
| 1 | Sign in with Google | Old | Keep |
| 2 | Email-link sign-in for students without Google | New | Optional (not in the mockups; Google only, as tptv3) |
| 3 | Application forms (personal, school, 3 programs) | Old | Keep (cleaner fields) |
| 4 | Extra uploads: Form 138, valid ID | New (from the tpt-recreate-v2 plan) | **Cut**: only the 2×2 photo and the receipt are collected; the ID is shown at the door |
| 5 | Photo shrunk on the phone | New | Keep (fixes 26 GB of uploads) |
| 6 | Receipt upload + reviewer approval | Old | Keep |
| 7 | Cashier console (record the OR no.) | Asked | Keep, simple version |
| 8 | Fee waiver | New | Optional |
| 9 | Refunds | New | **Cut** for v1 (accounting handles it) |
| 10 | Reconciliation against GCash/Landbank statements | New | **Cut** for v1 |
| 11 | School years with 1–3 schedules | Asked ("three schedules") | Keep; confirm what the three schedules are |
| 12 | School year setup wizard (5 steps) | New | Simplify to plain forms |
| 13 | Rooms with seats per room | Old (as a room count) | Keep, simple |
| 14 | Rooms CSV import | New | **Cut** |
| 15 | Schedule by date; times only as a guide | Asked | Keep |
| 16 | Morning/afternoon batches | Old (hard-coded in tptv3) | **Removed** (the office asked). tptv3 split each day's seats in half for AM/PM (`slots / 2`), guessed rooms with 50 seats hard-coded, and printed "Time: Not Assigned"; v4 has one session per exam day |
| 17 | Auto-assign seats to stragglers | New | Optional |
| 18 | Permit with QR + public verify page | Old (permit) + New (verify) | Keep (cheap) |
| 19 | Offline proctor check-in app | New | **Optional, off by default** (tptv3 has no proctor). Absent is still recorded: anyone with a slot but no score in the results file is marked absent at import (fixes the 635 gap) |
| 20 | Score import from the Testing Center Excel, with checks and preview | Old (import) + Asked | Keep |
| 21 | Scheduled result release | New (old: a toggle) | Keep (simple) |
| 22 | Qualification by cut-off + student chooses a program | New (from the v2 plan) | Confirm with the admission office |
| 23 | Survey | Old (was a gate) | Keep, optional to answer |
| 24 | Notifications: in-app, email, SMS per event | Asked (old had 2 emails) | Keep; SMS needs a budget |
| 25 | Notification preferences for students | New | **Cut** |
| 26 | Message blasts, templates, send log, resend | New | Optional (keep the send log) |
| 27 | Reports and Excel exports | Old | Keep |
| 28 | Report charts (funnel, histogram, demand) | New | Optional |
| 29 | Dashboard with seats per exam day | Asked | Keep |
| 30 | Global search (`/`) | New | Keep (cheap, saves time) |
| 31 | Bulk actions (remind, export) | New | Optional |
| 32 | Saved views | New | **Cut** |
| 33 | Duplicate-applicant detector | New | Optional (flag only; no merge) |
| 34 | Roles: admin, cashier, reviewer, scores admin, proctor | New (old: admin and applicant) | Keep a few: admin, cashier, proctor |
| 35 | Activity logs | New | Keep |
| 36 | Undo in the activity logs | New | **Cut** |
| 37 | Welcome and splash screens in the app | New | Optional |
| 38 | Applicant app tabs, bottom sheets, wallet permit | Asked (mobile look) | Keep |
| 39 | Support requests (tickets): topic, message, optional photo; thread with the office; Open → Answered → Closed; one open at a time, 5 per school year, reply and size limits; admin search, filters, assign, close, change details, pause a student | Asked (tptv3 has no way to ask) | Keep, simple: no priorities or SLAs |
| 40 | Official email setting: sender name, from address, reply-to, footer, test email | New | Keep (students should see the university address) |
| 41 | Admin bell: new questions, finished imports, failed sends | New | Keep (small) |
| 42 | Results import reads the Testing Center Excel as it is: picks the sheet, joins two header rows, ignores extra columns, remembers the column match | Old (Excel upload) | Keep (handles a new layout each year) |
| 43 | Transferee test (2nd semester) in the same system: a schedule is set to Freshmen or Transferees; transferees give 2 choices plus current school and course; the program chairperson or dean approves before payment; cashier payment only; one exam day and venue | Asked (today it is a paper walk-in form) | Keep |
| 44 | Program chair login: sees only their program's transferee applicants, approves or declines with a reason | Asked (part of #43) | Keep, small |
| 45 | Payment methods per school year: cashier always on; online receipt upload + admin review as a switch, **off for now** | Asked (no online payment yet) | Keep the switch; build online later |
| 46 | Details locked after approval; changes only through a support request or an admin, with a reason | Asked | Keep |
| 47 | Exam guide times shown wherever an exam day appears | Asked | Keep |

**If you cut every "Cut" and "Optional"**, v1 is:

1. Sign in.
2. Apply.
3. Pay (cashier or upload).
4. Approve.
5. Pick a date.
6. Permit.
7. Attendance.
8. Import scores.
9. Release.
10. Notify.
11. Reports.

That's the old process, done properly.
