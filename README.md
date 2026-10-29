# SKSU TPT v4

This repo holds the planning work for rebuilding the SKSU Admission Test (TPT) system. It has no app code yet. The old app is `tptv3`, a Laravel 9 + Livewire app that runs on sksu-tpt.com.

**Status (28 Oct 2026):** the mockups and docs are ready for discussion. The polish comes later.

## Start here

1. `docs/PRD.html`: decisions, flows (section 8) and real-life scenarios (section 5).
2. `docs/SCOPE-CHECK.html`: everything v4 adds beyond tptv3. Mark each one keep or cut.
3. `mockups/ADMIN-JOURNEY-MOCKUP.html`, then the applicant, cashier and proctor journeys.
4. `mockups/index.html` lists every page, the interaction rules, the chart choices and the old-route coverage table.

## What's here

| Folder | What it is |
|---|---|
| `mockups/` | 71 linked HTML pages with every state (forms, dialogs, toasts, loading, empty, errors). Generated; don't edit by hand. |
| `mockups/*-JOURNEY-MOCKUP.html` | Journeys for admin (the whole school year), applicant (phone app), cashier and proctor |
| `docs/` | PRD, scope check, forms and payments, results import, CSV findings (each `.md` also has a readable `.html` with the diagrams drawn) |
| `tools/` | `gen_mockups.py` builds every mockup page. `base.css`, `theme*.css` hold the styles. `render_docs.py` turns the docs into HTML. `tpt-scores-template.csv` is the score import template. |
| `assets/brand/` | Official SKSU seal, logo and campus photo from sksu.edu.ph. `SOURCES.md` lists the links and colours. |

The longer audit of the old system (security findings, server details, key names) is in a Claude Doc: https://claude.ai/artifact/N75VWKWsNrpWHrLgo8ywi6. The exploit details are kept offline, not in this repo.

## Resume on another PC

```bash
git clone https://github.com/orbitsdev/sksu-tpt-v4.git
cd sksu-tpt-v4
python tools/gen_mockups.py      # needs Python 3.10+; nothing to install
python tools/render_docs.py      # rebuilds docs/*.html
start mockups/index.html         # Windows; on macOS use `open`
```

Each page is built by one call:

- `phone(...)`: applicant app screens.
- `admin(...)`: staff screens.
- `cashier(...)`: the cashier console.
- `pro(...)`: proctor screens.
- `board(...)`: the journey pages.

States are `modal(...)`, `toast(...)`, `drawer(...)` and `inmain(...)`, opened by `#id` links. The yellow bar at the top of a page lists them.

## Rules for this repo

- Never commit student data (CSV/XLSX exports, names, scores), `.env` files or server passwords. `private/` is git-ignored for anything sensitive.
- Mockups use sample data only.
- Every new screen goes in the generator with all of its states.
- Keep the old process. Anything new must be listed in `docs/SCOPE-CHECK.md`.

## Open questions for the admission office

1. What are the "three schedules": three exam schedules a year, or something else?
2. Confirm date-only scheduling. What are the real report and start times?
3. Exam fee, payment accounts, and whether cashiers will use the system.
4. Cut-off scores per program, and the official stanine labels.
5. Testing Center Excel columns (the template is in `tools/tpt-scores-template.xlsx`).
6. SMS provider and budget.
7. Can absent examinees move to the next schedule for free?
8. Which documents are required (Form 138, valid ID), and which personal fields (tribe, religion) are needed under the Data Privacy Act?

## Old system (still to do)

1. Close the open test routes on the live server (the script is kept offline).
2. Make the old `tptv3` GitHub repo private and remove the student CSVs from its history.
3. Harden the old server: keys-only SSH, new credentials, backups.
