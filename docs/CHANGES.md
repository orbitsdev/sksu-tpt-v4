# Changes · Oct 29, 2026

Everything changed in the mockups and docs today. ✅ = done.

## Words (same as the old system)

- ✅ **School year → Schedule → Exam slot** everywhere (was season / round / session). Example: "SY 2027–2028 · Schedule 2".
- ✅ "Pick your exam slot" (was "pick a seat"). Room 4 · seat 27 stays as the seat number.
- ✅ "Excel" for the Testing Center results file (was CSV).
- ✅ Real values from the SKSU post: fee **₱275.00**, **1st batch 8:00 AM / 2nd batch 1:00 PM**, exam-day items (pencil No. 2, permit, valid ID, official receipt), Guidance and Testing Center contact.
- ✅ File names follow the new words: schedules.html, exam-slots.html.

## Process (kept like tptv3)

- ✅ **One review** like tptv3: the admin approves, or **sends back with remarks** (what to fix: photo, details, documents or receipt + a free-text remark). The student sees "Sent back: please fix" and resends.
- ✅ **Publish / Unpublish** a schedule: setting it up never makes it public.
- ✅ **Results**: Publish now, or set a release date, and Hide again. Shows the status clearly.
- ✅ **Absent comes from the results import** (has an exam slot, no score). Proctor check-in is **optional, off by default**.
- ✅ **Apply again**: a rejected or absent applicant can apply in a later schedule.
- ✅ One list of application statuses used on every page.

## New on purpose (listed in the scope check)

- ✅ **Cashier counter**: find the person, type the OR no., press Enter. Counter and Applicants are now **one screen** (list left, payment right). Tabs: Counter · Paid · Info.
- ✅ **Student questions**: "Ask the admission office" from Notifications; the admin answers on the applicant's page; the reply arrives in the app and by email.
- ✅ **Official email setting** (sender, reply-to, footer, test email).
- ✅ **Admin bell**: small dropdown with new questions, finished imports, failed messages.
- ✅ **Landing page settings**: announcement, requirements, questions and answers, contact.
- ✅ **System status** page: website, people online, email and SMS usage, server, backups.
- ✅ **Transferee test (2nd semester)**: a schedule can be for Transferees; 2 program choices + current school and course; the **program chairperson approves** before paying; cashier payment only; new Program chair page.
- ✅ Transferee picks 1st or 2nd batch.

## Results import

- ✅ Takes the Testing Center Excel **as it is**: picks the right sheet, reads the two header rows, matches columns by name (remembered for next year), ignores extra columns, stops with a plain message if the examinee number column is missing.
- ✅ Vertical step guide: Upload → Match columns → Check rows → Approve → Publish.
- ✅ A real Excel template to download.

## Only the data we need

- ✅ Uploads cut to the **2×2 ID photo** (for the permit) and the **payment receipt** (online payment only). Transferees add their grades for the chairperson. No Form 138 or ID copies: the ID is shown at the door.

## Look and feel (calm, minimal, like euphoria)

- ✅ **Sidebar in work order with groups**: Applicants · Exam · Reports · Management · **System** (technical pages at the bottom).
- ✅ Stat cards: white, grey label, dark number; red only for real problems.
- ✅ Selected tab or menu item: dark bold text or a grey chip, no green box.
- ✅ Header: solid SKSU green; "Registration open · Schedule 2" as a plain link.
- ✅ Bell is a dropdown, not a popup in the middle.
- ✅ **Vertical step guide** on long forms: New school year (5 steps), Import scores (5 steps). Short forms stay as one dialog.
- ✅ One green button per page; other actions under "···".
- ✅ Removed: "?" bubbles, extra description lines, orange fills, developer talk.
- ✅ **Dashboard**: 4 numbers that drive the work, "Where applicants are" (signed up → submitted → paid → picked a slot), applications per day, exam seats by day, 1st choice by campus, needs attention.
- ✅ Exam schedules and Exam slots pages cleaned up (your two screenshots).
- ✅ Last coloured boxes and status colours toned down.

## Fixes found by the page-by-page review

- ✅ Permit screen no longer cuts off the details.
- ✅ Progress dots match the steps.
- ✅ Notifications in date order, one consistent story.
- ✅ Sign out is a quiet link.
- ✅ Wrong dates on Exam slots (Schedule 2 showed Mar 14).
- ✅ Removing things the scope check cut (saved views, merge, undo, refunds, notification settings, extra roles).
- ✅ Same numbers and dates on every page.

## Student app redesign

- ✅ euphoria's phone frame (dark bezel, camera dot); numbered screens with captions on the journey board.
- ✅ Flat white screens, thin dividers, no card inside a card, one solid green button, no gradients or glow.
- ✅ Messages pop up inside the phone; bottom sheets stay in the phone.
- ✅ Right fields: calendar for birth date, +63 mobile keypad, number keypad, search pickers for school and program, camera or gallery for the photo.
- ✅ Plain office wording ("SKSU TPT · SY 2027–2028"), no "Let's start!".

## Fields and lists (admin and cashier)

- ✅ Date pickers with a calendar, number, email and phone fields where they belong.
- ✅ Search, filters, sortable columns and pages of 25 on every list that can grow.
- ✅ Public landing, sign-in and the proctor app in the same calm style.

## Docs

- ✅ **UI rules** (new): when to use a page, dialog, drawer or step form; buttons; what happens after a click; errors; long-term rules.
- ✅ Scope check: rows 39–44 added (questions, official email, bell, Excel import, transferees, program chair).
- ✅ PRD: re-apply per schedule, transferee section, new words.
- ✅ Results import doc: Excel as it is, absent rule.
- ✅ PRD aligned with every mockup.

## Open questions for the Guidance and Testing Center

1. Is the freshman TPT fee also ₱275?
2. Can an absent examinee take a later schedule without paying again?
3. Can someone with a result retake in the same school year?
4. Transferees: if the 1st-choice chairperson declines, does the 2nd choice get a turn?
5. Online payment accounts (GCash / Maya / Landbank).
6. Will cashiers type the OR no. in the system?
7. Cut-off score per program; official stanine labels.
8. Official sender email; SMS provider and budget.
9. Transferees: is approval in the system enough, or do you still need the chairperson's signature on paper?

## Not touched

- Nothing committed or pushed yet.
- No production server changes.
