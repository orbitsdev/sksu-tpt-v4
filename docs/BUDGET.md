# What to buy and budget

What SKSU needs to pay for to run SKSU TPT v4, and what is free. Prices are **estimates to check before buying** (they change, and some are in US dollars). Developer work is not included.

## 1. Must have (to run the system)

| Item | What it is for | Estimated cost | Notes |
|---|---|---|---|
| **Server** | Runs the website, student app and admin | **No new purchase:** v4 uses the **existing TPT server** (already paid by SKSU) | v4 runs next to tptv3 until the switch. Ubuntu 20.04 should be upgraded in a quiet month |
| **Extra power on peak days** | Results day and registration opening | About **US$1–3 per day** of upgrade | Resize up for the day, then back down |
| **Backups** (DigitalOcean weekly backups) | Restore the server if something breaks | About **20% of the droplet price** (≈ US$10 a month) | Plus daily database backups |
| **Off-server storage** (DigitalOcean Spaces) | Daily backups and student files kept outside the server | About **US$5 a month** (250 GB) | Protects against losing the server |
| **Email sending** | Approved, exam slot, results, support replies | **Option A:** a mail service (e.g. Amazon SES) about **US$0.10 per 1,000 emails** (≈ US$1–5 a year). **Option B:** the university's Google Workspace address, free but about 2,000 emails a day | The current sksutpt@gmail.com can only send about 500 a day: not enough for results day |
| **Web address** | e.g. `tpt.sksu.edu.ph` | **Free** if the university's IT adds it under sksu.edu.ph | Or a domain like sksutpt.com, about **₱800–1,000 a year** |
| **HTTPS certificate** | Secure connection | **Free** (Let's Encrypt) | Renews by itself |

**New monthly costs: about US$15–20 (≈ ₱900–1,200)** for backups and off-server storage, plus email (a few dollars a year) and a few dollars on peak days. The server itself is the one SKSU already pays for.

## 2. Optional (later)

| Item | What it is for | Estimated cost | When |
|---|---|---|---|
| **SMS** (e.g. Semaphore, a Philippine SMS provider) | Text reminders: exam tomorrow, results out | About **₱0.50 per text** (check the provider's price). Example: 10,000 students × 3 texts ≈ **₱15,000 per school year** | Only if there is a budget; v1 uses in-app + email |
| **Online payment** (GCash / Maya / bank) | Students pay online and upload a receipt | Depends on the account; the switch already exists in the system | When the office has an official account |
| **Cloudflare** | Speeds up and protects the website on peak days | **Free** plan is enough | Recommended before results day |
| **Uptime monitor** (e.g. UptimeRobot) | Alerts if the website goes down | **Free** plan | Recommended |

## 3. Free (no purchase)

- Laravel, Inertia, Vue, shadcn-vue, Tailwind, Redis, MySQL, Laravel Horizon: open source.
- The student app as a PWA: no App Store or Play Store fees.
- Load testing tool (k6): free.
- Google sign-in for students: free.

## 4. One-time costs to plan

| Item | Estimated cost |
|---|---|
| Setting up v4 next to tptv3 on the existing server, testing, then switching the address | Developer time |
| Load test before go-live (a temporary test server for a day) | About **US$2–5** |
| Printing (OR booklets, payment slips paper for cashiers) | Office supplies |

## 5. What to decide

1. **Server:** use the existing TPT server (decided); resize to 4 cores on peak days.
2. **Email:** mail service (Option A) or university Google Workspace address (Option B).
3. **SMS:** now or later (and the yearly budget if now).
4. **Web address:** a `sksu.edu.ph` subdomain from the university's IT, or a separate domain.
5. **Who pays and whose account:** the DigitalOcean account should be owned by SKSU, with the developer added as a team member.
