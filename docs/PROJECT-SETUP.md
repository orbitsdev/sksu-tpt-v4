# Project setup

How the SKSU TPT v4 code is organised and run, so every developer works the same way and nothing gets guessed.

## In short (for the owner)

- **Two repositories.** This one (`sksu-tpt-v4`) keeps the mockups and the documents, as the plan everyone reads. The real app lives in a **new private repository**, `sksu-tpt-v4-app`, so student-facing code and secrets are never public.
- **Built on a developer's computer first.** Nothing touches the live server until the app is finished (see GO-LIVE.md).
- **Every rule has an automatic test.** Payments, examinee numbers, imports and publishing are checked by tests on every change, before anything is accepted.
- **Only made-up data** is ever used for development and tests. No real student data in code, tests or repositories.
- **Every push is checked automatically**: formatting, mistakes, tests and the build. A red check means it doesn't go in.

## 1. Repositories

| Repo | Visibility | Holds | Why |
|---|---|---|---|
| `orbitsdev/sksu-tpt-v4` (this one) | Public | Mockups, docs, the mockup generator | The shared plan; safe to share (sample data only) |
| `orbitsdev/sksu-tpt-v4-app` (new) | **Private** | The Laravel app | Real code, deploy settings and future secrets stay private; its own history, issues and checks |

Why not an `/app` folder in this repo: this repo is public, and mixing a static mockup site with the real app makes deploys and permissions messy. Two repos keep each one simple.

## 2. Create the app (reference commands)

On the developer's computer (Windows, with Laravel Herd: PHP 8.4, Composer, Node 22 LTS):

```bash
# Laravel 13 with the official Vue + Inertia starter (TypeScript)
laravel new sksu-tpt-v4-app --vue --pest
cd sksu-tpt-v4-app

# make sure we're on the latest majors
composer require laravel/framework:^13.0 inertiajs/inertia-laravel:^3.0
npm install @inertiajs/vue3@^3 vue@^3 typescript

# Tailwind 4 and shadcn-vue (copies only the components we add)
npm install tailwindcss@^4 @tailwindcss/vite
npx shadcn-vue@latest init
npx shadcn-vue@latest add button input select dialog sheet table tabs badge calendar popover dropdown-menu checkbox radio-group switch toast skeleton
```

Use the latest stable patch versions on the day the project starts.

## 3. Packages, in install order

Install one group at a time, run the tests, then commit. Check each supports Laravel 13 first.

| Order | Packages | For |
|---|---|---|
| 1 | `laravel/socialite` | Google sign-in |
| 2 | `spatie/laravel-permission` | Roles and permissions (see ROUTES.md) |
| 3 | `spatie/laravel-data` + TypeScript transformer, `laravel/wayfinder` | Typed data and typed routes between Laravel and Vue |
| 4 | `spatie/laravel-query-builder` | Lists: search, filters, sorting, paging |
| 5 | `spatie/laravel-settings` | School year and system settings |
| 6 | `spatie/laravel-medialibrary`, `intervention/image` | Photos, files, PDFs |
| 7 | `spatie/laravel-activitylog` | Activity log |
| 8 | `predis/predis` or phpredis, `laravel/horizon` | Redis queue and its dashboard |
| 9 | `spatie/simple-excel` | Testing Center Excel import, exports |
| 10 | `barryvdh/laravel-dompdf`, `simplesoftwareio/simple-qrcode` | Result PDFs, QR codes |
| 11 | `spatie/laravel-backup`, `spatie/laravel-health`, `laravel/pulse` | Backups, System status, monitoring |
| Dev | `larastan/larastan`, `laravel/pint`, `barryvdh/laravel-debugbar` | Quality checks and local debugging |
| Front end | `@tanstack/vue-table`, `vite-plugin-pwa`, `browser-image-compression` | Big tables, installable student app, photo shrinking |

## 4. Folder structure

```
app/
  Actions/            business rules, one class per action
                      (RecordPayment, IssueExamineeNumber, BookExamSlot,
                       ApproveScoreImport, PrepareResultPdfs, PublishResults…)
  Enums/              statuses (ApplicationStatus, PaymentKind, PdfStatus…)
  Data/               typed data sent to each Vue page (spatie/laravel-data)
  Http/Controllers/   thin: check, call an Action, return a page
    App/ Admin/ Cashier/ Public/
  Http/Requests/      validation per form
  Jobs/               queued work (BuildResultPdf, SendResultWave, ImportScoresFile)
  Models/
  Policies/           who may do what, per model
  Settings/           spatie settings classes
database/
  factories/ seeders/ migrations/
resources/js/
  pages/
    public/           landing, sign-in, verify, privacy
    app/              student PWA screens
    admin/            admin screens
    cashier/          cashier screens
  components/
    ui/               shadcn-vue components (ours to edit)
    shared/           list page, filters, status chip, phone sheet…
  layouts/            AppLayout (phone), AdminLayout (sidebar), CashierLayout
tests/
  Feature/  Unit/
```

## 5. Coding rules

- **Thin controllers.** A controller checks permission, validates (Form Request), calls one **Action**, returns a page or redirect. Rules live in Actions so they can be tested and reused.
- **Statuses are Enums**, with the allowed transitions written once (DATABASE.md section 4).
- **Policies** for every model; scope rules (chair sees only their program, cashier only payment fields) are enforced on the server, never only hidden in the UI.
- **Money in centavos** (`27500` = ₱275.00), never floats.
- **Times stored in UTC, shown in Asia/Manila**; deadlines are 11:59 PM Philippine time.
- **No N+1 queries**: load related data together; lazy loading is turned off in development so mistakes fail loudly.
- **Small page data**: send only what the screen shows; deferred props for slow parts; lists paged 25 at a time.
- **Locks and transactions** for payments, examinee numbers, seating, import approval and publishing (DATABASE.md section 5).
- **Heavy work in jobs** (PDFs, emails, Excel), never while a user waits.
- **Names and words follow the mockups**: School year, Schedule, Exam slot, Examinee no., OR no.
- **Delete unused code**; no commented-out code; no "maybe later" columns or switches.

## 6. Testing

- **Pest feature tests for every rule**, at minimum:
  - Record payment: approves, issues the next examinee number, rejects a used OR no., blocks a double click, spoiled and late payments, void retires the number.
  - Examinee numbers: pattern, prefix/digits, never reused, two cashiers at the same time get different numbers.
  - Exam slots: one per campus per day, seats never overbooked, typhoon move keeps seats.
  - Score import: 2026 layout, column matching, wrong-schedule file refused, re-upload shows changes only.
  - Results: prepare PDFs, publish rules (prepare-then-publish, emergency override for super admin only), hide one student.
  - Permissions: each role sees and does only what ROUTES.md allows.
  - Support limits: one open, 5 per school year.
- **Factories with made-up people only.** Never copy real student data into tests, seeders or fixtures.
- A test that fails blocks the change.

## 7. Checks on every push (GitHub Actions)

| Check | Tool | Fails when |
|---|---|---|
| Formatting | Laravel Pint | code isn't formatted |
| Mistakes | Larastan | type errors, wrong calls |
| Tests | Pest | any rule test fails |
| Front end types | `vue-tsc` | Vue/TypeScript errors |
| Build | `npm run build` | the app doesn't build |

## 8. Local development

- **Laravel Herd** on Windows (PHP 8.4, nginx, Composer, Node in one installer). Sail (Docker) works too, but Herd is lighter on a Windows laptop.
- **MySQL 8** and **Redis** locally (Herd's services or DBngin).
- `php artisan horizon` for the queue, `npm run dev` for the screens.
- Mail goes to a local catcher (Mailpit) during development; nothing is emailed to real people.

## 9. Demo data (seeders)

`php artisan db:seed --class=DemoSeeder` creates a school year that matches the mockups: SY 2027–2028, Schedules 1–4, 7 campuses with programs and cut-offs (ESM/overall), rooms, exam slots, staff for every role, and made-up applicants (Maria S. Dela Cruz, 500214, and the rest), so every screen can be compared with its mockup.

## 10. Branches, commits, secrets

- `main` is always working. Work on short branches (`feature/cashier-counter`), merge with a pull request after the checks pass.
- Commit messages say what changed and why, in plain English.
- **`.env` is never committed.** Passwords, mail and storage keys live only in `.env` on each machine and on the server. `.env.example` lists the names with no values.
- No exports, student files or database dumps in the repository (`.gitignore` blocks `*.csv`, `*.xlsx`, `*.sql`, `storage/`).

## 11. From mockups to screens

| Mockup | Vue page |
|---|---|
| `mockups/applicant/*.html` | `resources/js/pages/app/*` (PWA layout) |
| `mockups/admin/*.html` | `resources/js/pages/admin/*` (sidebar layout) |
| `mockups/cashier/*.html` | `resources/js/pages/cashier/*` |
| `mockups/public/*.html` | `resources/js/pages/public/*` |
| The yellow "States on this page" | Each state becomes a real case: loading, empty, error, dialog, toast |

The shared list pattern, status chips, step rail and phone sheets become components in `components/shared`, so every page looks like its mockup without repeating code.
