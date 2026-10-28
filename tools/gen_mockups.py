"""Build the SKSU TPT v4 mockups: one linked HTML page per screen, with every UI state.

Run:  python tools/gen_mockups.py
Writes into mockups/ (style from tools/base.css, logo from tools/sksu-seal.png).
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mockups"
TOOLS = ROOT / "tools"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700'
         '&family=Geist+Mono:wght@500;600;700&family=Lexend:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">')

PAGES = {}  # path -> html


# ---------------------------------------------------------------- building blocks
def doc(path, title, body, cls="", states=None):
    depth = path.count("/")
    up = "../" * depth
    bar = ""
    if states:
        links = "".join(f'<a href="#{i}">{label}</a>' for i, label in states)
        bar = f'<div class="states"><b>States on this page:</b>{links}<a href="#">Reset</a></div>'
    body = body.replace("{UP}", up)
    PAGES[path] = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · SKSU TPT</title>
{FONTS}
<link rel="stylesheet" href="{up}assets/style.css">
<script>if (window.self !== window.top) document.documentElement.classList.add("framed");</script>
</head>
<body{f' class="{cls}"' if cls else ''}>
{bar}
{body}
</body>
</html>
"""


def modal(mid, kind, icon, title, text, acts):
    return (f'<div class="modal" id="{mid}"><a class="scrim" href="#" aria-label="Close"></a>'
            f'<div class="dialog" role="dialog" aria-labelledby="{mid}-t"><div class="ico {kind}">{icon}</div>'
            f'<h3 id="{mid}-t">{title}</h3>{text}<div class="acts">{acts}</div></div></div>')


def toast(tid, kind, icon, title, text):
    return (f'<div class="toast" id="{tid}" role="status"><div class="ico {kind}" style="width:28px;height:28px;'
            f'border-radius:99px;display:flex;align-items:center;justify-content:center;flex-shrink:0">{icon}</div>'
            f'<div><b>{title}</b><span class="muted">{text}</span></div><a class="x" href="#" aria-label="Dismiss">×</a></div>')


def B(kind, text):
    return f'<span class="b {kind}">{text}</span>'


def table(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def two(a, b):
    return f'{a}<span class="sub">{b}</span>'


def btn(label, href="#", kind=""):
    return f'<a class="btn {kind}" href="{href}">{label}</a>'


def _ico(path):
    return f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>'


OK = _ico('<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>')
BAD = _ico('<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>')
WARN = _ico('<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17.5v.01"/>')
INFO = _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.01"/>')
PENDING = _ico('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>')
BELL = _ico('<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>')
EMPTY_ICONS = {"list": _ico('<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>'), "inbox": _ico('<path d="M3 13l3-8h12l3 8v6H3z"/><path d="M3 13h5l1 3h6l1-3h5"/>'),
               "search": _ico('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>'), "file": _ico('<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4"/>'), "bell": BELL}


def empty(kind, title, line, action=""):
    return f'<div class="empty"><span class="eico">{EMPTY_ICONS[kind]}</span><b class="ink">{title}</b><span>{line}</span>{action}</div>'


def skel_table(rows=7, cols=5):
    widths = [70, 85, 55, 40, 65, 50]
    head = "".join('<span class="skel" style="width:60%"></span>' for _ in range(cols))
    body = "".join('<div class="sr">' + "".join(f'<span class="skel" style="width:{widths[c % 6]}%"></span>' for c in range(cols)) + "</div>" for _ in range(rows))
    return f'<div class="skt"><div class="sr sh">{head}</div>{body}</div>'


def inmain(iid, html):
    """A whole-page state (skeleton or empty) shown in place of the page body."""
    return f'<div class="inmain" id="{iid}"><a href="#" class="x" aria-label="Back to the page">×</a>{html}</div>'


# ---------------------------------------------------------------- public pages
def pubnav(active=""):
    return ('<header class="pubnav"><img src="{UP}assets/sksu-seal.png" alt="SKSU seal">'
            '<div class="brandline"><b>SKSU Admission Test</b><span>Sultan Kudarat State University</span></div>'
            '<nav class="sp"><a href="landing.html">Home</a><a href="landing.html#how">How it works</a><a href="privacy.html">Privacy</a>'
            '<a class="btn primary" href="login.html">Apply / Sign in</a></nav></header>')


doc("public/landing.html", "Home", f"""<div class="pub">{pubnav()}
<section class="hero"><div style="display:flex;flex-direction:column;gap:18px">
<div class="wm lg"><b>Sultan Kudarat</b><span>State University</span></div><span class="b ok" style="align-self:flex-start">Season 2027 registration is open</span>
<h1>Take the SKSU Admission Test, all from your phone.</h1>
<p class="muted">Apply, pay the exam fee, choose your exam day and get your permit. No lines, no paper forms.</p>
<div style="display:flex;gap:10px"><a class="btn primary lg" href="login.html">Start my application</a><a class="btn lg" href="#how">How it works</a></div>
<small class="muted">Already applied? <a href="login.html">Sign in</a> to see your status, permit or result.</small></div>
<img src="{{UP}}assets/sksu-seal.png" alt="" style="width:260px;height:260px;opacity:.95"></section>
<section id="how" class="road"><h2>How it works</h2>
<ol class="tline">
<li class="now"><i>1</i><b>Apply</b><span>Details, school, 3 programs</span><em>Jan 1 – Feb 28 · open now</em></li>
<li><i>2</i><b>Pay</b><span>Cashier, GCash or Landbank</span><em>Before Feb 28</em></li>
<li><i>3</i><b>Pick your exam day</b><span>Choose your campus and date; we give you a room and seat</span><em>After approval</em></li>
<li><i>4</i><b>Take the test</b><span>Show your permit QR at the door</span><em>Mar 14 – 15</em></li>
<li><i>5</i><b>See your result</b><span>Scores and the programs you qualify for</span><em>Apr 20, 9:00 AM</em></li>
</ol>
<p class="muted">Registration is open and closes Feb 28. Tests are held at 7 SKSU campuses · <a href="#centers">See test centers</a></p></section>
<div class="modal" id="centers"><a class="scrim" href="#"></a><div class="dialog" role="dialog"><h3>Test centers</h3><ul class="centers"><li><b>ACCESS Campus</b><span>EJC Montilla, Tacurong City</span></li><li><b>Isulan Campus</b><span>Kalawag II, Isulan</span></li><li><b>Tacurong Campus</b><span>Tacurong City</span></li><li><b>Kalamansig Campus</b><span>Kalamansig</span></li><li><b>Bagumbayan Campus</b><span>Bagumbayan</span></li><li><b>Palimbang Campus</b><span>Palimbang</span></li><li><b>Lutayan Campus</b><span>Lutayan</span></li></ul><div class="acts"><a class="btn" href="#">Close</a></div></div></div>
<footer class="muted" style="padding:24px 32px;border-top:1px solid var(--line);display:flex;gap:16px"><span>© Sultan Kudarat State University</span><a href="privacy.html">Privacy and terms</a><a href="staff-login.html" style="margin-left:auto">Staff sign-in</a></footer></div>""")

doc("public/login.html", "Sign in", f"""<div class="pub">{pubnav()}
<div class="auth"><div class="authcard">
<img src="{{UP}}assets/sksu-seal.png" alt="" style="width:56px;height:56px;align-self:center">
<h1 style="text-align:center;font-size:22px">Sign in to apply</h1>
<p class="muted" style="margin:0;text-align:center">Use the Google account you check most. Your result and permit will be linked to it.</p>
<a class="gbtn" href="#loading"><span style="font-weight:700;color:#4285f4">G</span>Continue with Google</a>
<div class="muted" style="text-align:center;font-size:13px">No Google account? <a href="#magic">Get a sign-in link by email</a></div>
<div id="error-box"></div>
<small class="muted" style="text-align:center">By continuing you agree to the <a href="privacy.html">privacy notice</a>.</small>
<a href="../applicant/home.html" class="btn">Mockup: continue as a signed-in applicant →</a>
</div></div></div>
{modal("loading", "info", '<span class="spin"></span>', "Signing you in…", '<p class="muted" style="margin:0">Waiting for Google. Keep this tab open.</p>', btn("Cancel", "#"))}
{modal("magic", "info", "@", "Get a sign-in link", '<div class="fld"><label for="em">Email</label><input id="em" value="maria.delacruz@yahoo.com"></div>', btn("Cancel", "#") + btn("Send link", "#sent", "primary"))}
{toast("sent", "ok", OK, "Link sent", "Check maria.delacruz@yahoo.com. The link works for 15 minutes.")}
{modal("google-error", "bad", BAD, "Google sign-in didn’t finish", '<p class="muted" style="margin:0">The sign-in window was closed or timed out. Nothing was saved. Try again.</p>', btn("Try again", "#loading", "primary"))}
{modal("closed", "warn", WARN, "Registration is closed", '<p class="muted" style="margin:0">Season 2027 registration ended Feb 28. You can still sign in to see your permit or result.</p>', btn("OK", "#"))}""",
    states=[("loading", "Loading"), ("magic", "Email link dialog"), ("sent", "Success toast"), ("google-error", "Error"), ("closed", "Season closed")])

doc("public/staff-login.html", "Staff sign-in", f"""<div class="pub">{pubnav()}
<div class="auth"><div class="authcard">
<h1 style="font-size:22px">Staff sign-in</h1><p class="muted" style="margin:0">For admission, cashier, testing center and proctor staff. Accounts are by invite only.</p>
<a class="gbtn" href="../admin/dashboard.html"><span style="font-weight:700;color:#4285f4">G</span>Continue with Google (sksu.edu.ph)</a>
<div class="fld"><label for="se">Or email</label><input id="se" value="cashier1@sksu.edu.ph"></div>
<a class="btn primary lg" href="#sent">Email me a sign-in link</a>
<a href="../proctor/rooms.html" class="muted" style="font-size:13px">Mockup: open as a proctor →</a>
</div></div></div>
{toast("sent", "ok", OK, "Sign-in link sent", "Open it on this device within 15 minutes.")}
{modal("not-staff", "bad", BAD, "This account isn’t staff", '<p class="muted" style="margin:0">maria.delacruz@gmail.com has no staff role. Ask the admission office for an invite.</p>', btn("OK", "#"))}
{modal("expired", "warn", WARN, "That link has expired", '<p class="muted" style="margin:0">Sign-in links last 15 minutes. Send a new one.</p>', btn("Send a new link", "#sent", "primary"))}""",
    states=[("sent", "Link sent"), ("not-staff", "Not staff"), ("expired", "Expired link")])

doc("public/verify.html", "Verify a permit", f"""<div class="pub">{pubnav()}
<div class="auth"><div class="authcard">
<span class="b ok" style="align-self:flex-start">Valid permit</span>
<h1 style="font-size:22px">Examinee no. <span class="mono">500214</span></h1>
<div class="kv"><span>Name</span><span class="ink">Maria S. Dela Cruz</span><span>Session</span><span>Isulan · Sat, Mar 14</span><span>Room and seat</span><span>Room 4 · seat 27</span><span>Checked</span><span>Oct 28, 2026 10:42 AM</span></div>
<small class="muted">This page opens from the permit QR. It shows only what a proctor needs, never the address or phone.</small>
</div></div></div>
{modal("invalid", "bad", BAD, "Permit not valid", '<p class="muted" style="margin:0">This QR was changed or the permit was cancelled. Send the examinee to the help desk.</p>', btn("OK", "#"))}""",
    states=[("invalid", "Invalid or tampered QR")])

doc("public/privacy.html", "Privacy and terms", f"""<div class="pub">{pubnav()}
<div class="idx" style="max-width:760px"><h1>Privacy and terms</h1>
<p>We collect your name, birth date, contact details, school, program choices, payment receipt and photo to run the admission test. Only admission staff can see them.</p>
<p>Your results are shown only to you and the admission office. We keep application data for [RETENTION PERIOD] and then delete it.</p>
<p>Questions: [ADMISSION OFFICE EMAIL]. This follows the Data Privacy Act of 2012 (RA 10173).</p></div></div>""")

doc("public/error.html", "Error pages", f"""<div class="pub">{pubnav()}
<div class="auth" style="flex-direction:column;gap:16px">
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:var(--green)">404</span><h1 style="font-size:20px">We can’t find that page</h1><a class="btn primary" href="landing.html">Go home</a></div>
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:#d97706">503</span><h1 style="font-size:20px">Many people are on the site right now</h1><p class="muted" style="margin:0">You’re in line. This page refreshes by itself in 20 seconds.</p><span class="spin"></span></div>
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:#dc2626">500</span><h1 style="font-size:20px">Something broke on our side</h1><p class="muted" style="margin:0">It has been reported. Your saved answers are safe. Error code <span class="mono">E-7F3A</span>.</p><a class="btn" href="landing.html">Try again</a></div>
</div></div>""")


# ---------------------------------------------------------------- applicant pages
FLOW = [("notifications", "Notifications"), ("home", "Home"), ("apply-personal", "About you"), ("apply-school", "School"), ("apply-programs", "Programs"),
        ("apply-review", "Review"), ("payment", "Payment"), ("payment-waiting", "Waiting"), ("payment-rejected", "Rejected"),
        ("seat", "Pick a seat"), ("permit", "Permit"), ("result-pending", "Result not yet"), ("survey", "Survey"),
        ("result", "Result"), ("profile", "My account")]
DOTS = {"notifications": 0, "home": 0, "apply-personal": 1, "apply-school": 1, "apply-programs": 1, "apply-review": 1, "payment": 2,
        "payment-waiting": 2, "payment-rejected": 2, "seat": 3, "permit": 4, "result-pending": 4, "survey": 4, "result": 4, "profile": 0}


TAB_OF = {"home": "home", "notifications": "alerts", "seat": "schedule", "permit": "permit", "profile": "me"}
TABS = [("home", "Home", "home.html", '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>'),
        ("schedule", "Schedule", "seat.html", '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
        ("permit", "Permit", "permit.html", '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9h6M7 13h4M15 12h3v3h-3z"/>'),
        ("alerts", "Alerts", "notifications.html", '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>'),
        ("me", "Me", "profile.html", '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>')]
STATUS_BAR = ('<div class="sbar"><b>9:41</b><span><svg width="17" height="11" viewBox="0 0 17 11" aria-hidden="true"><rect x="0" y="7" width="3" height="4" rx="1"/><rect x="4.5" y="5" width="3" height="6" rx="1"/><rect x="9" y="2.5" width="3" height="8.5" rx="1"/><rect x="13.5" y="0" width="3" height="11" rx="1"/></svg>'
              '<svg width="25" height="12" viewBox="0 0 25 12" aria-hidden="true"><rect x=".5" y=".5" width="21" height="11" rx="3" fill="none" stroke="currentColor"/><rect x="2" y="2" width="15" height="8" rx="1.5"/><rect x="23" y="4" width="1.5" height="4" rx=".75"/></svg></span></div>')


TAB_PAGES = {"home", "notifications", "seat", "permit", "profile", "result", "result-pending"}


def phone(key, title, content, cta=None, back=None, extra="", overlays="", states=None, eyebrow=""):
    """An applicant screen drawn as a native app (euphoria app 2.0 pattern, SKSU light theme):
    status bar, slim nav, big title, scrolling body; tab pages get a floating tab bar, task pages a sticky action."""
    n = DOTS[key]
    in_flow = key.startswith(("apply", "payment"))
    crumbs = " · ".join(f'<a href="{k}.html">{t}</a>' if k != key else f"<b>{t}</b>" for k, t in FLOW)
    left = f'<a class="hbtn" href="{back}" aria-label="Back"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></a>' if back else '<img src="../assets/sksu-seal.png" alt="SKSU seal">'
    dots = '<div class="dots">' + "".join(f'<span class="{"now" if j == n else ("done" if j < n else "")}"></span>' for j in range(5)) + "</div>" if in_flow else ""
    head = "" if 'class="gh' in content else f'<h1 class="gh">{title}</h1>'
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    action = (f'<a class="go" href="{cta[0]}">{cta[1]}</a>' if cta else "") + extra
    tabbed = key in TAB_PAGES
    on = TAB_OF.get(key, "home")
    tabs = "".join(f'<a href="{h}" class="{"on" if t == on else ""}"><svg viewBox="0 0 24 24" aria-hidden="true">{ico}</svg><span>{label}</span>{"<i>2</i>" if t == "alerts" else ""}</a>' for t, label, h, ico in TABS)
    body = f"""<div class="crumbs"><a href="../index.html">All pages</a> | {crumbs}</div>
<div class="phone app{' tabbed' if tabbed else ''}">{STATUS_BAR}
<header class="apph">{left}{dots}<a href="notifications.html" class="hbtn bell" aria-label="Notifications, 2 unread">{BELL}<i>2</i></a></header>
<div class="appb">{eb}{head}{content}{f'<div class="inline-cta">{action}</div>' if tabbed and action else ''}</div>
{f'<div class="appcta">{action}</div>' if action and not tabbed else ''}
{f'<nav class="tabbar">{tabs}</nav>' if tabbed else ''}
</div>{overlays}"""
    doc(f"applicant/{key}.html", title, body, "phone-page", states)


def intro(key, title, content, cta, alt="", dark=False):
    """Splash and welcome screens: no nav, big type, one action."""
    doc(f"applicant/{key}.html", title, f"""<div class="crumbs"><a href="../index.html">All pages</a> | <a href="splash.html">Splash</a> · <a href="welcome-1.html">Welcome 1</a> · <a href="welcome-2.html">2</a> · <a href="welcome-3.html">3</a> · <a href="../public/login.html">Sign in</a></div>
<div class="phone app intro{' dark' if dark else ''}">{STATUS_BAR}<div class="introb">{content}</div>{f'<div class="appcta">{cta}{alt}</div>' if cta else ''}</div>""", "phone-page")


SAVED = toast("saved", "ok", OK, "Saved", "Your answers are saved. You can close this and come back.")
OFFLINE = toast("offline", "warn", WARN, "You’re offline", "We’ll keep what you type and save it when you’re back online.")

NOTE_ICON = {"ok": OK, "info": INFO, "bad": BAD, "warn": WARN}
intro("splash", "Splash", """<div class="splash"><img src="../assets/sksu-seal.png" alt="SKSU seal"><div class="wm lg"><b>Sultan Kudarat</b><span>State University</span></div><p>Admission Test</p><div class="load"><span></span></div><small>Getting things ready…</small></div>""", "", dark=True)
for i, (eb, big, line) in enumerate([("SKSU Admission Test", "Your college<br>starts here.", "Apply, pay, pick your exam day and see your result, all on your phone."),
                                     ("No lines", "Pay, then pick<br>your day.", "Pay at the cashier or by GCash. Then choose your campus and date; we give you a room and seat."),
                                     ("Exam day", "One QR,<br>right room.", "Show your permit at the door. It works even without signal.")], 1):
    nxt = f"welcome-{i + 1}.html" if i < 3 else "../public/login.html"
    pages_dots = "".join(f'<span class="{"now" if j == i else ""}"></span>' for j in range(1, 4))
    intro(f"welcome-{i}", f"Welcome {i} of 3", f"""<a class="skip" href="../public/login.html">Skip</a><div class="hero-ph" style="background-position:{['30% 50%', '60% 40%', '85% 30%'][i - 1]}"></div>
<p class="eyebrow">{eb}</p><h1 class="big">{big}</h1><p class="lead">{line}</p><div class="pdots">{pages_dots}</div>""",
          f'<a class="go" href="{nxt}">{"Get started" if i == 3 else "Next"}</a>', '<div class="alt"><a href="../public/login.html">I already applied</a><a href="../public/landing.html">Look around first</a></div>' if i == 3 else "")

phone("notifications", "Notifications", """<h1 class="gh">Notifications</h1>
<div class="notes">""" + "".join(f'<a class="note{" unread" if u else ""}" href="{h}"><span class="ni {k}">{NOTE_ICON[k]}</span><span><b>{t}</b><span>{d}</span><small>{w}</small></span></a>' for t, d, w, k, u, h in [('Your TPT 2027 result is out', 'You qualify for all 3 of your choices. Tap to see your scores.', 'Apr 20 · 9:00 AM', 'ok', True, 'result.html'), ('Seat booked', 'Isulan · Sat, Mar 14 · Room 4, seat 27. Your permit is ready.', 'Jan 13 · 9:42 AM', 'ok', True, 'permit.html'), ('Payment approved', 'Your examinee number is 500214. Pick your exam seat now.', 'Jan 12 · 4:30 PM', 'ok', True, 'seat.html'), ('Receipt received', 'We’re checking it. Usually within one working day.', 'Jan 12 · 8:10 AM', 'info', False, 'payment-waiting.html'), ('Application submitted', 'Next: pay the exam fee and send your receipt.', 'Jan 11 · 7:55 PM', 'info', False, 'payment.html'), ('Welcome to the SKSU Admission Test', 'Your account is ready. Start your application any time before Feb 28.', 'Jan 11 · 7:31 PM', 'info', False, 'home.html')]) + """</div>
<small class="center" style="color:#757575">You also get these by email. Texts are on for exam-day reminders.</small>""",
      cta=("#prefs", "Notification settings"), back="home.html",
      overlays=modal("prefs", "info", "", "How should we reach you?", '<label class="check"><input type="checkbox" checked disabled>Email · maria.delacruz@gmail.com (always on)</label><label class="check"><input type="checkbox" checked>Text messages to 0917 123 4567</label><div class="fld"><label class="cap" for="lang">Language</label><select id="lang"><option>English</option><option>Filipino</option></select></div><small style="color:#757575">Approval, schedule changes, exam-day reminders and results are always sent.</small>', '<a class="go" href="#prefs-ok">Save</a><a class="back" href="#">Cancel</a>')
      + toast("prefs-ok", "ok", OK, "Saved", "We’ll text you as well as email.")
      + '<div class="modal" id="empty"><a class="scrim" href="#"></a><div class="dialog">' + empty("bell", "No notifications yet", "We’ll tell you here, by email and by text when something changes.") + '</div></div>',
      states=[("prefs", "Preferences"), ("prefs-ok", "Saved"), ("empty", "Empty")])

phone("home", "Home", """<h1 class="gh center">Welcome, Maria!</h1><p class="lead center">Four steps to exam day. We save as you go.</p>
<div class="lb">
<div class="st"><span class="n on">1</span><div>Fill in your application<small>About 10 minutes</small></div></div>
<div class="st"><span class="n">2</span><div>Pay and send your receipt<small>GCash or bank, then a photo</small></div></div>
<div class="st"><span class="n">3</span><div>Pick your exam seat<small>After we approve your payment</small></div></div>
<div class="st"><span class="n">4</span><div>Show your permit<small>On your phone or printed</small></div></div></div>
<div class="alertbox info">Round 1 registration closes <b>Feb 28</b>. Rounds 2 and 3 are on Apr 25 and May 30.</div>""",
      cta=("apply-personal.html", "Let’s start"),
      overlays=modal("closed", "warn", WARN, "Registration is closed", '<p style="margin:0;color:#545454">Season 2027 registration ended. If you already paid, you can still pick a seat.</p>', btn("OK", "#")) + OFFLINE,
      states=[("closed", "Season closed"), ("offline", "Offline")])

phone("apply-personal", "About you", """<h1 class="gh">About you</h1><span class="cap">Step 1 of 3</span>
<div class="fld"><label class="cap" for="n">Full name</label><input id="n" value="Maria Santos Dela Cruz"></div>
<div class="two"><div class="fld err"><label class="cap" for="d">Birth date</label><input id="d" value="May 12, 2018"><span class="errmsg">You must be at least 15. Check the year.</span><small class="hint">As on your birth certificate, e.g. May 12, 2008.</small></div>
<div class="fld"><label class="cap" for="s">Sex</label><select id="s"><option>Female</option><option>Male</option></select></div></div>
<div class="fld"><label class="cap" for="p">Mobile number</label><input id="p" value="0917 123 4567"></div>
<div class="fld"><label class="cap" for="a">Home address</label><input id="a" value="Brgy. Kalawag II, Isulan, Sultan Kudarat"></div>
<span class="cap">2×2 photo</span>
<div style="border:2px dashed #d5eaf0;border-radius:18px;padding:14px;display:flex;gap:14px;align-items:center"><div style="width:56px;height:56px;border-radius:12px;background:#eef7fa"></div>
<div style="flex:1;display:flex;flex-direction:column;gap:6px"><b style="font-weight:600">photo.jpg · uploading 64%</b><div class="progress"><span style="width:64%"></span></div><small style="color:#757575">Shrinking 3.9 MB to about 250 KB on your phone</small></div></div>""",
      cta=("apply-school.html", "Next: school"), back="home.html",
      overlays=SAVED + OFFLINE + modal("photo-bad", "bad", BAD, "That photo won’t work", '<p style="margin:0;color:#545454">We couldn’t find a face, or it’s too dark. Use a plain background and good light.</p>', '<a class="go" href="#">Choose another photo</a>')
      + toast("upload-failed", "bad", BAD, "Upload failed", "The signal dropped at 64%. Tap the photo to try again."),
      states=[("saved", "Autosaved"), ("photo-bad", "Photo rejected"), ("upload-failed", "Upload failed"), ("offline", "Offline")])

phone("apply-school", "School", """<h1 class="gh">Your school</h1><span class="cap">Step 2 of 3</span>
<div class="fld"><label class="cap" for="t">I am a</label><select id="t"><option>Senior high graduate (Freshman)</option><option>Transferee</option><option>ALS passer</option></select></div>
<div class="fld"><label class="cap" for="h">Senior high school</label><input id="h" value="Isulan National High School"></div>
<div class="two"><div class="fld"><label class="cap" for="y">Year graduated</label><input id="y" value="2026"></div><div class="fld"><label class="cap" for="g">GWA</label><input id="g" value="91.4"></div></div>
<div class="fld"><label class="cap" for="st">Strand</label><select id="st"><option>STEM</option><option>ABM</option><option>HUMSS</option><option>TVL</option></select></div>
<span class="cap">Documents</span>
<div class="lb" style="gap:10px"><div class="choice" style="border:0;padding:0"><b>✓</b><div><b style="font:600 15px var(--round);color:#212121">Form 138 (report card)</b><small>form138.jpg · 410 KB</small></div></div>
<div class="choice" style="border:0;padding:0"><b style="color:#757575">+</b><div><b style="font:600 15px var(--round);color:#212121">Valid ID</b><small>School ID, PhilSys or passport · photo of the front</small></div></div></div>
<div class="fld err"><label class="cap" for="aw">Honors (optional)</label><input id="aw" value="With High Honors, Best in Research, Most Outstanding Student Leader, Division Science Quiz Bee 1st place, Regional…"><span class="errmsg">Keep it under 200 characters (you have 236).</span></div>""",
      cta=("apply-programs.html", "Next: programs"), back="apply-personal.html", overlays=SAVED, states=[("saved", "Autosaved")])

phone("apply-programs", "Programs", """<h1 class="gh">Pick 3 programs</h1><span class="cap">Step 3 of 3 · in order of preference</span>
<div class="lb" style="gap:0;padding:4px 14px">
<div class="choice"><b>1</b><div><b style="font:600 15px var(--round);color:#212121">BS Civil Engineering</b><small>Isulan Campus</small></div></div>
<div class="choice"><b>2</b><div><b style="font:600 15px var(--round);color:#212121">BS Information Technology</b><small>ACCESS Campus, Tacurong</small></div></div>
<div style="padding:12px 0"><a href="#picker" style="color:var(--blue-btn);font-weight:600">+ Add your 3rd choice</a></div></div>
<div class="alertbox warn">Add a 3rd choice so you have a fallback if your first two fill up.</div>""",
      cta=("apply-review.html", "Review my application"), back="apply-school.html",
      overlays=modal("picker", "info", "+", "Choose a program", '<div class="fld"><label for="cm">Campus</label><select id="cm"><option>Isulan</option><option>ACCESS, Tacurong</option><option>Tacurong</option><option>Kalamansig</option><option>Bagumbayan</option><option>Palimbang</option><option>Lutayan</option></select></div><div class="fld"><label for="pg">Program</label><select id="pg"><option>BS Criminology</option><option>BS Nursing</option><option>BS Agriculture</option></select></div>', '<a class="go" href="#">Add as 3rd choice</a><a class="back" href="#">Cancel</a>')
      + toast("dup", "bad", BAD, "Already picked", "BS Civil Engineering in Isulan is already your 1st choice."),
      states=[("picker", "Program picker dialog"), ("dup", "Duplicate choice error")])

phone("apply-review", "Review", """<h1 class="gh">Check and submit</h1>
<div class="lb"><div class="head"><b style="font-weight:600">About you</b><a href="apply-personal.html">Edit</a></div><span style="color:#545454">Maria Santos Dela Cruz · May 12, 2008 · Female · 0917 123 4567</span></div>
<div class="lb"><div class="head"><b style="font-weight:600">School</b><a href="apply-school.html">Edit</a></div><span style="color:#545454">Isulan National High School · 2026 · STEM · GWA 91.4</span></div>
<div class="lb"><div class="head"><b style="font-weight:600">Programs</b><a href="apply-programs.html">Edit</a></div><span style="color:#545454">1 BS Civil Engineering (Isulan) · 2 BS IT (ACCESS) · 3 BS Criminology (Isulan)</span></div>
<label style="display:flex;gap:10px;font-size:14px;color:#545454"><input type="checkbox" checked style="width:20px;height:20px">Everything is true and I agree to the privacy notice.</label>""",
      cta=("#confirm", "Submit application"), back="apply-programs.html",
      overlays=modal("confirm", "warn", WARN, "Submit your application?", '<p style="margin:0;color:#545454">After this you can still change your program choices until Feb 28, but not your name or birth date.</p>', '<a class="go" href="#submitting">Yes, submit</a><a class="back" href="#">Not yet</a>')
      + modal("submitting", "info", '<span class="spin"></span>', "Submitting…", '<p style="margin:0;color:#545454">Don’t close this page.</p>', '<a class="go" href="payment.html#submitted">Mockup: finish →</a>')
      + toast("missing", "bad", BAD, "2 things are missing", "Add your mobile number and your 3rd program choice."),
      states=[("confirm", "Confirm dialog"), ("submitting", "Submitting"), ("missing", "Validation error")])

phone("payment", "Payment", """<h1 class="gh">Pay the exam fee</h1>
<span class="cap">How will you pay?</span>
<div class="paym"><a class="ses on" href="#"><span class="h">GCash or Maya<em>Instant check</em></span><span style="color:#545454">Pay, then add the reference and a screenshot</span></a>
<a class="ses" href="#cashier"><span class="h">At an SKSU cashier<em>No upload</em></span><span style="color:#545454">Show your code; the cashier records it</span></a>
<a class="ses" href="#"><span class="h">Landbank (LinkBiz or deposit)<em>1 working day</em></span><span style="color:#545454">Add the transaction no. and the slip photo</span></a></div>
<div class="lb" style="align-items:center;gap:4px"><span class="cap">To pay</span><span class="big">[EXAM FEE]</span><span style="color:#545454">to [GCASH OR BANK ACCOUNT]</span></div>
<ol class="howto"><li>Open GCash › Send money and pay the exact amount.</li><li>Copy the 13-digit reference number from the receipt.</li><li>Screenshot the receipt and add it below.</li></ol>
<div class="fld"><label class="cap" for="r">Reference number</label><input id="r" value="1009 284 551 203" style="font:600 17px var(--mono)"></div>
<div style="border:2px dashed #d5eaf0;border-radius:18px;padding:14px;display:flex;gap:14px;align-items:center"><div style="width:52px;height:64px;border-radius:10px;background:#eef7fa"></div><div><b style="font-weight:600">Receipt photo added</b><small style="display:block;color:#23873b">Made smaller: 4.8 MB to 310 KB</small><small style="color:#757575">Tap to change</small></div></div>""",
      cta=("payment-waiting.html#sent", "Send for checking"), back="apply-review.html",
      overlays=toast("submitted", "ok", OK, "Application submitted", "Next, pay the exam fee and send your receipt.")
      + modal("cashier", "info", "", "Pay at an SKSU cashier", '<div class="lb" style="align-items:center;gap:6px"><span class="cap">Show this at the cashier</span><span class="mono" style="font-size:24px;font-weight:700">APP-27-10422</span><span style="color:#545454">Maria S. Dela Cruz</span></div><small style="color:#757575">Any campus cashier, Mon–Fri 8 AM–5 PM. You’ll get an official receipt and a text when it’s recorded; nothing to upload.</small>', '<a class="go" href="#">Got it</a>')
      + toast("ref-used", "bad", BAD, "Reference already used", "This GCash reference was sent by another applicant. Check your receipt.")
      + modal("uploading", "info", '<span class="spin"></span>', "Sending your receipt… 72%", '<div class="progress"><span style="width:72%"></span></div>', '<a class="back" href="#">Cancel</a>'),
      states=[("submitted", "Arrived after submit"), ("cashier", "Pay at cashier code"), ("uploading", "Uploading"), ("ref-used", "Duplicate reference error")])

phone("payment-waiting", "Waiting for approval", """<div class="okmark" style="background:#d97706"><span class="spin" style="border-color:#fff4;border-top-color:#fff"></span></div>
<h1 class="gh center">We’re checking your receipt</h1><p class="lead center">Usually within one working day. We’ll email you either way.</p>
<div class="lb"><div class="kv" style="grid-template-columns:120px 1fr"><span>Reference</span><span class="mono">1009 284 551 203</span><span>Sent</span><span>Jan 13, 2027 · 9:14 AM</span><span>Status</span><span>""" + B("warn", "In review") + """</span></div></div>""",
      extra='<a class="mocklink" href="seat.html#approved">Mockup: payment approved →</a><a class="mocklink" href="payment-rejected.html">Mockup: payment rejected →</a>',
      overlays=toast("sent", "ok", OK, "Receipt sent", "We’ll email you when it’s checked."), states=[("sent", "Just sent")])

phone("payment-rejected", "Payment rejected", """<div class="okmark" style="background:#dc2626;color:#fff;font-size:28px;font-weight:700">!</div>
<h1 class="gh center">Please send your receipt again</h1>
<div class="alertbox bad"><div><b>Reason:</b> The receipt photo is blurry. We can’t read the reference number.<br><small>Checked by the cashier, Jan 13 · 4:22 PM</small></div></div>
<div class="fld"><label class="cap" for="r2">Reference number</label><input id="r2" value="1009 284 551 203" style="font:600 17px var(--mono)"></div>
<div class="drop">Tap to add a clearer photo of the receipt</div>""",
      cta=("payment-waiting.html#sent", "Send again"), back="home.html")

phone("seat", "Pick a seat", """<h1 class="gh center">Pick your exam day</h1><p class="lead center" style="font-size:14px">Choose a campus and date. We give you a room and seat.</p>
<div style="display:flex;gap:6px;justify-content:center"><span class="ses on" style="padding:8px 12px">Round 1 · Mar 14–15</span><span class="ses" style="padding:8px 12px">Round 2 · Apr 25</span></div>
<a class="ses on" href="#confirm"><span class="h">Isulan Campus<em>38 seats left</em></span><span style="color:#545454">Sat, Mar 14</span></a>
<a class="ses" href="#confirm"><span class="h">ACCESS, Tacurong<em>112 seats left</em></span><span style="color:#545454">Sun, Mar 15</span></a>
<div class="ses full"><span class="h">Kalamansig Campus<em>Full</em></span><span style="color:#545454">Sun, Mar 15</span></div>
<div class="lb" style="padding:12px 14px;gap:2px"><b style="font-weight:600">Report by 7:30 AM · exam starts 8:00 AM</b><small style="color:#757575">Same for every campus. The exam takes about 3 hours.</small></div><small class="center" style="color:#757575">Your seat is locked the moment you confirm. Can’t make Round 1? Pick Round 2 instead.</small>""",
      cta=("#confirm", "Confirm my seat"), back="home.html",
      overlays=toast("approved", "ok", OK, "Payment approved", "Your examinee number is 500214. Now pick a seat.")
      + modal("confirm", "info", "?", "Isulan · Sat, Mar 14?", '<p style="margin:0;color:#545454">You can change it once until Mar 1.</p>', '<a class="go" href="permit.html#booked">Yes, book this seat</a><a class="back" href="#">Pick another</a>')
      + toast("taken", "bad", BAD, "That session just filled up", "Someone took the last seat a second ago. Pick another session.")
      + modal("loading", "info", '<span class="spin"></span>', "Loading sessions…", '<div class="skel" style="width:90%"></div><div class="skel" style="width:70%"></div><div class="skel" style="width:80%"></div>', ""),
      states=[("approved", "Arrived after approval"), ("loading", "Loading"), ("confirm", "Confirm dialog"), ("taken", "Seat taken error")])

phone("permit", "My permit", """<div class="wallet"><div class="wt"><div class="wtop"><img src="../assets/sksu-seal.png" alt="SKSU seal"><small>Valid · Round 1</small></div><b class="wtitle">Exam permit</b><span>Isulan Campus · Sat, Mar 14</span></div><div class="perf"></div>
<div class="wq"><svg width="150" height="150" viewBox="0 0 7 7" role="img" aria-label="Permit QR code" shape-rendering="crispEdges"><rect width="7" height="7" fill="#fff"/><path d="M0 0h3v3H0zM4 0h3v3H4zM0 4h3v3H0zM4 4h1v1H4zM6 4h1v1H6zM5 5h1v1H5zM4 6h1v1H4zM6 6h1v1H6z" fill="#1c1f1d"/><path d="M1 1h1v1H1zM5 1h1v1H5zM1 5h1v1H1z" fill="#fff"/></svg><b class="no">500214</b><span>Maria S. Dela Cruz</span><span class="dotok">Ready to scan</span></div>
<div class="wg"><div><small>Campus</small><b>Isulan</b></div><div><small>Date</small><b>Sat, Mar 14</b></div><div><small>Report by</small><b>7:30 AM</b></div><div><small>Room · seat</small><b>4 · 27</b></div></div></div>
<div class="lb" style="gap:4px"><b style="font-weight:600">Bring</b><span style="color:#545454">This permit (phone or printed) · one valid ID · two pencils</span></div>
<small class="center" style="color:#757575">Works offline once opened. Show the QR at the door.</small>""",
      cta=("../docs/permit-pdf.html", "Save permit PDF"), extra='<a class="mocklink" href="result-pending.html">Mockup: after exam day →</a>',
      overlays=toast("booked", "ok", OK, "Seat booked", "Isulan · Room 4 · seat 27. Your permit is ready.")
      + modal("making", "info", '<span class="spin"></span>', "Making your PDF…", '<p style="margin:0;color:#545454">Takes a second. It’s saved for next time.</p>', ""),
      states=[("booked", "Arrived after booking"), ("making", "PDF loading")])

phone("result-pending", "Result not yet", """<h1 class="gh center">Results come out Apr 20</h1>
<div class="lb" style="align-items:center;text-align:center"><span class="cap">Release</span><span class="big" style="font-size:26px">Apr 20 · 9:00 AM</span><span style="color:#545454">We’ll email you. Come back here then.</span></div>
<div class="alertbox ok">You were marked <b>present</b> on Mar 14, Room 4.</div>
<div class="empty">While you wait, tell us how exam day went. It takes 1 minute and is optional.</div>""",
      cta=("survey.html", "Answer the short survey"), extra='<a class="mocklink" href="result.html">Mockup: results released →</a>',
      overlays=modal("absent", "warn", WARN, "You were marked absent", '<p style="margin:0;color:#545454">The proctor did not check you in on Mar 14. If that’s wrong, contact the admission office by Mar 21.</p>', '<a class="go" href="#">OK</a>'),
      states=[("absent", "Absent state")])

phone("survey", "Survey", """<h1 class="gh">How did it go?</h1><span class="cap">Optional · 1 minute</span>
<div class="lb"><b style="font-weight:600">Was it easy to find your room?</b><div style="display:flex;gap:8px">""" + "".join(f'<span class="ses" style="padding:10px 14px;{"border:2.5px solid var(--green-btn);background:var(--green-tint)" if i == 4 else ""}">{i}</span>' for i in range(1, 6)) + """</div></div>
<div class="lb"><b style="font-weight:600">Was the time enough?</b><div style="display:flex;gap:8px">""" + "".join(f'<span class="ses" style="padding:10px 14px;{"border:2.5px solid var(--green-btn);background:var(--green-tint)" if i == 3 else ""}">{i}</span>' for i in range(1, 6)) + """</div></div>
<div class="fld"><label class="cap" for="c">Anything else?</label><input id="c" placeholder="Optional"></div>""",
      cta=("result-pending.html#thanks", "Send"), extra='<a class="back" href="result-pending.html">Skip</a>')

subj = [("English", 612, 8), ("Science", 548, 6), ("Mathematics", 571, 7), ("Filipino", 655, 9), ("Social Studies", 530, 6), ("ESM Competency", 566, 7)]
sbars = "".join(f'<div class="subj"><div class="h"><span>{n}</span><span><b class="mono">{s}</b><span style="color:#757575"> · stanine {t}</span></span></div><div class="t"><span style="width:{round((s - 200) / 6)}%"></span></div></div>' for n, s, t in subj)
phone("result", "Result", f"""<div class="lb" style="align-items:center;gap:4px"><span class="cap">Overall standard score</span><span class="mono" style="font-size:48px;font-weight:700;color:#006b2e;line-height:1.1">584</span>
<span style="background:var(--green-btn);color:#fff;border-radius:999px;padding:4px 14px;font-weight:600;font-size:14px">Stanine 7 of 9</span>
<span class="center" style="color:#545454;margin-top:6px">Higher than about 80% of this year’s examinees. 500 is the average.</span></div>
<div class="lb" style="gap:6px"><span class="cap">You qualify for</span><b style="font-weight:600">All 3 of your choices, and 41 other programs</b><a href="#choose" style="font-weight:600">Choose the program to enrol in →</a></div><span class="cap">By subject</span>{sbars}<small style="color:#757575">The grey line marks 500. Scores run from 200 to 800.</small>""",
      cta=("../docs/result-pdf.html", "Save result PDF"), extra='<a class="go blue" href="#cutoffs">See program cut-offs</a>',
      overlays=modal("cutoffs", "info", "i", "Programs you qualify for", '<div class="kv" style="grid-template-columns:1fr auto"><span>BS Civil Engineering · Isulan</span>' + B("ok", "Qualified") + '<span>BS IT · ACCESS</span>' + B("ok", "Qualified") + '<span>BS Criminology · Isulan</span>' + B("ok", "Qualified") + '</div><p style="margin:0;color:#545454">The admission office will contact you about enrolment.</p>', '<a class="go" href="#">OK</a>')
      + modal("choose", "info", "", "Choose your program", '<a class="ses on" href="#chosen"><span class="h">BS Civil Engineering<em>Your 1st choice</em></span><span style="color:#545454">Isulan · cut-off 530 · you have 584</span></a><a class="ses" href="#chosen"><span class="h">BS Information Technology<em>2nd choice</em></span><span style="color:#545454">ACCESS · cut-off 400</span></a><small style="color:#757575">You can change this until the enrolment period starts.</small>', '<a class="go" href="#chosen">Confirm</a><a class="back" href="#">Not yet</a>')
      + toast("chosen", "ok", OK, "BS Civil Engineering chosen", "The Isulan registrar will contact you about enrolment."),
      states=[("cutoffs", "Cut-offs dialog"), ("choose", "Choose a program"), ("chosen", "Chosen")])

phone("profile", "My account", """<h1 class="gh">My account</h1>
<div class="lb"><div class="kv" style="grid-template-columns:110px 1fr"><span>Signed in as</span><span>maria.delacruz@gmail.com</span><span>Examinee no.</span><span class="mono">500214</span><span>Status</span><span>""" + B("info", "Scheduled") + """</span></div></div>
<a class="ses" href="#photo"><span class="h">Change my photo<em>Until Mar 1</em></span></a>
<a class="ses" href="apply-programs.html"><span class="h">Change program choices<em>Until Feb 28</em></span></a>
<a class="ses" href="seat.html"><span class="h">Change my seat<em>1 change left</em></span></a>
<a class="ses" href="#history"><span class="h">My history<em>6 events</em></span></a>""",
      cta=("../public/landing.html", "Sign out"), back="home.html",
      overlays=modal("photo", "info", "📷", "Change your photo", '<div class="drop">Tap to take or choose a photo</div>', '<a class="go" href="#photo-ok">Save photo</a><a class="back" href="#">Cancel</a>')
      + toast("photo-ok", "ok", OK, "Photo updated", "Your permit now shows the new photo.")
      + modal("history", "info", "i", "My history", '<div class="tl"><div><i></i><span>Jan 13 · Seat booked: Isulan, Room 4 seat 27</span></div><div><i></i><span>Jan 12 · Payment approved, no. 500214</span></div><div><i></i><span>Jan 12 · Receipt sent</span></div><div><i></i><span>Jan 11 · Application submitted</span></div></div>', '<a class="go" href="#">Close</a>'),
      states=[("photo", "Change photo dialog"), ("photo-ok", "Photo saved"), ("history", "History")])


# ---------------------------------------------------------------- documents (PDFs and emails)
QR = '<svg width="110" height="110" viewBox="0 0 7 7" role="img" aria-label="QR code" shape-rendering="crispEdges"><rect width="7" height="7" fill="#fff"/><path d="M0 0h3v3H0zM4 0h3v3H4zM0 4h3v3H0zM4 4h1v1H4zM6 4h1v1H6zM5 5h1v1H5zM4 6h1v1H4zM6 6h1v1H6z" fill="#18181b"/><path d="M1 1h1v1H1zM5 1h1v1H5zM1 5h1v1H1z" fill="#fff"/></svg>'
LETTERHEAD = '<div style="display:flex;gap:14px;align-items:center;border-bottom:3px solid var(--green);padding-bottom:14px"><img src="../assets/sksu-seal.png" alt="SKSU seal" style="width:64px;height:64px"><div><b style="font-size:18px">SULTAN KUDARAT STATE UNIVERSITY</b><div class="muted">Office of Admission · Tacurong City, Sultan Kudarat</div></div></div>'
doc("docs/permit-pdf.html", "Permit PDF", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../applicant/permit.html">Back to permit</a></div>
<div class="paper">{LETTERHEAD}<h1 style="text-align:center">EXAMINATION PERMIT · TPT 2027</h1>
<div style="display:flex;gap:24px"><div style="width:140px;height:140px;border:1px solid var(--line);display:flex;align-items:center;justify-content:center" class="muted">2×2 photo</div>
<div class="kv" style="flex:1"><span>Examinee no.</span><b class="mono" style="font-size:20px">500214</b><span>Name</span><b>DELA CRUZ, Maria Santos</b><span>Test center</span><span>Isulan Campus</span><span>Date and time</span><span>Saturday, March 14, 2027 · report by 7:30 AM, exam starts 8:00 AM</span><span>Room / seat</span><span>Room 4 · Seat 27</span></div>{QR}</div>
<div class="alertbox info">Bring this permit and one valid ID. Arrive by 7:30 AM. No phones inside the room.</div>
<div style="margin-top:auto;display:flex;justify-content:space-between" class="muted"><span>Scan the QR to verify: sksu-tpt.com/v/…</span><span>Generated Jan 13, 2027</span></div></div>""")
doc("docs/result-pdf.html", "Result PDF", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../applicant/result.html">Back to result</a></div>
<div class="paper">{LETTERHEAD}<h1 style="text-align:center">TPT 2027 · RESULT</h1>
<div class="kv"><span>Examinee no.</span><b class="mono">500214</b><span>Name</span><b>DELA CRUZ, Maria Santos</b><span>Tested</span><span>March 14, 2027 · Isulan, Room 4</span></div>
{table(["Subject", "Standard score", "Stanine", "Meaning"], [(n, f'<span class="mono">{s}</span>', t, ["", "Very low", "Low", "Below average", "Low average", "Average", "High average", "Above average", "Very high", "Outstanding"][t]) for n, s, t in subj] + [("<b>Overall</b>", '<b class="mono">584</b>', "<b>7</b>", "<b>Above average</b>")])}
<small class="muted">Scores as provided by the SKSU Testing Center.</small>
<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end"><span class="muted">Verify: sksu-tpt.com/v/…</span><div style="text-align:center"><div style="border-top:1px solid #18181b;width:220px;padding-top:4px">[DIRECTOR, TESTING CENTER]</div></div></div></div>""")
doc("docs/sms.html", "Text messages", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../admin/messages.html">Messages admin</a></div>
<div class="smsgrid">""" + "".join(f'<div class="smsw"><b>{t}</b><div class="sms">{m}</div><small class="muted">{len(m)} of 160 characters</small></div>' for t, m in [('Payment approved', 'SKSU TPT: Payment approved. Exam no. 500214. Pick your seat by Mar 1: sksu-tpt.com/seat'), ('Payment rejected', 'SKSU TPT: We couldn’t read your receipt. Please send it again: sksu-tpt.com/pay'), ('Seat booked', 'SKSU TPT: Isulan, Sat Mar 14, Room 4 seat 27. Report by 7:30AM. Permit: sksu-tpt.com/permit'), ('Schedule changed', 'SKSU TPT: Your exam moved to ACCESS, Sun Mar 15, Room 18 seat 6. New permit: sksu-tpt.com/permit'), ('Exam tomorrow', 'SKSU TPT: Exam tomorrow, Isulan Room 4. Report by 7:30AM, exam 8:00AM. Bring your permit and an ID. Be there by 7:30.'), ('Results out', 'SKSU TPT: Your TPT 2027 result is ready: sksu-tpt.com/result')]) + """</div>""")
doc("docs/email-approved.html", "Email: approved", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Your payment is approved, Maria</b><p style="margin:0">Your examinee number is <b class="mono">500214</b>. Next, pick your exam seat. Seats go fast at Isulan.</p>
<a class="btn primary lg" href="../applicant/seat.html">Pick my seat</a><small class="muted">You got this because you applied for the SKSU Admission Test 2027.</small></div></div>""")
doc("docs/email-rejected.html", "Email: rejected", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Please send your receipt again</b><div class="alertbox bad">The receipt photo is blurry. We can’t read the reference number.</div>
<p style="margin:0">Nothing is lost. Your application is saved. Send a clearer photo and we’ll check it again within one working day.</p>
<a class="btn primary lg" href="../applicant/payment-rejected.html">Send it again</a></div></div>""")
doc("docs/email-results.html", "Email: results out", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Your TPT 2027 result is ready</b><p style="margin:0">Sign in to see your scores and which programs you qualify for.</p>
<a class="btn primary lg" href="../applicant/result.html">See my result</a></div></div>""")


# ---------------------------------------------------------------- proctor pages
def pro(key, title, content, overlays="", states=None):
    doc(f"proctor/{key}.html", title, f"""<div class="crumbs"><a href="../index.html">All pages</a> | <a href="rooms.html">My rooms</a> · <a href="checkin.html">Check-in</a> · <a href="summary.html">Room summary</a></div>
<div class="pro">{STATUS_BAR}<div class="ph"><div style="display:flex;gap:10px;align-items:center"><img src="../assets/sksu-seal.png" alt="SKSU seal"><div><b class="ink" style="font-size:16px">Proctor</b><small class="muted" style="display:block">L. Cabañero · Isulan</small></div></div><span class="b warn">Offline · 3 to send</span></div>
<div class="pb">{content}</div></div>{overlays}""", "phone-page", states)


pro("rooms", "My rooms", """<h2>Today · Sat, Mar 14</h2>
<a class="ses" href="checkin.html" style="font-family:var(--sans)"><span class="h">Room 4 · Sat, Mar 14<em>50 examinees</em></span><span class="muted">Isulan, Main Building</span></a>
<a class="ses" href="checkin.html" style="font-family:var(--sans)"><span class="h">Room 4 · Sun, Mar 15<em>48 examinees</em></span><span class="muted">Isulan, Main Building</span></a>
<div class="alertbox info">The examinee list is saved on this phone, so check-in works with no signal.</div>
<a class="btn primary lg" href="#download">Download today’s lists</a>""",
    modal("download", "info", '<span class="spin"></span>', "Saving lists to this phone… 2 of 2", '<div class="progress"><span style="width:100%"></span></div>', btn("Done", "#", "primary")), [("download", "Downloading lists")])

pro("checkin", "Check-in", """<div class="k"><div><small class="muted">Present</small><b style="color:var(--ok)">31</b></div><div><small class="muted">Absent</small><b style="color:var(--bad)">2</b></div><div><small class="muted">Of</small><b class="ink">50</b></div></div>
<div class="cam"><span></span><small>Point at the permit QR</small></div>
<div class="hit"><b style="font-size:22px;color:var(--ok)">✓ Right room</b><div style="display:flex;gap:12px;align-items:center"><div style="width:56px;height:70px;border-radius:8px;background:var(--chip)"></div><div><b class="mono" style="color:var(--green-btn)">500214</b><div class="ink" style="font-size:17px;font-weight:600">Maria S. Dela Cruz</div><small class="muted">Seat 27 · check the face and ID</small></div></div></div>
<div class="pbtn"><a href="#absent" style="border:1px solid var(--line);background:var(--side);color:var(--ink)">Absent</a><a href="#present" style="background:var(--green-btn);color:#fff;font-weight:700">Present · next</a></div>
<a href="#search" class="muted" style="text-align:center;font-size:13px">No QR? Search by name or number</a>""",
    toast("present", "ok", OK, "Maria S. Dela Cruz: present", "Saved on this phone. 32 of 50.")
    + modal("wrong", "bad", BAD, "Wrong room", '<p class="muted" style="margin:0">500231 Jomar Abdullah is in <b>Room 7</b>, seat 12. Send him there.</p>', btn("OK, next", "#", "primary"))
    + modal("dupe", "warn", WARN, "Already checked in", '<p class="muted" style="margin:0">500214 was checked in at 7:41 AM. Check the ID; someone may be using a copy.</p>', btn("OK", "#", "primary"))
    + modal("absent", "warn", WARN, "Mark 500214 absent?", '<p class="muted" style="margin:0">You can undo this until you close the room.</p>', btn("Cancel", "#") + btn("Mark absent", "#", "danger"))
    + modal("search", "info", "⌕", "Find an examinee", '<input placeholder="Name or examinee no." value="dela cruz"><div class="tl"><div><i></i><span>500214 · Maria S. Dela Cruz · seat 27</span></div></div>', btn("Close", "#")),
    [("present", "Checked in"), ("wrong", "Wrong room error"), ("dupe", "Already scanned"), ("absent", "Mark absent dialog"), ("search", "Manual search")])

pro("summary", "Room summary", """<h2>Room 4 · Sat, Mar 14</h2>
<div class="k"><div><small class="muted">Present</small><b style="color:var(--ok)">47</b></div><div><small class="muted">Absent</small><b style="color:var(--bad)">3</b></div><div><small class="muted">Not scanned</small><b class="ink">0</b></div></div>
<div class="alertbox warn">3 check-ins are still on this phone. They’ll send when you have signal.</div>
<a class="btn primary lg" href="#close">Close the room</a>""",
    modal("close", "warn", WARN, "Close Room 4?", '<p class="muted" style="margin:0">After this, check-ins can only be changed by the admission office.</p>', btn("Cancel", "#") + btn("Close room", "#closed", "primary"))
    + toast("closed", "ok", OK, "Room 4 closed", "47 present, 3 absent. Sent to the admission office.")
    + toast("sync-fail", "bad", BAD, "Couldn’t send yet", "No signal. We’ll retry every minute; don’t uninstall the app."),
    [("close", "Close room dialog"), ("closed", "Closed"), ("sync-fail", "Sync error")])


# ---------------------------------------------------------------- admin pages
ICONS = {
    "dashboard": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    "applications": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>',
    "payments": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    "seasons": '<path d="M4 4h16v16H4z"/><path d="M4 9h16M9 4v16"/>',
    "sessions": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "checkin": '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2M7 12h10"/>',
    "scores": '<circle cx="12" cy="9" r="6"/><path d="M8.5 14 7 22l5-3 5 3-1.5-8"/>',
    "results": '<path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/>',
    "reports": '<path d="M3 3v18h18"/><path d="M8 17v-6M13 17V7M18 17v-4"/>',
    "exports": '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 21h16"/>',
    "campuses": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 7h1M14 7h1M9 11h1M14 11h1M10 21v-3h4v3"/>',
    "staff": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    "audit": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    "messages": '<path d="M4 5h16v11H8l-4 4z"/>',
    "cashier": '<path d="M4 7h16v12H4z"/><path d="M8 7V4h8v3M12 11v4M10 13h4"/>',
    "rooms": '<path d="M4 21V4h11v17M15 8h5v13M8 8h3M8 12h3M8 16h3"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
}
NAV = [(None, [("dashboard", "Dashboard")]),
       ("Applicants", [("applications", "Applications"), ("cashier", "Cashier counters"), ("payments", "Payment review"), ("messages", "Messages")]),
       ("Exam", [("seasons", "Seasons and rounds"), ("rooms", "Rooms"), ("sessions", "Schedule days"), ("checkin", "Check-in"), ("scores", "Scores import"), ("results", "Results")]),
       ("Insight", [("reports", "Reports"), ("exports", "Downloads")]),
       ("Setup", [("campuses", "Campuses and programs"), ("staff", "Staff and roles"), ("audit", "Activity logs")])]


ROUNDS_RE = re.compile(r'^\s*(<div class="tabsbar rounds">.*?Manage rounds</a></div>)', re.S)
HEAD_RE = re.compile(r'^\s*<div class="head"><span class="muted">(.*?)</span>(.*?)</div>', re.S)
HINT_RE = re.compile(r'^\s*<small class="hint">(.*?)</small>', re.S)


def pagehead(title, content):
    """One page template: title, one-line description and the primary action on top; then filters; then content."""
    rounds = ""
    m = ROUNDS_RE.match(content)
    if m:
        rounds, content = m.group(1), content[m.end():]
    desc, acts = "", ""
    m = HEAD_RE.match(content) or HINT_RE.match(content)
    if m:
        desc = m.group(1)
        acts = m.group(2) if m.re is HEAD_RE else ""
        content = content[m.end():]
    if "<table" in content and 'class="search"' not in content and "Dashboard" not in title:
        acts = '<input class="search" aria-label="Search this list" placeholder="Search this list">' + acts
    return (f'<div class="pagehead"><div><h1>{title}</h1>{f"<p>{desc}</p>" if desc else ""}</div><div class="pacts">{acts}</div></div>'
            f'{rounds}{content}')


def admin(key, title, content, active=None, overlays="", states=None, crumb=""):
    active = active or key
    links = []
    for group, items in NAV:
        if group:
            links.append(f'<div class="grp">{group}</div>')
        for k, label in items:
            on = ' class="on"' if k == active else ""
            count = '<span class="count">214</span>' if k == "payments" else ""
            links.append(f'<a href="{k}.html"{on}><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg>{label}{count}</a>')
    doc(f"admin/{key}.html", title, f"""<div class="strip"><strong>SKSU TPT · ADMIN MOCKUP</strong><span class="muted">sample data</span><a class="sp" href="../index.html">All pages</a></div>
<header class="top"><img src="../assets/sksu-seal.png" alt="SKSU seal"><span class="name">SKSU TPT</span><span class="muted">Admin</span>
<a class="gsearch" href="search.html">Search name, examinee no., reference<kbd>/</kbd></a><span class="pill ok">Season 2027 · Round 2 open</span><a href="account.html" class="avatar" style="text-decoration:none">A</a><div style="line-height:1.15"><div class="ink">Admission</div><small class="muted">Super admin</small></div></header>
<nav class="mtabs">{''.join(f'<a href="{k}.html"{" class=on" if k == active else ""}>{label}</a>' for _, items in NAV for k, label in items)}</nav>
<div class="shell"><nav class="side">{''.join(links)}</nav>
<main>{crumb}{pagehead(title, content)}</main></div>{overlays}""", states=states)


def line_chart(vals, labels, w=380, h=150):
    """Trend over time: area line, last point marked."""
    top = max(vals)
    xs = [round(i * (w - 20) / (len(vals) - 1)) + 10 for i in range(len(vals))]
    ys = [round(h - 24 - v / top * (h - 44)) for v in vals]
    pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    area = f"10,{h - 24} {pts} {xs[-1]},{h - 24}"
    ticks = "".join(f'<text x="{x}" y="{h - 6}" text-anchor="middle">{t}</text>' for x, t in zip(xs, labels) if t)
    return (f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Sign-ups per day, last 14 days; today {vals[-1]}">'
            f'<line x1="10" x2="{w - 10}" y1="{h - 24}" y2="{h - 24}" class="axis"/><polygon points="{area}" class="area"/><polyline points="{pts}" class="ln"/>'
            f'<circle cx="{xs[-1]}" cy="{ys[-1]}" r="4" class="pt"/><text x="{xs[-1] - 6}" y="{ys[-1] - 10}" text-anchor="end" class="val">{vals[-1]} so far today</text>{ticks}</svg>')


def hbars(rows, unit=""):
    """Compare categories: horizontal bars, sorted, value at the end."""
    top = max(v for _, _, v in rows)
    return '<div class="hbars">' + "".join(
        f'<div class="hb"><span class="l">{n}<small>{c}</small></span><span class="t"><span style="width:{round(v / top * 100)}%"></span></span><b>{v:,}{unit}</b></div>' for n, c, v in rows) + "</div>"


def funnel(stages):
    """Pipeline: each stage as a bar of the first, with the drop shown."""
    first = stages[0][1]
    out, prev = [], None
    for name, v in stages:
        drop = f'<small class="drop">−{prev - v:,}</small>' if prev else ""
        out.append(f'<div class="hb"><span class="l">{name}</span><span class="t"><span style="width:{round(v / first * 100)}%"></span></span><b>{v:,}</b>{drop}</div>')
        prev = v
    return '<div class="hbars funnel">' + "".join(out) + "</div>"


def histogram():
    """Score distribution: 50-point bins from 200 to 800, stanine bands marked."""
    counts = [227, 310, 520, 640, 1150, 1260, 1614, 1869, 1110, 1146, 561, 330]
    top = max(counts)
    w, h = 560, 190
    bw = (w - 40) / len(counts)
    bars = "".join(f'<rect x="{20 + i * bw + 2:.0f}" y="{h - 30 - c / top * (h - 50):.0f}" width="{bw - 4:.0f}" height="{c / top * (h - 50):.0f}" class="{"hi" if i == 7 else "bar"}"/>' for i, c in enumerate(counts))
    ticks = "".join(f'<text x="{20 + i * bw:.0f}" y="{h - 12}" text-anchor="middle">{200 + i * 50}</text>' for i in range(0, len(counts) + 1, 2))
    mean = 20 + 6 * bw
    return (f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Overall standard scores, 9,098 examinees, centred on 500">{bars}'
            f'<line x1="20" x2="{w - 20}" y1="{h - 30}" y2="{h - 30}" class="axis"/><line x1="{mean:.0f}" x2="{mean:.0f}" y1="14" y2="{h - 30}" class="mean"/>'
            f'<text x="{mean + 6:.0f}" y="24" class="val">500 = average</text>{ticks}</svg>')


def rounds_bar(on=1):
    rounds = [(1, "Round 1", "Mar 14–15", B("gray", "Exam done")), (2, "Round 2", "Apr 25", B("ok", "Registration open")), (3, "Round 3", "May 30", B("warn", "Draft"))]
    tabs = "".join(f'<a href="#" class="{"on" if n == on else ""}"><b>{t}</b> · {d} {b}</a>' for n, t, d, b in rounds)
    return f'<div class="tabsbar rounds"><span class="muted" style="padding:8px 12px 8px 0">Season 2027:</span>{tabs}<a href="seasons.html" style="margin-left:auto">Manage rounds</a></div>'


def drawer(did, title, sub, body, acts):
    return (f'<div class="drawer" id="{did}"><a class="scrim" href="#" aria-label="Close"></a><aside class="dr" role="dialog" aria-labelledby="{did}-t">'
            f'<header><div><h3 id="{did}-t">{title}</h3><span class="muted">{sub}</span></div><a href="#" class="x" aria-label="Close">×</a></header>'
            f'<div class="drb">{body}</div><footer>{acts}</footer></aside></div>')


def menu(mid, items):
    out = []
    for label, href, kind, hint in items:
        if label == "-":
            out.append('<hr>')
            continue
        out.append(f'<a class="{kind}" href="{href}"><span>{label}</span>{f"<small>{hint}</small>" if hint else ""}</a>')
    return f'<div class="menu" id="{mid}" role="menu">{"".join(out)}</div>'


def tip(text):
    return f'<span class="tip" tabindex="0" data-tip="{text}">?</span>'


def hint(text):
    return f'<small class="hint">{text}</small>'


def stepper(steps, cur):
    out = []
    for i, (label, href) in enumerate(steps, 1):
        cls = "done" if i < cur else ("now" if i == cur else "")
        out.append(f'<a class="stp {cls}" href="{href}"><i>{"✓" if i < cur else i}</i><span>{label}</span></a>')
    return f'<nav class="stepper" aria-label="Steps">{"".join(out)}</nav>'


ROW_MENU = menu("menu", [("Quick look", "#view", "", "Opens on the right"), ("Open full record", "applicant.html", "", ""), ("Edit details", "applicant.html#edit", "", "Name, birth date, contact"),
                         ("Move to another session", "applicant.html#move", "", ""), ("Resend permit email", "#resent", "", ""), ("Print permit", "../docs/permit-pdf.html", "", ""), ("Waive the fee", "applicant.html#waive", "", "Scholar or indigent, with a reason"), ("Refund", "applicant.html#refund", "", "Paid twice or cancelled season"),
                         ("-", "", "", ""), ("Cancel application", "applicant.html#cancel", "danger", "Frees the seat")])
ACT = '<span class="act"><a class="btn" href="#view">View</a> <a class="btn" href="#menu" aria-label="More actions">···</a></span>'
ACT1 = ACT + ROW_MENU

# dashboard
days = [612, 540, 498, 702, 1210, 880, 655, 590, 611, 720, 1302, 940, 812, 212]
dl = ["1", "", "", "", "5", "", "", "", "9", "", "", "", "13", "Now"]
bars = "".join(f'<div><span style="height:{round(v / 1302 * 120)}px"></span></div>' for v in days)
prog = [("BS Information Technology", "ACCESS", 1180), ("BS Nursing", "ACCESS", 1012), ("BS Criminology", "Isulan", 884), ("BS Civil Engineering", "Isulan", 610), ("BSEd English", "ACCESS", 522), ("BS Accountancy", "ACCESS", 498), ("BS Agriculture", "Tacurong", 341), ("BS Fisheries", "Palimbang", 88)]
pbars = "".join(f'<div><b class="ink">{k:,}</b><span style="height:{round(k / 1180 * 160)}px"></span></div>' for _, _, k in prog)
att = [("214 payments waiting", "Oldest waited 6 h. Two reviewers are online.", "payments.html"), ("Isulan Sun Mar 15 is full", "41 Isulan applicants have no seat yet.", "sessions.html"), ("Same reference used twice", "Aisah K. Mangudadatu used Maria Dela Cruz’s GCash reference.", "payments.html"), ("627 approved, no seat picked", "Send a reminder, or seat them automatically on Mar 1.", "applications.html"), ("Mail quota at 71%", "1,420 of 2,000 emails today.", "audit.html")]
admin("dashboard", "Dashboard", f"""<div class="tabs"><span class="on">Round 2</span><span>Whole season</span><span class="muted" style="margin-left:auto;font-size:13px">Updated 9:14 AM</span></div>
<div class="kpis">
<a class="kpi act" href="payments.html"><span>Payments to review</span><b>214</b><small>Oldest waited 6 h · <u>Review now</u></small></a>
<a class="kpi act" href="applications.html"><span>Approved, no seat yet</span><b>627</b><small>Seats auto-assigned Mar 1 · <u>Send reminder</u></small></a>
<a class="kpi" href="sessions.html"><span>Seats left</span><b>987</b><small>of 9,200 · Isulan Sun is full</small></a>
<a class="kpi" href="applications.html"><span>Submitted</span><b>12,287</b><small>of 16,408 signed up · 212 today</small></a></div>
<div class="panel"><div class="head"><h2>Seats · Round 2</h2><span class="muted" style="font-size:13px">9,200 total · 8,213 taken · <b class="ink">987 left</b> · 8 exam days open</span></div>
{table(['Exam day', 'Campus', 'Seats', 'Left', ''], [(d, c, f'<div class="meter"><div class="t"><span class="{cls}" style="width:{p}%"></span></div></div>', f'<b class="mono">{left}</b>', B('bad', 'Full') if left == 0 else (B('warn', 'Nearly full') if left < 60 else '')) for d, c, p, left, cls in [('Sat, Apr 25', 'ACCESS, Tacurong', 99, 12, 'hi'), ('Sat, Apr 25', 'Isulan', 100, 0, 'full'), ('Sat, Apr 25', 'Tacurong', 92, 48, 'hi'), ('Sun, Apr 26', 'ACCESS, Tacurong', 61, 470, ''), ('Sun, Apr 26', 'Kalamansig', 74, 104, '')]])}
<a href="sessions.html" style="font-size:13px">All schedule days →</a></div>
<div class="row"><div class="panel grow"><div class="head"><h2>Needs attention</h2><span class="muted" style="font-size:13px">5 items</span></div>
{''.join(f'<div class="attn"><div><b>{t}</b><span class="muted">{d}</span></div><a class="btn" href="{h}">Open</a></div>' for t, d, h in att)}</div>
<div class="panel" style="width:420px;flex-shrink:0"><div class="head"><h2>Sign-ups, last 14 days</h2><a href="reports.html" style="font-size:13px">Reports →</a></div>{line_chart(days, ["Jan 1", "", "", "", "", "", "Jan 7", "", "", "", "", "", "", "Today"])}</div></div>""",
      overlays=inmain("loading", '<div class="kpis">' + '<div class="kpi"><span class="skel" style="width:50%"></span><span class="skel" style="height:26px;width:40%;margin:6px 0"></span><span class="skel" style="width:70%"></span></div>' * 4 + '</div>' + skel_table(5, 2)),
      states=[("loading", "Loading")])

apps = [("500214", "Maria S. Dela Cruz", "maria.delacruz@gmail.com", "BS Civil Engineering", "Isulan", B("info", "Scheduled"), "Mar 14", "Room 4 · seat 27"),
        ("500215", "Jomar P. Abdullah", "jomar.abdullah@gmail.com", "BS Information Technology", "ACCESS", B("ok", "Approved"), "—", "picks a seat next"),
        ("—", "Aisah K. Mangudadatu", "aisah.m@gmail.com", "BS Nursing", "ACCESS", B("warn", "In review"), "—", ""),
        ("500223", "Ramon T. Villanueva", "ramon.v@gmail.com", "BS Agriculture", "Tacurong", B("info", "Scheduled"), "Mar 15", "Room 12 · seat 3"),
        ("—", "Lea M. Sampulna", "lea.sampulna@gmail.com", "BSEd Mathematics", "Kalamansig", B("gray", "Draft"), "—", ""),
        ("—", "Noel B. Guiamal", "noel.guiamal@gmail.com", "BS Criminology", "Isulan", B("bad", "Rejected"), "—", "ref. already used"),
        ("500198", "Princess A. Lumabao", "princess.l@gmail.com", "BS Accountancy", "ACCESS", B("info", "Scheduled"), "Mar 14", "Room 7 · seat 41"),
        ("500176", "Datu R. Mamalinta", "datu.mamalinta@gmail.com", "BS Fisheries", "Palimbang", B("vio", "Scored"), "Mar 15", "Room 1 · seat 18")]
VIEW_DRAWER = drawer("view", "Maria S. Dela Cruz", "500214 · Season 2027 · Round 1", f"""<div>{B("info", "Scheduled")}</div>
<div class="kv"><span>Email</span><span>maria.delacruz@gmail.com</span><span>Mobile</span><span>0917 123 4567</span><span>1st choice</span><span>BS Civil Engineering · Isulan</span>
<span>Payment</span><span>Approved Jan 12 by Cashier 2 · ref <span class="mono">1009284551203</span></span><span>Seat</span><span>Isulan · Sat, Mar 14 · Room 4 · seat 27</span></div>
<h4>Latest</h4><div class="tl"><div><i></i><span>Jan 13 · booked Room 4 seat 27</span></div><div><i></i><span>Jan 12 · payment approved, 500214 issued</span></div><div><i></i><span>Jan 11 · submitted the application</span></div></div>""",
                     btn("Resend permit", "#resent") + btn("Move session", "applicant.html#move") + btn("Open full record", "applicant.html", "primary"))
DUPES = drawer("dupes", "3 possible duplicates", "Same name and birth date, or same mobile number", f"""{hint("Merging keeps the older account and moves its payment and seat. Nothing is deleted; the merge is in the activity log and can be undone for 7 days.")}
<div class="dupe"><div><b>Maria S. Dela Cruz</b><span class="muted">maria.delacruz@gmail.com · signed up Jan 11 · Scheduled</span></div><div><b>Maria Santos Dela Cruz</b><span class="muted">mariadc08@yahoo.com · signed up Jan 20 · Draft</span></div><div class="acts">{btn("Not the same person")}{btn("Merge into the older one", "#merged", "primary")}</div></div>
<div class="dupe"><div><b>Jomar P. Abdullah</b><span class="muted">0917 555 0101 · Approved</span></div><div><b>Jomar Abdullah</b><span class="muted">0917 555 0101 · In review</span></div><div class="acts">{btn("Not the same person")}{btn("Merge into the older one", "#merged", "primary")}</div></div>""", btn("Close", "#"))
BULK = f"""<div class="bulkbar" id="bulk"><b>3 selected</b><a class="btn" href="#bulk-remind">Send reminder</a><a class="btn" href="sessions.html#auto">Assign seats automatically</a><a class="btn" href="exports.html#queued">Export selected</a><a class="btn" href="#">Clear</a></div>"""
admin("applications", "Applications", f"""<div class="filters"><span class="muted" style="font-size:13px">Saved views</span><a class="chip on" href="#">Everyone</a><a class="chip" href="#">Waiting payment &gt; 24 h</a><a class="chip" href="#">Approved, no seat</a><a class="chip" href="#">Isulan · Round 2</a><a class="chip add" href="#saveview">+ Save this view</a></div>
<div class="panel"><div class="filters"><span class="seg"><span class="on">All</span><span>Freshmen</span><span>Transferees</span></span>
<select aria-label="Round"><option>All rounds</option><option>Round 1</option><option>Round 2</option><option>Round 3</option></select><select aria-label="Status"><option>Any status</option></select><select aria-label="Campus"><option>Any campus</option></select>
<input class="search" aria-label="Search" placeholder="Search name, email, no. or reference"><span style="margin-left:auto;display:flex;gap:6px">{btn("Print")}{btn("Excel", "exports.html#queued")}</span></div>
{BULK}
{table(['<input type="checkbox" aria-label="Select all">', "Examinee no.", "Applicant", "1st choice", "Status", "Session", ""], [(f'<input type="checkbox" aria-label="Select {a[1]}"{" checked" if i in (1, 4, 5) else ""}>', f'<b class="mono ink">{a[0]}</b>', two(a[1], a[2]), two(a[3], a[4]), a[5], two(a[6], a[7]), ACT1 if i == 0 else ACT) for i, a in enumerate(apps)])}
<div class="head"><span class="muted">Showing 1–8 of 16,408 · <a href="#dupes">3 possible duplicates</a></span><span style="display:flex;gap:6px">{btn("Previous")}{btn("Next")}</span></div></div>""",
      overlays=VIEW_DRAWER + DUPES
      + toast("resent", "ok", OK, "Permit email sent", "To maria.delacruz@gmail.com.")
      + toast("merged", "ok", OK, "Merged", "Kept the Jan 11 account. You can undo this from the activity log for 7 days.")
      + modal("bulk-remind", "info", "✉", "Remind 3 applicants?", f'<div class="fld"><label for="bt">Template</label><select id="bt"><option>Pick your seat (reminder)</option><option>Payment still waiting</option></select></div><div class="preview">Hi Jomar, your payment is approved but you haven’t picked a seat. Seats at ACCESS are filling up. Pick yours: sksu-tpt.com/seat</div><div class="fld"><label for="bc">Send by</label><select id="bc"><option>Email and SMS</option><option>Email only</option></select>{hint("SMS costs about ₱0.50 each. 3 messages.")}</div>', btn("Cancel", "#") + btn("Send to 3", "#sent3", "primary"))
      + toast("sent3", "ok", OK, "Reminders sent", "3 emails and 3 texts. See them under Messages.")
      + modal("saveview", "info", "★", "Save this view", f'<div class="fld"><label for="sv">Name</label><input id="sv" value="Isulan · Round 2 · no seat"></div>{hint("Saved views keep your filters and columns. Only you see them unless you share.")}<label style="display:flex;gap:8px;font-size:14px"><input type="checkbox" style="height:18px;width:18px">Share with all admission staff</label>', btn("Cancel", "#") + btn("Save view", "#", "primary"))
      + inmain("empty", empty("search", "No applications match “zzz”", "Check the spelling, or search by examinee number or GCash reference.", btn("Clear search", "#")))
      + inmain("loading", '<div class="filters"><span class="skel" style="width:220px;height:34px"></span><span class="skel" style="width:120px;height:34px"></span><span class="skel" style="width:260px;height:34px"></span></div>' + skel_table(8, 6))
      + drawer("view-loading", '<span class="skel" style="width:200px;height:18px;display:block"></span>', "Loading…", '<span class="skel" style="width:30%"></span><div class="kv">' + '<span class="skel"></span><span class="skel"></span>' * 5 + '</div>', ""),
      states=[("view-loading", "Drawer loading"), ("view", "View: quick-look drawer"), ("menu", "··· menu open"), ("bulk", "Bulk bar"), ("bulk-remind", "Bulk reminder"), ("sent3", "Sent"), ("dupes", "Duplicates drawer"), ("merged", "Merged"), ("saveview", "Save view"), ("resent", "Resent"), ("loading", "Loading"), ("empty", "Empty search")])

admin("search", "Search: “dela cruz”", f"""<span class="muted">Search works from every page: press <kbd>/</kbd> and type a name, examinee number, email or GCash reference.</span>
<div class="panel"><h2>Applicants · 3</h2>{table(["", "", "", ""], [('<b class="mono ink">500214</b>', two("Maria S. Dela Cruz", "maria.delacruz@gmail.com"), B("info", "Scheduled"), btn("Open", "applicant.html")), ('<b class="mono ink">—</b>', two("Maria Santos Dela Cruz", "mariadc08@yahoo.com"), B("gray", "Draft"), btn("Open", "applicant.html")), ('<b class="mono ink">501990</b>', two("Joel R. Dela Cruz", "joeldc@gmail.com"), B("ok", "Approved"), btn("Open", "applicant.html"))])}</div>
<div class="panel"><h2>Payments · 1</h2>{table(["", "", "", ""], [('<span class="mono">1009284551203</span>', "Maria S. Dela Cruz", B("ok", "Approved"), btn("Open", "payments.html"))])}</div>""", active="applications")

admin("applicant", "Maria S. Dela Cruz", f"""<div class="tabsbar"><a class="on" href="#">Overview</a><a href="#">Application</a><a href="#">Payment</a><a href="#">Permit</a><a href="#">Result</a><a href="#">History</a></div>
<div class="row"><div class="panel grow"><h2>Application</h2><div class="kv">
<span>Status</span><span>{B("info", "Scheduled")}</span><span>Examinee no.</span><span class="mono ink">500214</span><span>Email</span><span>maria.delacruz@gmail.com</span><span>Mobile</span><span>0917 123 4567</span>
<span>Birth date</span><span>May 12, 2008 (18)</span><span>School</span><span>Isulan National High School · 2026 · STEM · GWA 91.4</span>
<span>Choices</span><span>1 BS Civil Engineering (Isulan) · 2 BS IT (ACCESS) · 3 BS Criminology (Isulan)</span><span>Session</span><span>Isulan · Sat, Mar 14 · Room 4 · seat 27</span></div>
<h2 style="margin-top:8px">Uploads</h2>
<div class="uploads"><div class="up"><div class="thumb">Photo</div><div><b>2×2 photo</b><span class="muted">photo.jpg · 248 KB · Jan 11</span>{B("ok", "Accepted")}</div>{btn("View", "#photo")}</div>
<div class="up"><div class="thumb">Receipt</div><div><b>Payment receipt</b><span class="muted">gcash-receipt.jpg · 310 KB · Jan 12</span>{B("ok", "Approved")}</div>{btn("View", "payments.html")}</div></div>
<div style="display:flex;gap:8px">{btn("Edit details", "#edit")}{btn("Move session", "#move")}{btn("View permit", "../docs/permit-pdf.html")}{btn("Cancel application", "#cancel", "danger")}</div></div>
<div class="panel" style="width:360px;flex-shrink:0"><h2>History</h2><div class="tl">
<div><i></i><span>Jan 13 9:42 AM · Maria booked Isulan, Room 4 seat 27</span></div><div><i></i><span>Jan 12 4:30 PM · Cashier 2 approved payment, issued 500214</span></div>
<div><i></i><span>Jan 12 8:10 AM · Maria sent receipt 1009 284 551 203</span></div><div><i></i><span>Jan 11 7:55 PM · Maria submitted the application</span></div><div><i></i><span>Jan 11 7:31 PM · Maria signed up with Google</span></div></div></div></div>""",
      active="applications", crumb='<a href="applications.html" class="muted">← Applications</a>',
      overlays=modal("edit", "info", "✎", "Edit details", '<div class="fld"><label for="e1">Full name</label><input id="e1" value="Maria Santos Dela Cruz"></div><div class="fld err"><label for="e2">Birth date</label><input id="e2" value="2008-13-12"><span class="errmsg">Not a real date.</span></div><div class="fld"><label for="e3">Reason (goes in the history)</label><input id="e3" value="Typo in middle name, applicant emailed"></div>', btn("Cancel", "#") + btn("Save", "#saved", "primary"))
      + toast("saved", "ok", OK, "Saved", "The change and your reason are in the history.")
      + modal("move", "info", "⇄", "Move to another session", '<select><option>ACCESS · Sun Mar 15 · 112 left</option><option>Tacurong · Sat Mar 14 · 12 left</option></select><p class="muted" style="margin:0">Maria gets an email with the new room and seat.</p>', btn("Cancel", "#") + btn("Move", "#moved", "primary"))
      + toast("moved", "ok", OK, "Moved", "ACCESS · Room 18 · seat 6. Email sent.")
      + modal("cancel", "bad", BAD, "Cancel this application?", '<p class="muted" style="margin:0">Her seat is freed and her permit stops working. She can’t take the test this season. Type CANCEL to confirm.</p><input placeholder="CANCEL">', btn("Keep it", "#") + btn("Cancel application", "#", "danger"))
      + modal("waive", "warn", WARN, "Waive Maria’s exam fee?", '<div class="fld"><label for="wv">Reason</label><select id="wv"><option>Indigent (certificate from the barangay)</option><option>Scholar (CHED or LGU)</option><option>SKSU employee dependent</option></select></div><div class="fld"><label for="wvd">Proof (optional)</label><input id="wvd" placeholder="e.g. certificate no. 2027-0193"></div>' + hint("She is approved at once and gets an examinee number. Waivers show in the Payments report."), btn("Cancel", "#") + btn("Waive fee", "#", "primary"))
      + modal("refund", "warn", WARN, "Record a refund", '<div class="fld"><label for="rf">Why</label><select id="rf"><option>Paid twice</option><option>Round cancelled</option></select></div><div class="fld"><label for="rfa">Amount</label><input id="rfa" value="[EXAM FEE]"></div>' + hint("The cashier pays it back; this keeps the books and the applicant’s status right."), btn("Cancel", "#") + btn("Record refund", "#", "primary"))
      + modal("photo", "info", "▢", "2×2 photo", '<div class="thumb" style="width:200px;height:200px;align-self:center">Photo</div><div class="fld"><label for="pr">If it’s not usable</label><select id="pr"><option>Face not clear</option><option>Not a 2×2 ID photo</option><option>Someone else</option></select></div>', btn("Close", "#") + btn("Ask for a new photo", "#asked", "danger"))
      + toast("asked", "ok", OK, "Photo request sent", "Maria gets an email and can upload a new one; her seat is kept."),
      states=[("edit", "Edit dialog with error"), ("saved", "Saved"), ("move", "Move session"), ("moved", "Moved"), ("cancel", "Danger confirm"), ("photo", "Review a photo"), ("asked", "New photo requested")])

admin("cashier", "Cashier counters", f"""<div class="head"><span class="muted">Cashiers take the exam fee in their own console. Admins can open it too.</span>{btn("Open the cashier console", "../cashier/console.html", "primary")}</div>
<div class="kpis" style="grid-template-columns:repeat(3,1fr)"><div class="kpi"><span>Recorded today</span><b>₱61,500</b><small>123 payments at 5 counters</small></div><div class="kpi"><span>Counters open</span><b>4</b><small>of 7</small></div><div class="kpi"><span>Voided today</span><b>2</b><small>by an admin, with a reason</small></div></div>
{table(["Counter", "Cashier", "Payments", "Collected", "Status", ""], [("Isulan counter 1", "Cashier 1", "36", "₱18,000", B("ok", "Open"), btn("View", "../cashier/today.html")), ("ACCESS counter 1", "Cashier 2", "52", "₱26,000", B("ok", "Open"), btn("View", "../cashier/today.html")), ("ACCESS counter 2", "Cashier 3", "21", "₱10,500", B("ok", "Open"), btn("View", "../cashier/today.html")), ("Tacurong counter 1", "Cashier 4", "14", "₱7,000", B("gray", "Closed"), btn("View", "../cashier/today.html"))])}""")

q = [("Aisah K. Mangudadatu", "1009284551203", "6 h", B("warn", "Same ref."), True), ("Lea M. Sampulna", "1009284552455", "5 h", B("gray", "Waiting"), False), ("Ramon T. Villanueva", "1009284552310", "5 h", B("gray", "Waiting"), False), ("Noel B. Guiamal", "1009284552601", "3 h", B("gray", "Waiting"), False), ("Princess A. Lumabao", "1009284552711", "2 h", B("gray", "Waiting"), False), ("Datu R. Mamalinta", "1009284552840", "40 min", B("gray", "Waiting"), False)]
admin("payments", "Payment review", f"""<div class="row">
<div class="queue"><div class="qh"><span>Waiting · oldest first</span><span class="muted" style="font-size:12px">A approve · R reject</span></div><div style="padding:8px 12px;border-bottom:1px solid var(--line)"><input class="search" style="width:100%" aria-label="Search waiting payments" placeholder="Search name or reference"></div>{''.join(f'<a href="#"{" class=on" if on else ""}><span><span class="ink">{n}</span><span class="sub mono">{r} · {a}</span></span>{b}</a>' for n, r, a, b, on in q)}</div>
<div class="panel grow"><div class="head"><h2>Proof of payment</h2><span class="muted" style="font-size:12px">gcash-receipt.jpg · 310 KB</span></div>
<div class="proof"><div class="receipt"><b style="color:var(--info)">Receipt image</b><div><span class="muted">Amount</span><b>[EXAM FEE]</b></div><div><span class="muted">Ref. no.</span><b class="mono">1009284551203</b></div><div><span class="muted">Date</span><b>Jan 13, 2027</b></div></div></div></div>
<div style="width:320px;flex-shrink:0;display:flex;flex-direction:column;gap:12px">
<div class="panel"><h2 style="font-size:18px">Aisah K. Mangudadatu</h2><span class="muted">1st: BS Nursing, ACCESS</span>
<div class="head"><span class="muted">Typed reference</span><b class="mono ink">1009284551203</b></div><div class="head"><span class="muted">Paid on</span><span class="ink">Jan 13, 2027</span></div>
<div class="note warn">Same reference as Maria S. Dela Cruz (approved Jan 12)</div></div>
{btn("Approve and issue number", "#approve", "primary lg")}
<label for="rej" class="muted" style="font-size:13px">Reject reason</label><select id="rej"><option>Reference already used</option><option>Receipt is blurry</option><option>Amount is short</option><option>Reference does not match</option></select>
{btn("Reject and email the reason", "#reject", "danger lg")}<small class="muted">Each decision goes in the activity log and opens the next one.</small></div></div>""",
      overlays=modal("approve", "warn", WARN, "Approve a reused reference?", '<p class="muted" style="margin:0">This reference was already approved for Maria S. Dela Cruz. Approve only if you checked the GCash records.</p>', btn("Cancel", "#") + btn("Approve anyway", "#approved", "primary"))
      + toast("approved", "ok", OK, "Approved · 500216 issued", "Aisah was notified in the app, by email and by text. Next: Lea M. Sampulna.")
      + modal("reject", "bad", BAD, "Reject and email Aisah?", '<p class="muted" style="margin:0">Reason sent: “Reference already used”. She can send a new receipt.</p>', btn("Cancel", "#") + btn("Reject", "#rejected", "danger"))
      + toast("rejected", "ok", OK, "Rejected · email sent", "Next: Lea M. Sampulna.")
      + toast("conflict", "bad", BAD, "Cashier 2 already decided this one", "It was approved 10 s ago. Showing the next one.")
      + inmain("empty", empty("inbox", "All caught up", "No payments are waiting. New ones appear here by themselves.", btn("Go to applications", "applications.html")))
      + inmain("loading", '<div class="row"><div class="queue">' + skel_table(8, 1) + '</div><div class="grow">' + skel_table(3, 2) + '</div></div>'),
      states=[("loading", "Loading"), ("approve", "Approve warning"), ("approved", "Approved toast"), ("reject", "Reject confirm"), ("rejected", "Rejected toast"), ("conflict", "Two reviewers conflict"), ("empty", "Empty queue")])

admin("seasons", "Seasons and rounds", f"""<div class="head"><span class="muted">A season is a school year. Each season has one or more exam rounds, each with its own registration, exam days, seats, scores and release. Nothing is tied to a year in the code.</span>{btn("New season", "setup-1.html", "primary")}</div>
<div class="panel"><div class="head"><h2>Season 2027 · 3 rounds</h2>{btn("Add round", "#round", "primary")}</div>
{table(["Round", "Registration", "Exam days", "Results", "Applicants", "Status", ""], [('<b class="ink">Round 1</b>', "Jan 1 – Feb 28", "Mar 14–15", "Apr 20 · released", '<span class="mono">9,733</span>', B("gray", "Done"), btn("Open", "results.html")), ('<b class="ink">Round 2</b>', "Mar 1 – Apr 10", "Apr 25", "May 15 · scheduled", '<span class="mono">2,118</span>', B("ok", "Registration open"), btn("Edit", "#round")), ('<b class="ink">Round 3</b>', "Apr 11 – May 15", "May 30", "Jun 19", '<span class="mono">0</span>', B("warn", "Draft"), btn("Edit", "#round"))])}
<span class="muted">An applicant applies once per season and takes one round. Missed or absent in Round 1? They can move to Round 2 without paying again, if you allow it below.</span>
<label style="display:flex;gap:8px;align-items:center"><input type="checkbox" checked style="height:18px;width:18px">Let absent examinees move to a later round for free</label></div>
<h2>All seasons</h2>
{table(["Season", "Registration", "Exam days", "Results", "Status", ""], [
    ('<b class="ink">2027</b>', "Jan 1 – May 15, 2027", "3 rounds: Mar 14–15, Apr 25, May 30", "Round 1 released", B("ok", "Open"), btn("Edit", "#new")),
    ('<b class="ink">2026</b>', "Jan 3 – Feb 25, 2026", "Mar 8", "Released Apr 7", B("gray", "Closed"), btn("View")),
    ('<b class="ink">October 2025</b>', "Sep 1 – Oct 10, 2025", "Oct 25", "Released Nov 20", B("gray", "Closed"), btn("View"))])}""",
      overlays=modal("new", "info", "+", "New season", '<div class="fld"><label for="s1">Name</label><input id="s1" value="2028"></div><div class="two" style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="s2">Registration opens</label><input id="s2" type="date" value="2028-01-03"></div><div class="fld"><label for="s3">Closes</label><input id="s3" type="date" value="2028-02-26"></div></div><div class="fld"><label for="s4">Exam fee</label><input id="s4" value="[EXAM FEE]"></div><div class="fld"><label for="s5">Rounds</label><select id="s5"><option>3 rounds</option><option>2 rounds</option><option>1 round</option></select></div><label style="display:flex;gap:8px;font-size:14px"><input type="checkbox" checked>Copy campuses, programs, rooms and staff from 2027</label>', btn("Cancel", "#") + btn("Create", "#open-conflict", "primary"))
      + modal("open-conflict", "warn", WARN, "Season 2027 is still open", '<p class="muted" style="margin:0">Close 2027 first, or save 2028 as a draft to open later.</p>', btn("Save as draft", "#created") + btn("Close 2027 and open 2028", "#", "danger"))
      + toast("created", "ok", OK, "Season 2028 saved as draft", "It opens on Jan 3, 2028.")
      + modal("round", "info", "+", "Round 3 · Season 2027", '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="r1">Registration opens</label><input id="r1" type="date" value="2027-04-11"></div><div class="fld"><label for="r2">Closes</label><input id="r2" type="date" value="2027-05-15"></div><div class="fld"><label for="r3">Exam day(s)</label><input id="r3" type="date" value="2027-05-30"></div><div class="fld err"><label for="r4">Results release</label><input id="r4" type="date" value="2027-05-20"><span class="errmsg">Must be after the exam day.</span></div></div><label style="display:flex;gap:8px;font-size:14px"><input type="checkbox" checked>Copy the Round 2 sessions and rooms</label>', btn("Cancel", "#") + btn("Save round", "#round-saved", "primary"))
      + toast("round-saved", "ok", OK, "Round 3 saved", "It opens for registration on Apr 11."),
      states=[("new", "New season form"), ("open-conflict", "Conflict warning"), ("created", "Created"), ("round", "Round form with error"), ("round-saved", "Round saved")])

SETUP_STEPS = [("Basics", "setup-1.html"), ("Rounds", "setup-2.html"), ("Campuses and programs", "setup-3.html"), ("Sessions and rooms", "setup-4.html"), ("Review and open", "setup-5.html")]


def setup(n, body, nxt):
    back = btn("Back", f"setup-{n - 1}.html") if n > 1 else btn("Cancel", "seasons.html")
    admin(f"setup-{n}", "New season · 2028", f"""{stepper(SETUP_STEPS, n)}
<div class="panel formpage"><div class="scrollx">{body}</div></div>
<div class="formfoot">{back}<span class="muted" style="margin-left:auto;font-size:13px">Saved as a draft as you go</span>{btn("Save draft", "seasons.html#created")}{nxt}</div>""", active="seasons",
          crumb='<a href="seasons.html" class="muted">← Seasons and rounds</a>',
          overlays=modal("open", "warn", WARN, "Open Season 2028 registration?", '<p class="muted" style="margin:0">Applicants can sign up from Jan 3, 2028. Season 2027 must be closed first; it is.</p>', btn("Cancel", "#") + btn("Open registration", "seasons.html#created", "primary")) if n == 5 else "",
          states=[("open", "Open confirm")] if n == 5 else None)


setup(1, f"""<h2>Basics</h2>{hint("A season is one school year of admission testing. You set its rounds on the next step.")}
<div class="formgrid"><div class="fld"><label for="n1">Season name</label><input id="n1" value="2028">{hint("Shown to applicants, e.g. “SKSU Admission Test 2028”.")}</div>
<div class="fld"><label for="n2">School year</label><input id="n2" value="2028–2029"></div>
<div class="fld"><label for="n3">Exam fee</label><input id="n3" value="[EXAM FEE]">{hint("Applicants see this on the payment step.")}</div>
<div class="fld"><label for="n4">Payment to</label><input id="n4" value="[GCASH OR BANK ACCOUNT]"></div></div>
<label class="check"><input type="checkbox" checked>Copy campuses, programs, rooms, staff and message templates from Season 2027 {tip("You can change anything on the next steps. Applicants and scores are never copied.")}</label>""", btn("Next: rounds", "setup-2.html", "primary"))
setup(2, f"""<h2>Rounds</h2>{hint("Each round has its own registration window, exam day and result release. Most seasons use three.")}
{table(["Round", "Registration opens", "Closes", "Exam day", "Results", ""], [(f"<b>Round {i}</b>", f'<input type="date" value="{o}">', f'<input type="date" value="{c}">', f'<input type="date" value="{e}">', f'<input type="date" value="{r}">', btn("Remove", "#")) for i, o, c, e, r in [(1, "2028-01-03", "2028-02-26", "2028-03-11", "2028-04-14"), (2, "2028-02-27", "2028-04-08", "2028-04-22", "2028-05-12"), (3, "2028-04-09", "2028-05-13", "2028-05-27", "2028-06-16")]])}
<a class="btn" href="#" style="align-self:flex-start">+ Add a round</a>
<div class="alertbox info">Dates can overlap only between registration of one round and the exam of the round before.</div>""", btn("Next: campuses", "setup-3.html", "primary"))
setup(3, f"""<h2>Campuses and programs</h2>{hint("Copied from 2027. Switch off what isn’t offered in 2028; applicants can’t pick it.")}
{table(["Campus", "Programs offered", "Test center", ""], [(c, f"{p} of {p}", '<a class="switch on" href="#"></a>', btn("Edit programs", "campuses.html")) for c, p in [("ACCESS, Tacurong", 22), ("Isulan", 14), ("Tacurong", 9), ("Kalamansig", 5), ("Bagumbayan", 2), ("Palimbang", 2), ("Lutayan", 2)]])}""", btn("Next: sessions", "setup-4.html", "primary"))
setup(4, f"""<h2>Sessions and rooms</h2>{hint("A session is one campus, one date and start time. Seats = rooms × 50.")}
{table(["Round", "Sessions", "Rooms", "Seats", ""], [("Round 1 · Mar 11", "8 (copied)", "83", "4,150", btn("Edit", "sessions.html")), ("Round 2 · Apr 22", "5 (copied)", "40", "2,000", btn("Edit", "sessions.html")), ("Round 3 · May 27", "0", "0", "0", btn("Copy from Round 2", "#"))])}
<div class="alertbox warn">Round 3 has no sessions yet. You can open the season and add them later.</div>""", btn("Next: review", "setup-5.html", "primary"))
setup(5, f"""<h2>Review and open</h2>
<div class="kv"><span>Season</span><span class="ink">2028 · school year 2028–2029</span><span>Exam fee</span><span>[EXAM FEE]</span><span>Rounds</span><span>3 · Mar 11, Apr 22, May 27</span><span>Campuses</span><span>7 · 56 programs</span><span>Seats</span><span>Round 1: 4,150 · Round 2: 2,000 · Round 3: none yet</span><span>Staff</span><span>5 copied from 2027</span></div>
<div class="alertbox ok">Everything needed to open Round 1 is ready.</div>""", btn("Open registration", "#open", "primary"))

ses = [("ACCESS, Tacurong", "Sat, Mar 14", 24, 1188, True), ("ACCESS, Tacurong", "Sun, Mar 15", 24, 1040, True), ("Isulan", "Sat, Mar 14", 4, 162, True), ("Isulan", "Sun, Mar 15", 4, 200, False), ("Tacurong", "Sat, Mar 14", 12, 588, True), ("Kalamansig", "Sun, Mar 15", 8, 371, True), ("Bagumbayan", "Sat, Mar 14", 4, 128, True), ("Lutayan", "Sat, Mar 14", 3, 93, True)]
srows = []
for c, w, r, t, op in ses:
    cap = r * 50
    p = round(t / cap * 100)
    cls = "full" if t >= cap else ("hi" if p > 85 else "")
    state = B("bad", "Full") if t >= cap else (B("ok", "Open") if op else B("gray", "Closed"))
    srows.append((f'<span class="ink">{c}</span>', w, f'<span class="mono">{r}</span>', f'<div class="meter"><div class="t"><span class="{cls}" style="width:{p}%"></span></div><span class="mono" style="width:84px">{t} / {cap}</span></div>', state, f'<a class="switch{" on" if op else ""}" href="#toggle" aria-label="Open or close"></a>', btn("Seat plan", "../docs/seat-plan.html")))
admin("sessions", "Schedule days", f"""{rounds_bar(2)}<div class="panel" style="flex-direction:row;align-items:center;gap:24px;flex-wrap:wrap"><div><span class="muted" style="font-size:13px">Shown on every permit as a guide</span><div class="ink" style="font-weight:600">Report by 7:30 AM · exam starts 8:00 AM {btn("Edit", "#times")}</div></div>
<div style="margin-left:auto;display:flex;align-items:center;gap:10px"><span>Morning and afternoon sittings</span><a class="switch" href="#sittings" aria-label="Turn on two sittings a day"></a>{tip("Off: one exam per day, like the Civil Service exam. Turn on only if a day overflows; each day then has AM and PM sittings.")}</div></div>
<div class="head"><span class="muted">A schedule day is a campus and a date. Applicants pick the day; the room and seat are assigned for them.</span><span style="display:flex;gap:8px">{btn("Auto-assign seats", "#auto")}{btn("Add a day", "#add", "primary")}</span></div>
{table(["Campus", "Date", "Rooms", "Seats taken", "Status", "Open", ""], srows)}""",
      overlays=modal("add", "info", "+", "Add a schedule day", '<div class="fld"><label for="a1">Campus</label><select id="a1"><option>Isulan</option></select></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="a2">Date</label><input id="a2" type="date" value="2027-03-15"></div><div class="fld"><label for="a3">Report by (guide)</label><input id="a3" type="time" value="07:30"></div></div><div class="fld err"><label for="a4">Rooms</label><select id="a4"><option>Pick rooms…</option></select><span class="errmsg">Pick at least 1 room.</span><small class="hint">Rooms come from the Rooms page; seats add up by themselves.</small></div>', btn("Cancel", "#") + btn("Add day", "#added", "primary"))
      + toast("added", "ok", OK, "Session added", "Isulan · Sun, Mar 15 · 200 seats. 41 waiting applicants were emailed.")
      + modal("toggle", "warn", WARN, "Close Isulan, Sat Mar 14?", '<p class="muted" style="margin:0">162 people keep their seats. Nobody new can pick it.</p>', btn("Cancel", "#") + btn("Close session", "#", "primary"))
      + modal("times", "info", "", "Guide times for Round 2", f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="g1">Report by</label><input id="g1" type="time" value="07:30"></div><div class="fld"><label for="g2">Exam starts</label><input id="g2" type="time" value="08:00"></div></div>{hint("A guide only; nobody books a time. Changing it updates every permit and sends one text to everyone scheduled.")}', btn("Cancel", "#") + btn("Save and notify", "#", "primary"))
      + modal("sittings", "warn", WARN, "Turn on two sittings a day?", '<p class="muted" style="margin:0">Each day then has a morning and an afternoon sitting with their own seats. Use it only when a date is overbooked. People already scheduled keep the morning sitting.</p>', btn("Keep one per day", "#") + btn("Turn on", "#", "primary"))
      + modal("auto", "info", "⇄", "Auto-assign seats · Round 2", f'{hint("For approved applicants who haven’t picked a seat. Nobody who already picked is moved.")}<div class="fld"><label for="au1">Rule</label><select id="au1"><option>Campus of their 1st choice, earliest session first</option><option>Nearest campus with room</option></select></div><div class="kv"><span>Applicants</span><span>627</span><span>Will get a seat</span><span>586</span><span>No room left</span><span>41 (Isulan) · add a session first</span></div>', btn("Cancel", "#") + btn("Assign 586 seats", "#assigned", "primary"))
      + toast("assigned", "ok", OK, "586 seats assigned", "Each applicant got an email with their room and seat. Undo from the activity log for 1 hour."),
      states=[("times", "Guide times"), ("sittings", "Two sittings switch"), ("add", "Add a day, with error"), ("added", "Added"), ("toggle", "Close session confirm"), ("auto", "Auto-assign preview"), ("assigned", "Assigned")])

rooms = [("ACCESS · Room 1", "J. Ampatuan", 47, 2, 1, B("ok", "Synced")), ("ACCESS · Room 2", "R. Sinsuat", 45, 3, 2, B("ok", "Synced")), ("ACCESS · Room 3", "M. Usman", 31, 0, 19, B("warn", "3 queued, offline")), ("Isulan · Room 4", "L. Cabañero", 48, 2, 0, B("ok", "Closed")), ("Tacurong · Room 2", "E. Mangelen", 0, 0, 50, B("bad", "Not seen for 40 min")), ("Kalamansig · Room 1", "A. Bagundang", 46, 4, 0, B("ok", "Synced"))]
admin("checkin", "Check-in monitor · Sat, Mar 14", f"""{rounds_bar(1)}<div class="stats"><div><small>Expected today</small><b>4,212</b></div><div><small>Present</small><b style="color:var(--ok)">3,904</b></div><div><small>Absent</small><b style="color:var(--bad)">121</b></div><div><small>Not scanned yet</small><b style="color:var(--warn)">187</b></div><div><small>Proctor phones</small><b>88 / 91 synced</b></div></div>
{table(["Room", "Proctor", "Present", "Absent", "Pending", "Phone", ""], [(f'<span class="ink">{r[0]}</span>', r[1], f'<span class="mono" style="color:var(--ok)">{r[2]}</span>', f'<span class="mono" style="color:var(--bad)">{r[3]}</span>', f'<span class="mono">{r[4]}</span>', r[5], btn("Call proctor", "#call") if "Not seen" in r[5] else "") for r in rooms])}
<a href="../proctor/checkin.html">See the proctor’s phone screen →</a>""",
      overlays=modal("call", "warn", WARN, "Tacurong Room 2 hasn’t synced", '<div class="kv"><span>Proctor</span><span>E. Mangelen</span><span>Mobile</span><span>0918 555 0142</span><span>Last seen</span><span>7:21 AM</span></div>', btn("Close", "#") + btn("Assign another proctor", "#", "primary")),
      states=[("call", "Offline proctor dialog")])

SUBJECTS = ["english", "science", "math", "filipino", "social_studies", "esm", "overall"]
TEMPLATE_COLS = ["examinee_no", "name"] + [f"{x}_{k}" for x in SUBJECTS for k in ("ss", "stanine")]
admin("scores", "Scores import", f"""{rounds_bar(1)}{stepper([("Upload CSV", "#uploading"), ("Match columns", "#map"), ("Check", "#"), ("Approve", "#commit"), ("Publish", "results.html")], 3)}
<div class="panel"><div class="head"><h2>tpt-2027-round1.csv</h2><span class="muted" style="font-size:13px">From the Testing Center · uploaded Apr 18, 3:40 PM · original kept unchanged</span></div>
<span class="hint">The Testing Center computes the scores; this screen never changes them. It checks the file against who registered and who was present, and shows what will change. Need the format? {btn("Download the CSV template", "../docs/tpt-scores-template.csv", "sm")}</span>
<div class="kpis" style="grid-template-columns:repeat(5,1fr)"><div class="kpi"><span>Rows in file</span><b>9,104</b></div><div class="kpi"><span>Ready</span><b>9,088</b></div><div class="kpi"><span>Not registered</span><b style="color:var(--bad)">4</b></div><div class="kpi"><span>Duplicate or out of range</span><b style="color:var(--bad)">10</b></div><div class="kpi"><span>Present, no score</span><b style="color:var(--warn)">2</b></div></div></div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>Needs a look · 16</h2>{btn("Download these rows (CSV)", "#")}</div>
{table(["Row", "Examinee no.", "Problem", "What to do"], [("212", '<span class="mono">500912</span>', B("bad", "Not registered this round"), "Check the number with the Testing Center"), ("1,044", '<span class="mono">50O233</span>', B("bad", "Letter O instead of zero"), "Fix in the file and upload again"), ("2,871", '<span class="mono">500655</span>', B("bad", "Appears twice"), "Keep one row"), ("5,002", '<span class="mono">502460</span>', B("bad", "Overall 910 is above 800"), "Ask the Testing Center"), ("6,310", '<span class="mono">501990</span>', B("warn", "Stanine 9 but score 512"), "Ask the Testing Center"), ("—", '<span class="mono">501877</span>', B("warn", "Checked in, no score in file"), "Missing answer sheet?")])}</div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>What changes if you approve</h2><span class="muted" style="font-size:13px">compared with what is in the system now</span></div>
{table(["", "Examinees", "Example"], [(B("ok", "New"), '<span class="mono">9,080</span>', "500214 · Overall 584 · stanine 7"), (B("warn", "Changed"), '<span class="mono">8</span>', "500176 · Overall 498 → 512"), (B("gray", "Unchanged"), '<span class="mono">0</span>', "—")])}</div>
<div class="panel"><h2>Files for this round</h2>{table(["File", "Uploaded", "By", "Status", ""], [("tpt-2027-round1.csv", "Apr 18, 3:40 PM", "Testing Center", B("warn", "Checking"), ""), ("tpt-2027-round1-draft.csv", "Apr 17, 10:12 AM", "Testing Center", B("gray", "Replaced"), btn("Download original"))])}</div>
<div class="formfoot" style="max-width:none">{btn("Upload a fixed file", "#uploading")}<span style="margin-left:auto" class="muted">The 16 rows stay out until fixed; the rest can be approved now.</span>{btn("Approve 9,088 scores", "#commit", "primary")}</div>""",
      overlays=modal("uploading", "info", '<span class="spin"></span>', "Reading tpt-2027-round1.csv… 41%", '<div class="progress"><span style="width:41%"></span></div><p class="muted" style="margin:0">3,732 of 9,104 rows checked.</p>', btn("Cancel", "#"))
      + modal("checking", "info", '<span class="spin"></span>', "Checking rows… 6,410 of 9,104", '<div class="progress"><span style="width:70%"></span></div><p class="muted" style="margin:0">Matching examinee numbers with registrations and check-ins. 12 problems so far.</p>', btn("Run in background", "#bg", "primary"))
      + toast("bg", "info", INFO, "Import runs in the background", "You can leave this page. We’ll notify you when it’s done (bell, top right).")
      + modal("summary", "info", "", "Import finished", '<div class="kpis" style="grid-template-columns:repeat(3,1fr)"><div class="kpi"><span>Ready to approve</span><b>9,088</b></div><div class="kpi"><span>Skipped</span><b>0</b></div><div class="kpi"><span>Problems</span><b style="color:var(--bad)">16</b></div></div>' + hint("Took 38 seconds. Nothing is visible to students yet."), btn("Download problem rows (CSV)") + btn("Review and approve", "#", "primary"))
      + modal("map", "info", "", "Match the columns", '<p class="muted" style="margin:0">Guessed from the header row. Fix any that are wrong; it is remembered for next time.</p>' + table(["In the file", "Means"], [("Examinee Number", "<select><option>Examinee no.</option></select>"), ("Name of Examinee", "<select><option>Name (only to double-check)</option></select>"), ("English · Standard Score", "<select><option>English · standard score</option></select>"), ("English · Stanine", "<select><option>English · stanine</option></select>"), ("Qualitative Interpretation", "<select><option>Ignore (worked out from stanine)</option></select>")]), btn("Cancel", "#") + btn("Use these columns", "#", "primary"))
      + modal("badfile", "bad", BAD, "This file has two tables side by side", '<p class="muted" style="margin:0">Columns 32–33 hold a second list (examinee number + program) next to the scores. Save only the scores table as its own CSV, with one header row, and upload again.</p>', btn("Download the template", "../docs/tpt-scores-template.csv") + btn("OK", "#", "primary"))
      + modal("commit", "warn", WARN, "Approve 9,088 scores?", '<p class="muted" style="margin:0">They are saved exactly as in the file. Students cannot see them until you publish. The file and your approval go in the activity log.</p>', btn("Cancel", "#") + btn("Approve", "results.html#committed", "primary")),
      states=[("uploading", "Uploading"), ("checking", "Checking rows"), ("bg", "Running in background"), ("summary", "Import summary"), ("map", "Match columns"), ("badfile", "Two tables in one file"), ("commit", "Approve confirm")])

admin("results", "Results", f"""{rounds_bar(1)}<div class="stats"><div><small>Scored</small><b>9,098</b></div><div><small>Absent</small><b>635</b></div><div><small>Not in file</small><b>6</b></div><div><small>Release</small><b>Apr 20 · 9:00 AM</b></div></div>
<div class="panel" style="flex-direction:row;align-items:center"><label for="rel" class="ink" style="font-weight:600">Release on</label><input id="rel" type="datetime-local" value="2027-04-20T09:00"><span class="muted grow">Pages and PDFs are pre-built before this time, so release day stays fast.</span>{btn("Release now", "#release", "primary")}</div>
<div class="filters"><input placeholder="Search examinee" style="width:260px"><select><option>All programs</option></select>{btn("Ranking report", "report-view.html")}</div>
{table(["Examinee no.", "Name", "1st choice", "Overall SS", "Stanine", ""], [('<span class="mono ink">500214</span>', "Maria S. Dela Cruz", "BS Civil Engineering · Isulan", '<span class="mono">584</span>', "7", btn("View", "result-detail.html")), ('<span class="mono ink">500176</span>', "Datu R. Mamalinta", "BS Fisheries · Palimbang", '<span class="mono">512</span>', "6", btn("View", "result-detail.html")), ('<span class="mono ink">500198</span>', "Princess A. Lumabao", "BS Accountancy · ACCESS", '<span class="mono">661</span>', "9", btn("View", "result-detail.html")), ('<span class="mono ink">500231</span>', "Jomar P. Abdullah", "BS IT · ACCESS", "—", B("gray", "Absent"), btn("View", "result-detail.html"))])}""",
      overlays=inmain("none", empty("list", "No scores for Round 2 yet", "Import the raw scores after exam day; they appear here to check before release.", btn("Import scores", "scores.html", "primary")))
      + toast("committed", "ok", OK, "9,098 scores committed", "Release is scheduled for Apr 20, 9:00 AM.")
      + modal("release", "warn", WARN, "Release results to 9,098 examinees now?", '<p class="muted" style="margin:0">They get an email and can see scores at once. You can’t take this back.</p>', btn("Cancel", "#") + btn("Release now", "#releasing", "primary"))
      + modal("releasing", "info", '<span class="spin"></span>', "Sending 9,098 emails… 2,310 sent", '<div class="progress"><span style="width:25%"></span></div><p class="muted" style="margin:0">Safe to close. This keeps going in the background.</p>', btn("Close", "#released"))
      + toast("released", "ok", OK, "Results released", "Emails and texts are going out. See the delivery report.")
      + modal("report", "info", "", "Results released · delivery", '<div class="kpis" style="grid-template-columns:repeat(3,1fr)"><div class="kpi"><span>In app</span><b>9,098</b></div><div class="kpi"><span>Email delivered</span><b>9,061</b></div><div class="kpi"><span>Text delivered</span><b>8,977</b></div></div><div class="kv"><span>Email bounced</span><span>37 · mailbox full or wrong address</span><span>Text failed</span><span>121 · number not in service</span></div>' + hint("Failed ones can be fixed and resent from Messages."), btn("Open send log", "messages.html") + btn("Done", "#", "primary")),
      states=[("none", "Empty: no scores yet"), ("report", "Delivery report"), ("committed", "After commit"), ("release", "Release confirm"), ("releasing", "Sending progress"), ("released", "Released")])

admin("result-detail", "Result · 500214 Maria S. Dela Cruz", table(["Subject", "Raw", "Standard score", "Stanine"], [(n, '<span class="mono">' + str(r) + "</span>", f'<span class="mono">{s}</span>', t) for (n, s, t), r in zip(subj, [44, 29, 28, 43, 29, 26])]) + f'<div style="display:flex;gap:8px">{btn("Result PDF", "../docs/result-pdf.html")}{btn("Correct a score", "#fix")}</div>',
      active="results", crumb='<a href="results.html" class="muted">← Results</a>',
      overlays=modal("fix", "warn", WARN, "Correct a score", '<div class="fld"><label for="f1">Science raw</label><input id="f1" value="31"></div><div class="fld"><label for="f2">Reason</label><input id="f2" value="Answer sheet re-checked by testing center"></div><p class="muted" style="margin:0">The standard score is recomputed. Old and new values stay in the history.</p>', btn("Cancel", "#") + btn("Save", "#", "primary")),
      states=[("fix", "Correction dialog")])

EVENTS = [("Account created", "✓", "", "", "Welcome"), ("Application submitted", "✓", "✓", "", "Next: pay"), ("Upload needs redoing", "✓", "✓", "✓", "Photo or receipt problem"), ("Receipt received", "✓", "✓", "", "We’re checking"),
          ("Payment approved", "✓", "✓", "✓", "Examinee no., pick a seat"), ("Payment rejected", "✓", "✓", "✓", "Reason, send again"), ("Seat booked · permit ready", "✓", "✓", "✓", "Room, seat, permit link"),
          ("Schedule changed", "✓", "✓", "✓", "New room and seat"), ("Exam reminder (day before, 5 PM)", "✓", "✓", "✓", "Time, room, what to bring"), ("Marked absent", "✓", "✓", "", "Move to next round"),
          ("Results released", "✓", "✓", "✓", "Link to result")]
admin("messages", "Messages", f"""{hint("Every email and text the system sends lives here. Automatic ones go out by themselves; blasts are sent by you.")}
<div class="panel"><div class="head"><h2>Automatic notifications to students</h2>{tip("In-app is always on. Email is always on. Texts cost money, so they’re only for events a student must not miss.")}</div>
{table(["Event", "In app", "Email", "Text", "Says", ""], [(f'<span class="ink">{e}</span>', i, m, t, f'<span class="muted">{w}</span>', btn("Edit", "#tpl")) for e, i, m, t, w in EVENTS])}
<a href="../docs/sms.html">See every text message →</a></div>
<div class="row"><div class="panel grow"><div class="head"><h2>Templates</h2>{btn("New template", "#tpl")}</div>
{table(["Template", "Sent when", "Channel", ""], [("Payment approved", "A cashier approves", "Email", btn("Edit", "#tpl")), ("Payment rejected", "A cashier rejects, with the reason", "Email + SMS", btn("Edit", "#tpl")), ("Pick your seat", "Reminder, sent by you", "Email + SMS", btn("Edit", "#tpl")), ("Exam tomorrow", "Day before exam, 5:00 PM", "SMS", btn("Edit", "#tpl")), ("Results are out", "On release", "Email", btn("Edit", "#tpl"))])}</div>
<div class="panel" style="width:420px;flex-shrink:0"><h2>Send a blast</h2>
<div class="fld"><label for="m1">To</label><select id="m1"><option>Round 2 · approved, no seat (627)</option><option>Round 1 · absent (121)</option><option>Saved view: Isulan · Round 2</option></select></div>
<div class="fld"><label for="m2">Template</label><select id="m2"><option>Pick your seat</option></select></div>
<div class="preview">Hi {{{{first_name}}}}, your payment is approved but you haven’t picked a seat yet. Pick yours before Mar 1: sksu-tpt.com/seat</div>
<div class="fld"><label for="m3">Send</label><select id="m3"><option>Now</option><option>Schedule…</option></select>{hint("627 emails + 627 texts. Texts cost about ₱313.")}</div>
{btn("Send to 627", "#confirm", "primary lg")}</div></div>
<div class="panel"><div class="head"><h2>Send log</h2><span class="seg"><span class="on">All</span><span>Failed · 4</span></span></div>{table(["When", "Student", "Message", "Channel", "Status", ""], [
    ('<span class="mono muted">9:05 AM</span>', "Jomar P. Abdullah", "Payment approved", "Email + text", B("ok", "Delivered"), ""),
    ('<span class="mono muted">8:00 AM</span>', "Rhea L. Sumagka", "Pick your seat (blast)", "Text", B("bad", "Failed · number not in service"), btn("Fix number and resend", "#resend")),
    ('<span class="mono muted">8:00 AM</span>', "Kevin D. Alonto", "Pick your seat (blast)", "Email", B("warn", "Bounced · mailbox full"), btn("Resend", "#resend")),
    ('<span class="mono muted">Yesterday</span>', "Maria S. Dela Cruz", "Seat booked", "Email + text", B("ok", "Delivered"), "")])}</div>""",
      overlays=modal("confirm", "warn", WARN, "Send to 627 applicants now?", '<p class="muted" style="margin:0">Messages can’t be recalled once sent.</p>', btn("Cancel", "#") + btn("Send now", "#sending", "primary"))
      + modal("sending", "info", '<span class="spin"></span>', "Sending… 212 of 627", '<div class="progress"><span style="width:34%"></span></div>', btn("Run in background", "#sent"))
      + toast("sent", "ok", OK, "Blast sent", "627 emails, 627 texts. 3 numbers bounced; see Recent.")
      + modal("tpl", "info", "✎", "Edit template · Pick your seat", f'<div class="fld"><label for="t1">Subject</label><input id="t1" value="Pick your exam seat"></div><div class="fld"><label for="t2">Message</label><textarea id="t2" rows="4" style="border:1px solid var(--line);border-radius:6px;padding:10px;font:14px var(--sans)">Hi {{{{first_name}}}}, your payment is approved…</textarea>{hint("Fields: {{{{first_name}}}}, {{{{examinee_no}}}}, {{{{session}}}}, {{{{seat}}}}. SMS is cut at 160 characters.")}</div>', btn("Cancel", "#") + btn("Save", "#", "primary"))
      + modal("resend", "info", "", "Resend to Rhea L. Sumagka", '<div class="fld"><label for="rn">Mobile number</label><input id="rn" value="0917 555 0199"></div>' + hint("The number on her account is updated too."), btn("Cancel", "#") + btn("Resend", "#resent", "primary"))
      + toast("resent", "ok", OK, "Resent", "Delivered to 0917 555 0199."),
      states=[("tpl", "Edit template"), ("confirm", "Send confirm"), ("sending", "Sending"), ("sent", "Sent"), ("resend", "Resend a failed one"), ("resent", "Resent")])

reps = [("Registrations by day", "Sign-ups and submissions per day, by campus"), ("Applicant list", "Every field, filterable, for the registrar"), ("Program demand", "1st, 2nd and 3rd choices per campus and program"), ("Payments", "Approved, rejected and waiting, with reviewer and time"), ("Seat plan per room", "Printable list for proctors, by session and room"), ("Attendance", "Present and absent per session, from check-in"), ("Score distribution", "Standard scores and stanines per subject"), ("Ranking per program", "Examinees ranked within each program choice"), ("Qualified students", "Who meets each program cut-off"), ("Survey answers", "What examinees said about exam day")]
admin("reports", "Reports", f"""<div class="row"><div class="panel grow"><div class="head"><h2>Where applicants drop off · Round 1</h2>{tip("A funnel: each bar is a share of everyone who signed up. The red number is how many stopped at that step.")}</div>
{funnel([("Signed up", 16408), ("Submitted", 12287), ("Paid and approved", 9471), ("Picked a seat", 8844), ("Took the exam", 8990 - 146), ("Scored", 8844 - 6)])}</div>
<div class="panel grow"><div class="head"><h2>Most wanted programs · 1st choice</h2><a href="report-view.html" style="font-size:13px">All 56 →</a></div>
{hbars([(n, c, v) for n, c, v in prog])}</div></div>
<div class="panel"><div class="head"><h2>Overall score distribution · Round 1</h2><span class="muted" style="font-size:13px">9,098 examinees · each bar is 50 points, one stanine band</span></div>{histogram()}</div>
""" + table(["Report", "What it shows", ""], [(f'<span class="ink">{r[0]}</span>', r[1], f'<span class="act">{btn("View", "report-view.html")} {btn("Excel", "exports.html#queued")}</span>') for r in reps]))

admin("report-view", "Ranking per program", f"""<div class="filters"><select><option>BS Civil Engineering · Isulan</option></select><select><option>1st choice only</option></select><span style="margin-left:auto;display:flex;gap:6px">{btn("Print")}{btn("Excel", "exports.html#queued")}</span></div>
{table(["Rank", "Examinee no.", "Name", "Overall SS", "Stanine", "Qualified"], [("1", '<span class="mono">500891</span>', "Rhea L. Sumagka", '<span class="mono">742</span>', "9", B("ok", "Yes")), ("2", '<span class="mono">500433</span>', "Kevin D. Alonto", '<span class="mono">701</span>', "9", B("ok", "Yes")), ("41", '<span class="mono">500214</span>', "Maria S. Dela Cruz", '<span class="mono">584</span>', "7", B("ok", "Yes")), ("180", '<span class="mono">501120</span>', "Joel P. Kamid", '<span class="mono">402</span>', "3", B("gray", "No"))])}""",
      active="reports", crumb='<a href="reports.html" class="muted">← Reports</a>')

admin("exports", "Downloads", table(["File", "Asked by", "Status", ""], [
    ("applicants-2027.xlsx", "Admission Office · now", '<div class="meter"><div class="t"><span style="width:62%"></span></div><span class="mono">62%</span></div>', '<span class="spin"></span>'),
    ("ranking-civil-eng-isulan.xlsx", "Admission Office · 10 min ago", B("ok", "Ready · 84 KB"), btn("Download", "#")),
    ("payments-jan.xlsx", "Cashier 1 · yesterday", B("ok", "Ready · 1.2 MB"), btn("Download", "#")),
    ("attendance-mar14.xlsx", "Testing Center · Mar 14", B("bad", "Failed · timed out"), btn("Try again", "#retry"))]) + '<span class="muted">Files are kept for 7 days.</span>',
      overlays=inmain("empty", empty("file", "No downloads yet", "Exports you start from any list land here and stay for 7 days.", btn("Go to reports", "reports.html"))) + toast("queued", "info", INFO, "Building your file", "It will appear here in a minute. You can keep working.") + toast("retry", "info", INFO, "Trying again", "attendance-mar14.xlsx is back in the queue."),
      states=[("queued", "Export queued"), ("retry", "Retry"), ("empty", "Empty")])

camp = [("ACCESS, Tacurong", 22, "4,343"), ("Isulan", 14, "1,884"), ("Tacurong", 9, "1,663"), ("Kalamansig", 5, "731"), ("Bagumbayan", 2, "128"), ("Palimbang", 2, "94"), ("Lutayan", 2, "93")]
admin("rooms", "Rooms", f"""{hint("Rooms belong to a campus and are reused every season. A session picks its rooms from here, so seats always add up.")}
<div class="filters"><span class="seg"><span class="on">Isulan</span><span>ACCESS</span><span>Tacurong</span><span>Kalamansig</span><span>Bagumbayan</span><span>Palimbang</span><span>Lutayan</span></span><span style="margin-left:auto">{btn("Import rooms (CSV)", "#import")}</span>{btn("Add room", "#room", "primary")}</div>
{table(["Building", "Room", "Seats", "Exam use", "Used in", ""], [("Main Building", "Room 1", '<span class="mono">50</span>', '<a class="switch on" href="#"></a>', "Round 1 · Round 2", btn("Edit", "#room")), ("Main Building", "Room 4", '<span class="mono">50</span>', '<a class="switch on" href="#"></a>', "Round 1 · Round 2", btn("Edit", "#room")), ("Engineering", "ENG 201", '<span class="mono">45</span>', '<a class="switch on" href="#"></a>', "Round 1", btn("Edit", "#room")), ("Engineering", "ENG 202", '<span class="mono">45</span>', '<a class="switch" href="#"></a>', "—", btn("Edit", "#room")), ("Library", "AVR", '<span class="mono">80</span>', '<a class="switch on" href="#"></a>', "Round 2", btn("Edit", "#room"))])}
<span class="muted">Isulan: 4 of 5 rooms used for exams · 225 seats per session.</span>""",
      overlays=modal("room", "info", "+", "Add a room · Isulan", f'<div class="fld"><label for="ro1">Building</label><input id="ro1" value="Engineering"></div><div class="fld"><label for="ro2">Room name</label><input id="ro2" value="ENG 203"></div><div class="fld"><label for="ro3">Seats for an exam</label><input id="ro3" value="45">{hint("Count the chairs with one seat gap between examinees, not the room’s class size.")}</div>', btn("Cancel", "#") + btn("Add room", "#added", "primary"))
      + toast("added", "ok", OK, "Room added", "ENG 203 · 45 seats. Pick it when you add a session.")
      + modal("import", "info", "↑", "Import rooms", f'<div class="drop">Drop a CSV: campus, building, room, seats</div>{hint("We show a preview first. Rooms already listed are updated, not duplicated.")}', btn("Cancel", "#") + btn("Preview", "#", "primary")),
      states=[("room", "Add room form"), ("added", "Added"), ("import", "Import CSV")])

admin("campuses", "Campuses and programs", f"""<div class="head"><span class="muted">A program belongs to one campus and is switched on per season.</span><span style="display:flex;gap:8px">{btn("Add campus", "#campus")}{btn("Add program", "#program", "primary")}</span></div>
<div class="cards">{''.join(f'<div class="tile"><b style="font:600 15px var(--sans)">{c}</b><span class="muted">{p} programs offered</span><span class="mono" style="color:var(--blue)">{d} 1st-choice picks</span></div>' for c, p, d in camp)}</div>
<h2>Isulan programs</h2>{table(["Program", "Short name", "Board program", "Cut-off score", "Offered in 2027", ""], [("BS Civil Engineering", "BSCE", "Yes", '<span class="mono">530</span>', '<a class="switch on" href="#off"></a>', btn("Edit", "#program")), ("BS Criminology", "BSCrim", "Yes", '<span class="mono">530</span>', '<a class="switch on" href="#off"></a>', btn("Edit", "#program")), ("BS Midwifery", "BSM", "Yes", '<span class="mono">530</span>', '<a class="switch" href="#off"></a>', btn("Edit", "#program"))])}""",
      overlays=modal("program", "info", "+", "Add a program", '<div class="fld"><label for="p1">Campus</label><select id="p1"><option>Isulan</option></select></div><div class="fld"><label for="p2">Name</label><input id="p2" value="BS Information Technology"></div><div class="fld"><label for="p3">Short name</label><input id="p3" value="BSIT"></div>', btn("Cancel", "#") + btn("Add", "#added", "primary"))
      + modal("campus", "info", "+", "Add a campus", '<div class="fld"><label for="c1">Name</label><input id="c1"></div>', btn("Cancel", "#") + btn("Add", "#added", "primary"))
      + toast("added", "ok", OK, "Program added", "BS Information Technology · Isulan, offered in 2027.")
      + modal("off", "warn", WARN, "Stop offering BS Criminology in Isulan?", '<p class="muted" style="margin:0">884 applicants picked it. They keep their choice; new applicants can’t pick it.</p>', btn("Cancel", "#") + btn("Stop offering", "#", "danger")),
      states=[("program", "Add program"), ("campus", "Add campus"), ("added", "Added"), ("off", "Turn off warning")])

staff = [("Admission Office", "sksutpt@gmail.com", "Super admin", "Everything", "Now"), ("Cashier 1", "cashier1@sksu.edu.ph", "Payment reviewer", "Approve and reject payments", "5 min ago"), ("Cashier 2", "cashier2@sksu.edu.ph", "Payment reviewer", "Approve and reject payments", "1 h ago"), ("Isulan proctor lead", "isulan.tpt@sksu.edu.ph", "Proctor", "Check-in for Isulan rooms", "Mar 14"), ("Testing Center", "testing@sksu.edu.ph", "Scores admin", "Import scores, release results", "Apr 18"), ("cashier3@sksu.edu.ph", "invited Jan 10", "Payment reviewer", "—", B("warn", "Invite pending"))]
PERMS = [("See applicants", "✓", "✓", "✓", "Own rooms"), ("Approve payments", "✓", "✓", "", ""), ("Edit applicants", "✓", "", "", ""), ("Sessions and seats", "✓", "", "", ""), ("Check in examinees", "✓", "", "", "✓"), ("Import scores, release", "✓", "", "✓", ""), ("Messages and blasts", "✓", "", "", ""), ("Staff and roles", "✓", "", "", "")]
admin("staff", "Staff and roles", f"""<div class="head"><span class="muted">Staff join by invite only. Roles are set here, never by an email list in the code.</span>{btn("Invite staff", "#invite", "primary")}</div>
<div class="panel"><div class="head"><h2>What each role can do</h2>{tip("Roles are fixed so nobody gets more access by accident. Ask IT for a new role.")}</div>{table(["", "Super admin", "Payment reviewer", "Scores admin", "Proctor"], PERMS)}</div>
{table(["Staff", "Role", "Can", "Last active", ""], [(two(f'<span class="ink">{s[0]}</span>', s[1]), B("vio", s[2]), s[3], s[4], btn("Change role", "#role")) for s in staff])}""",
      overlays=modal("invite", "info", "+", "Invite staff", '<div class="fld"><label for="i1">Email</label><input id="i1" value="proctor.kalamansig@sksu.edu.ph"></div><div class="fld"><label for="i2">Role</label><select id="i2"><option>Proctor</option><option>Payment reviewer</option><option>Scores admin</option><option>Super admin</option></select></div>', btn("Cancel", "#") + btn("Send invite", "#invited", "primary"))
      + toast("invited", "ok", OK, "Invite sent", "proctor.kalamansig@sksu.edu.ph can sign in within 7 days.")
      + modal("role", "warn", WARN, "Change Cashier 2’s role?", '<select><option>Payment reviewer</option><option>Proctor</option><option>No access</option></select><p class="muted" style="margin:0">Takes effect on their next click.</p>', btn("Cancel", "#") + btn("Save", "#", "primary"))
      + modal("last-admin", "bad", BAD, "You can’t remove the last super admin", '<p class="muted" style="margin:0">Make someone else a super admin first.</p>', btn("OK", "#")),
      states=[("invite", "Invite form"), ("invited", "Invited"), ("role", "Change role"), ("last-admin", "Guard error")])

audit = [("Today 9:05", "Cashier 1", "Approved Jomar P. Abdullah’s payment and issued 500215"), ("Today 8:58", "Cashier 1", "Rejected Noel B. Guiamal: reference already used"), ("Jan 13 2:10 PM", "Admission Office", "Closed session Isulan, Sun Mar 15 (full)"), ("Jan 13 9:42 AM", "Maria S. Dela Cruz", "Booked Isulan, Room 4 seat 27"), ("Jan 12 4:30 PM", "Cashier 2", "Approved Maria S. Dela Cruz’s payment and issued 500214"), ("Jan 10 8:30 AM", "Admission Office", "Invited Cashier 2 as Payment reviewer"), ("Jan 2 7:00 AM", "System", "Nightly backup: database 31 MB, files 412 MB, copied off-site"), ("Jan 1 12:00 AM", "Admission Office", "Opened Season 2027")]
admin("audit", "Activity log", '<div class="filters"><select><option>Anyone</option></select><select><option>Any action</option></select><input type="date" value="2027-01-13"></div>' + hint("Approvals, moves, merges and bulk actions can be undone for a short time. Undo writes its own line here.") + table(["When", "Who", "What", ""], [(f'<span class="mono muted">{a[0]}</span>', f'<span class="ink">{a[1]}</span>', a[2], btn("Undo", "#undo") if i in (0, 1) else "") for i, a in enumerate(audit)]),
      overlays=modal("undo", "warn", WARN, "Undo this approval?", '<p class="muted" style="margin:0">Jomar P. Abdullah goes back to “In review” and examinee no. 500215 is retired, never reused. He gets no email.</p>', btn("Cancel", "#") + btn("Undo approval", "#undone", "primary")) + toast("undone", "ok", OK, "Undone", "Jomar P. Abdullah is back in the payment queue."),
      states=[("undo", "Undo confirm"), ("undone", "Undone")])

admin("account", "My account", f"""<div class="panel" style="max-width:640px"><div class="kv"><span>Name</span><span class="ink">Admission Office</span><span>Email</span><span>sksutpt@gmail.com</span><span>Role</span><span>{B("vio", "Super admin")}</span><span>Signed in on</span><span>This PC · Chrome · since 7:58 AM</span></div>
<div style="display:flex;gap:8px">{btn("Sign out other devices", "#others")}{btn("Sign out", "../public/staff-login.html")}</div></div>""",
      active="", overlays=toast("others", "ok", OK, "Signed out 2 other devices", "Only this PC stays signed in."), states=[("others", "Signed out others")])

doc("docs/seat-plan.html", "Seat plan", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../admin/sessions.html">Back to sessions</a></div>
<div class="paper">{LETTERHEAD}<h1>Seat plan · Isulan · Room 4 · Sat, Mar 14</h1>
{table(["Seat", "Examinee no.", "Name", "Signature"], [(str(i), f'<span class="mono">5002{i:02d}</span>', n, "") for i, n in zip(range(26, 30), ["Rodel A. Sangki", "Maria S. Dela Cruz", "Jomar P. Abdullah", "Aisah K. Mangudadatu"])])}
<span class="muted">50 seats. Printed Mar 13, 2027.</span></div>""")


# ---------------------------------------------------------------- journey boards (frames with captions)
def frame(kind, src, n, title, caption, state=False, pre="../"):
    page = src.split("#")[0]
    tip_text = caption.replace('"', "&quot;")
    if kind == "phone":
        dev = f'<div class="dev"><div class="scr"><iframe src="{pre}{src}" loading="lazy" title="{title}" tabindex="-1"></iframe></div></div>'
    else:
        dev = (f'<div class="win"><div class="bar"><i></i><i></i><i></i><span>sksu-tpt.com/{page.replace(".html", "")}</span></div>'
               f'<div class="scr"><iframe src="{pre}{src}" loading="lazy" title="{title}" tabindex="-1"></iframe></div></div>')
    return (f'<a class="fr k-{kind}" href="{pre}{src}" title="{tip_text}">{dev}'
            f'<span class="cap"><span class="n{" state" if state else ""}">{n}</span>{title}</span></a>')


def board(path, title, intro, sections, rules):
    pre = "../" * path.count("/")
    def rows(frames):
        full = [f if len(f) == 6 else (*f, False) for f in frames]
        out = ""
        for kind in ("desk", "phone"):
            group = [f for f in full if f[0] == kind]
            if group:
                out += f'<div class="frames f-{kind}">' + "".join(frame(*f, pre=pre) for f in group) + "</div>"
        return out
    secs = "".join(f'<h2 class="sec" id="stage-{i}">{name}</h2>{rows(frames)}' for i, (name, frames) in enumerate(sections))
    chips = "".join(f'<a href="#stage-{i}">{name}</a>' for i, (name, _) in enumerate(sections))
    rule_html = "".join(f"<div><b>{t}</b>{d}</div>" for t, d in rules)
    doc(path, title, f"""<div class="board">
<div class="crumbs"><a href="{pre}index.html">All pages</a></div>
<div class="bhead"><img src="{pre}assets/sksu-seal.png" alt="SKSU seal"><div><h1>{title}</h1><div class="kicker">Mockup for review · 28 Oct 2026</div></div></div>
<p class="intro">{intro}</p>
<nav class="stagebar">{chips}</nav>
{secs}
<h2 class="sec">Calm rules</h2><div class="rules">{rule_html}</div></div>""", "boardpage")


P, D = "phone", "desk"
board("APPLICANT-JOURNEY-MOCKUP.html", "Applicant: the full journey",
      "Every screen a student sees, from the public page to the result, drawn on a phone because most applicants use one. "
      "Click any screen to open it.",
      [("Start", [
          (P, "applicant/splash.html", "S", "Splash", "Seal and wordmark while the app loads."),
          (P, "applicant/welcome-1.html", "W1", "Welcome 1 of 3", "Big type, one idea, Skip on top."),
          (P, "applicant/welcome-2.html", "W2", "Welcome 2 of 3", ""),
          (P, "applicant/welcome-3.html", "W3", "Welcome 3 of 3", "Get started, or sign in if you already applied.")]),
       ("Find and sign in", [
          (D, "public/landing.html", "1", "Public home", "What the test is, the four steps and the season dates. One green button."),
          (P, "public/landing.html", "1b", "Public home on a phone", "Same page at phone width; the menu folds away.", True),
          (P, "public/login.html", "2", "Sign in", "Google first; an email link for students without Google."),
          (P, "public/login.html#loading", "2a", "Signing in", "Shown while Google answers.", True),
          (P, "public/login.html#magic", "2b", "Email link form", "For students with no Google account.", True),
          (P, "public/login.html#google-error", "2c", "Sign-in failed", "Nothing saved; one Try again button.", True),
          (P, "public/login.html#closed", "2d", "Season closed", "Can still sign in to see a permit or result.", True)]),
       ("Apply", [
          (P, "applicant/home.html", "3", "Home", "The four steps and where Maria is. Closing date shown."),
          (P, "applicant/home.html#offline", "3a", "Offline", "Typing is kept and saved when the signal is back.", True),
          (P, "applicant/apply-personal.html", "4", "About you", "Form with a birth-date error and the photo uploading at 64%."),
          (P, "applicant/apply-personal.html#photo-bad", "4a", "Photo rejected", "No face found or too dark; choose another.", True),
          (P, "applicant/apply-personal.html#upload-failed", "4b", "Upload failed", "Signal dropped; tap to retry.", True),
          (P, "applicant/apply-personal.html#saved", "4c", "Autosaved", "A quiet confirmation, no button to press.", True),
          (P, "applicant/apply-school.html", "5", "School", "Type, school, year, GWA, strand; honors over the limit."),
          (P, "applicant/apply-programs.html", "6", "Programs", "Three choices in order; a nudge to add the third."),
          (P, "applicant/apply-programs.html#picker", "6a", "Program picker", "Campus first, then program.", True),
          (P, "applicant/apply-programs.html#dup", "6b", "Duplicate choice", "Can’t pick the same program twice.", True),
          (P, "applicant/apply-review.html", "7", "Review", "Everything on one screen with Edit links."),
          (P, "applicant/apply-review.html#confirm", "7a", "Submit?", "Says what can and can’t change after.", True),
          (P, "applicant/apply-review.html#submitting", "7b", "Submitting", "Don’t close the page.", True),
          (P, "applicant/apply-review.html#missing", "7c", "Something missing", "Names exactly what is missing.", True)]),
       ("Pay", [
          (P, "applicant/payment.html#submitted", "8", "Pay the fee", "Amount, where to pay, reference and receipt photo."),
          (P, "applicant/payment.html#uploading", "8a", "Sending receipt", "Progress with Cancel.", True),
          (P, "applicant/payment.html#ref-used", "8b", "Reference already used", "Caught before a cashier has to.", True),
          (P, "applicant/payment-waiting.html#sent", "9", "Waiting for approval", "What was sent, and that an email will come."),
          (P, "applicant/payment-rejected.html", "10", "Rejected", "The cashier’s reason and a way to send again."),
          (D, "docs/email-approved.html", "11", "Email: approved", "Examinee number and one button: pick a seat."),
          (D, "docs/email-rejected.html", "12", "Email: rejected", "The reason and a link straight back.")]),
       ("Seat and permit", [
          (P, "applicant/seat.html#approved", "13", "Pick a seat", "Live seats left per session; full ones are greyed."),
          (P, "applicant/seat.html#loading", "13a", "Loading sessions", "Skeleton rows, never a blank screen.", True),
          (P, "applicant/seat.html#confirm", "13b", "Confirm seat", "One change allowed until Mar 1.", True),
          (P, "applicant/seat.html#taken", "13c", "Seat just taken", "Someone booked the last seat first.", True),
          (P, "applicant/permit.html#booked", "14", "Permit", "QR, number, room and seat. Works offline once opened."),
          (P, "applicant/permit.html#making", "14a", "Making the PDF", "Built once, saved for next time.", True),
          (D, "docs/permit-pdf.html", "15", "Permit PDF", "A4 with letterhead, photo and verify QR.")]),
       ("After exam day", [
          (P, "applicant/result-pending.html", "16", "Waiting for results", "Release date and attendance."),
          (P, "applicant/result-pending.html#absent", "16a", "Marked absent", "Who to contact and by when.", True),
          (P, "applicant/survey.html", "17", "Survey", "Optional, one minute, can skip."),
          (D, "docs/email-results.html", "18", "Email: results out", "One button to the result."),
          (P, "applicant/result.html", "19", "Result", "Overall score, stanine, plain meaning, each subject."),
          (P, "applicant/result.html#cutoffs", "19a", "Program cut-offs", "Qualified or not per choice.", True),
          (D, "docs/result-pdf.html", "20", "Result PDF", "Official copy with verify link.")]),
       ("Notifications", [
          (P, "applicant/notifications.html", "23", "Notification centre", "Every update in one list; unread on top."),
          (P, "applicant/notifications.html#prefs", "23a", "How to reach me", "Email always, texts optional, English or Filipino.", True),
          (P, "applicant/notifications.html#empty", "23b", "Nothing yet", "", True),
          (D, "docs/sms.html", "24", "Text messages", "Every SMS, under 160 characters.")]),
       ("Account", [
          (P, "applicant/profile.html", "21", "My account", "Change photo, choices or seat while allowed."),
          (P, "applicant/profile.html#photo", "21a", "Change photo", "", True),
          (P, "applicant/profile.html#history", "21b", "My history", "Every step with its date.", True),
          (D, "public/error.html", "22", "Error pages", "404, busy queue and server error, each with a next step.")])],
      [("Big and few words", "Lexend, 16 px inputs, 60 px buttons, one action per screen."), ("Never lose work", "Autosave, offline typing, retry on upload."),
       ("Say what happens next", "Every success says the next step; every error says how to fix it."), ("Safe answer first", "Dialogs put Cancel or Back below the main action."),
       ("Status in words", "Colour never carries meaning alone."), ("Phone first", "Every applicant screen is drawn at 390 px.")])

admin_pages = [("dashboard", "", "Dashboard", "Today’s numbers, sign-ups, demand and what needs attention."),
               ("applications", "", "Applications", "Search, filter, export; status in words."),
               ("applications", "rowmenu", "Row actions", "Open, resend permit, move, cancel."),
               ("applications", "loading", "Searching", "Skeleton while 16k rows are searched."),
               ("applications", "empty", "No results", "Empty state with Clear search."),
               ("applicant", "", "Applicant record", "Everything about one applicant plus the full history."),
               ("applicant", "edit", "Edit details", "Form with a date error; a reason is required."),
               ("applicant", "move", "Move session", ""), ("applicant", "cancel", "Cancel application", "Type CANCEL to confirm."),
               ("payments", "", "Payment review", "Queue, receipt and decision side by side; keyboard keys."),
               ("payments", "approve", "Reused reference warning", ""), ("payments", "approved", "Approved", "Number issued, next one opens."),
               ("payments", "reject", "Reject confirm", ""), ("payments", "conflict", "Two reviewers", "Someone else decided first."),
               ("payments", "empty", "All caught up", ""),
               ("seasons", "", "Seasons", "One open season at a time."), ("seasons", "new", "New season form", ""), ("seasons", "open-conflict", "Season conflict", ""),
               ("sessions", "", "Sessions and seats", "Live seat meters, open or close each session."), ("sessions", "add", "Add session form", "With a rooms error."),
               ("sessions", "added", "Session added", "Waiting applicants are emailed."), ("sessions", "toggle", "Close session", ""),
               ("checkin", "", "Check-in monitor", "Every room live on exam day."), ("checkin", "call", "Proctor offline", ""),
               ("scores", "", "Scores import", "Upload, check, commit; problem rows listed."), ("scores", "uploading", "Reading the file", ""),
               ("scores", "badfile", "Bad file", ""), ("scores", "commit", "Commit confirm", ""),
               ("results", "", "Results", "Schedule or release; search results."), ("results", "release", "Release confirm", "Can’t be taken back."),
               ("results", "releasing", "Sending emails", ""), ("result-detail", "", "One result", "Raw and standard scores per subject."),
               ("result-detail", "fix", "Correct a score", ""), ("reports", "", "Reports", "Every old report, plus attendance and survey."),
               ("report-view", "", "Ranking report", ""), ("exports", "", "Downloads", "Big files build in the background."),
               ("exports", "queued", "Export queued", ""), ("campuses", "", "Campuses and programs", ""), ("campuses", "program", "Add program form", ""),
               ("campuses", "off", "Stop offering", ""), ("staff", "", "Staff and roles", "Invite only."), ("staff", "invite", "Invite form", ""),
               ("staff", "last-admin", "Last admin guard", ""), ("audit", "", "Activity log", "Who did what, filterable."), ("account", "", "My account", "")]


def admin_frames(kind):
    out, n, sub = [], 0, 0
    for page, st, title, cap in admin_pages:
        if st:
            sub += 1
            num = f"{n}{chr(96 + sub)}"
        else:
            n += 1
            sub = 0
            num = str(n)
        out.append((kind, f"admin/{page}.html" + (f"#{st}" if st else ""), num, title, cap, bool(st)))
    return out


def numbered(kind, items):
    """Number screens 1, 2, 3 and their states 1a, 1b; items are (src, title, caption)."""
    out, n, sub = [], numbered.n, 0
    for src, title, cap in items:
        if "#" in src:
            sub += 1
            out.append((kind, src, f"{n}{chr(96 + sub)}", title, cap, True))
        else:
            n += 1
            sub = 0
            out.append((kind, src, str(n), title, cap, False))
    numbered.n = n
    return out


numbered.n = 0
ADMIN_CYCLE = [
    ("1 · Sign in", [
        ("public/staff-login.html", "Staff sign-in", "Invite-only. Google with the sksu.edu.ph account, or an email link."),
        ("public/staff-login.html#sent", "Link sent", "The link works for 15 minutes."),
        ("public/staff-login.html#not-staff", "Not a staff account", "A student’s Google account can’t get in."),
        ("public/staff-login.html#expired", "Expired link", "One button sends a new one.")]),
    ("2 · Set up the season", [
        ("admin/seasons.html", "Seasons and rounds", "A season (school year) holds 1–3 exam rounds; nothing is tied to a year in code."),
        ("admin/setup-1.html", "New season · step 1 Basics", "A stepper, because each step needs the one before."),
        ("admin/setup-2.html", "Step 2 Rounds", ""),
        ("admin/setup-3.html", "Step 3 Campuses and programs", ""),
        ("admin/setup-4.html", "Step 4 Sessions and rooms", ""),
        ("admin/setup-5.html", "Step 5 Review and open", ""),
        ("admin/setup-5.html#open", "Open registration", ""),
        ("admin/seasons.html#open-conflict", "Another season is open", "Save as draft, or close the old one first."),
        ("admin/seasons.html#created", "Season saved", ""),
        ("admin/seasons.html#round", "Add or edit a round", "Each round has its own registration, exam day and release; date error shown."),
        ("admin/seasons.html#round-saved", "Round saved", ""),
        ("admin/campuses.html", "Campuses and programs", "Seven campuses; each program is switched on per season."),
        ("admin/campuses.html#program", "Add program form", ""),
        ("admin/campuses.html#campus", "Add campus form", ""),
        ("admin/campuses.html#off", "Stop offering a program", "Says how many applicants already picked it."),
        ("admin/staff.html", "Staff and roles", "Cashiers, proctors and the testing center, by role."),
        ("admin/staff.html#invite", "Invite staff form", ""),
        ("admin/staff.html#invited", "Invite sent", ""),
        ("admin/staff.html#role", "Change a role", ""),
        ("admin/staff.html#last-admin", "Last admin guard", "The system refuses, instead of warning.")]),
    ("3 · Exam schedule and rooms", [
        ("admin/rooms.html", "Rooms", "Buildings, rooms and exam seats per campus, reused every season."),
        ("admin/rooms.html#room", "Add a room", "With a hint on how to count seats."),
        ("admin/rooms.html#import", "Import rooms", ""),
        ("admin/sessions.html", "Schedule days", "Campus and date only; report and start times are a guide on the permit."),
        ("admin/sessions.html#times", "Guide times", ""),
        ("admin/sessions.html#sittings", "Two sittings a day (off)", "Only if a day overflows."),
        ("admin/sessions.html#add", "Add session form", "Shown with a validation error on rooms."),
        ("admin/sessions.html#added", "Session added", "Waiting applicants are emailed by themselves."),
        ("admin/sessions.html#toggle", "Close a session", "People already booked keep their seats."),
        ("admin/sessions.html#auto", "Auto-assign seats", "Preview who gets a seat before it happens."),
        ("admin/sessions.html#assigned", "Seats assigned", "Undo for one hour."),
        ("docs/seat-plan.html", "Seat plan printout", "One sheet per room for the proctor and the door.")]),
    ("4 · Registration is running", [
        ("admin/dashboard.html", "Dashboard", "Only what needs action: payments to review, approved with no seat, seats left, then the attention list."),
        ("admin/dashboard.html#loading", "Loading", "Skeleton, never a blank page."),
        ("admin/applications.html", "Applications", "16k applicants, filters, export; status in words."),
        ("admin/applications.html#loading", "Searching", ""),
        ("admin/applications.html#empty", "No match", ""),
        ("admin/applications.html#view", "View: quick look", "A drawer on the right keeps the list in place."),
        ("admin/applications.html#menu", "··· menu", "Every row action, with the destructive one last and red."),
        ("admin/applications.html#bulk", "Bulk actions", "Tick rows, then remind, auto-seat or export."),
        ("admin/applications.html#bulk-remind", "Bulk reminder", "Template preview and cost before sending."),
        ("admin/applications.html#dupes", "Duplicate applicants", "Side by side; merge or mark not the same."),
        ("admin/applications.html#saveview", "Save a view", "Filters you use daily, one click away."),
        ("admin/search.html", "Global search", "Press / anywhere: names, numbers, references."),
        ("admin/applications.html#resent", "Permit email resent", ""),
        ("admin/messages.html", "Messages", "Templates, blasts and delivery."),
        ("admin/messages.html#tpl", "Edit a template", ""),
        ("admin/messages.html#confirm", "Send a blast", ""),
        ("admin/messages.html#sent", "Blast sent", ""),
        ("admin/messages.html#resend", "Resend a failed message", "Fix the number, resend, see it delivered."),
        ("admin/applicant.html", "One applicant", "Full record and every change with who and when."),
        ("admin/applicant.html#edit", "Edit details form", "Date error shown; a reason is required."),
        ("admin/applicant.html#saved", "Saved with reason", ""),
        ("admin/applicant.html#move", "Move to another session", ""),
        ("admin/applicant.html#moved", "Moved, email sent", ""),
        ("admin/applicant.html#cancel", "Cancel application", "Type CANCEL; the seat is freed."),
        ("admin/applicant.html#photo", "Review an upload", "Ask for a new photo without losing the seat.")]),
    ("5 · Payments, numbers and permits", [
        ("cashier/console.html", "Cashier console", "Its own role and screen: search, fixed fee, OR no., Enter."),
        ("admin/cashier.html", "Cashier counters", "Every counter’s payments and voids."),
        ("admin/payments.html", "Payment review (uploaded receipts)", "Queue, receipt and decision side by side; A and R keys."),
        ("admin/payments.html#approve", "Reused reference warning", "Caught before a double approval."),
        ("admin/payments.html#approved", "Approved, number issued", "Examinee no. comes from the season counter; next one opens."),
        ("admin/payments.html#reject", "Reject confirm", "The reason goes to the applicant by email."),
        ("admin/payments.html#rejected", "Rejected", ""),
        ("admin/payments.html#conflict", "Two cashiers, one receipt", "Whoever is second is told and moved on."),
        ("admin/payments.html#empty", "All caught up", ""),
        ("docs/email-approved.html", "What the applicant gets: approved", ""),
        ("docs/email-rejected.html", "What the applicant gets: rejected", ""),
        ("docs/permit-pdf.html", "Permit issued", "After the applicant picks a seat; QR links to the verify page.")]),
    ("6 · Exam day", [
        ("admin/checkin.html", "Check-in monitor", "Every room live: present, absent, pending, phone sync."),
        ("admin/checkin.html#call", "A proctor is offline", "Name, number, and assign someone else."),
        ("proctor/checkin.html", "What the proctor sees", "Their phone at the door, scanning permits."),
        ("proctor/summary.html#closed", "Room closed", "Counts arrive on the monitor.")]),
    ("7 · Scores", [
        ("admin/scores.html", "Scores import", "Upload the Testing Center CSV, match columns, see problem rows and what changes, approve."),
        ("admin/scores.html#uploading", "Uploading the CSV", "Progress while the file goes up."),
        ("admin/scores.html#checking", "Checking rows", "A row counter and problems found so far."),
        ("admin/scores.html#bg", "Running in the background", "Leave the page; the bell tells you when it’s done."),
        ("admin/scores.html#summary", "Import summary", "Ready, skipped, problems; download the problem rows."),
        ("admin/scores.html#map", "Match columns", "Remembered for next time."),
        ("admin/scores.html#badfile", "Two tables in one file", "The 2026 layout is caught with a clear fix."),
        ("admin/scores.html#commit", "Commit confirm", "Scores are computed and frozen, not yet visible.")]),
    ("8 · Review and publish results", [
        ("admin/results.html#committed", "Results", "Scheduled release; scored, absent and missing counted."),
        ("admin/results.html#release", "Release now?", "Can’t be taken back."),
        ("admin/results.html#releasing", "Sending emails", "Runs in the background."),
        ("admin/results.html#released", "Released", ""),
        ("admin/results.html#report", "Delivery report", "In app, email and text delivered; failures to resend."),
        ("admin/result-detail.html", "One result", "Raw and standard score per subject."),
        ("admin/result-detail.html#fix", "Correct a score", "Recomputed, with the old value kept."),
        ("docs/email-results.html", "What the applicant gets", ""),
        ("docs/result-pdf.html", "Official result PDF", "")]),
    ("9 · Reports, downloads and audit", [
        ("admin/reports.html", "Reports", "Every old report plus attendance and survey."),
        ("admin/report-view.html", "Ranking per program", ""),
        ("admin/exports.html", "Downloads", "Big files build in the background."),
        ("admin/exports.html#queued", "Export queued", ""),
        ("admin/exports.html#retry", "Retry a failed export", ""),
        ("admin/audit.html", "Activity log", "Who did what, with Undo on recent actions."),
        ("admin/audit.html#undo", "Undo an approval", ""),
        ("admin/account.html", "My account", ""),
        ("admin/account.html#others", "Signed out other devices", "")]),
]
ADMIN_PHONE = ["admin/dashboard.html", "admin/applications.html", "admin/applicant.html", "admin/payments.html", "admin/payments.html#approved",
               "admin/sessions.html", "admin/sessions.html#add", "admin/checkin.html", "admin/results.html#release", "admin/staff.html#invite"]

sections = [(name, numbered(D, items)) for name, items in ADMIN_CYCLE]
sections.append(("10 · The same pages on a phone", numbered(P, [(src, "Phone: " + next(t for _, its in ADMIN_CYCLE for s2, t, _c in its if s2 == src), "") for src in ADMIN_PHONE])))
board("ADMIN-JOURNEY-MOCKUP.html", "Admin: the full season",
      "Everything the admission office does in one season, in order: sign in, set up the season, build the exam schedule, run registration, "
      "approve payments and issue numbers, run exam day, import scores, publish results, then report. Every form and every state is its own frame. "
      "Click any screen to open it.",
      sections,
      [("One green button per area", "Danger actions are red and always behind a confirm."), ("Every change has a reason", "Edits, moves and corrections ask why and write the history."),
       ("Nothing waits on a spinner", "Exports, emails and score maths run in the background."), ("Tables fold on a phone", "Each row becomes a card; filters stack."),
       ("Guards, not warnings", "Can’t remove the last admin, can’t double-approve, can’t overbook."), ("Same words as the applicant sees", "Draft, In review, Approved, Scheduled, Scored.")])


board("PROCTOR-JOURNEY-MOCKUP.html", "Proctor: exam day",
      "What a proctor does on exam day, on their own phone, with no signal needed after the lists are downloaded.",
      [("Before the exam", [(P, "proctor/rooms.html", "1", "My rooms", "Today’s rooms and how many examinees."),
                            (P, "proctor/rooms.html#download", "1a", "Saving lists", "Lists are stored on the phone.", True)]),
       ("At the door", [(P, "proctor/checkin.html", "2", "Scan permits", "Right room, photo to compare, Present or Absent."),
                        (P, "proctor/checkin.html#present", "2a", "Checked in", "", True), (P, "proctor/checkin.html#wrong", "2b", "Wrong room", "Says where to send them.", True),
                        (P, "proctor/checkin.html#dupe", "2c", "Already scanned", "A copied permit is caught.", True), (P, "proctor/checkin.html#absent", "2d", "Mark absent", "", True),
                        (P, "proctor/checkin.html#search", "2e", "No QR", "Search by name or number.", True),
                        (P, "public/verify.html", "3", "Verify page", "What the QR opens on any phone."), (P, "public/verify.html#invalid", "3a", "Invalid permit", "", True)]),
       ("After", [(P, "proctor/summary.html", "4", "Room summary", "Counts and anything still unsent."), (P, "proctor/summary.html#close", "4a", "Close room", "", True),
                  (P, "proctor/summary.html#closed", "4b", "Closed", "", True), (P, "proctor/summary.html#sync-fail", "4c", "No signal", "Retries by itself.", True),
                  (D, "admin/checkin.html", "5", "Admin sees it live", "Every room’s counts on the check-in monitor.")])],
      [("Works offline", "Lists download first; check-ins queue and send later."), ("Big targets", "60 px buttons, one hand."), ("Catch mistakes", "Wrong room and copied permits are flagged on scan.")])


# ---------------------------------------------------------------- cashier console (its own role and screen)
def cashier(key, title, body, tab="counter", overlays="", states=None):
    tabs = "".join(f'<a href="{h}" class="{"on" if t == tab else ""}">{label}</a>' for t, label, h in [("counter", "Counter", "console.html"), ("list", "Applicants", "applicants.html"), ("today", "Today", "today.html")])
    doc(f"cashier/{key}.html", title, f"""<div class="strip"><strong>SKSU TPT · CASHIER MOCKUP</strong><span class="muted">sample data</span><a class="sp" href="../index.html">All pages</a></div>
<div class="cshell"><header class="ctop"><img src="../assets/sksu-seal.png" alt="SKSU seal"><b>Cashier</b><nav>{tabs}</nav>
<span class="cwho"><span class="dot"></span>Cashier 1 · Isulan counter 1</span><span class="cshift">Today ₱18,000 · 36 paid</span></header>
<main class="cmain">{body}</main></div>{overlays}""", states=states)


APPLICANT_CARD = f"""<div class="ccard"><div class="thumb cthumb">Photo</div><div class="cinfo"><b>Lea M. Sampulna</b><span class="mono">APP-27-10422</span><span>BSEd Mathematics · Kalamansig · Round 2</span>{B("warn", "Waiting for payment")}</div></div>"""
RECENT = [("9:41", "Ramon T. Villanueva", "0048213", "Cash"), ("9:12", "Princess A. Lumabao", "0048212", "Cash"), ("8:47", "Datu R. Mamalinta", "0048211", "GCash at counter")]
STRIP = '<div class="cstrip"><b>Last paid</b>' + "".join(f'<a href="today.html"><span class="mono">{t}</span>{n}<span class="mono">OR {o}</span></a>' for t, n, o, _ in RECENT) + '<a class="more" href="today.html">All today →</a></div>'

cashier("console", "Counter", f"""<section class="cleft"><label for="find" class="clabel">Find the applicant</label>
<div class="cfind"><input id="find" value="Lea Sampulna" placeholder="Name, application no. or examinee no." autofocus></div>
<small class="hint">Press <kbd>/</kbd> to search. The application number is on the applicant’s Pay screen.</small>
{APPLICANT_CARD}</section>
<section class="cright"><span class="clabel">Exam fee</span><div class="fee">₱500.00</div><small class="hint">Fixed for Season 2027. A fee waiver is set by the admission office, not here.</small>
<div class="fld"><label for="or">Official receipt no.</label><input id="or" class="orno" value="0048214" autofocus>{hint("The next number on your OR booklet. It must be unused.")}</div>
<div class="fld"><label>Paid with</label><div class="seg big"><span class="on">Cash</span><span>GCash at counter</span><span>Check</span></div></div>
<a class="btn primary xl" href="#done">Record payment <kbd>Enter</kbd></a></section>
{STRIP}""",
        overlays=modal("done", "ok", OK, "Paid · Lea M. Sampulna", '<div class="kv"><span>OR no.</span><b class="mono">0048214</b><span>Amount</span><b>₱500.00 cash</b><span>Examinee no.</span><b class="mono">500231</b></div><p class="muted" style="margin:0">Lea got a text and an email and can now pick her exam day. Ready for the next person in 5 s…</p><div class="progress"><span style="width:40%"></span></div>', btn("Print OR copy") + btn("Next person", "console.html", "primary"))
        + modal("paid", "warn", WARN, "Already paid", '<p class="muted" style="margin:0">Jomar P. Abdullah paid on Jan 12 (OR 0048190, Isulan counter 2). Don’t take another payment.</p>', btn("Reprint that OR") + btn("OK", "#", "primary"))
        + modal("orused", "bad", BAD, "OR 0048213 is already used", '<p class="muted" style="margin:0">It was recorded at 9:41 for Ramon T. Villanueva. Check your booklet and type the next number.</p>', btn("OK", "#", "primary"))
        + modal("notfound", "info", "", "No applicant found for “Lea Sampolna”", '<p class="muted" style="margin:0">Check the spelling, or ask for the application number on their phone (Home screen). Walk-ins must apply online first.</p>', btn("OK", "#", "primary"))
        + modal("round", "warn", WARN, "Applied for Round 3, not open yet", '<p class="muted" style="margin:0">Round 3 payments start Apr 11. Ask the applicant to come back then, or move to Round 2 in their app.</p>', btn("OK", "#", "primary"))
        + modal("waived", "info", "", "Fee waived", '<p class="muted" style="margin:0">Aisah K. Mangudadatu’s fee was waived by the admission office (indigent). Nothing to collect.</p>', btn("OK", "#", "primary")),
        states=[("done", "Recorded"), ("paid", "Already paid"), ("orused", "OR already used"), ("notfound", "Not found"), ("round", "Wrong round"), ("waived", "Fee waived")])

CROWS = [("APP-27-10422", "Lea M. Sampulna", "BSEd Mathematics", "Kalamansig", False), ("APP-27-10431", "Noel B. Guiamal", "BS Criminology", "Isulan", False), ("APP-27-10437", "Jasmine O. Kusain", "BS Information Technology", "ACCESS", False),
         ("APP-27-10440", "Rodel A. Sangki", "BS Agriculture", "Tacurong", False), ("APP-27-10398", "Ramon T. Villanueva", "BS Agriculture", "Tacurong", True), ("APP-27-10377", "Princess A. Lumabao", "BS Accountancy", "ACCESS", True)]
cashier("applicants", "Applicants", f"""<div class="pagehead"><div><h1>Applicants · Round 2</h1><p>Everyone who submitted an application. Click a row to record their payment. Nothing else can be changed here.</p></div></div>
<div class="filters"><input class="search" aria-label="Search applicants" placeholder="Search name or application no." style="width:320px"><span class="seg"><span class="on">Waiting for payment · 1,204</span><span>Paid · 9,471</span><span>All</span></span><select aria-label="Campus"><option>All campuses</option><option>Isulan</option><option>ACCESS</option></select></div>
{table(["Application no.", "Applicant", "1st choice", "Campus", "Payment", ""], [(f'<span class="mono">{a}</span>', n, prg, c, B("ok", "Paid") if paid else B("warn", "Waiting"), "" if paid else btn("Record payment", "console.html", "sm primary")) for a, n, prg, c, paid in CROWS])}
<div class="head"><span class="muted">Showing 6 of 1,204 waiting</span><span style="display:flex;gap:6px">{btn("Previous")}{btn("Next")}</span></div>""", tab="list")

cashier("today", "Today", f"""<div class="pagehead"><div><h1>Today at Isulan counter 1</h1><p>Every payment you recorded today, to match against your OR booklet. Only an admin can void a payment.</p></div><div class="pacts">{btn("Export today’s list (Excel)", "../admin/exports.html#queued")}{btn("Print list")}</div></div>
<div class="kpis" style="grid-template-columns:repeat(3,1fr)"><div class="kpi"><span>Collected</span><b>₱18,000.00</b><small>36 payments</small></div><div class="kpi"><span>Cash</span><b>₱16,500.00</b><small>33</small></div><div class="kpi"><span>GCash at counter</span><b>₱1,500.00</b><small>3</small></div></div>
{table(["Time", "Applicant", "OR no.", "Paid with", "Amount", ""], [(f'<span class="mono muted">{t}</span>', n, f'<span class="mono">{o}</span>', m, "₱500.00", '<span class="act">' + btn("Reprint", "#") + "</span>") for t, n, o, m in RECENT] + [('<span class="mono muted">8:20</span>', "Jasmine O. Kusain", '<span class="mono">0048210</span>', "Cash", '<s>₱500.00</s> ' + B("bad", "Voided"), "")])}""",
        tab="today")

board("CASHIER-JOURNEY-MOCKUP.html", "Cashier: one counter, one fee",
      "A cashier records that the exam fee was paid: OR number, amount, who and when. Cash handling and remittance stay in the university’s own accounting. Click any screen to open it.",
      [("Take a payment", [(D, "cashier/console.html", "2", "Counter", "Search, fixed fee, OR no., Enter."),
                           (D, "cashier/console.html#done", "2b", "Paid", "Print OR copy, next person.", True),
                           (D, "cashier/console.html#paid", "2c", "Already paid", "", True), (D, "cashier/console.html#orused", "2d", "OR already used", "", True),
                           (D, "cashier/console.html#notfound", "2e", "Not found", "", True), (D, "cashier/console.html#round", "2f", "Wrong round", "", True),
                           (D, "cashier/console.html#waived", "2g", "Fee waived", "", True)]),
       ("During the day", [(D, "cashier/applicants.html", "2h", "Applicants list", "Browse waiting applicants; click to record."), (D, "cashier/today.html", "3", "Today", "Reprint; export to match the OR booklet."), (D, "admin/cashier.html", "4", "Admin sees every counter", "")])],
      [("One fee, no typing amounts", "The fee is fixed; waivers come from the admission office."), ("Keyboard first", "/ to search, Enter to record, Esc to clear."), ("Nothing is deleted", "Only an admin can void, with a reason; voided payments stay on the list.")])


# ---------------------------------------------------------------- index with coverage checklist
MAP = [
    ("/", "welcome", "public/landing.html"), ("/auth/google, /auth/google/callback", "auth/login", "public/login.html"),
    ("/admin/login", "auth/login-admin", "public/staff-login.html"), ("/forgot-password, register, reset-password, verify-email, two-factor", "auth/*", "public/login.html (Google or email link) · public/staff-login.html"),
    ("/privacy-policy, terms, policy", "privacy-policy, terms, policy", "public/privacy.html"),
    ("(none)", "", "public/verify.html · public/error.html (new)"),
    ("/dashboard", "dashboard", "No page: sends you to applicant/home or admin/dashboard by role"),
    ("/applicant/home", "applicant/home, get-started-button, menu", "applicant/home.html"),
    ("/applicant/fill/application", "fill-application, personal-info, previous-school, program-choice, button-submit-application", "applicant/apply-personal → apply-school → apply-programs → apply-review"),
    ("/applicant/payment", "payment, payment-section, resubmit-payment", "applicant/payment · payment-waiting · payment-rejected"),
    ("/applicant/select-test-center", "select-test-center, select-testing-center", "applicant/seat.html"),
    ("/applicant/permit, /permit/{permit}, /generate-pdf/{permit}", "permit, permit-layout, view-permit", "applicant/permit.html · docs/permit-pdf.html"),
    ("/applicant/survey", "survey", "applicant/survey.html (optional now)"),
    ("/applicant/select-course", "select-courses", "applicant/apply-programs.html (choices kept, no second pick)"),
    ("/applicant/result and the result-PDF routes", "result, result-2026, examination-result-pdf, result-pdf-2026", "applicant/result-pending · result · docs/result-pdf.html"),
    ("(profile)", "update-photo, update-program-choice, profile/*", "applicant/profile.html · admin/account.html"),
    ("(emails)", "emails/application-approve, application-reject", "docs/email-approved · email-rejected · email-results"),
    ("/admin/dashboard", "admin/dashboard", "admin/dashboard.html"),
    ("/admin/users", "admin/users, livewire/admin/user", "admin/applications.html · admin/staff.html"),
    ("/admin/manage-examination/{id}/applications", "manage-examination/applications, applications/*", "admin/applications.html · admin/applicant.html"),
    ("(payments)", "admin/payments, applications/view-payment", "admin/payments.html"),
    ("/admin/examinations", "admin/examinations, examination/*", "admin/seasons.html"),
    ("/admin/manage-examination/{id}/applications/slots", "manage-examination/slot, manage-slot", "admin/sessions.html · docs/seat-plan.html"),
    ("/admin/monitoring", "admin/monitoring", "admin/checkin.html"),
    ("(results upload)", "results import", "admin/scores.html"),
    ("/admin/examination-with-results, /examination-results/{id}, /examinee-result-details/{id}", "examination-with-result-page, examination-result-page, examinee-result-details", "admin/results.html · admin/result-detail.html"),
    ("/admin/report, student-list, registration-date, student-report, ranking, qualified, students-score", "reports, *-report, ranking-result, student-scores", "admin/reports.html · admin/report-view.html"),
    ("/admin/export/*, /admin/exports, /exports/download/{f}", "exports/*", "admin/exports.html"),
    ("/admin/campuses, /admin/programs", "campuses, programs, program-offers/*, campus-management", "admin/campuses.html"),
    ("/admin/permit/{permit}/view", "view-only-permit", "admin/applicant.html (Permit tab) · docs/permit-pdf.html"),
    ("(none)", "", "admin/staff.html · admin/audit.html · proctor/rooms · checkin · summary (new)"),
    ("Test and debug routes (list kept offline)", "test views", "Removed on purpose"),
]
groups = [
    ("Journey mockups (start here)", ["ADMIN-JOURNEY-MOCKUP.html", "APPLICANT-JOURNEY-MOCKUP.html", "CASHIER-JOURNEY-MOCKUP.html", "PROCTOR-JOURNEY-MOCKUP.html"]),
    ("Cashier", ["cashier/console.html", "cashier/applicants.html", "cashier/today.html"]),
    ("Public", ["public/landing.html", "public/login.html", "public/staff-login.html", "public/verify.html", "public/privacy.html", "public/error.html"]),
    ("Applicant (phone)", ["applicant/splash.html", "applicant/welcome-1.html", "applicant/welcome-2.html", "applicant/welcome-3.html"] + [f"applicant/{k}.html" for k, _ in FLOW]),
    ("Emails and printouts", ["docs/sms.html", "docs/email-approved.html", "docs/email-rejected.html", "docs/email-results.html", "docs/permit-pdf.html", "docs/result-pdf.html", "docs/seat-plan.html"]),
    ("Proctor (phone)", ["proctor/rooms.html", "proctor/checkin.html", "proctor/summary.html"]),
    ("Admin", [f"admin/{k}.html" for k in ["dashboard", "search", "messages", "rooms", "cashier", "setup-1", "setup-2", "setup-3", "setup-4", "setup-5", "applications", "applicant", "payments", "seasons", "sessions", "checkin", "scores", "results", "result-detail", "reports", "report-view", "exports", "campuses", "staff", "audit", "account"]]),
]
flows = [("Applicant, start to result", "public/landing.html"), ("Payment review", "admin/payments.html"), ("Exam day", "proctor/rooms.html"), ("Scores to release", "admin/scores.html")]


def title_of(path):
    html = PAGES[path]
    return html[html.index("<title>") + 7:html.index(" · SKSU TPT</title>")]


grid = "".join(f'<section><h2 style="margin-bottom:10px">{g}</h2><div class="grid">' + "".join(f'<a href="{p}"><b>{title_of(p)}</b><span class="muted mono" style="font-size:12px">{p}</span></a>' for p in items) + "</div></section>" for g, items in groups)
flow_links = " ".join(f'<a class="btn" href="{h}">{t} →</a>' for t, h in flows)
maptable = table(["Old route (tptv3)", "Old views", "New mockup page"], [(f'<span class="mono">{r}</span>', f'<span class="muted">{v}</span>', p) for r, v, p in MAP])
doc("index.html", "All pages", f"""<div class="idx"><header><img src="assets/sksu-seal.png" alt="SKSU seal"><div><div class="wm"><b>Sultan Kudarat</b><span>State University</span></div><h1>Admission Test (TPT) v4 mockups</h1>
<span class="muted">{len(PAGES) + 1} pages, one per screen. Light mode, sample data. Buttons and menus link like the real app. The yellow bar on a page lists its states (dialogs, toasts, loading, errors).</span></div></header>
<div class="toplinks"><a href="ADMIN-JOURNEY-MOCKUP.html"><b>Admin journey</b><span>The whole season in order, every form and state</span></a><a href="APPLICANT-JOURNEY-MOCKUP.html"><b>Applicant journey</b><span>Public page to result, on a phone</span></a><a href="PROCTOR-JOURNEY-MOCKUP.html"><b>Proctor journey</b><span>Exam day at the door</span></a></div>
<section><h2 style="margin-bottom:10px">Walk a flow</h2><div style="display:flex;gap:8px;flex-wrap:wrap">{flow_links}</div></section>
{grid}
<section><h2 style="margin-bottom:10px">Coverage: every tptv3 route and view</h2><div class="mapt">{maptable}</div></section>
<section><h2 style="margin-bottom:10px">Interaction rules</h2>{table(["When you need to…", "Use", "Example"], [
    ("Look at one record without losing the list", "Side drawer", '<a href="admin/applications.html#view">View an applicant</a>'),
    ("Pick one of several actions on a row", "··· menu; destructive item last, in red", '<a href="admin/applications.html#menu">Row menu</a>'),
    ("Change 1 to 6 fields", "Modal", '<a href="admin/applicant.html#edit">Edit details</a>'),
    ("Fill a long form or several sections", "Full page", '<a href="admin/applicant.html">Applicant record</a>'),
    ("Do steps that depend on the one before", "Stepper", '<a href="admin/setup-1.html">New season</a> · <a href="admin/scores.html">Scores</a> · applicant registration'),
    ("Delete, cancel, release or send to many", "Confirm dialog that says what happens", '<a href="admin/results.html#release">Release results</a>'),
    ("Confirm something worked", "Toast, 5 seconds, with Undo when possible", '<a href="admin/sessions.html#assigned">Seats assigned</a>'),
    ("Explain a field or step", "Grey hint under it; ? tooltip for rare cases", '<a href="admin/setup-1.html">Season basics</a>')])}</section>
<section><h2 style="margin-bottom:10px">Chart choices</h2>{table(["Question", "Chart", "Why", "Where"], [
    ("How are sign-ups going?", "Line with the area filled", "A trend over days; the line shows direction at a glance", '<a href="admin/dashboard.html">Dashboard</a>'),
    ("Where do applicants drop off?", "Funnel of horizontal bars", "Ordered stages; the drop between them is the point", '<a href="admin/reports.html">Reports</a>'),
    ("Which programs are most wanted?", "Horizontal bars, sorted", "Long names fit; easy to compare lengths", '<a href="admin/reports.html">Reports</a>'),
    ("How did scores spread?", "Histogram with the 500 line", "A distribution; bins match the 50-point stanine bands", '<a href="admin/reports.html">Reports</a>'),
    ("How many seats are left?", "Small progress meter per session", "One share per row; a chart would be noise", '<a href="admin/sessions.html">Sessions</a>'),
    ("Payments waiting, approved with no seat", "Plain number tile", "One number to act on; a chart adds nothing", '<a href="admin/dashboard.html">Dashboard</a>'),
    ("Pie charts", "Not used", "Hard to compare slices; bars say the same more clearly", "—")])}</section>
<section><h2 style="margin-bottom:10px">Admin features added</h2><div class="grid">{"".join(f'<a href="{h}"><b>{t}</b><span class="muted">{d}</span></a>' for t, d, h in [
    ("Global search", "Press / anywhere for names, numbers, references", "admin/search.html"),
    ("Bulk actions", "Remind, auto-seat or export many at once", "admin/applications.html#bulk"),
    ("Saved views", "Your everyday filters, shareable", "admin/applications.html#saveview"),
    ("Duplicate detector", "Same name + birth date or mobile; merge safely", "admin/applications.html#dupes"),
    ("Auto seat assignment", "Preview, then assign; undo for 1 hour", "admin/sessions.html#auto"),
    ("Messages and blasts", "Templates, email + SMS, cost shown first", "admin/messages.html"),
    ("Season setup wizard", "Copy last season, 5 steps", "admin/setup-1.html"),
    ("Score import checks", "Not registered, duplicate, out-of-range and missing rows before approval", "admin/scores.html"),
    ("Scheduled release", "Pre-built pages so release day stays fast", "admin/results.html"),
    ("Activity log with undo", "Every change, reversible for a while", "admin/audit.html#undo"),
    ("Role permissions", "Fixed roles, clear matrix", "admin/staff.html"),
    ("Proctor offline check-in", "Phones work without signal", "proctor/checkin.html")])}</div></section>
<a href="design-system.html">Design system →</a></div>""")

doc("design-system.html", "Design system", f"""<div class="idx"><div class="crumbs"><a href="index.html">All pages</a></div>
<header><img src="assets/sksu-seal.png" alt="SKSU seal"><div><h1>SKSU TPT design system</h1><span class="muted">Colours from the SKSU seal (tptv3 public/images/sksu1.png). Layout rules follow our v2 admin and app patterns. Light mode.</span></div></header>
<section class="panel"><h2>Colour</h2><div class="sw">{''.join(f'<div><i style="background:{c}"></i><b class="ink">{n}</b><span class="mono muted">{c}</span><span class="muted">{u}</span></div>' for c, n, u in [("#009A3C", "SKSU green", "brand"), ("#007A30", "Button green", "white text 5.4:1"), ("#007CC2", "SKSU blue", "charts, links"), ("#FFFF00", "Seal yellow", "small accents only"), ("#DA251C", "Seal red", "reserved"), ("#F6F8F6", "Panel", "sidebar, table heads")])}</div>
<div style="display:flex;gap:6px;flex-wrap:wrap">{B("gray", "Draft")}{B("warn", "In review")}{B("ok", "Approved")}{B("info", "Scheduled")}{B("ok", "Present")}{B("bad", "Rejected")}{B("bad", "Absent")}{B("vio", "Scored")}</div></section>
<section class="panel"><h2>Type</h2><div style="font-size:24px;font-weight:600" class="ink">Geist · staff screens</div><div style="font:700 24px var(--round)" class="ink">Lexend · applicant screens</div><div class="mono ink" style="font-size:20px;font-weight:700">500214 · 1009 284 551 203</div></section>
<section class="panel"><h2>Buttons</h2><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">{btn("Primary · md 40", "#", "primary")}{btn("Secondary", "#")}{btn("Ghost", "#", "ghost")}{btn("Cancel application", "#", "danger")}{btn("Disabled", "#", "primary disabled")}{btn("Saving", "#", "primary loading")}</div>
<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">{btn("Small · 32 (tables, toolbars)", "#", "sm")}{btn("Medium · 40 (default)", "#")}{btn("Large · 48 (main task)", "#", "lg primary")}<a class="go" href="#" style="width:260px;height:52px">Mobile CTA · 52</a></div>
<span class="muted">One primary button per view. Secondary and ghost are quieter. Red only for something that destroys or cancels.</span></section>
<section class="panel"><h2>States</h2><div style="display:flex;gap:8px;flex-wrap:wrap">{btn("Dialog", "#d", "")}{btn("Danger dialog", "#dd")}{btn("Success toast", "#t1")}{btn("Error toast", "#t2")}{btn("Loading", "#l")}</div>
<div class="alertbox ok">Success message</div><div class="alertbox warn">Warning message</div><div class="alertbox bad">Error message</div><div class="alertbox info">Info message</div>
<div class="fld err"><label for="x">Field with an error</label><input id="x" value="2008-13-12"><span class="errmsg">Not a real date.</span></div>
<div class="progress"><span style="width:64%"></span></div><div class="skel"></div><div class="empty">Empty state: nothing here yet.</div></section></div>
{modal("d", "info", "i", "A dialog", '<p class="muted" style="margin:0">One question, two buttons, safe answer first.</p>', btn("Cancel", "#") + btn("Confirm", "#", "primary"))}
{modal("dd", "bad", BAD, "A danger dialog", '<p class="muted" style="margin:0">Says what will be lost.</p>', btn("Keep it", "#") + btn("Delete", "#", "danger"))}
{toast("t1", "ok", OK, "Saved", "What happened, in one line.")}{toast("t2", "bad", BAD, "Couldn’t save", "What to do next.")}
{modal("l", "info", '<span class="spin"></span>', "Loading…", '<div class="skel"></div>', "")}""")


# ---------------------------------------------------------------- write
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "assets").mkdir(parents=True)
(OUT / "assets" / "style.css").write_text("".join((TOOLS / f).read_text(encoding="utf-8") for f in ("base.css", "theme.css", "theme-extra.css", "theme-app.css", "theme-admin.css", "theme-calm.css")), encoding="utf-8")
shutil.copyfile(TOOLS / "sksu-seal.png", OUT / "assets" / "sksu-seal.png")
(OUT / "docs").mkdir(parents=True, exist_ok=True)
shutil.copyfile(TOOLS / "tpt-scores-template.csv", OUT / "docs" / "tpt-scores-template.csv")
for extra in ("seal-faint.png", "seal-white.png", "campus-duo.jpg"):
    shutil.copyfile(TOOLS / extra, OUT / "assets" / extra)
for path, html in PAGES.items():
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")
print(f"wrote {len(PAGES)} pages to {OUT}")
