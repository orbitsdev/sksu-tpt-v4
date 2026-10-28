# SKSU TPT v4

This repo holds the planning work for rebuilding the SKSU Admission Test (TPT) system. It has no app code yet. The old app is `tptv3`, a Laravel 9 + Livewire app that runs on sksu-tpt.com.

## What's here

| Folder | What it is |
|---|---|
| `mockups/` | Page-by-page HTML mockups, light mode, SKSU branding. Open `mockups/index.html` in a browser. |
| `mockups/*-JOURNEY-MOCKUP.html` | Journey mockups for admin (the whole season), applicant and proctor: every screen and state in device frames with captions. |
| `tools/` | `gen_mockups.py` builds every mockup page; `base.css` holds layout and components, `theme.css` the SKSU look (deep green, mint, gold, campus photo, waves). Edit these, never the generated files. |
| `assets/brand/` | Official SKSU seal and logo from sksu.edu.ph. `SOURCES.md` lists the links and colours. |
| `docs/` | `csv-findings-2026.md` analyses the 2026 results CSV. It contains no names or scores. |

## Docs

| File | What it is |
|---|---|
| `docs/PRD.md` | Decisions, core modules, old process → new process, known gaps, scenarios, notifications, data model, flows and architecture (Mermaid, renders on GitHub), earlier attempts, plan, admin UI rules, usability walk-through |
| `docs/SCOPE-CHECK.md` | Everything v4 adds beyond tptv3, to keep or cut |
| `docs/FORMS-AND-PAYMENTS.md` | Every tptv3 form and field reviewed, records per step, payment flow (cashier, online + proof, waiver, refunds, reconciliation) |
| `docs/RESULTS-IMPORT.md` | How tptv3 imports scores, its flaws, the v4 CSV template and import rules |
| `docs/csv-findings-2026.md` | Analysis of the 2026 results CSV |
| `mockups/index.html` | Every page, interaction rules, chart choices and the route coverage table |

The longer audit (security findings, server details, key names) is in a Claude Doc: https://claude.ai/artifact/N75VWKWsNrpWHrLgo8ywi6

## Resume on another PC

```bash
git clone <this repo>
cd sksu-tpt-v4
python tools/gen_mockups.py      # needs Python 3.10+; nothing to install
start mockups/index.html         # Windows; on macOS use `open`
```

To change a screen, edit `tools/gen_mockups.py` (or `tools/base.css` for styles), then run the generator again. Each page is built by one call: `phone(...)` for applicant screens, `admin(...)` for staff screens and `pro(...)` for proctor screens. States are `modal(...)` and `toast(...)` overlays opened by `#id` links. The yellow bar at the top of a page lists them.

## Rules for this repo

- Never commit student data (CSV/XLSX exports, names, scores), `.env` files or server passwords.
- Mockups use sample data only.
- Every new screen goes in the generator with all of its states: form errors, dialogs, toasts, loading, empty and success.

## Still open

1. Security findings for the old live system are kept offline (not in this repo). Ask Brian.
2. Make the old `tptv3` GitHub repo private and remove the student CSVs from its history.
3. Harden the old server (keys-only SSH, new credentials, backups).
4. Confirm the stanine labels and the exam fee with the testing center.
