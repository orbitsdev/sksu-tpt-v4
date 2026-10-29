# Go-live runbook

> **Do not run any step until the app is finished and the owner says go.** This is a written plan only. Nothing here has been run.

## In short (for the owner)

- v4 goes on the **existing TPT server**, **next to tptv3**, which keeps working until switch day.
- First a **full snapshot** of the server: the "undo button" for everything after it.
- Then fix the security hole, set up backups, add what v4 needs, put v4 on a **test address**, and test it hard (including 10,000 simulated students).
- **Switch day:** point the real address to v4. If anything goes wrong, **point it back to tptv3 in under 10 minutes**.
- Later, in a quiet month: upgrade Ubuntu and clean the old uploads.

Every step has: what it's for, the commands (for reference), **how we know it worked**, and **how to undo it**.

**Server today** (read-only check, Oct 29, 2026): 128.199.96.48 · Ubuntu 20.04 · 2 cores / 8 GB RAM / 97 GB disk (44 GB free) · PHP 8.4 · MySQL 8.0 · nginx · tptv3 live in `/var/www/tptv3` (also `tptv2`, `sksutpt`, `pre-reg` folders).

---

## Step 0. Read-only pre-check

**For:** know the server's state before changing anything.

```bash
ssh tpt 'nproc; free -h; df -h /; uptime; lsb_release -ds; php -v | head -1; mysql --version; nginx -v; \
  systemctl is-active nginx mysql php8.4-fpm; ls /var/www; ls -ld /root; find /root -maxdepth 1 ! -user root -printf "%u %p\n"'
```

**Check:** services active, disk above 20 GB free, tptv3 opens in a browser, the list of `/root` files not owned by root is known.
**Undo:** nothing changed.

## Step 1. Snapshot

**For:** a full copy of the server to roll back to.

DigitalOcean → Droplets → the TPT droplet → **Snapshots → Take live snapshot** (name: `before-v4-YYYY-MM-DD`).

**Check:** the snapshot shows "Complete" with the right size.
**Undo:** keep it until v4 has run a full school year; restoring it returns the server to this moment.

## Step 2. Fix /root ownership (security)

**For:** today most of `/root` belongs to the web user (`www-data`), which lets the website take over the server.

```bash
# who still uses those files? (should print nothing)
ssh tpt 'sudo -u www-data find / -xdev -path /proc -prune -o -lname "/root/*" -print 2>/dev/null | head; \
  grep -rl "/root" /etc/nginx /etc/php/8.4/fpm/pool.d /etc/supervisor 2>/dev/null'
# then
ssh tpt 'chown -R root:root /root && chmod 700 /root'
```

**Check:** `ls -la /root` shows only `root`; tptv3 still loads; `ssh tpt` still works.
**Undo:** if tptv3 breaks, `chown -R www-data:www-data /root/<the one path it needs>` and move that file out of `/root` properly.

## Step 3. Off-server backups

**For:** if the server dies, nothing is lost.

1. Create a DigitalOcean **Spaces** bucket (private) and an access key.
2. In v4: `spatie/laravel-backup` set to back up the database daily and files weekly to Spaces, keep 14 daily / 8 weekly.
3. tptv3's database: a nightly `mysqldump` copied to the same bucket until tptv3 is retired.

**Check:** a backup appears in Spaces; **restore test**: download it and load it into a fresh local database; the row counts match.
**Undo:** delete the bucket or the schedule; nothing on the live site changes.

## Step 4. Redis and Supervisor

**For:** cache, sessions and the queue (PDFs, emails, imports).

```bash
ssh tpt 'apt-get update && apt-get install -y redis-server supervisor && \
  sed -i "s/^# *maxmemory .*/maxmemory 512mb/; s/^# *maxmemory-policy .*/maxmemory-policy allkeys-lru/" /etc/redis/redis.conf && \
  systemctl enable --now redis-server supervisor && redis-cli ping'
```

Supervisor program for Horizon (in step 5, once v4 is deployed):

```ini
[program:tpt-v4-horizon]
command=php /var/www/sksu-tpt-v4/current/artisan horizon
user=www-data
autostart=true
autorestart=true
stopwaitsecs=3600
```

**Check:** `redis-cli ping` → `PONG`; `supervisorctl status` shows the worker RUNNING; tptv3 unaffected.
**Undo:** `apt-get remove redis-server supervisor` (tptv3 doesn't use them).

## Step 5. v4 next to tptv3

**For:** v4 running on the same server, on a test address, without touching tptv3.

1. Folder `/var/www/sksu-tpt-v4` (releases + `current` symlink), owned by a deploy user, web user read-only except `storage/`.
2. Database: new schema `tpt_v4` and its own MySQL user with access only to it.
3. `.env` written on the server only (never in git): app key, DB, Redis, mail, Spaces, Google sign-in.
4. nginx site for a **test address** (e.g. `tpt-test.<domain>`), PHP 8.4-FPM, HTTPS with Let's Encrypt (`certbot --nginx -d tpt-test.<domain>`).
5. Deploy: `git pull` of the private app repo → `composer install --no-dev -o` → `npm ci && npm run build` → `php artisan migrate --force` → `php artisan optimize` → switch `current` → `php artisan horizon:terminate`.
6. Seed the real school year setup (campuses, programs, rooms) through the admin screens, not by script.

**Check:** the test address opens over HTTPS; sign-in works; Horizon dashboard shows workers; tptv3 still works at its own address.
**Undo:** remove the nginx site and folder, drop `tpt_v4` and its user; tptv3 was never touched.

## Step 6. Smoke test and load test

**For:** prove it works and holds the crowd before students see it.

- **Smoke test** (checklist): apply on a phone, install the PWA, pay at a test counter, examinee number, pick a slot, permit offline, import a sample Excel, prepare PDFs, publish to test accounts, survey, choose a program, support ticket, email arrives.
- **Load test** with k6 against the **test address**, at a quiet time (night): 10,000 simulated students over the results-day pattern (waves), plus a registration-opening burst.

**Check:** pages answer under 1 second for 95% of requests, no errors, CPU below 80%, queue keeps up. If not: tune, or plan a 4-core resize for peak days.
**Undo:** stop the test; nothing persists (test data in a separate test school year, deleted after).

## Step 7. Switch day

**For:** move students from tptv3 to v4 with no data lost.

Pick a quiet day **outside** registration and results. Checklist:

1. Announce on the landing page a day before ("short maintenance").
2. Final backup of tptv3 (DB + uploads) to Spaces.
3. **Freeze tptv3 writes** (maintenance mode: `php artisan down` in `/var/www/tptv3`), keep it readable for staff if needed.
4. Point the real address to v4 (nginx `server_name` or DNS), HTTPS certificate for it.
5. Open the admin, cashier and a student phone; run the smoke checklist on the real address.
6. Watch Pulse, Horizon and the error log for the first hours.

**Check:** students reach v4; no errors in the log; staff can work.
**Undo:** step 8.

## Step 8. Rollback (target: under 10 minutes)

1. Point the address back to tptv3 (restore its nginx `server_name` / DNS record).
2. `php artisan up` in `/var/www/tptv3`.
3. Put v4 in maintenance (`php artisan down` in v4).
4. Post a notice; investigate on the test address.

If the server itself is broken: restore the **step 1 snapshot** (longer, about 30–60 minutes).

## Step 9. After go-live

**Ubuntu upgrade** (a quiet month, never near registration or results):

1. New snapshot.
2. `do-release-upgrade` 20.04 → 22.04; check PHP 8.4, MySQL, nginx, Redis, Supervisor, v4.
3. Again 22.04 → 24.04; same checks.
4. About 1–2 hours of downtime at night; notice on the landing page.

**Undo:** restore the snapshot taken just before.

**Cleanup of tptv3 uploads** (about 40 GB):

1. Back up all tptv3 uploads to Spaces.
2. Shrink oversized photos or archive old school years to Spaces.
3. Delete only what the office approves, in writing.
4. Retire tptv3 (read-only archive or removed) once the office agrees.

**Check:** free disk goes from about 44 GB to about 80 GB; old records still reachable in the archive.
**Undo:** restore from the Spaces backup.
