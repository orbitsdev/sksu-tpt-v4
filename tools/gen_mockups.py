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


def table(headers, rows, sortable=(), active=None):
    """sortable: header labels people can sort by; active: (label, "asc"|"desc") shows the arrow."""
    def th(h):
        if h not in sortable:
            return f"<th>{h}</th>"
        if active and h == active[0]:
            arrow, aria = ("↑", "ascending") if active[1] == "asc" else ("↓", "descending")
            return f'<th class="sort on" aria-sort="{aria}"><a href="#">{h}<i>{arrow}</i></a></th>'
        return f'<th class="sort"><a href="#">{h}<i>↕</i></a></th>'
    head = "".join(th(h) for h in headers)
    body = "".join(r if isinstance(r, str) else "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def pager(first, last, total):
    """One quiet line under a long list: what is shown, then Previous / Next."""
    return f'<div class="pager"><span class="muted">{first}–{last} of {total}</span><span>{btn("Previous", "#", "sm")}{btn("Next", "#", "sm")}</span></div>'


PROVINCES = {"Sultan Kudarat": ["Isulan", "Tacurong City", "Bagumbayan", "Columbio", "Esperanza", "Kalamansig", "Lambayong", "Lebak", "Lutayan", "Palimbang", "President Quirino", "Sen. Ninoy Aquino"],
             "Cotabato": ["Kidapawan City", "M'lang", "Tulunan"], "South Cotabato": ["Koronadal City", "Surallah", "Banga"], "Maguindanao del Sur": ["Buluan", "Datu Paglas", "Pandag"]}


def filters(search, selects=(), right="", extra="", more=False, showing=""):
    """The filter line of a list: plain selects, a search box that says exactly what it searches, quiet buttons on the right.
    more: a "More filters" link that opens the home-location filter (Province, then Municipality or city).
    showing: the line that appears when a filter is set ("Showing 790 · Waiting for payment · Isulan")."""
    sel = "".join(f'<select aria-label="{label}">{"".join(f"<option>{o}</option>" for o in opts)}</select>' for label, opts in selects)
    more_link = '<a class="fmore" href="#more">More filters</a>' if more else ""
    right_html = f'<span class="fright">{right}</span>' if right else ""
    line = f'<div class="filters"><input class="search" type="search" aria-label="Search" placeholder="{search}">{sel}{extra}{more_link}{right_html}</div>'
    if more:
        towns = "".join(f"<option>{t}</option>" for t in PROVINCES["Sultan Kudarat"])
        line += (f'<div class="morefilters" id="more"><span class="muted">Home location</span><select aria-label="Province"><option>Any province</option>{"".join(f"<option>{k}</option>" for k in PROVINCES)}</select>'
                 f'<select aria-label="Municipality or city"><option>Any municipality or city</option>{towns}</select><a class="btn sm" href="{'#filtered' if showing else '#'}">Apply</a><a class="fclear" href="#">Close</a></div>')
    if showing:
        line += f'<div class="factive" id="filtered">{showing}<a class="fclear" href="#">× Clear</a></div>'
    return line


def rowact(view, more="#menu", action=None):
    """Row actions, all visible as quiet text: View, at most one action that fits the row, then ··· for rare or risky ones."""
    act = f'<a class="btn" href="{action[1]}">{action[0]}</a> ' if action else ""
    dots = f'<a class="btn" href="{more}" aria-label="More actions">···</a>' if more else ""
    view_html = f'<a class="btn" href="{view}">View</a> ' if view else ""
    return f'<span class="act">{view_html}{act}{dots}</span>'


def stabs(items, on=0):
    """Status tabs with counts above a list; the active one is underlined."""
    return '<nav class="stabs">' + "".join(f'<a href="#"{" class=on" if i == on else ""}>{label}{f" <span>{n}</span>" if n else ""}</a>' for i, (label, n) in enumerate(items)) + "</nav>"


def ptabs(items):
    """Page tabs when one page holds two jobs (e.g. Staff | Roles). The first is the default; the others open by #id."""
    return '<nav class="ptabs">' + "".join(f'<a href="#{"" if i == 0 else k}" data-pane="{k}">{label}</a>' for i, (k, label) in enumerate(items)) + "</nav>"


SETUP_STEPS_ALL = [("School year and fee", "setup-1.html", True), ("Schedules", "setup-2.html", True), ("Campuses and programs", "campuses.html", False),
                   ("Rooms", "rooms.html", False), ("Exam slots", "exam-slots.html", False), ("Staff (cashiers)", "staff.html", False), ("Publish Schedule 1", "schedules.html", False)]
SETUP_OPTIONAL = [("Official email", "email.html", True), ("Student app", "landing.html", False)]


def setup_line(state_id=""):
    """One slim line: dots (filled = done, ringed = next, empty = to do), "2 of 7 done", the next step, Continue, ··· Hide."""
    done = sum(1 for *_, d in SETUP_STEPS_ALL if d)
    nxt = next(i for i, (*_, d) in enumerate(SETUP_STEPS_ALL) if not d)
    dots = "".join(f'<i class="{"d" if d else ("n" if i == nxt else "")}"></i>' for i, (*_, d) in enumerate(SETUP_STEPS_ALL))
    ident = f' id="{state_id}"' if state_id else ""
    return (f'<div class="setupline{" st" if state_id else ""}"{ident}><b>Set up SY 2028–2029</b><span class="dots" aria-hidden="true">{dots}</span>'
            f'<a class="cnt" href="setup.html">{done} of {len(SETUP_STEPS_ALL)} done</a><span class="nx">Next: <em>{SETUP_STEPS_ALL[nxt][0]}</em></span>'
            f'<span class="sh">Turn on the programs each campus offers this year.</span><span class="grow"></span>'
            f'{btn("Continue", SETUP_STEPS_ALL[nxt][1], "sm")}{btn("···", "#setupmenu", "sm")}</div>')


GUIDES = {
    "schedules": ("Exam schedules", "A school year has one or more exam schedules. Each schedule has its own registration dates, exam days, exam slots and result release. Nothing is public until you publish it.",
                  ["Add a schedule with its registration dates, exam days and result date.", "Add exam slots for it (campus and date) on the Exam slots page.", "Press Publish. Students can apply only while it is published and registration is open.", "Unpublish stops new applications; people who already applied keep their place."],
                  ["Schedule 1 · registration Jan 1 – Feb 28 · exam Mar 14–15 · results Apr 20.", "Schedule 4 is for transferees: the program chairperson approves before they pay at the cashier.", "Absent in Schedule 1? With the switch on, they can take Schedule 2 without paying again."]),
    "setup-1": ("New school year", "Sets up a whole school year in five steps. Everything is saved as a draft; students see nothing until you publish Schedule 1.",
                ["Basics: school year, exam fee, first examinee number, payment methods.", "Schedules: up to three or more, with dates.", "Campuses and programs: copied from last year; switch off what isn't offered.", "Exam slots and rooms.", "Review and publish."],
                ["SY 2028–2029 · fee ₱275.00 · first examinee no. 600001.", "Copying last year saves typing campuses, programs, rooms and staff."]),
    "exam-slots": ("Exam slots", "An exam slot is a campus and a date. Students pick one; their room and seat are assigned from the real room sizes.",
                   ["Add an exam slot: campus, date, rooms.", "The seats add up from the rooms you pick.", "When a slot is full it closes by itself; you can also close it.", "Assign rooms and seats places everyone who hasn't been placed yet."],
                   ["Isulan · Sat, Apr 25 · 4 rooms · 200 seats.", "Report by 7:30 AM, exam starts 8:00 AM: one guide time for the day; there are no morning or afternoon groups."]),
    "scores": ("Import scores", "Brings in the Testing Center's results Excel. The system never computes or changes scores; it checks the file and saves them exactly as given.",
               ["Upload the Excel as it is.", "Check the column match once (it is remembered for next year).", "Look at the rows that need a look; fix them with the Testing Center or upload again.", "Approve: scores are saved but still hidden.", "Publish on the Results page."],
               ["Examinee no. with the letter O instead of zero is flagged.", "Someone with an exam slot but no score is marked absent when you approve."]),
    "results": ("Results", "Shows the approved scores of a schedule and controls when students see them.",
                ["Set a release date and time, or press Publish now.", "Students get a notification and an email when results are published.", "Hide results takes them back down; emails already sent stay sent."],
                ["Release Apr 20, 9:00 AM.", "Qualified for 1st choice: overall score at or above the program's cut-off."]),
    "applications": ("Applications", "Every application in a schedule, with what each person needs next.",
                     ["Click a status tab to see one group, for example Waiting for payment.", "Search a name, examinee no., application code or OR no.; an exact number opens the record.", "Each row shows the one action that fits it: Remind, Pick slot, Resend permit.", "Click a row to see the person's steps and details.", "Select rows to remind or export several at once."],
                     ["Waiting for payment · 790: remind them before registration closes.", "Approved, no exam slot · 627: pick a slot for them, or they are seated automatically."]),
    "support": ("Support", "Questions and change requests from students, answered from here.",
                ["Open requests come first, oldest waiting at the top.", "Reply; the student gets it in the app and by email.", "For a change request, use Change details: a reason is needed and it goes in the history.", "Close when solved. A student can have one open request and 5 per school year."],
                ["#1046 · Change my details · birth date typed wrong.", "#1042 · Payment · Is the Isulan cashier open on Saturday?"]),
    "campuses": ("Campuses and programs", "Which programs each campus offers this school year, and each program's cut-off score.",
                 ["Pick a campus.", "Switch a program on or off for this school year; students can only choose programs that are on.", "Edit a program for its cut-off score and whether it has a board exam."],
                 ["BS Nursing · Isulan · cut-off 600.", "BS Midwifery switched off: nobody can pick it this year."]),
    "survey": ("Survey", "The survey students answer after their result and before choosing a program. The default statements are the ones the office already submits.",
               ["Edit, add, reorder or switch off statements for a school year.", "Once students have answered, saving starts a new version; old answers keep the statement they answered.", "Results and the Excel for the office are under Survey results."],
               ["1. The pre-registration process is easy and convenient.", "Answers: Strongly Agree to Strongly Disagree."]),
    "console": ("Cashier counter", "Records exam fee payments at the counter. Recording a payment approves the application and gives the student an examinee number.",
                ["Find the person: type their name, application code (APP-27-…) or pick them from the waiting list.", "Check the name and program on the right.", "Type the official receipt number from your booklet and how they paid.", "Press Enter. The student sees their examinee number in the app right away."],
                ["Lea M. Sampulna · APP-27-10422 · ₱275.00 cash · OR 0048214.", "OR already used? The screen says who it was used for; type the next number.", "Paid already? The screen shows when and where; don't take a second payment."]),
    "staff": ("Staff and roles", "Who can sign in to the admin, cashier and proctor screens, and what each role can do.",
              ["Staff join by invite only: enter their email and role.", "Change a role at any time; it applies on their next click.", "The Roles tab shows exactly what each role can do."],
              ["Cashier 1 · Isulan counter 1.", "Program chair · BS Information Technology, or College dean · every program in the college: approves transferees."]),
}


def guide_modal(key):
    title, purpose, steps, examples = GUIDES[key]
    body = (f'<div class="guide"><h4>What this page is for</h4><p>{purpose}</p><h4>How it works</h4><ol>{"".join(f"<li>{x}</li>" for x in steps)}</ol>'
            f'<h4>Examples</h4><ul class="ex">{"".join(f"<li>{x}</li>" for x in examples)}</ul></div>')
    return modal("guide", "info", "", f"Guide · {title}", body, btn("Close", "#"))


GUIDE_BTN = '<a class="btn ghost guidebtn" href="#guide"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/></svg>Guide</a>'


def list_page(*parts, count="", actions=""):
    """Every list looks the same: muted count and page actions on the title line, then one white panel holding
    status tabs (when the list has statuses), the filter line, the table and the "1–25 of N" footer."""
    head = f'<div class="head"><span class="muted">{count}</span>{actions}</div>' if (count or actions) else ""
    return head + '<div class="panel list">' + "".join(parts) + "</div>"


def calendar(month, first_weekday, days, sel_from, sel_to, today=None):
    """A month grid with a selected range, for the date-picker states."""
    cells = ['<span></span>'] * first_weekday
    for d in range(1, days + 1):
        cls = "on" if d in (sel_from, sel_to) else ("in" if sel_from < d < sel_to else "")
        cells.append(f'<a href="#" class="{cls}{" today" if d == today else ""}">{d}</a>')
    head = "".join(f"<b>{w}</b>" for w in "SMTWTFS")
    return (f'<div class="cal"><div class="calhead"><a href="#" aria-label="Previous month">‹</a><b>{month}</b><a href="#" aria-label="Next month">›</a></div>'
            f'<div class="calgrid">{head}{"".join(cells)}</div></div>')


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
<p class="announce pub-announce">Schedule 2 registration is open until Apr 10.</p>
<div class="pubmaint" id="maintenance"><img src="../assets/sksu-seal.png" alt="SKSU seal" width="64" height="64"><h1>SKSU TPT is under maintenance</h1><p>Back by 3:00 PM today. Your application is saved.</p><a href="#">Back to the page</a></div>
<section class="phero"><div class="ptext">
<p class="pkick">Guidance and Testing Center</p>
<h1>SKSU Tertiary Placement Test<br>SY 2027–2028</h1>
<p>Apply online, pay the ₱275.00 testing fee at an SKSU cashier, pick your exam slot and keep your permit on your phone.</p>
<div class="pacts2"><a class="btn primary lg" href="login.html">Apply or sign in</a><a class="btn lg" href="#how">How it works</a></div></div>
<dl class="pdates"><dt>Schedule 1</dt><dd>Registration Jan 1 – Feb 28</dd><dd>Exam Sat–Sun, Mar 14–15</dd><dd>Results Apr 20</dd>
<dt>Schedule 2</dt><dd>Registration Mar 1 – Apr 10</dd><dd>Exam Sat–Sun, Apr 25–26</dd>
<dt>Testing fee</dt><dd>₱275.00</dd></dl></section>
<section id="install" class="pinstall"><div><h2>Install the app</h2><p>Use SKSU TPT like an app, with its own icon. No Play Store or App Store needed.</p></div>
<div class="pinstall-how"><a class="btn primary" href="#">Install the app</a><span class="muted">On iPhone: tap Share, then Add to Home Screen, then Add.</span></div></section>
<section id="how" class="road"><h2>How it works</h2>
<ol class="tline">
<li class="now"><i>1</i><b>Apply</b><span>Details, school, 3 programs</span><em>Jan 1 – Feb 28 · open now</em></li>
<li><i>2</i><b>Pay</b><span>At an SKSU cashier, with your application code</span><em>Before Feb 28</em></li>
<li><i>3</i><b>Pick your exam slot</b><span>Choose your campus and date; we give you a room and seat</span><em>After approval</em></li>
<li><i>4</i><b>Take the test</b><span>Show your permit QR at the door</span><em>Mar 14 – 15</em></li>
<li><i>5</i><b>See your result</b><span>Scores and the programs you qualify for</span><em>Apr 20, 9:00 AM</em></li>
</ol>
<h2 style="margin-top:24px">On exam day, bring</h2><p class="muted">Pencil No. 2 with eraser · this permit · school ID or any valid ID · official receipt (if paid at the cashier)</p>
<p class="muted">Schedule 1 registration closes Feb 28; Schedules 2 and 3 open later. Tests are held at 7 SKSU campuses · <a href="#centers">See test centers</a></p></section>
<div class="modal" id="centers"><a class="scrim" href="#"></a><div class="dialog" role="dialog"><h3>Test centers</h3><ul class="centers"><li><b>ACCESS Campus</b><span>EJC Montilla, Tacurong City</span></li><li><b>Isulan Campus</b><span>Kalawag II, Isulan</span></li><li><b>Tacurong Campus</b><span>Tacurong City</span></li><li><b>Kalamansig Campus</b><span>Kalamansig</span></li><li><b>Bagumbayan Campus</b><span>Bagumbayan</span></li><li><b>Palimbang Campus</b><span>Palimbang</span></li><li><b>Lutayan Campus</b><span>Lutayan</span></li></ul><div class="acts"><a class="btn" href="#">Close</a></div></div></div>
<footer class="pfoot"><span>Guidance and Testing Center · SKSU ACCESS Campus, EJC Montilla, Tacurong City</span><span>© Sultan Kudarat State University</span><a href="privacy.html">Privacy and terms</a><a href="staff-login.html" style="margin-left:auto">Staff sign-in</a></footer></div>""", states=[("maintenance", "Maintenance screen")])

doc("public/login.html", "Sign in", f"""<div class="pub">{pubnav()}
<div class="auth"><div class="authcard">
<img src="{{UP}}assets/sksu-seal.png" alt="" style="width:56px;height:56px;align-self:center">
<h1 style="text-align:center;font-size:22px">Sign in to apply</h1>
<p class="muted" style="margin:0;text-align:center">Use the Google account you check most. Your result and permit will be linked to it.</p>
<a class="gbtn" href="#loading"><span style="font-weight:700;color:#4285f4">G</span>Continue with Google</a>
<div id="error-box"></div>
<label class="chk consent"><input type="checkbox" required> I have read the <a href="privacy.html#privacy">Privacy notice</a> and the <a href="privacy.html#terms">Terms of use</a>.</label>
<a href="../applicant/home.html" class="btn">Mockup: continue as a signed-in applicant →</a>
</div></div></div>
{modal("loading", "info", '<span class="spin"></span>', "Signing you in…", '<p class="muted" style="margin:0">Waiting for Google. Keep this tab open.</p>', btn("Cancel", "#"))}
{modal("google-error", "bad", BAD, "Google sign-in didn’t finish", '<p class="muted" style="margin:0">The sign-in window was closed or timed out. Nothing was saved. Try again.</p>', btn("Try again", "#loading", "primary"))}
{modal("closed", "warn", WARN, "Schedule 1 registration is closed", '<p class="muted" style="margin:0">Schedule 2 registration opens Mar 1. You can still sign in to see your permit or result.</p>', btn("OK", "#"))}""",
    states=[("loading", "Loading"), ("google-error", "Error"), ("closed", "Registration closed")])

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
<div class="kv"><span>Name</span><span class="ink">Maria S. Dela Cruz</span><span>Exam slot</span><span>Isulan · Sat, Mar 14</span><span>Room and seat</span><span>Room 4 · seat 27</span><span>Checked</span><span>Oct 28, 2026 10:42 AM</span></div>
<small class="muted">This page opens from the permit QR. It shows only what a proctor needs, never the address or phone.</small>
</div></div></div>
{modal("invalid", "bad", BAD, "Permit not valid", '<p class="muted" style="margin:0">This QR was changed or the permit was cancelled. Send the examinee to the help desk.</p>', btn("OK", "#"))}""",
    states=[("invalid", "Invalid or tampered QR")])

PRIVACY_COLLECT = [("About you", "name, date of birth, sex, home address, mobile number, email"), ("School", "school, year graduated, strand, general average; transferees: current school and course, and a grades file"),
                   ("Your choices", "three programs (two for transferees) and your exam slot"), ("Photo", "your 2×2 ID photo, printed on your permit"),
                   ("Payment", "the official receipt (OR) number and where you paid"), ("Exam", "examinee number, scores and stanines from the Testing Center"),
                   ("Afterwards", "your survey answers and support messages")]
PRIVACY_SEE = [("Admission staff", "your whole application, to run the test"), ("Cashiers", "your name, application code and payment only"),
               ("Program chairpersons and deans", "transferee applicants to their own program or college only"), ("Proctors", "the list for their room, only if check-in is used"),
               ("The Testing Center", "examinee numbers, to score the test")]
PRIVACY_RIGHTS = ["Be told how your data is used (this notice)", "See a copy of your data", "Correct wrong data", "Object to how it is used",
                  "Ask us to delete it when we no longer need it", "Get your data in a common file format", "Complain to the National Privacy Commission (privacy.gov.ph)"]

doc("public/privacy.html", "Privacy and terms", f"""<div class="pub">{pubnav()}
<div class="legal"><h1>Privacy and terms</h1><p class="muted">SKSU Tertiary Placement Test · version 1 · effective Jan 1, 2027</p>
<nav class="legaltabs"><a class="on" href="#privacy">Privacy notice</a><a href="#terms">Terms of use</a></nav>
<section id="privacy"><h2>Privacy notice</h2>
<h3>Who we are</h3><p>Sultan Kudarat State University, through its Guidance and Testing Center, EJC Montilla, Tacurong City, runs the SKSU Tertiary Placement Test (SKSU TPT). Data Protection Officer: [DPO NAME], [DPO EMAIL].</p>
<h3>What we collect</h3><dl class="legaldl">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in PRIVACY_COLLECT)}</dl>
<h3>Why</h3><p>To register you, schedule your exam, issue your permit, release your result and process your admission. We rely on your consent and on the university's function of admitting students.</p>
<h3>Who can see it</h3><dl class="legaldl">{"".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in PRIVACY_SEE)}</dl>
<p>Companies that host the website and send our emails and texts handle your data only to deliver this service. We never sell your data and share it with no one else unless the law requires it.</p>
<h3>How long we keep it</h3><p>Applications and results are kept for [RETENTION PERIOD, to confirm with the DPO], then deleted or made anonymous. Photos are deleted [PHOTO RETENTION] after the school year ends.</p>
<h3>How we protect it</h3><p>The site uses an encrypted connection. Staff see only what their role needs, and every staff action is logged.</p>
<h3>Your rights</h3><ul>{"".join(f"<li>{r}</li>" for r in PRIVACY_RIGHTS)}</ul>
<p>To use them, open Support in the app and pick the topic <b>Privacy request</b>, or email the Data Protection Officer.</p>
<h3>Cookies</h3><p>We use only what is needed to keep you signed in. No advertising or tracking cookies.</p>
<h3>Applicants under 18</h3><p>[To confirm with the DPO: whether a parent or guardian must also agree.]</p>
<h3>Changes</h3><p>If this notice changes, we show the new version and date here and ask you to agree again.</p></section>
<section id="terms"><h2>Terms of use</h2><ul>
<li>One account per person. Do not apply for someone else.</li>
<li>Your information must be true. By applying you certify that all information you give is true and correct, and that any misrepresentation may cause disqualification from admission to SKSU.</li>
<li>Keep your permit to yourself. It is checked against your photo and ID on exam day.</li>
<li>Use Support for real questions. Repeated or abusive messages may pause your support for 7 days.</li>
<li>The admission office may cancel an application that has false information.</li></ul></section></div></div>""")

doc("public/error.html", "Error pages", f"""<div class="pub">{pubnav()}
<div class="auth" style="flex-direction:column;gap:16px">
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:var(--green)">404</span><h1 style="font-size:20px">We can’t find that page</h1><a class="btn primary" href="landing.html">Go home</a></div>
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:#d97706">503</span><h1 style="font-size:20px">Many people are on the site right now</h1><p class="muted" style="margin:0">You’re in line. This page refreshes by itself in 20 seconds.</p><span class="spin"></span></div>
<div class="authcard" style="align-items:center;text-align:center"><span class="mono" style="font-size:48px;font-weight:700;color:#dc2626">500</span><h1 style="font-size:20px">Something broke on our side</h1><p class="muted" style="margin:0">It has been reported. Your saved answers are safe. Error code <span class="mono">E-7F3A</span>.</p><a class="btn" href="landing.html">Try again</a></div>
</div></div>""")


# ---------------------------------------------------------------- applicant pages
FLOW = [("notifications", "Notifications"), ("home", "Home"), ("apply-personal", "About you"), ("apply-school", "School"), ("apply-programs", "Programs"),
        ("apply-review", "Review"), ("apply-t-school", "Transferee: school"), ("apply-t-programs", "Transferee: programs"), ("payment-chair", "Transferee: chairperson"), ("payment", "Payment"), ("payment-waiting", "Waiting"), ("payment-rejected", "Sent back"),
        ("seat", "Pick an exam slot"), ("permit", "Permit"), ("result-pending", "Result not yet"), ("survey", "Survey"),
        ("result", "Result"), ("profile", "My account"), ("support", "Support"), ("support-ticket", "Support request")]
DOTS = {"notifications": 0, "home": 0, "apply-personal": 0, "apply-school": 1, "apply-programs": 2, "apply-review": 3, "apply-t-school": 1, "apply-t-programs": 2, "payment-chair": 4, "payment": 4,
        "payment-waiting": 4, "payment-rejected": 4, "seat": 0, "permit": 0, "result-pending": 0, "survey": 0, "result": 0, "profile": 0, "support": 0, "support-ticket": 0}


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
    in_flow = key.startswith("apply") or key == "payment"
    crumbs = " · ".join(f'<a href="{k}.html">{t}</a>' if k != key else f"<b>{t}</b>" for k, t in FLOW)
    left = f'<a class="hbtn" href="{back}" aria-label="Back"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg></a>' if back else '<img src="../assets/sksu-seal.png" alt="SKSU seal">'
    # top app bar: the step while applying, the test name on Home, nothing else (the screen has its own heading)
    ttl = f"Application · step {n + 1} of 5" if in_flow else ("SKSU TPT<small>SY 2027–2028</small>" if key == "home" else "")
    dots = f'<span class="ttl">{ttl}</span>'
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
{overlays}</div>"""
    doc(f"applicant/{key}.html", title, body, "phone-page", states)


def intro(key, title, content, cta, alt="", dark=False):
    """Splash and welcome screens: no nav, big type, one action."""
    doc(f"applicant/{key}.html", title, f"""<div class="crumbs"><a href="../index.html">All pages</a> | <a href="splash.html">Splash</a> · <a href="welcome-1.html">Welcome 1</a> · <a href="welcome-2.html">2</a> · <a href="welcome-3.html">3</a> · <a href="../public/login.html">Sign in</a></div>
<div class="phone app intro{' dark' if dark else ''}">{STATUS_BAR}<div class="introb">{content}</div>{f'<div class="appcta">{cta}{alt}</div>' if cta else ''}</div>""", "phone-page")


SAVED = toast("saved", "ok", OK, "Saved", "Your answers are saved. You can close this and come back.")
OFFLINE = toast("offline", "warn", WARN, "You’re offline", "We’ll keep what you type and save it when you’re back online.")

NOTE_ICON = {"ok": OK, "info": INFO, "bad": BAD, "warn": WARN}
intro("splash", "Splash", """<div class="splash"><img src="../assets/sksu-seal.png" alt="SKSU seal"><div class="wm lg"><b>Sultan Kudarat</b><span>State University</span></div><p>Admission Test</p><div class="load"><span></span></div><small>Loading</small></div>""", "", dark=True)
for i, (eb, big, line) in enumerate([("SKSU TPT · SY 2027–2028", "Apply for the<br>SKSU TPT.", "Apply, pay the exam fee, pick an exam slot and see your result in this app."),
                                     ("Payment", "₱275.00 at an<br>SKSU cashier.", "Show your application code. Once the cashier records it, choose a campus and date. Your room and seat are assigned."),
                                     ("Exam day", "Bring your permit<br>and a valid ID.", "The permit shows your room and seat. It opens without signal.")], 1):
    nxt = f"welcome-{i + 1}.html" if i < 3 else "../public/login.html"
    pages_dots = "".join(f'<span class="{"now" if j == i else ""}"></span>' for j in range(1, 4))
    intro(f"welcome-{i}", f"Welcome {i} of 3", f"""<a class="skip" href="../public/login.html">Skip</a><div class="hero-ph" style="background-position:{['30% 50%', '60% 40%', '85% 30%'][i - 1]}"></div>
<p class="eyebrow">{eb}</p><h1 class="big">{big}</h1><p class="lead">{line}</p><div class="pdots">{pages_dots}</div>""",
          f'<a class="go" href="{nxt}">{"Get started" if i == 3 else "Next"}</a>', '<div class="alt"><a href="../public/login.html">I already applied</a><a href="../public/landing.html">Look around first</a></div>' if i == 3 else "")

def row(title, sub="", end="", href="", cls="", lead=""):
    """One row of a grouped list (settings style): optional lead (radio, number), title + sub, value at the end."""
    tag = "a" if href else "div"
    ref = f' href="{href}"' if href else ""
    sub_html = f"<small>{sub}</small>" if sub else ""
    end_html = f'<span class="end{" chev" if href and not end else ""}">{end}</span>' if (end or href) else ""
    return f'<{tag} class="{cls}"{ref}>{lead}<span class="grow"><b>{title}</b>{sub_html}</span>{end_html}</{tag}>'


def plist(*rows):
    return '<div class="plist">' + "".join(rows) + "</div>"


RADIO = '<span class="radio"></span>'
SHEET_NOTE = '<p style="margin:0">{}</p>'

phone("notifications", "Notifications", """<h1 class="gh">Notifications</h1>
<div class="notes">""" + "".join(f'<a class="note{" unread" if u else ""}" href="{h}"><span><b>{t}</b><span>{d}</span><small>{w}</small></span></a>' for t, d, w, u, h in [
    ("Result released", "SKSU TPT, Schedule 1. You qualify for all 3 of your choices.", "Apr 20 · 9:00 AM", True, "result.html"),
    ("Exam slot booked", "Isulan Campus · Sat, Mar 14 · report by 7:30 AM, exam starts 8:00 AM · Room 4, seat 27. Your permit is ready.", "Jan 13 · 9:42 AM", False, "permit.html"),
    ("Reply to your request #1042", "Isulan cashier is open Saturday, 8:00 AM – 12:00 noon.", "Jan 12 · 4:35 PM", False, "support-ticket.html"),
    ("Payment recorded", "Paid at Isulan cashier, OR 0048190. Examinee no. 500214. Pick your exam slot by Mar 1.", "Jan 12 · 4:30 PM", False, "seat.html"),
        ("Application submitted", "Next: pay ₱275.00 at an SKSU cashier. Show code APP-27-10422.", "Jan 11 · 7:55 PM", False, "payment.html")]) + """</div>
""" + plist(row("Support", "Ask the admission office · 1 request answered", href="support.html")) + """
<small>Notifications also go to your email.</small>""",
      back="home.html",
      overlays='<div class="modal" id="empty"><a class="scrim" href="#"></a><div class="dialog">' + empty("bell", "No notifications", "Updates about your application appear here and in your email.") + '</div></div>',
      states=[("empty", "Empty")])

# Home always shows where the student is and the one next thing to do.
STEPS = ["Apply", "Pay", "Exam slot", "Exam", "Result"]
T_STEPS = ["Apply", "Chairperson", "Pay", "Exam", "Result"]


def progress(cur, steps=STEPS):
    """Compact step line: done steps green, the current one bold, the rest grey."""
    return '<div class="prog">' + "".join(
        f'<span class="{"done" if i < cur else ("now" if i == cur else "")}">{t}</span>' for i, t in enumerate(steps)) + "</div>"


def home_view(status, cur, body, cta=None, eyebrow=None, name="Maria Santos Dela Cruz", steps=STEPS):
    """One Home variant: who, where they are, the one emphasised thing, the next action."""
    eyebrow = eyebrow or ("Schedule 1 · exam Mar 14–15" if cur >= 3 else "Schedule 1 · registration until Feb 28")
    action = f'<div class="inline-cta"><a class="go" href="{cta[0]}">{cta[1]}</a></div>' if cta else ""
    return (f'<p class="eyebrow">{eyebrow}</p><h1 class="gh">{name}</h1>{progress(cur, steps)}'
            f'<p class="hstat"><span class="dot"></span>{status}</p>{body}{action}')


def home_state(sid, html):
    """A full Home variant shown in place of the default view (picked from the states bar)."""
    return f'<div class="hvar" id="{sid}"><div class="appb">{html}</div></div>'


CASHIER_HOURS = "<small>Cashiers are open Monday to Friday, 8:00 AM – 5:00 PM. Isulan also opens Saturday until 12:00 noon.</small>"
HOME = {
    "not-started": home_view("Not started", 0, plist(
        row("Fill in the application", "Personal details, school, 3 programs, 2×2 photo", "", "apply-personal.html", "", '<span class="num">1</span>'),
        row("Pay the exam fee", "₱275.00 at an SKSU cashier", "", "", "", '<span class="num">2</span>'),
        row("Pick your exam slot", "After the cashier records your payment", "", "", "", '<span class="num">3</span>'),
        row("Take the exam", "Mar 14–15 · report by 7:30 AM", "", "", "", '<span class="num">4</span>')),
        ("apply-personal.html", "Start the application")),
    "draft": home_view("Draft · saved Jan 10, 8:42 PM", 0, plist(
        row("About you", "", "Done", "apply-personal.html"),
        row("School", "", "Done", "apply-school.html"),
        row("Programs", "Pick 3 programs", "Next", "apply-programs.html"),
        row("Review and submit", "", "", "apply-review.html")),
        ("apply-programs.html", "Continue · step 3 of 5")),
    "chair": home_view("Waiting for the program chairperson", 1,
        '<div class="hero"><span class="lbl">1st choice</span><span class="amt" style="font-size:22px">BS Information Technology</span><span class="lbl">ACCESS Campus, Tacurong · sent Nov 10</span></div>'
        '<small>The chairperson checks your grades and the slots left. This usually takes up to 3 working days. You will be told here and by email.</small>',
        ("payment-chair.html", "View my application"), "Schedule 4 · Transferees · exam Dec 12", "Kenneth L. Abo", T_STEPS),
    "sent-back": home_view("Sent back · Jan 12", 0,
        '<div class="alertbox warn"><b>2×2 photo:</b> the face is not clear. Use a plain white background and good light.</div>'
        '<small>Everything else stays as you sent it. Fix this part and send it again.</small>',
        ("payment-rejected.html", "Fix and send again")),
    "approved": home_view("Paid · examinee number issued", 2,
        '<div class="hero"><span class="lbl">Examinee number</span><span class="amt mono">500214</span><span class="lbl">Paid Jan 12 · OR 0048190</span></div>'
        '<small>Pick your exam slot by Mar 1. After that date, one is assigned to you.</small>',
        ("seat.html", "Pick exam slot")),
    "booked": home_view("Exam slot booked", 3,
        '<div class="hero"><span class="lbl">Exam</span><span class="amt" style="font-size:26px">Sat, Mar 14</span><span class="lbl">Isulan Campus · Room 4, seat 27</span><span class="lbl">Report by 7:30 AM · exam starts 8:00 AM</span></div>'
        '<small>Bring your permit, a No. 2 pencil with eraser and a valid ID.</small>',
        ("permit.html", "View permit")),
    "exam-done": home_view("Exam taken · Mar 14", 4,
        '<div class="hero"><span class="lbl">Results release</span><span class="amt" style="font-size:26px">Apr 20</span><span class="lbl">You will be told here, by email and by text</span></div>'
        ),
    "result-out": home_view("Result released · Apr 20", 4,
        '<div class="hero"><span class="lbl">Overall standard score</span><span class="amt">584</span><span class="lbl">Stanine 7 · Above average · qualifies for 3 of 3 choices</span></div>',
        ("result.html", "See result")),
    "chosen": home_view("Program chosen · Apr 22", 5,
        '<div class="hero"><span class="lbl">Your program</span><span class="amt" style="font-size:22px">BS Civil Engineering</span><span class="lbl">Isulan Campus</span></div>'
        '<small>The Registrar’s Office will contact you about enrolment.</small>' + plist(row("Result PDF", "Official copy with a verify link", "", "../docs/result-pdf.html"))),
    "absent": home_view("Absent · Mar 14", 3,
        '<div class="alertbox warn">There is no score for you in the Testing Center file, so you are marked absent.</div>'
        '<small>You can take the exam in Schedule 2 (Apr 25–26) without paying again. Your details are filled in.</small>'
        + plist(row("Ask the admission office", "If you took the exam", "", "support.html#new")),
        ("apply-review.html", "Apply for Schedule 2")),
    "closed": home_view("Registration closed", 0,
        '<div class="hero"><span class="lbl">Schedule 2 registration opens</span><span class="amt" style="font-size:26px">Mar 1</span><span class="lbl">Exam Apr 25–26</span></div>'
        '<small>Schedule 1 registration closed on Feb 28. If you already paid, you can still pick an exam slot.</small>',
        None, "Schedule 1 · registration closed"),
}

phone("home", "Home", '<p class="announce">Schedule 2 registration is open until Apr 10.</p>' + home_view("Application submitted · Jan 11", 1,
    '<div class="hero"><span class="lbl">Pay ₱275.00 at an SKSU cashier · show this code</span><span class="amt mono" style="font-size:28px">APP-27-10422</span><span class="lbl">The cashier records it and your examinee number appears here.</span></div>'
    + CASHIER_HOURS + plist(row("Where to pay", "Cashier offices per campus", "", "payment.html")),
    ("payment.html", "Show my code")),
      overlays="".join(home_state(k, v) for k, v in HOME.items()) + OFFLINE
      + home_state("maintenance", '<div class="maintscreen"><img src="../assets/sksu-seal.png" alt="SKSU seal" width="56" height="56"><h1 class="gh">SKSU TPT is under maintenance</h1><p>Back by 3:00 PM today. Your application is saved; nothing is lost.</p><small>Questions: Guidance and Testing Center, 0997 780 1758</small></div>')
      + home_state("apps-paused", '<p class="announce">New applications are paused for now. Check back later or ask the Guidance and Testing Center.</p>' + home_view("Not started", 0, '<p class="muted" style="margin:0">You can still sign in, see your status and keep your permit.</p>'))
      + home_state("maint-notice", '<p class="announce">SKSU TPT will be down Sat, Apr 18, 10:00–11:30 PM for maintenance.</p>' + home_view("Application submitted · Jan 11", 1, '<div class="hero"><span class="lbl">Pay ₱275.00 at an SKSU cashier · show this code</span><span class="amt mono" style="font-size:28px">APP-27-10422</span></div>', ("payment.html", "Show my code"))),
      states=[("not-started", "Not started"), ("draft", "Draft"), ("chair", "Waiting for chairperson"), ("sent-back", "Sent back"), ("approved", "Approved: pick exam slot"),
              ("booked", "Exam slot picked"), ("exam-done", "Waiting for results"), ("result-out", "Result out"), ("chosen", "Program chosen"), ("absent", "Absent"),
              ("closed", "Registration closed"), ("offline", "Offline"), ("maintenance", "Maintenance screen"), ("maint-notice", "Scheduled maintenance notice"), ("apps-paused", "Applications paused")])

phone("apply-personal", "About you", """<h1 class="gh">Personal details</h1>
<div class="fld"><label class="cap" for="ln">Last name</label><input id="ln" value="Dela Cruz" autocomplete="family-name"></div>
<div class="two"><div class="fld"><label class="cap" for="fn">First name</label><input id="fn" value="Maria" autocomplete="given-name"></div><div class="fld"><label class="cap" for="mn">Middle name</label><input id="mn" value="Santos"></div></div>
<div class="fld"><label class="cap" for="d">Date of birth</label><a class="picker" href="#cal" style="border:1px solid #8a918d;border-radius:8px;padding:0 14px;height:56px"><span class="grow"><span>May 12, 2008</span></span><span class="end">📅</span></a><small>As on your birth certificate.</small></div>
<div class="fld"><label class="cap">Sex</label><div class="plist" style="margin:0;border-top:0">""" + row("Female", lead=RADIO, cls="on") + row("Male", lead=RADIO) + """</div></div>
<div class="fld"><label class="cap" for="p">Mobile number</label><div class="pre"><span>+63</span><input id="p" type="tel" inputmode="tel" value="917 123 4567" autocomplete="tel-national"></div><small>For exam-day reminders by text.</small></div>
<span class="cap">Home address</span>
<div class="fld"><label class="cap" for="pv">Province</label><select id="pv"><option>Sultan Kudarat</option><option>Cotabato</option><option>South Cotabato</option><option>Maguindanao del Sur</option></select></div>
<div class="fld"><label class="cap" for="mc">Municipality or city</label><select id="mc">""" + "".join(f"<option{' selected' if t == 'Isulan' else ''}>{t}</option>" for t in PROVINCES["Sultan Kudarat"]) + """</select><small>The list follows the province you picked.</small></div>
<div class="fld"><label class="cap" for="bg">Barangay</label><select id="bg"><option>Kalawag II</option><option>Kalawag I</option><option>Kalawag III</option><option>Bambad</option><option>New Pangasinan</option></select></div>
<div class="fld"><label class="cap" for="st">House no. and street (optional)</label><input id="st" value="" autocomplete="address-line1"></div>
<div class="fld"><label class="cap">2×2 ID photo</label><a class="picker" href="#photo-pick"><span class="ph"></span><span class="grow"><b>photo.jpg</b><small>Made smaller on your phone: 3.9 MB to 248 KB</small></span><span class="end">Change</span></a><small>White background, face clearly seen. Used on your permit.</small></div>""",
      cta=("apply-school.html", "Next"), back="home.html",
      overlays=SAVED + OFFLINE
      + modal("cal", "info", "", "Date of birth", '<div class="calhead"><span>‹</span><span>May 2008</span><span>›</span></div><div class="cal">' + "".join(f"<b>{d}</b>" for d in "SMTWTFS") + "<span></span>" * 4 + "".join(f'<span class="{"on" if i == 12 else ""}">{i}</span>' for i in range(1, 32)) + '</div>', '<a class="go" href="#">Done</a><a class="back" href="#">Cancel</a>')
      + modal("photo-pick", "info", "", "2×2 ID photo", plist(row("Take a photo", "Uses your camera", href="#uploading"), row("Choose from gallery", "JPG or PNG", href="#uploading")), '<a class="back" href="#">Cancel</a>')
      + modal("photo-bad", "bad", BAD, "This photo can't be used", '<p style="margin:0">No face was found, or the photo is too dark. Use a plain white background and good light.</p>', '<a class="go" href="#photo-pick">Choose another photo</a>')
      + toast("upload-failed", "bad", BAD, "Upload stopped at 64%", "The connection dropped. Tap the photo to try again.")
      + modal("uploading", "info", '<span class="spin"></span>', "Adding photo · 64%", '<div class="progress"><span style="width:64%"></span></div><small>Making it smaller on your phone first.</small>', '<a class="back" href="#">Cancel</a>')
      + toast("age", "bad", BAD, "Check the date of birth", "May 12, 2018 gives age 8. Applicants must be at least 15."),
      states=[("cal", "Date picker"), ("photo-pick", "Photo source"), ("saved", "Autosaved"), ("uploading", "Uploading photo"), ("photo-bad", "Photo rejected"), ("upload-failed", "Upload failed"), ("age", "Date of birth error"), ("offline", "Offline")])

phone("apply-school", "School", """<h1 class="gh">School</h1>
<div class="fld"><label class="cap">I am a</label><div class="plist" style="margin:0;border-top:0">""" + row("Senior high graduate", lead=RADIO, cls="on") + row("ALS passer", lead=RADIO) + """</div><small>Transferees apply during the transferee schedule (2nd semester).</small></div>
<div class="fld"><label class="cap" for="h">Senior high school</label><a class="picker" href="#school" style="border:1px solid #8a918d;border-radius:8px;padding:0 14px;height:56px"><span class="grow"><span>Isulan National High School</span></span><span class="end">⌕</span></a></div>
<div class="two"><div class="fld"><label class="cap" for="y">Year graduated</label><select id="y"><option>2026</option><option>2025</option><option>2024</option></select></div><div class="fld"><label class="cap" for="g">General average</label><input id="g" inputmode="decimal" value="91.4"><small>60 to 100</small></div></div>
<div class="fld"><label class="cap" for="st">Strand</label><select id="st"><option>STEM</option><option>ABM</option><option>HUMSS</option><option>GAS</option><option>TVL</option></select></div>
<div class="fld"><label class="cap" for="aw">Honors (optional)</label><select id="aw"><option>With High Honors</option><option>None</option><option>With Honors</option><option>With Highest Honors</option></select></div>""",
      cta=("apply-programs.html", "Next"), back="apply-personal.html",
      overlays=SAVED
      + modal("school", "info", "", "Senior high school", '<input placeholder="Type the school name" value="Isulan Na" aria-label="Search schools">' + plist(row("Isulan National High School", "Isulan, Sultan Kudarat", href="#"), row("Isulan National High School – Annex", "Kalawag III, Isulan", href="#")) + '<small>Not listed? <a href="#">Type it in</a></small>', '<a class="back" href="#">Cancel</a>')
      + toast("too-long", "bad", BAD, "General average is out of range", "Enter a number from 60 to 100."),
      states=[("school", "School search"), ("saved", "Autosaved"), ("too-long", "Out of range error")])

phone("apply-programs", "Programs", """<h1 class="gh">Programs</h1><p>Choose 3, in order of preference. Your result decides which ones you qualify for.</p>
""" + plist(row("BS Civil Engineering", "Isulan Campus", "Remove", "#", "", '<span class="num">1</span>'),
            row("BS Information Technology", "ACCESS Campus, Tacurong", "Remove", "#", "", '<span class="num">2</span>'),
            row("Add 3rd choice", "", "", "#picker", "", '<span class="num">3</span>')),
      cta=("apply-review.html", "Next"), back="apply-school.html",
      overlays=modal("picker", "info", "", "3rd choice", '<input type="search" class="psearch" placeholder="Search programs" aria-label="Search programs"><select class="pselect" aria-label="Campus"><option>All campuses</option><option>Isulan</option><option>ACCESS, Tacurong</option><option>Tacurong</option><option>Kalamansig</option></select>'
      + '<div class="ghead">Isulan Campus</div>' + plist(row("BS Civil Engineering", "Your 1st choice", "", "", "off"), row("BS Criminology", "", "Cut-off 480", "#"))
      + '<div class="ghead">ACCESS Campus, Tacurong</div>' + plist(row("BS Information Technology", "Your 2nd choice", "", "", "off"), row("BS Nursing", "", "Cut-off 600", "#"))
      + '<div class="ghead">Kalamansig Campus</div>' + plist(row("BSEd Mathematics", "", "Cut-off 450", "#")), '<a class="back" href="#">Cancel</a>')
      + toast("dup", "bad", BAD, "Already chosen", "BS Civil Engineering, Isulan is your 1st choice."),
      states=[("picker", "Program picker"), ("dup", "Duplicate choice error")])

phone("apply-review", "Review", """<h1 class="gh">Review</h1>
""" + plist(row("Personal details", "Maria Santos Dela Cruz · May 12, 2008 · Female · +63 917 123 4567", "Edit", "apply-personal.html"),
            row("School", "Isulan National High School · 2026 · STEM · 91.4", "Edit", "apply-school.html"),
            row("Programs", "1 BS Civil Engineering, Isulan · 2 BS Information Technology, ACCESS · 3 BS Criminology, Isulan", "Edit", "apply-programs.html")) + """
<label class="chk"><input type="checkbox" required>I certify that all information is true and correct. I understand that misrepresentation may cause disqualification. I have read the <a href="../public/privacy.html#privacy">Privacy notice</a> and the <a href="../public/privacy.html#terms">Terms of use</a>.</label>""",
      cta=("#confirm", "Submit application"), back="apply-programs.html",
      overlays=modal("confirm", "warn", WARN, "Submit the application?", '<p style="margin:0">You can change your program choices until Feb 28. Your name and date of birth can only be changed by the admission office.</p>', '<a class="go" href="#submitting">Submit</a><a class="back" href="#">Cancel</a>')
      + modal("submitting", "info", '<span class="spin"></span>', "Submitting", '<p style="margin:0">Keep this screen open.</p>', '<a class="mocklink" href="payment.html#submitted">Mockup: finish →</a>')
      + toast("missing", "bad", BAD, "2 items missing", "Mobile number and 3rd program choice."),
      states=[("confirm", "Confirm"), ("submitting", "Submitting"), ("missing", "Missing items error")])

# transferee schedule (2nd semester): 2 choices, current school and course, grades; the chairperson approves before paying
phone("apply-t-school", "School", """<p class="eyebrow">Transferee test · 2nd semester</p><h1 class="gh">Current school</h1>
<div class="fld"><label class="cap" for="ts">School attended</label><a class="picker" href="#" style="border:1px solid #8a918d;border-radius:8px;padding:0 14px;height:56px"><span class="grow"><span>Notre Dame of Tacurong College</span></span><span class="end">⌕</span></a></div>
<div class="fld"><label class="cap" for="tc">Current course</label><input id="tc" value="BS Computer Science"></div>
<div class="fld"><label class="cap" for="ty">Year level</label><select id="ty"><option>1st year</option><option>2nd year</option><option>3rd year</option></select></div>
<div class="fld"><label class="cap">Transcript of records or certificate of grades</label><a class="picker" href="#"><span class="ph"></span><span class="grow"><b>grades-1st-sem.pdf</b><small>620 KB</small></span><span class="end">Change</span></a><small>The program chairperson reviews your grades before you pay.</small></div>""",
      cta=("apply-t-programs.html", "Next"), back="apply-personal.html", overlays=SAVED, states=[("saved", "Autosaved")])

phone("apply-t-programs", "Programs", """<p class="eyebrow">Transferee test · 2nd semester</p><h1 class="gh">Programs</h1><p>Choose 2, in order of preference.</p>
""" + plist(row("BS Information Technology", "ACCESS Campus, Tacurong", "Remove", "#", "", '<span class="num">1</span>'),
            row("BS Computer Engineering", "Isulan Campus", "Remove", "#", "", '<span class="num">2</span>')),
      cta=("apply-review.html", "Next"), back="apply-t-school.html")

phone("payment-chair", "Chairperson", """<p class="eyebrow">Transferee test · 2nd semester</p><h1 class="gh">For the program chairperson's approval</h1>
<p>The chairperson of BS Information Technology reviews your grades and the available slots. Do not pay yet.</p>
""" + plist(row("1st choice", "", "BS Information Technology"), row("Sent", "", "Nov 4, 9:12 AM"), row("Status", "", '<span class="dot a"></span>Waiting')),
      back="home.html", extra='<a class="mocklink" href="#approved">Mockup: approved →</a><a class="mocklink" href="#declined">Mockup: declined →</a>',
      overlays=modal("approved", "ok", OK, "Approved by the chairperson", '<p style="margin:0">Pay ₱275.00 at any SKSU cashier. Give the cashier this code. Your exam is on Sun, Dec 12, Testing Room, Guidance and Testing Center, SKSU ACCESS Campus: report by 7:30 AM, exam starts 8:00 AM. It shows on your permit after you pay.</p><div class="hero"><span class="lbl">Application code</span><span class="amt mono" style="font-size:26px">APP-27-20418</span></div>', '<a class="go" href="#">OK</a>')
      + modal("declined", "bad", BAD, "Not approved for BS Information Technology", '<div class="alertbox warn"><div>Reason: no slots left for 2nd-year transferees this semester.</div></div><p style="margin:0">Your 2nd choice, BS Computer Engineering, is reviewed next. Do not pay yet.</p>', '<a class="go" href="#">OK</a>'),
      states=[("approved", "Approved: pay at the cashier"), ("declined", "Declined, with the reason")])

phone("payment", "Payment", """<h1 class="gh">Pay at an SKSU cashier</h1>
<div class="hero"><span class="lbl">Show this code</span><span class="amt mono" style="font-size:28px">APP-27-10422</span><span class="lbl">Maria S. Dela Cruz · ₱275.00</span></div>
<div class="ghead">Where to pay</div>""" + plist(
    row("Isulan Campus", "Cashier's Office, Admin Building", "Mon–Sat"),
    row("ACCESS Campus, Tacurong", "Cashier's Office, Main Gate", "Mon–Fri"),
    row("Kalamansig, Bagumbayan, Lutayan, Palimbang", "Campus cashier", "Mon–Fri")) + """
<small>Open 8:00 AM – 5:00 PM (Saturday until 12:00 noon). Bring this code or your application number. After you pay, the cashier records it and you get your examinee number here.</small>""",
      cta=("home.html", "Done"), back="apply-review.html",
      extra='<a class="mocklink" href="seat.html#approved">Mockup: cashier recorded the payment →</a>',
      overlays=toast("submitted", "ok", OK, "Application submitted", "Next, pay at an SKSU cashier.")
      + modal("online", "info", "", "Online payment (when turned on)", '<p style="margin:0">Shown instead of the cashier screen only if the office turns on online payment for the school year.</p><div class="hero"><span class="lbl">Send ₱275.00 to</span><span class="amt" style="font-size:20px">[GCASH OR BANK ACCOUNT]</span></div><div class="fld"><label class="cap" for="r">Reference number</label><input id="r" inputmode="numeric" value="1009 284 551 203" class="mono"><small>13 digits, from the GCash receipt.</small></div><div class="fld"><label class="cap">Receipt</label><a class="picker" href="#uploading"><span class="ph"></span><span class="grow"><b>receipt.jpg</b><small>Made smaller on your phone: 4.8 MB to 310 KB</small></span><span class="end">Change</span></a></div>', '<a class="go" href="payment-waiting.html#sent">Send receipt</a><a class="back" href="#">Close</a>')
      + toast("ref-used", "bad", BAD, "Reference number already used", "Another applicant sent this GCash reference. Check your receipt.")
      + modal("uploading", "info", '<span class="spin"></span>', "Sending receipt · 72%", '<div class="progress"><span style="width:72%"></span></div>', '<a class="back" href="#">Cancel</a>'),
      states=[("submitted", "Arrived after submit"), ("online", "Online payment (when turned on)"), ("uploading", "Online: uploading"), ("ref-used", "Online: reference already used")])

phone("payment-waiting", "Waiting for approval", """<p class="eyebrow">Only when online payment is turned on</p><h1 class="gh">Receipt sent</h1><p>The admission office checks receipts within one working day. You will get a notification and an email.</p>
""" + plist(row("Reference no.", "", '<span class="mono">1009 284 551 203</span>'), row("Sent", "", "Jan 12, 8:10 AM"), row("Status", "", '<span class="dot a"></span>For review')),
      extra='<a class="mocklink" href="seat.html#approved">Mockup: payment approved →</a><a class="mocklink" href="payment-rejected.html">Mockup: sent back →</a>',
      overlays=toast("sent", "ok", OK, "Receipt sent", "You will be notified when it is checked."), states=[("sent", "Just sent")])

phone("payment-rejected", "Sent back", """<h1 class="gh">Please fix your application</h1>
<div class="alertbox warn"><div>“The photo is not a 2×2 ID photo. Use a plain white background and show your whole face.”<br><small>Admission Office · Jan 13, 4:22 PM</small></div></div>
<p>The rest of your application stays as it is. Your payment and examinee number are not affected.</p>
<div class="fld"><label class="cap">2×2 ID photo</label><a class="picker" href="#"><span class="ph"></span><span class="grow"><b>Take or choose a new photo</b><small>Camera or gallery</small></span><span class="end">›</span></a></div>""",
      cta=("#resent", "Send again"), back="home.html",
      overlays=modal("voided", "warn", WARN, "Payment cancelled", '<div class="alertbox warn"><div>Reason: the OR number was recorded for another applicant.</div></div><p style="margin:0">Your exam slot was released. Pay again at an SKSU cashier, then pick an exam slot. Your application stays as it is.</p>', '<a class="go" href="payment.html">Pay again</a><a class="back" href="#">Close</a>')
      + modal("closed-out", "warn", WARN, "Schedule 2 registration has closed", '<p style="margin:0">It closed before you sent the fix. You can apply for Schedule 3. Your details are copied from this application.</p>', '<a class="go" href="apply-review.html">Apply for Schedule 3</a><a class="back" href="#">Close</a>')
      + toast("resent", "ok", OK, "Sent again", "The admission office will check it. You will get a notification.")
      + modal("receipt", "warn", WARN, "Please fix your receipt (online payment)", '<div class="alertbox warn"><div>“The receipt photo is blurry. The reference number cannot be read.”</div></div><div class="fld"><label class="cap" for="r2">Reference number</label><input id="r2" inputmode="numeric" value="1009 284 551 203" class="mono"></div>', '<a class="go" href="payment-waiting.html#sent">Send again</a><a class="back" href="#">Close</a>'),
      states=[("resent", "Sent again"), ("receipt", "Online: receipt sent back"), ("voided", "Payment voided by the admission office"), ("closed-out", "Too late for this schedule")])

phone("seat", "Pick an exam slot", """<h1 class="gh">Exam slot</h1><p>Choose a campus and date. Your room and seat are assigned when you confirm.</p>
<select class="pselect" aria-label="Campus"><option>All campuses</option><option>Isulan</option><option>ACCESS, Tacurong</option><option>Tacurong</option><option>Kalamansig</option></select>
<div class="ghead">Schedule 1 · Mar 14–15</div>""" + plist(
    row("Isulan Campus", "Sat, Mar 14 · report by 7:30 AM", "38 seats left", "#confirm", "on", RADIO),
    row("ACCESS Campus, Tacurong", "Sun, Mar 15 · report by 7:30 AM", "112 seats left", "#confirm", "", RADIO),
    row("Tacurong Campus", "Sat, Mar 14 · report by 7:30 AM", "48 seats left", "#confirm", "", RADIO),
    row("Kalamansig Campus", "Sun, Mar 15 · report by 7:30 AM", "Full", "", "off", RADIO)) + """
<small>Times are a guide; come at the report time. The exam starts at 8:00 AM and takes about 3 hours.</small>""",
      cta=("#confirm", "Confirm exam slot"), back="home.html",
      overlays=toast("approved", "ok", OK, "Payment approved", "Examinee no. 500214. Pick your exam slot.")
      + modal("confirm", "info", "", "Isulan Campus · Sat, Mar 14", '<p style="margin:0">Report by 7:30 AM · exam starts 8:00 AM. You can change your exam slot once, until Mar 1.</p>', '<a class="go" href="permit.html#booked">Confirm</a><a class="back" href="#">Choose another</a>')
      + toast("taken", "bad", BAD, "That exam slot is now full", "Choose another campus or date.")
      + modal("loading", "info", '<span class="spin"></span>', "Loading exam slots", '<div class="skel" style="width:90%"></div><div class="skel" style="width:70%"></div><div class="skel" style="width:80%"></div>', ""),
      states=[("approved", "Arrived after approval"), ("loading", "Loading"), ("confirm", "Confirm"), ("taken", "Exam slot full error")])

phone("permit", "My permit", """<div class="permit"><div class="ph1"><img src="../assets/sksu-seal.png" alt="SKSU seal"><div><b>SULTAN KUDARAT STATE UNIVERSITY</b><small>Examination permit · SKSU TPT · SY 2027–2028</small></div></div>
<div class="pb"><div class="pphoto">2×2 photo</div><div class="pname"><b>DELA CRUZ, Maria Santos</b><small>Examinee no.</small><span class="mono">500214</span></div></div>
<div class="pg"><div><small>Schedule</small><b>Schedule 1</b></div><div><small>Campus</small><b>Isulan</b></div><div class="wide"><small>Date</small><b>Sat, Mar 14, 2027</b></div><div class="wide"><small>Time</small><b>Report by 7:30 AM · exam starts 8:00 AM</b></div><div><small>Room</small><b>Room 4, Main Bldg.</b></div><div><small>Seat</small><b>27</b></div></div>
<div class="pq"><svg width="132" height="132" viewBox="0 0 7 7" role="img" aria-label="Permit QR code" shape-rendering="crispEdges"><rect width="7" height="7" fill="#fff"/><path d="M0 0h3v3H0zM4 0h3v3H4zM0 4h3v3H0zM4 4h1v1H4zM6 4h1v1H6zM5 5h1v1H5zM4 6h1v1H4zM6 6h1v1H6z" fill="#1b1d1c"/><path d="M1 1h1v1H1zM5 1h1v1H5zM1 5h1v1H1z" fill="#fff"/></svg><small>Show at the room door. Works without signal.</small></div></div>
<div class="ghead">Bring</div>""" + plist(row("Pencil No. 2 with eraser"), row("This permit, on your phone or printed"), row("School ID or any valid ID"), row("Official receipt, if paid at the cashier")),
      cta=("../docs/permit-pdf.html", "Save as PDF"), extra='<a class="mocklink" href="result-pending.html">Mockup: after exam day →</a>',
      overlays=toast("booked", "ok", OK, "Exam slot booked", "Isulan Campus · Sat, Mar 14 · report by 7:30 AM · Room 4, seat 27.")
      + modal("making", "info", '<span class="spin"></span>', "Preparing the PDF", '<p style="margin:0">It is saved on your phone after this.</p>', ""),
      states=[("booked", "Arrived after booking"), ("making", "PDF loading")])

phone("result-pending", "Result not yet", """<h1 class="gh">Result</h1>
<div class="hero"><span class="lbl">Release</span><span class="amt" style="font-size:26px">Apr 20, 9:00 AM</span><span class="lbl">You will get a notification and an email.</span></div>
""" + plist(row("Exam taken", "", "Sat, Mar 14 · Isulan")),
      extra='<a class="mocklink" href="result.html">Mockup: results released →</a>',
      overlays=modal("absent", "warn", WARN, "No score: marked absent", '<p style="margin:0">The Testing Center has no score for you from Mar 14. If you took the exam, ask the admission office by Apr 27. You can also apply for Schedule 3; your details are copied from this application.</p>', '<a class="go" href="apply-review.html">Apply for Schedule 3</a><a class="back" href="support.html#new">Ask the admission office</a>')
,
      states=[("absent", "Absent")])

# The tptv3 exam survey, word for word: the office submits these results, so they are the defaults.
SURVEY_SCALE = ["Strongly Agree", "Agree", "Neither Disagree nor Agree", "Disagree", "Strongly Disagree"]
SURVEY_QS = [
    "The pre-registration process is easy and convenient.",
    "The testing personnel (ex. examiners, proctors, peer helpers, security guards and staff) responds efficiently to the needs and concerns of the examinees.",
    "The signages in the testing site are visible and easy to follow.",
    "There are enough rooms and facilities to cater the examinees.",
    "The testing room is conducive and well-ventilated.",
    "The examinees are well-guided of the instructions and procedures before, during and after the examination.",
    "The test materials are readable, sufficient and in good condition.",
    "The duration of the test is adequate.",
    "The test items per subject are adequate and appropriate.",
    "The test questions are comprehensible.",
]
# sample answers (1,204 per question), Strongly Agree first
SURVEY_COUNTS = [(612, 431, 104, 41, 16), (538, 489, 121, 39, 17), (402, 466, 211, 92, 33), (311, 428, 262, 151, 52), (288, 401, 248, 187, 80),
                 (566, 472, 120, 33, 13), (497, 503, 142, 46, 16), (341, 452, 230, 131, 50), (402, 518, 199, 63, 22), (377, 541, 208, 59, 19)]


phone("survey", "Survey", """<h1 class="gh">Exam survey</h1><p>10 statements, about 2 minutes. Answer them before you choose your program.</p>""" + "".join(
    f'<p class="sq"><b>{i}.</b> {q}</p><div class="plist">' + "".join(row(o, lead=RADIO, cls="on" if (i <= 6 and j == (1 if i % 3 else 0)) else "") for j, o in enumerate(SURVEY_SCALE)) + "</div>"
    for i, q in enumerate(SURVEY_QS, 1)) + """
<div class="fld"><label for="c">Comments and suggestions (optional)</label><textarea id="c" rows="3"></textarea></div>""",
      cta=("#thanks", "Submit"), back="result.html",
      overlays=toast("missing", "bad", BAD, "Answer question 7", "All 10 statements need an answer. Comments are optional.")
      + toast("thanks", "ok", OK, "Thank you", "Now choose your program.")
      + modal("already", "info", "", "You already answered the survey", '<p style="margin:0">Thank you. You can choose your program now.</p>', '<a class="go" href="result.html#choose">Choose your program</a>'),
      states=[("missing", "Missing answer"), ("thanks", "Sent"), ("already", "Already answered")])

subj = [("English", 612, 8), ("Science", 548, 6), ("Mathematics", 571, 7), ("Filipino", 655, 9), ("Social Studies", 530, 6), ("ESM Competency", 566, 7)]
sbars = "".join(f'<div class="subj"><div class="h"><span>{n}</span><span><b class="mono">{s}</b><span style="color:#5f6662"> · stanine {t}</span></span></div><div class="t"><span style="width:{round((s - 200) / 6)}%"></span></div></div>' for n, s, t in subj)
phone("result", "Result", f"""<p class="eyebrow">SKSU TPT · Schedule 1 · released Apr 20</p>
<div class="score"><span class="lbl" style="color:#5f6662;font-size:13px">Overall standard score</span><span class="n">584</span><span>Stanine 7 of 9 · Above average</span></div>
<div class="ghead">Programs you qualify for</div>""" + plist(
    row("BS Civil Engineering", "Isulan · cut-off 530", '<span class="dot g"></span>1st choice'),
    row("BS Information Technology", "ACCESS · cut-off 500", '<span class="dot g"></span>2nd choice'),
    row("BS Criminology", "Isulan · cut-off 480", '<span class="dot g"></span>3rd choice'),
    row("41 other programs", "", "", "#cutoffs")) + f"""
<div class="ghead">By subject</div>{sbars}<small>Scores are as given by the SKSU Testing Center. 500 is the average.</small>
<small>Before you choose, answer the 10-statement exam survey.</small>""",
      cta=("survey.html", "Choose your program"), extra='<a class="back" href="../docs/result-pdf.html">Save result as PDF</a>',
      overlays=modal("cutoffs", "info", "", "Programs you qualify for", plist(row("BS Civil Engineering", "Isulan", "530"), row("BS Information Technology", "ACCESS", "500"), row("BS Criminology", "Isulan", "480"), row("BS Agriculture", "Tacurong", "450")) + '<small>Cut-off = lowest overall score that qualifies.</small>', '<a class="back" href="#">Close</a>')
      + modal("choose", "info", "", "Choose your program", '<div class="plist" style="margin:0">' + row("BS Civil Engineering", "Isulan · cut-off 530 · your score 584", "1st choice", "#chosen", "on", RADIO) + row("BS Information Technology", "ACCESS · cut-off 500 · your score 584", "2nd choice", "#chosen", "", RADIO) + '</div><small>The campus registrar contacts you about enrolment.</small>', '<a class="go" href="#chosen">Confirm</a><a class="back" href="#">Cancel</a>')
      + toast("chosen", "ok", OK, "BS Civil Engineering chosen", "The Isulan registrar will contact you."),
      states=[("cutoffs", "Cut-offs"), ("choose", "Choose a program"), ("chosen", "Chosen")])

phone("profile", "My account", """<h1 class="gh">Account</h1>
""" + plist(row("Maria Santos Dela Cruz", "maria.delacruz@gmail.com · Google"), row("Examinee no.", "", '<span class="mono">500214</span>'), row("Status", "", '<span class="dot"></span>Exam slot picked')) + """
<div class="ghead">My details</div>""" + plist(
    row("Personal details", "Maria Santos Dela Cruz · May 12, 2008 · +63 917 123 4567"), row("School", "Isulan National High School · 2026 · STEM"),
    row("Programs", "BS Civil Engineering · BS Information Technology · BS Criminology"), row("2×2 ID photo", "Added Jan 11")) + """
<small>Locked after approval. To change something, ask the admission office.</small>""" + plist(
    row("Request a change", "Opens a support request", "", "support.html#new-change"), row("Exam slot", "1 change left, until Mar 1", "", "seat.html"),
    row("Support", "1 request", "", "support.html"), row("History", "6 events", "", "#history")),
      extra='<a class="back" href="../public/landing.html">Sign out</a>', back="home.html",
      overlays=modal("photo", "info", "", "2×2 ID photo", plist(row("Take a photo", "Uses your camera", href="#photo-ok"), row("Choose from gallery", "JPG or PNG", href="#photo-ok")), '<a class="back" href="#">Cancel</a>')
      + toast("photo-ok", "ok", OK, "Photo updated", "Your permit shows the new photo.")
      + modal("history", "info", "", "History", plist(row("Exam slot booked", "Isulan, Room 4, seat 27", "Jan 13"), row("Payment recorded", "Isulan cashier · OR 0048190 · examinee no. 500214", "Jan 12"), row("Application submitted", "", "Jan 11"), row("Signed in with Google", "", "Jan 11")), '<a class="back" href="#">Close</a>')
      + modal("before", "info", "", "Before approval", '<p style="margin:0">Until the cashier records your payment, your details stay editable.</p>' + plist(row("Personal details", "", "Edit", "apply-personal.html"), row("School", "", "Edit", "apply-school.html"), row("Programs", "", "Edit", "apply-programs.html"), row("2×2 ID photo", "", "Change", "#photo")), '<a class="back" href="#">Close</a>'),
      states=[("before", "Before approval: editable"), ("photo", "Change photo"), ("photo-ok", "Photo saved"), ("history", "History")])


# support: a small ticket system with limits (one open request, 5 per school year)
TOPICS = '<option>Payment</option><option>Application</option><option>Change my details</option><option>Exam slot</option><option>Result</option><option>Privacy request</option><option>Other</option>'
NEW_REQ = ('<div class="fld"><label class="cap" for="nt">Topic</label><select id="nt">{topics}</select></div>'
           '<div class="fld"><label class="cap" for="nm">Message</label><textarea id="nm" rows="4" maxlength="1000">{msg}</textarea><small>10 to 1,000 characters. Links are shown as plain text.</small></div>'
           '<div class="fld"><label class="cap">Photo (optional)</label><a class="picker" href="#"><span class="ph"></span><span class="grow"><b>Add a photo</b><small>JPG or PNG, up to 2 MB, made smaller on your phone</small></span><span class="end">›</span></a></div>')
phone("support", "Support", """<h1 class="gh">Support</h1><p>Questions or changes to your details go to the admission office. You can have one open request at a time, and 5 in a school year.</p>
""" + plist(row("#1042 · Payment", "Is the Isulan cashier open on Saturday?", '<span class="dot g"></span>Answered', "support-ticket.html"),
            row("#0977 · Application", "How do I fix my middle name?", '<span class="dot"></span>Closed', "support-ticket.html")) + """
<small>4 of 5 requests left for SY 2027–2028.</small>""",
      cta=("#new", "New request"), back="notifications.html",
      overlays=modal("new", "info", "", "New request", NEW_REQ.format(topics=TOPICS, msg="Is the Isulan cashier open on Saturday?"), '<a class="go" href="#sent">Send</a><a class="back" href="#">Cancel</a>')
      + modal("new-change", "info", "", "Request a change", NEW_REQ.format(topics=TOPICS.replace("<option>Change my details</option>", "<option selected>Change my details</option>"), msg="Field: middle name. It should be Santos, not Santo.").replace('<div class="fld"><label class="cap" for="nm">', '<div class="fld"><label class="cap" for="nf">What to change</label><select id="nf"><option>Name</option><option>Birth date</option><option>Mobile number</option><option>School</option><option>Programs</option><option>2×2 photo</option></select></div><div class="fld"><label class="cap" for="nm">'), '<a class="go" href="#sent">Send</a><a class="back" href="#">Cancel</a>')
      + toast("sent", "ok", OK, "Request #1043 sent", "The reply will appear here and in your email.")
      + modal("one-open", "info", "", "You have an open request", '<p style="margin:0">You can open a new request when your current one is closed.</p>', '<a class="go" href="support-ticket.html">Open request #1042</a><a class="back" href="#">Close</a>')
      + modal("used-up", "warn", WARN, "No requests left", '<p style="margin:0">You’ve used your 5 requests for this school year. Visit or call the Guidance and Testing Center: (064) 201-0000.</p>', '<a class="back" href="#">Close</a>')
      + modal("muted", "warn", WARN, "Support is paused", '<p style="margin:0">The admission office paused support for your account until Jan 20. Visit or call the Guidance and Testing Center.</p>', '<a class="back" href="#">Close</a>')
      + toast("too-short", "bad", BAD, "Message too short", "Write at least 10 characters.")
      + toast("too-big", "bad", BAD, "Photo too large", "Use a JPG or PNG up to 2 MB."),
      states=[("new", "New request"), ("new-change", "Request a change"), ("sent", "Sent"), ("one-open", "Limit: one open request"), ("used-up", "Limit: 5 per school year"), ("muted", "Support paused"), ("too-short", "Too short"), ("too-big", "Photo too large")])

phone("support-ticket", "Support request", """<p class="eyebrow">#1042 · Payment · Answered</p><h1 class="gh">Is the Isulan cashier open on Saturday?</h1>
<div class="thread"><div class="msg me"><p>Is the Isulan cashier open on Saturday? I can only come on weekends.</p><small>You · Jan 12, 9:02 AM</small></div>
<div class="msg"><p>Yes. The Isulan cashier is open Saturday, 8:00 AM – 12:00 noon. Bring your application code APP-27-10422.</p><small>Ana R., Admission Office · Jan 12, 4:35 PM</small></div></div>
<div class="fld"><label class="cap" for="rp">Reply</label><textarea id="rp" rows="3" maxlength="1000" placeholder="Write a reply"></textarea><small>A reply reopens the request. It closes by itself after 7 days with no reply.</small></div>""",
      cta=("#solved", "Mark as solved"), back="support.html",
      overlays=toast("solved", "ok", OK, "Request closed", "You can open a new request any time.")
      + toast("slow", "bad", BAD, "Please wait a moment", "You can send one reply a minute."),
      states=[("solved", "Marked as solved"), ("slow", "Limit: one reply a minute")])


# ---------------------------------------------------------------- documents (PDFs and emails)
QR = '<svg width="110" height="110" viewBox="0 0 7 7" role="img" aria-label="QR code" shape-rendering="crispEdges"><rect width="7" height="7" fill="#fff"/><path d="M0 0h3v3H0zM4 0h3v3H4zM0 4h3v3H0zM4 4h1v1H4zM6 4h1v1H6zM5 5h1v1H5zM4 6h1v1H4zM6 6h1v1H6z" fill="#18181b"/><path d="M1 1h1v1H1zM5 1h1v1H5zM1 5h1v1H1z" fill="#fff"/></svg>'
LETTERHEAD = '<div style="display:flex;gap:14px;align-items:center;border-bottom:3px solid var(--green);padding-bottom:14px"><img src="../assets/sksu-seal.png" alt="SKSU seal" style="width:64px;height:64px"><div><b style="font-size:18px">SULTAN KUDARAT STATE UNIVERSITY</b><div class="muted">Guidance and Testing Center · Tacurong City, Sultan Kudarat</div></div></div>'
doc("docs/permit-pdf.html", "Permit PDF", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../applicant/permit.html">Back to permit</a></div>
<div class="paper">{LETTERHEAD}<h1 style="text-align:center">EXAMINATION PERMIT · SKSU TPT · SY 2027–2028</h1>
<div style="display:flex;gap:24px"><div style="width:140px;height:140px;border:1px solid var(--line);display:flex;align-items:center;justify-content:center" class="muted">2×2 photo</div>
<div class="kv" style="flex:1"><span>Examinee no.</span><b class="mono" style="font-size:20px">500214</b><span>Name</span><b>DELA CRUZ, Maria Santos</b><span>Schedule</span><span>Schedule 1</span><span>Test center</span><span>Isulan Campus</span><span>Date and time</span><span>Saturday, March 14, 2027 · report by 7:30 AM, exam starts 8:00 AM</span><span>Room / seat</span><span>Room 4 · Seat 27</span></div>{QR}</div>
<div class="alertbox info">Bring: Pencil No. 2 with eraser, this permit, school ID or any valid ID, and the official receipt if you paid at the cashier. Arrive by 7:30 AM.</div>
<div style="margin-top:auto;display:flex;justify-content:space-between" class="muted"><span>Scan the QR to verify: sksu-tpt.com/v/…</span><span>Generated Jan 13, 2027</span></div></div>""")
doc("docs/result-pdf.html", "Result PDF", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../applicant/result.html">Back to result</a></div>
<div class="paper">{LETTERHEAD}<h1 style="text-align:center">SKSU TPT · SY 2027–2028 · RESULT</h1>
<div class="kv"><span>Examinee no.</span><b class="mono">500214</b><span>Name</span><b>DELA CRUZ, Maria Santos</b><span>Tested</span><span>March 14, 2027 · Isulan, Room 4</span></div>
{table(["Subject", "Standard score", "Stanine", "Meaning"], [(n, f'<span class="mono">{s}</span>', t, ["", "Very low", "Low", "Below average", "Low average", "Average", "High average", "Above average", "Very high", "Outstanding"][t]) for n, s, t in subj] + [("<b>Overall</b>", '<b class="mono">584</b>', "<b>7</b>", "<b>Above average</b>")])}
<small class="muted">Scores as provided by the SKSU Testing Center.</small>
<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end"><span class="muted">Verify: sksu-tpt.com/v/…</span><div style="text-align:center"><div style="border-top:1px solid #18181b;width:220px;padding-top:4px">[DIRECTOR, TESTING CENTER]</div></div></div></div>""")
doc("docs/sms.html", "Text messages", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../admin/messages.html">Messages admin</a></div>
<div class="smsgrid">""" + "".join(f'<div class="smsw"><b>{t}</b><div class="sms">{m}</div><small class="muted">{len(m)} of 160 characters</small></div>' for t, m in [('Payment recorded', 'SKSU TPT: Paid at Isulan cashier, OR 0048190. Exam no. 500214. Pick your exam slot by Mar 1: sksu-tpt.com/slot'), ('Sent back', 'SKSU TPT: Please fix your application: the photo is not a 2x2 ID photo. Open sksu-tpt.com/fix'), ('Exam slot booked', 'SKSU TPT: Isulan, Sat Mar 14, Room 4 seat 27. Report by 7:30AM. Permit: sksu-tpt.com/permit'), ('Exam slot changed', 'SKSU TPT: Your exam moved to ACCESS, Sun Mar 15, Room 18 seat 6. New permit: sksu-tpt.com/permit'), ('Exam tomorrow', 'SKSU TPT: Exam tomorrow, Isulan Room 4. Report by 7:30AM, exam 8:00AM. Bring permit, ID, Pencil No. 2.'), ('Results out', 'SKSU TPT: Your result is ready: sksu-tpt.com/result')]) + """</div>""")
doc("docs/email-approved.html", "Email: approved", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Your payment is recorded, Maria</b><p style="margin:0">Paid at the Isulan cashier, OR 0048190. Your examinee number is <b class="mono">500214</b>. Next, pick your exam slot. Slots go fast at Isulan.</p>
<a class="btn primary lg" href="../applicant/seat.html">Pick my exam slot</a><small class="muted">You got this because you applied for the SKSU TPT · SY 2027–2028.</small></div></div>""")
doc("docs/email-rejected.html", "Email: rejected", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Please fix your application</b><div class="alertbox warn"><b>Fix:</b> 2×2 photo. The photo is not a 2×2 ID photo. Use a plain white background and show your whole face.</div>
<p style="margin:0">Nothing is lost. Everything else is saved. Fix that part and we’ll check it again within one working day.</p>
<a class="btn primary lg" href="../applicant/payment-rejected.html">Fix and send again</a></div></div>""")
doc("docs/email-results.html", "Email: results out", """<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a></div>
<div class="mail"><div class="mh"><img src="../assets/sksu-seal.png" alt="" style="width:40px"><b>SKSU Admission Test</b></div><div class="mb">
<b class="ink" style="font-size:18px">Your SKSU TPT result is ready</b><p style="margin:0">Sign in to see your scores and which programs you qualify for.</p>
<a class="btn primary lg" href="../applicant/result.html">See my result</a></div></div>""")


# ---------------------------------------------------------------- proctor pages
def pro(key, title, content, overlays="", states=None):
    doc(f"proctor/{key}.html", title, f"""<div class="crumbs"><a href="../index.html">All pages</a> | <a href="rooms.html">My rooms</a> · <a href="checkin.html">Check-in</a> · <a href="summary.html">Room summary</a></div>
<div class="pro">{STATUS_BAR}<div class="ph"><div style="display:flex;gap:10px;align-items:center"><img src="../assets/sksu-seal.png" alt="SKSU seal"><div><b class="ink" style="font-size:16px">Proctor</b><small class="muted" style="display:block">L. Cabañero · Isulan</small></div></div><span class="b warn">Offline · 3 to send</span></div>
<div class="pb">{content}</div>{overlays}</div>""", "phone-page", states)


pro("rooms", "My rooms", """<h2>Today · Sat, Mar 14</h2>
<a class="ses" href="checkin.html" style="font-family:var(--sans)"><span class="h">Room 4 · Sat, Mar 14<em>50 examinees</em></span><span class="muted">Isulan, Main Building</span></a>
<a class="ses" href="checkin.html" style="font-family:var(--sans)"><span class="h">Room 6 · Sat, Mar 14<em>48 examinees</em></span><span class="muted">Isulan, Main Building</span></a>
<div class="alertbox info">The examinee list is saved on this phone, so check-in works with no signal.</div>
<a class="btn primary lg" href="#download">Download today’s lists</a>""",
    modal("download", "info", '<span class="spin"></span>', "Saving lists to this phone… 2 of 2", '<div class="progress"><span style="width:100%"></span></div>', btn("Done", "#", "primary")), [("download", "Downloading lists")])

pro("checkin", "Check-in", """<div class="k"><div><small class="muted">Here</small><b>31</b></div><div><small class="muted">Not here</small><b>2</b></div><div><small class="muted">Of</small><b class="ink">50</b></div></div>
<div class="cam"><span></span><small>Point at the permit QR</small></div>
<div class="hit"><b class="hitt">Right room</b><div style="display:flex;gap:12px;align-items:center"><div style="width:56px;height:70px;border-radius:8px;background:var(--chip)"></div><div><b class="mono" style="color:var(--green-btn)">500214</b><div class="ink" style="font-size:17px;font-weight:600">Maria S. Dela Cruz</div><small class="muted">Seat 27 · check the face and ID</small></div></div></div>
<div class="pbtn"><a href="#absent" class="pquiet">Not here</a><a href="#present" class="pmain">Here · next</a></div>
<a href="#search" class="muted" style="text-align:center;font-size:13px">No QR? Search by name or number</a>""",
    toast("present", "ok", OK, "Maria S. Dela Cruz is here", "Saved on this phone. 32 of 50.")
    + modal("wrong", "bad", BAD, "Wrong room", '<p class="muted" style="margin:0">500231 Abdul R. Kanakan is in <b>Room 7, seat 12</b>. Send him there.</p>', btn("OK, next", "#", "primary"))
    + modal("dupe", "warn", WARN, "Already checked in", '<p class="muted" style="margin:0">500214 was checked in at 7:41 AM. Check the ID; someone may be using a copy.</p>', btn("OK", "#", "primary"))
    + modal("absent", "info", "", "Note 500214 as not here?", '<p class="muted" style="margin:0">A note for the office only. Absent is decided by the score import.</p>', btn("Cancel", "#") + btn("Note as not here", "#", "primary"))
    + modal("search", "info", "⌕", "Find an examinee", '<input placeholder="Name or examinee no." value="dela cruz"><div class="tl"><div><i></i><span>500214 · Maria S. Dela Cruz · seat 27</span></div></div>', btn("Close", "#")),
    [("present", "Checked in"), ("wrong", "Wrong room error"), ("dupe", "Already scanned"), ("absent", "Not here note"), ("search", "Manual search")])

pro("summary", "Room summary", """<h2>Room 4 · Sat, Mar 14</h2>
<div class="k"><div><small class="muted">Here</small><b>47</b></div><div><small class="muted">Not here</small><b>3</b></div><div><small class="muted">Not scanned</small><b class="ink">0</b></div></div>
<div class="alertbox warn">3 check-ins are still on this phone. They’ll send when you have signal.</div>
<a class="btn primary lg" href="#close">Close the room</a>""",
    modal("close", "warn", WARN, "Close Room 4?", '<p class="muted" style="margin:0">After this, check-ins can only be changed by the admission office.</p>', btn("Cancel", "#") + btn("Close room", "#closed", "primary"))
    + toast("closed", "ok", OK, "Room 4 closed", "47 here, 3 not here. Sent to the admission office as a note.")
    + toast("sync-fail", "bad", BAD, "Couldn’t send yet", "No signal. We’ll retry every minute; don’t uninstall the app."),
    [("close", "Close room dialog"), ("closed", "Closed"), ("sync-fail", "Sync error")])


# ---------------------------------------------------------------- admin pages
ICONS = {
    "dashboard": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    "applications": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>',
    "payments": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    "schedules": '<path d="M4 4h16v16H4z"/><path d="M4 9h16M9 4v16"/>',
    "exam-slots": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
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
    "survey": '<path d="M9 5h11M9 12h11M9 19h11"/><path d="m3 5 1.5 1.5L7 4M3 12l1.5 1.5L7 11M3 19l1.5 1.5L7 18"/>',
    "setup": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "survey-results": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "landing": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 13h8M8 16h5"/>',
    "chair": '<path d="M9 11l3 3 8-8"/><path d="M4 6h7M4 12h3M4 18h9"/>',
    "support": '<path d="M4 5h16v11H8l-4 4z"/><path d="M9 9h6M9 12h4"/>',
    "email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "system": '<rect x="3" y="4" width="18" height="7" rx="1"/><rect x="3" y="13" width="18" height="7" rx="1"/><path d="M7 7.5h.01M7 16.5h.01"/>',
}
NAV = [(None, [("dashboard", "Dashboard"), ("setup", "Setup")]),
       ("Applicants", [("applications", "Applications"), ("cashier", "Cashier counters"), ("support", "Support"), ("messages", "Announcements")]),
       ("Exam", [("schedules", "Exam schedules"), ("exam-slots", "Exam slots"), ("scores", "Import scores"), ("results", "Results")]),
       ("Reports", [("reports", "Reports"), ("survey-results", "Survey results"), ("exports", "Downloads")]),
       ("Management", [("campuses", "Campuses and programs"), ("rooms", "Rooms"), ("staff", "Staff and roles"), ("survey", "Survey"), ("landing", "Student app")]),
       ("System", [("email", "Email and SMS"), ("system", "System status"), ("audit", "Activity logs")])]


ROUNDS_RE = re.compile(r'^\s*(<div class="schedpick">.*?</div></div><!--/schedpick-->)', re.S)
HEAD_RE = re.compile(r'^\s*<div class="head"><span class="muted">(.*?)</span>(.*?)</div>', re.S)
HINT_RE = re.compile(r'^\s*<small class="hint">(.*?)</small>', re.S)


# Only list pages get a "Search this list" box; forms, imports and status pages don't need one.
LIST_PAGES = {"Applications", "Payment review", "Rooms", "Staff and roles", "Activity logs", "Downloads", "Reports"}


def pagehead(title, content, guide=False, setup=""):
    """One page template: title, one-line description and the primary action on top; then filters; then content."""
    schedules = ""
    m = ROUNDS_RE.match(content)
    if m:
        schedules, content = m.group(1), content[m.end():]
    desc, acts = "", ""
    m = HEAD_RE.match(content) or HINT_RE.match(content)
    if m:
        desc = m.group(1)
        acts = m.group(2) if m.re is HEAD_RE else ""
        content = content[m.end():]
    if title in LIST_PAGES and 'class="search"' not in content:
        acts = '<input class="search" aria-label="Search this list" placeholder="Search this list">' + acts
    if guide:
        acts = GUIDE_BTN + acts
    return (f'<div class="pagehead"><div><h1>{title}</h1>{schedules}{f"<p>{desc}</p>" if desc else ""}</div><div class="pacts">{acts}</div></div>'
            f'{setup}{content}')


BELL_ITEMS = [
    ("New support request #1046 · Change my details", "2 more open requests", "12 min ago", "support-ticket.html", True),
    ("Scores import finished", "16 rows need a look", "Apr 18 · 3:41 PM", "scores.html#summary", True),
    ("4 emails or texts failed", "See the send log", "8:00 AM", "messages.html", False),
]
BELL_POP = ('<div class="bellpop" id="q-open"><a class="scrim" href="#" aria-label="Close"></a><div class="pop" role="dialog" aria-label="Notifications">'
            '<div class="pophead"><b>Notifications</b><a href="#">Mark all read</a></div>'
            + "".join(f'<a class="pi{" unread" if u else ""}" href="{h}"><span><b>{t}</b><small>{d}</small></span><time>{w}</time></a>' for t, d, w, h, u in BELL_ITEMS)
            + '<a class="popfoot" href="messages.html">Open Messages</a></div></div>')


CHAIR_NAV = [(None, [("chair", "Transferee applicants")])]


SIDE_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>'
# Collapsible sidebar: wide screens remember the choice; phones open it as a drawer. #side-collapsed shows the collapsed state.
SIDE_SCRIPT = """<script>
function toggleSide(){var b=document.body;if(window.innerWidth<=900){b.classList.toggle("side-open");return}
var c=b.classList.toggle("side-collapsed");try{localStorage.setItem("tpt-side",c?"collapsed":"open")}catch(e){}}
(function(){var c=location.hash==="#side-collapsed";try{c=c||localStorage.getItem("tpt-side")==="collapsed"}catch(e){}
if(c)document.body.classList.add("side-collapsed")})();
function topIfPane(){var t=location.hash&&document.getElementById(location.hash.slice(1));if(t&&t.classList.contains("pane"))window.scrollTo(0,0)}
addEventListener("hashchange",topIfPane);addEventListener("load",topIfPane);
</script>"""


def admin(key, title, content, active=None, overlays="", states=None, crumb="", nav=None, user=("Admission", "Admin"), side_note=""):
    active = active or key
    nav = nav or NAV
    guide = guide_modal(key) if key in GUIDES else ""
    if guide:
        states = [("guide", "Guide")] + list(states or [])
    # the setup line: on the dashboard by default (new school year story), as a state on the busiest pages
    setup = ""
    if key == "dashboard":
        setup = setup_line()
    elif key in ("schedules", "exam-slots", "campuses", "applications") and nav is NAV:
        setup = setup_line("setup-on")
        states = list(states or []) + [("setup-on", "Setup in progress")]
    # search, open schedule and bell are for office staff; a program chair only sees their own list
    tools = "" if nav is CHAIR_NAV else f'''<a class="gsearch" href="search.html">Search name, examinee no., reference<kbd>/</kbd></a><a class="pill ok" href="schedules.html" title="Students can apply now. Click to manage.">Registration open · Schedule 2</a><a href="messages.html#q-open" class="abell" aria-label="Notifications, 3 new">{BELL}<i>3</i></a>'''
    links = []
    for group, items in nav:
        if group:
            links.append(f'<div class="grp">{group}</div>')
        for k, label in items:
            on = ' class="on"' if k == active else ""
            count = '<span class="count">214</span>' if k == "payments" else ""
            links.append(f'<a href="{k}.html"{on} title="{label}"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg><span class="lbl">{label}</span>{count}</a>')
    doc(f"admin/{key}.html", title, f"""<div class="strip"><strong>SKSU TPT · ADMIN MOCKUP</strong><span class="muted">sample data</span><a class="sp" href="../index.html">All pages</a></div>
<header class="top"><button class="sbtoggle" type="button" aria-label="Collapse or expand the menu" title="Menu" onclick="toggleSide()">{SIDE_ICON}</button><img src="../assets/sksu-seal.png" alt="SKSU seal"><span class="name">SKSU TPT</span><span class="muted">Admin</span>
{tools}<div style="line-height:1.15;text-align:right"><div class="ink">{user[0]}</div><small class="muted">{user[1]}</small></div><a href="account.html" class="avatar" style="text-decoration:none">A</a></header>
<nav class="mtabs">{''.join(f'<a href="{k}.html"{" class=on" if k == active else ""}>{label}</a>' for _, items in nav for k, label in items)}</nav>
<div class="shell"><nav class="side">{''.join(links)}{f'<small class="sidenote">{side_note}</small>' if side_note else ''}</nav>
<main>{crumb}{pagehead(title, content, guide=key in GUIDES, setup=setup)}<span id="side-collapsed" hidden></span></main></div>{overlays}{guide}{menu("setupmenu", [("Hide", "#", "", "Only for you; turn it back on in My account")]) if setup else ""}{SIDE_SCRIPT}""", states=states)


def line_chart(vals, labels, w=380, h=150):
    """Trend over time: area line, last point marked."""
    top = max(vals)
    xs = [round(i * (w - 20) / (len(vals) - 1)) + 10 for i in range(len(vals))]
    ys = [round(h - 24 - v / top * (h - 44)) for v in vals]
    pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    area = f"10,{h - 24} {pts} {xs[-1]},{h - 24}"
    anchor = lambda i: "start" if i == 0 else ("end" if i == len(xs) - 1 else "middle")
    ticks = "".join(f'<text x="{x}" y="{h - 6}" text-anchor="{anchor(i)}">{t}</text>' for i, (x, t) in enumerate(zip(xs, labels)) if t)
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
    return (f'<svg class="chart" viewBox="0 0 {w} {h}" style="max-width:{w}px" role="img" aria-label="Overall standard scores, 9,088 examinees, centred on 500">{bars}'
            f'<line x1="20" x2="{w - 20}" y1="{h - 30}" y2="{h - 30}" class="axis"/><line x1="{mean:.0f}" x2="{mean:.0f}" y1="14" y2="{h - 30}" class="mean"/>'
            f'<text x="{mean - 6:.0f}" y="24" text-anchor="end" class="val">average 500</text>{ticks}</svg>')


def rounds_bar(on=1):
    """The schedule picker under a page title: one button that opens a menu of every schedule, then the status as quiet text."""
    schedules = [(1, "Schedule 1", "Mar 14–15", "Finished"), (2, "Schedule 2", "Apr 25–26", "Registration open"), (3, "Schedule 3", "May 30", "Not published"), (4, "Schedule 4", "Dec 12 · Transferees", "Not published")]
    _, name, dates, status = schedules[on - 1]
    items = "".join(f'<a href="#" class="{"on" if n == on else ""}"><span>{t} · {d}</span><small>{st}</small></a>' for n, t, d, st in schedules)
    dot = "live" if status == "Registration open" else ""
    return (f'<div class="schedpick"><a class="schedbtn" href="#schedmenu" aria-haspopup="menu">{name} · {dates} <span aria-hidden="true">▾</span></a>'
            f'<span class="schedst {dot}">{status}</span><div class="menu" id="schedmenu" role="menu">{items}</div></div><!--/schedpick-->')


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


def hint(text):
    return f'<small class="hint">{text}</small>'


def rail(steps, cur, body):
    """Long forms: numbered steps down the left (euphoria's step rail), the form on the right.
    steps = (label, what it covers, href)."""
    items = []
    for i, (label, sub, href) in enumerate(steps, 1):
        cls = "done" if i < cur else ("on" if i == cur else "")
        items.append(f'<a class="{cls}" href="{href}"{' aria-current="step"' if i == cur else ""}><i>{"✓" if i < cur else i}</i><span>{label}<small>{sub}</small></span></a>')
    mini = f'<div class="railmini">Step {cur} of {len(steps)} · <b>{steps[cur - 1][0]}</b> · <a href="#">Show steps</a></div>'
    return (f'<span class="railtarget" id="rail-min"></span>{mini}<div class="railwrap"><nav class="step-rail" aria-label="Steps">{"".join(items)}'
            f'<a class="railhide" href="#rail-min">Hide steps</a></nav><div class="railbody">{body}</div></div>')


SENDBACK_FORM = ('<div class="fld"><label for="sbw">What to fix</label><select id="sbw"><option>2×2 photo</option><option>Personal details</option><option>School details</option></select></div>'
                 '<div class="fld"><label for="sbr">Reason</label><select id="sbr"><option>Photo is not a 2×2 ID photo</option><option>Name does not match the school record</option><option>Other</option></select></div>'
                 '<div class="fld"><label for="sbm">Remarks to the applicant</label><textarea id="sbm" rows="3">The photo is not a 2×2 ID photo. Use a plain white background and show your whole face.</textarea></div>')
SENDBACK_RECEIPT = ('<div class="fld"><label for="sbw2">What to fix</label><select id="sbw2"><option>Receipt</option><option>2×2 photo</option><option>Personal details</option></select></div>'
                    '<div class="fld"><label for="sbr2">Reason</label><select id="sbr2"><option>Reference already used</option><option>Receipt is blurry</option><option>Amount is short</option><option>Other</option></select></div>'
                    '<div class="fld"><label for="sbm2">Remarks to the applicant</label><textarea id="sbm2" rows="3">The reference number on your receipt was already used by another applicant. Please check your GCash receipt and send the right one.</textarea></div>')
ROW_MENU = menu("menu", [("Edit details", "applicant.html#edit", "", "Name, birth date, contact"), ("Move exam slot", "applicant.html#move", "", ""),
                         ("Send back with remarks", "applicant.html#sendback", "", "Photo or details"), ("-", "", "", ""), ("Cancel application", "applicant.html#cancel", "danger", "Frees the exam slot")])


def steps_list(steps):
    """The applicant's process as a quiet vertical list: done steps dark, the current one bold, the rest grey."""
    return '<ol class="vsteps">' + "".join(f'<li class="{state}"><b>{label}</b>{f"<small>{when}</small>" if when else ""}</li>' for label, when, state in steps) + "</ol>"


MARIA_STEPS = [("Submitted", "Jan 11", "done"), ("Paid at cashier", "Jan 12 · OR 0048190", "done"), ("Exam slot", "Isulan · Sat, Mar 14", "now"), ("Scored", "", ""), ("Program chosen", "", "")]


# the one visible action that fits an application's status
STATUS_ACTION = {"Waiting for payment": ("Remind", "#bulk-remind"), "Approved": ("Pick slot", "applicant.html#move"),
                 "Exam slot picked": ("Resend permit", "#resent"), "Sent back": ("See remarks", "applicant.html#sendback"), "Scored": ("See result", "result-detail.html")}


def app_row(i, a):
    no, name, prog, campus, status, day, room = a
    action = STATUS_ACTION.get(status)
    acts = '<span class="act">' + (f'<a class="btn" href="{action[1]}">{action[0]}</a> ' if action else "") + '<a class="btn" href="#view">View</a></span>' + (ROW_MENU if i == 0 else "")
    return (f'<tr data-href="#view" onclick="if(event.target.closest(\'a,input\'))return;location.hash=\'view\'"><td class="selcol"><input type="checkbox" aria-label="Select {name}"></td>'
            f'<td>{two(f"<span class=ink>{name}</span>", no or "no examinee no. yet")}</td><td>{two(prog, campus)}</td><td><span class="st">{status}</span></td>'
            f'<td>{two(day, room) if day else "—"}</td><td>{acts}</td></tr>')

# Schedule 2 exam slots: campus, date, rooms (50 seats each), seats taken, status. Used by the dashboard, Exam slots and the cashier.
SLOTS2 = [("ACCESS, Tacurong", "Sat, Apr 25", 24, 1188, "Open"), ("ACCESS, Tacurong", "Sun, Apr 26", 24, 730, "Open"), ("Isulan", "Sat, Apr 25", 4, 200, "Full"), ("Isulan", "Sun, Apr 26", 4, 162, "Open"),
       ("Tacurong", "Sat, Apr 25", 12, 552, "Open"), ("Kalamansig", "Sun, Apr 26", 8, 296, "Open"), ("Bagumbayan", "Sat, Apr 25", 4, 128, "Closed"), ("Lutayan", "Sat, Apr 25", 3, 93, "Open")]

# dashboard: the numbers the office acts on, one funnel, one trend, seats and campuses
days = [612, 540, 498, 702, 1210, 880, 655, 590, 611, 720, 1302, 940, 812, 212]
prog = [("BS Information Technology", "ACCESS", 1180), ("BS Nursing", "ACCESS", 1012), ("BS Criminology", "Isulan", 884), ("BS Civil Engineering", "Isulan", 610), ("BSEd English", "ACCESS", 522), ("BS Accountancy", "ACCESS", 498), ("BS Agriculture", "Tacurong", 341), ("BS Fisheries", "Palimbang", 88)]
att = [("12 photos to check", "Marked as not a 2×2 ID photo. Send back with remarks.", "applications.html"),
       ("627 approved, no exam slot yet", "Send a reminder, or they are seated automatically on Apr 11.", "applications.html"),
       ("3 questions from students", "The oldest is from 9:02 AM.", "messages.html")]
admin("dashboard", "Dashboard", f"""<div class="examday" id="exam-day">Check-in today: <b>3,904 of 4,212</b> · <a href="checkin.html#live">Open monitor</a></div><div class="tabs"><span class="on">Schedule 2</span><span>Whole school year</span><span class="muted" style="margin-left:auto;font-size:13px">Updated 9:14 AM</span></div>
<div class="kpis">
<a class="kpi" href="applications.html"><span>Applications submitted</span><b>4,980</b><small>212 today</small></a>
<a class="kpi" href="applications.html"><span>Paid</span><b>3,976</b><small>80% of submitted</small></a>
<a class="kpi" href="cashier.html"><span>Paid today</span><b>184</b><small>₱50,600 at 4 counters</small></a>
<a class="kpi" href="exam-slots.html"><span>Exam seats left</span><b>801</b><small>of 4,150</small></a></div>
<div class="row"><div class="panel grow"><div class="head"><h2>Where applicants are</h2></div>
{funnel([("Signed up", 6410), ("Submitted", 4980), ("Paid at the cashier", 3976), ("Picked an exam slot", 3349)])}</div>
<div class="panel" style="width:420px;flex-shrink:0"><div class="head"><h2>Applications per day</h2><a href="reports.html" style="font-size:13px">Reports →</a></div>{line_chart(days, ["Mar 1", "", "", "", "", "", "Mar 7", "", "", "", "", "", "", "Today"])}</div></div>
<div class="row"><div class="panel grow"><div class="head"><h2>Exam seats by day</h2><a href="exam-slots.html" style="font-size:13px">All exam slots →</a></div>
{table(['Exam day', 'Campus', 'Taken', 'Left', ''], [(w, c, f'<div class="meter"><div class="t"><span class="{"full" if t >= r * 50 else ""}" style="width:{round(t / (r * 50) * 100)}%"></span></div></div>', f'<span class="num">{r * 50 - t:,}</span>', B('bad', 'Full') if t >= r * 50 else '') for c, w, r, t, st in SLOTS2 if st != "Closed"])}</div>
<div class="panel" style="width:420px;flex-shrink:0"><div class="head"><h2>1st choice by campus</h2></div>
{hbars([("ACCESS, Tacurong", "", 2420), ("Isulan", "", 1050), ("Tacurong", "", 925), ("Kalamansig", "", 410), ("Bagumbayan", "", 72), ("Palimbang", "", 52), ("Lutayan", "", 51)])}</div></div>
<div class="panel"><div class="head"><h2>Needs attention</h2></div>
{''.join(f'<div class="attn"><div><b>{t}</b><span class="muted">{d}</span></div><a class="btn" href="{h}">Open</a></div>' for t, d, h in att)}</div>""",
      overlays=inmain("loading", '<div class="kpis">' + '<div class="kpi"><span class="skel" style="width:50%"></span><span class="skel" style="height:26px;width:40%;margin:6px 0"></span><span class="skel" style="width:70%"></span></div>' * 4 + '</div>' + skel_table(5, 2)),
      states=[("exam-day", "Exam day: check-in line"), ("loading", "Loading")])

apps = [("500214", "Maria S. Dela Cruz", "BS Civil Engineering", "Isulan", "Exam slot picked", "Sat, Apr 25", "Room 4 · seat 27"),
        ("500215", "Jomar P. Abdullah", "BS Information Technology", "ACCESS, Tacurong", "Approved", "", ""),
        ("", "Aisah K. Mangudadatu", "BS Nursing", "ACCESS, Tacurong", "Waiting for payment", "", ""),
        ("500223", "Ramon T. Villanueva", "BS Agriculture", "Tacurong", "Exam slot picked", "Sun, Apr 26", "Room 12 · seat 3"),
        ("", "Lea M. Sampulna", "BSEd Mathematics", "Kalamansig", "Waiting for payment", "", ""),
        ("", "Noel B. Guiamal", "BS Criminology", "Isulan", "Sent back", "", ""),
        ("500198", "Princess A. Lumabao", "BS Accountancy", "ACCESS, Tacurong", "Exam slot picked", "Sat, Apr 25", "Room 7 · seat 41")]
APP_ROWS = [app_row(i, a) for i, a in enumerate(apps)] + [app_row(9, ("", "Kenneth L. Abo · Transferee", "BS Information Technology", "ACCESS, Tacurong", "Waiting for payment", "", ""))]
VIEW_DRAWER = drawer("view", "Maria S. Dela Cruz", "500214 · SY 2027–2028 · Schedule 1", f"""<div>{B("info", "Exam slot picked")}</div>
<div class="kv"><span>Email</span><span>maria.delacruz@gmail.com</span><span>Mobile</span><span>0917 123 4567</span><span>1st choice</span><span>BS Civil Engineering · Isulan</span>
<span>Payment</span><span>Approved Jan 12 by Cashier 2 · ref <span class="mono">1009284551203</span></span><span>Seat</span><span>Isulan · Sat, Mar 14 · Room 4 · seat 27</span></div>
<h4>Steps</h4>{steps_list(MARIA_STEPS)}""",
                     btn("Close", "#") + btn("Open full record", "applicant.html", "primary"))
DUPES = drawer("dupes", "3 possible duplicates", "Same name and birth date, or same mobile number", f"""{hint("A flag only. If it is the same person, cancel the newer application; nothing is merged.")}
<div class="dupe"><div><b>Maria S. Dela Cruz</b><span class="muted">maria.delacruz@gmail.com · signed up Jan 11 · Exam slot picked</span></div><div><b>Maria Santos Dela Cruz</b><span class="muted">mariadc08@yahoo.com · signed up Jan 20 · Draft</span></div><div class="acts">{btn("Not the same person")}{btn("Open both", "applicant.html", "primary")}</div></div>
<div class="dupe"><div><b>Jomar P. Abdullah</b><span class="muted">0917 555 0101 · Approved</span></div><div><b>Jomar Abdullah</b><span class="muted">0917 555 0101 · In review</span></div><div class="acts">{btn("Not the same person")}{btn("Open both", "applicant.html", "primary")}</div></div>""", btn("Close", "#"))
BULK = f"""<div class="bulkbar" id="bulk"><b>3 selected</b><a class="btn" href="#bulk-remind">Send reminder</a><a class="btn" href="exports.html#queued">Export selected</a><a class="btn" href="#" onclick="document.querySelector('.panel.list').classList.remove('selecting')">Clear</a></div>"""
APP_TABS = [("All", "4,980"), ("Waiting for payment", "790"), ("Approved, no exam slot", "627"), ("Exam slot picked", "3,349"), ("Sent back", "12"), ("Scored", ""), ("Absent", "")]
SELECT = '<a class="btn" href="#bulk" onclick="this.closest(\'.panel\').classList.toggle(\'selecting\')">Select</a>'
admin("applications", "Applications", f"""{rounds_bar(2)}{list_page(stabs(APP_TABS), filters("Name, examinee no., application code (APP-27-…), OR no. or email", [("Campus", ["Any campus", "ACCESS, Tacurong", "Isulan", "Tacurong", "Kalamansig"]), ("Applicant type", ["Freshmen and transferees", "Freshmen", "Transferees"])], right=SELECT, more=True, showing="Showing <b>790</b> · Waiting for payment · Isulan"),
BULK, table(['<span class="selcol"><input type="checkbox" aria-label="Select all"></span>', "Applicant", "1st choice", "Status", "Exam slot", ""], APP_ROWS, sortable=("Applicant", "1st choice", "Exam slot"), active=("Applicant", "asc")),
pager(1, 25, "4,980"), count="4,980 applications", actions=btn("Export (Excel)", "exports.html#queued"))}
<script>if(location.hash==="#bulk")document.querySelector(".panel.list").classList.add("selecting")</script>""",
      overlays=VIEW_DRAWER + DUPES
      + toast("resent", "ok", OK, "Permit email sent", "To maria.delacruz@gmail.com.")
      + modal("bulk-remind", "info", "✉", "Remind 3 applicants?", f'<div class="fld"><label for="bt">Template</label><select id="bt"><option>Pick your exam slot (reminder)</option><option>Payment still waiting</option></select></div><div class="preview">Hi Jomar, your payment is approved but you haven’t picked an exam slot. ACCESS is filling up. Pick yours: sksu-tpt.com/slot</div><div class="fld"><label for="bc">Send by</label><select id="bc"><option>Email and SMS</option><option>Email only</option></select>{hint("SMS costs about ₱0.50 each. 3 messages.")}</div>', btn("Cancel", "#") + btn("Send to 3", "#sent3", "primary"))
      + toast("sent3", "ok", OK, "Reminders sent", "3 emails and 3 texts. See them under Messages.")
      + inmain("empty", empty("search", "No applications match “Sampolna” in Waiting for payment · Isulan", "Check the spelling, or search the examinee no., application code or OR no.", btn("Clear search and filters", "#")))
      + toast("exact", "info", INFO, "500214 is Maria S. Dela Cruz", "An exact examinee no. opens the record straight away.")
      + inmain("loading", '<div class="filters"><span class="skel" style="width:220px;height:34px"></span><span class="skel" style="width:120px;height:34px"></span><span class="skel" style="width:260px;height:34px"></span></div>' + skel_table(8, 6))
      + drawer("view-loading", '<span class="skel" style="width:200px;height:18px;display:block"></span>', "Loading…", '<span class="skel" style="width:30%"></span><div class="kv">' + '<span class="skel"></span><span class="skel"></span>' * 5 + '</div>', ""),
      states=[("side-collapsed", "Sidebar collapsed"), ("view-loading", "Drawer loading"), ("view", "Row clicked: drawer"), ("menu", "··· menu open"), ("bulk", "Select mode + bulk bar"), ("bulk-remind", "Bulk reminder"), ("sent3", "Sent"), ("dupes", "Possible duplicates"), ("resent", "Resent"), ("filtered", "Filter set"), ("more", "More filters: home location"), ("exact", "Exact examinee no. found"), ("loading", "Loading"), ("empty", "No results")])

admin("search", "Search: “dela cruz”", f"""<span class="muted">Search works from every page: press <kbd>/</kbd> and type a name, examinee number, email or GCash reference.</span>
<div class="panel"><h2>Applicants · 3</h2>{table(["", "", "", ""], [('<b class="mono ink">500214</b>', two("Maria S. Dela Cruz", "maria.delacruz@gmail.com"), B("info", "Exam slot picked"), btn("Open", "applicant.html")), ('<b class="mono ink">—</b>', two("Maria Santos Dela Cruz", "mariadc08@yahoo.com"), B("gray", "Draft"), btn("Open", "applicant.html")), ('<b class="mono ink">501990</b>', two("Joel R. Dela Cruz", "joeldc@gmail.com"), B("ok", "Approved"), btn("Open", "applicant.html"))])}</div>
<div class="panel"><h2>Payments · 1</h2>{table(["", "", "", ""], [('<span class="mono">1009284551203</span>', "Maria S. Dela Cruz", B("ok", "Approved"), btn("Open", "payments.html"))])}</div>""", active="applications")

admin("applicant", "Maria S. Dela Cruz", f"""<div class="tabsbar"><a class="on" href="#">Overview</a><a href="#">Application</a><a href="#">Payment</a><a href="#">Permit</a><a href="#">Result</a><a href="#">History</a></div>
<div class="row"><div class="panel grow"><h2>Application</h2><div class="kv">
<span>Status</span><span>{B("info", "Exam slot picked")}</span><span>Examinee no.</span><span class="mono ink">500214</span><span>Email</span><span>maria.delacruz@gmail.com</span><span>Mobile</span><span>0917 123 4567</span>
<span>Birth date</span><span>May 12, 2008 (18)</span><span>School</span><span>Isulan National High School · 2026 · STEM · GWA 91.4</span>
<span>Choices</span><span>1 BS Civil Engineering (Isulan) · 2 BS IT (ACCESS) · 3 BS Criminology (Isulan)</span><span>Exam slot</span><span>Isulan · Sat, Mar 14 · Room 4 · seat 27</span></div>
<h2 style="margin-top:8px">Uploads</h2>
<div class="uploads"><div class="up"><div class="thumb">Photo</div><div><b>2×2 photo</b><span class="muted">photo.jpg · 248 KB · Jan 11</span>{B("ok", "Accepted")}</div>{btn("View", "#photo")}</div>
</div><div class="kv"><span>Payment</span><span>₱275.00 · paid at Isulan cashier · OR <span class="mono">0048190</span> · Jan 12, 4:30 PM</span></div>
<div style="display:flex;gap:8px;flex-wrap:wrap">{btn("Edit details", "#edit")}{btn("Move exam slot", "#move")}{btn("···", "#amenu")}</div>{menu("amenu", [("View permit", "../docs/permit-pdf.html", "", ""), ("Send back with remarks", "#sendback", "", "Photo or details"), ("-", "", "", ""), ("Void payment", "#void", "danger", "Releases the exam slot"), ("Cancel application", "#cancel", "danger", "")])}</div>
<div style="width:360px;flex-shrink:0;display:flex;flex-direction:column;gap:16px"><div class="panel" id="q"><div class="head"><h2>Support</h2></div><p style="margin:0"><span class="mono">#1042</span> · Payment · Answered</p><p style="margin:0" class="muted">Is the Isulan cashier open on Saturday?</p><a href="support-ticket.html">Open request →</a></div>
<div class="panel"><h2>Steps</h2>{steps_list(MARIA_STEPS)}</div>
<div class="panel"><h2>History</h2><div class="tl">
<div><i></i><span>Jan 13 9:42 AM · Maria booked Isulan, Room 4 seat 27</span></div><div><i></i><span>Jan 12 4:30 PM · Cashier 2 recorded OR 0048190 at Isulan, issued 500214</span></div>
<div><i></i><span>Jan 11 7:55 PM · Maria submitted the application</span></div><div><i></i><span>Jan 11 7:31 PM · Maria signed up with Google</span></div></div></div></div></div>""",
      active="applications", crumb='<a href="applications.html" class="muted">← Applications</a>',
      overlays=modal("edit", "info", "✎", "Edit details", '<div class="fld"><label for="e1">Full name</label><input id="e1" value="Maria Santos Dela Cruz"></div><div class="fld err"><label for="e2">Birth date</label><input id="e2" type="date" value="2018-05-12"><span class="errmsg">Must be at least 15 years old on exam day.</span></div><div class="fld"><label for="e3">Reason (goes in the history)</label><input id="e3" value="Typo in middle name"></div><small class="muted">Only the admission office can change details after approval. A change asked by the student shows its support request number.</small>', btn("Cancel", "#") + btn("Save", "#saved", "primary"))
      + toast("saved", "ok", OK, "Saved", "The change and your reason are in the history.")
      + toast("replied", "ok", OK, "Reply sent", "Maria sees it in her app and by email. It is in the history too.")
      + modal("sendback", "warn", WARN, "Send back to Maria?", SENDBACK_FORM, btn("Cancel", "#") + btn("Send back", "#saved", "primary"))
      + modal("move", "info", "⇄", "Move to another exam slot", '<select><option>ACCESS · Sun Mar 15 · 112 left</option><option>Tacurong · Sat Mar 14 · 12 left</option></select><p class="muted" style="margin:0">Maria gets an email with the new room and seat.</p>', btn("Cancel", "#") + btn("Move", "#moved", "primary"))
      + toast("moved", "ok", OK, "Moved", "ACCESS · Room 18 · seat 6. Email sent.")
      + modal("cancel", "bad", BAD, "Cancel this application?", '<p class="muted" style="margin:0">Her exam slot is freed and her permit stops working. She can’t take the test this school year. Type CANCEL to confirm.</p><input placeholder="CANCEL">', btn("Keep it", "#") + btn("Cancel application", "#", "danger"))
      + modal("waive", "warn", WARN, "Waive Maria’s exam fee?", '<div class="fld"><label for="wv">Reason</label><select id="wv"><option>Indigent (certificate from the barangay)</option><option>Scholar (CHED or LGU)</option><option>SKSU employee dependent</option></select></div><div class="fld"><label for="wvd">Proof (optional)</label><input id="wvd" placeholder="e.g. certificate no. 2027-0193"></div>' + hint("She is approved at once and gets an examinee number. Waivers show in the Payments report."), btn("Cancel", "#") + btn("Waive fee", "#", "primary"))
      + modal("void", "warn", WARN, "Void Maria’s payment?", '<div class="fld"><label for="vr">Reason (required, sent to Maria)</label><select id="vr"><option>OR number recorded for the wrong applicant</option><option>Payment was reversed by the bank or GCash</option><option>Duplicate payment</option></select></div><div class="kv"><span>Then</span><span>Status goes back to “Waiting for payment”</span><span>Exam slot</span><span>Room 4 · seat 27 is released (the exam hasn’t happened)</span><span>Maria</span><span>Gets the reason in the app, by email and by text, and can pay again</span></div>', btn("Cancel", "#") + btn("Void payment", "#voided", "danger"))
      + toast("voided", "ok", OK, "Payment voided", "Maria was told why and can pay again. Her exam slot is free.")
      + modal("photo", "info", "▢", "2×2 photo", '<div class="thumb" style="width:200px;height:200px;align-self:center">Photo</div><div class="fld"><label for="pr">If it’s not usable</label><select id="pr"><option>Face not clear</option><option>Not a 2×2 ID photo</option><option>Someone else</option></select></div>', btn("Close", "#") + btn("Ask for a new photo", "#asked", "danger"))
      + toast("asked", "ok", OK, "Photo request sent", "Maria gets an email and can upload a new one; her exam slot is kept."),
      states=[("void", "Void payment"), ("voided", "Voided"), ("edit", "Edit dialog with error"), ("saved", "Saved"), ("move", "Move exam slot"), ("moved", "Moved"), ("cancel", "Danger confirm"), ("photo", "Review a photo"), ("asked", "New photo requested"), ("replied", "Question answered"), ("amenu", "··· menu"), ("sendback", "Send back with remarks")])

admin("cashier", "Cashier counters", f"""<div class="head"><span class="muted"></span>{btn("Open the cashier console", "../cashier/console.html", "primary")}</div>
<div class="kpis"><div class="kpi"><span>Recorded today</span><b>₱33,825</b><small>123 payments at 4 counters</small></div><div class="kpi"><span>Counters open</span><b>3</b><small>of 4</small></div><div class="kpi"><span>Voided today</span><b>2</b><small>by an admin, with a reason</small></div></div>
{table(["Counter", "Cashier", "Payments", "Collected", "Status", ""], [("Isulan counter 1", "Cashier 1", "36", "₱9,900", B("ok", "Open"), btn("View", "../cashier/paid.html")), ("ACCESS counter 1", "Cashier 2", "52", "₱14,300", B("ok", "Open"), btn("View", "../cashier/paid.html")), ("ACCESS counter 2", "Cashier 3", "21", "₱5,775", B("ok", "Open"), btn("View", "../cashier/paid.html")), ("Tacurong counter 1", "Cashier 4", "14", "₱3,850", B("gray", "Closed"), btn("View", "../cashier/paid.html"))])}""")

q = [("Aisah K. Mangudadatu", "1009284551203", "6 h", B("warn", "Same ref."), True), ("Lea M. Sampulna", "1009284552455", "5 h", B("gray", "Waiting"), False), ("Ramon T. Villanueva", "1009284552310", "5 h", B("gray", "Waiting"), False), ("Noel B. Guiamal", "1009284552601", "3 h", B("gray", "Waiting"), False), ("Princess A. Lumabao", "1009284552711", "2 h", B("gray", "Waiting"), False), ("Farida M. Ampatuan", "1009284552840", "40 min", B("gray", "Waiting"), False)]
admin("payments", "Payment review", f"""<div class="alertbox warn">Only when online payment is turned on for the school year. With cashier-only payment there is no receipt queue.</div>
<div class="row">
<div class="queue"><div class="qh"><span>Waiting · oldest first</span><span class="muted" style="font-size:12px">A approve · S send back</span></div><div style="padding:8px 12px;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:6px"><input class="search" style="width:100%" aria-label="Search waiting payments" placeholder="Search name or reference"><span style="display:flex;gap:6px"><select aria-label="Schedule" style="flex:1"><option>Schedule 2</option><option>All schedules</option></select><select aria-label="Campus" style="flex:1"><option>All campuses</option><option>Isulan</option><option>ACCESS, Tacurong</option></select></span></div>{''.join(f'<a href="#"{" class=on" if on else ""}><span><span class="ink">{n}</span><span class="sub mono">{r} · {a}</span></span>{b}</a>' for n, r, a, b, on in q)}<div class="pager" style="padding:8px 12px"><span class="muted">1–25 of 214</span><span>{btn('More', '#', 'sm')}</span></div></div>
<div class="panel grow"><div class="head"><h2>Proof of payment</h2><span class="muted" style="font-size:12px">gcash-receipt.jpg · 310 KB</span></div>
<div class="proof"><div class="receipt"><b>Receipt image</b><div><span class="muted">Amount</span><b>₱275.00</b></div><div><span class="muted">Ref. no.</span><b class="mono">1009284551203</b></div><div><span class="muted">Date</span><b>Jan 13, 2027</b></div></div></div></div>
<div style="width:320px;flex-shrink:0;display:flex;flex-direction:column;gap:12px">
<div class="panel"><h2 style="font-size:18px">Aisah K. Mangudadatu</h2><span class="muted">1st: BS Nursing, ACCESS · <a href="applicant.html">Application, photo and documents</a></span>
<div class="head"><span class="muted">Typed reference</span><b class="mono ink">1009284551203</b></div><div class="head"><span class="muted">Paid on</span><span class="ink">Jan 13, 2027</span></div>
<div class="note warn">Same reference as Maria S. Dela Cruz (approved Jan 12)</div></div>
{btn("Approve and issue number", "#approve", "primary lg")}
{btn("Send back with remarks", "#reject", "lg")}</div></div>""",
      overlays=modal("approve", "warn", WARN, "Approve a reused reference?", '<p class="muted" style="margin:0">This reference was already approved for Maria S. Dela Cruz. Approve only if you checked the GCash records.</p>', btn("Cancel", "#") + btn("Approve anyway", "#approved", "primary"))
      + toast("approved", "ok", OK, "Approved · 500216 issued", "Aisah was notified in the app, by email and by text. Next: Lea M. Sampulna.")
      + modal("reject", "warn", WARN, "Send back to Aisah?", SENDBACK_RECEIPT + '<p class="muted" style="margin:0">She sees the remarks in the app, by email and by text, fixes that part and sends it again.</p>', btn("Cancel", "#") + btn("Send back", "#rejected", "primary"))
      + toast("rejected", "ok", OK, "Sent back to Aisah", "Next: Lea M. Sampulna.")
      + toast("conflict", "bad", BAD, "Ben T. already decided this one", "It was approved 10 s ago. Showing the next one.")
      + inmain("empty", empty("inbox", "All caught up", "No payments are waiting. New ones appear here by themselves.", btn("Go to applications", "applications.html")))
      + inmain("loading", '<div class="row"><div class="queue">' + skel_table(8, 1) + '</div><div class="grow">' + skel_table(3, 2) + '</div></div>'),
      states=[("loading", "Loading"), ("approve", "Approve warning"), ("approved", "Approved toast"), ("reject", "Send back with remarks"), ("rejected", "Sent back toast"), ("conflict", "Two reviewers conflict"), ("empty", "Empty queue")])

EXAM_CAMPUSES = [("ACCESS, Tacurong", 24, 1200), ("Isulan", 4, 200), ("Tacurong", 12, 600), ("Kalamansig", 8, 400), ("Bagumbayan", 4, 200), ("Palimbang", 4, 200), ("Lutayan", 3, 150)]
WHERE_FORM = ('<h4 class="fsec">Where</h4><div class="campchecks">'
              + "".join(f'<label class="chkrow"><input type="checkbox" checked> {c} <span class="muted">· {r} rooms · {n:,} seats</span></label>' for c, r, n in EXAM_CAMPUSES)
              + '</div><small class="muted">Creates <b>7 exam slots · 2,950 seats</b> (one per campus for each exam day, using that campus’s rooms). Edit them later on Exam slots.</small>')
CAMPS = "Isulan, ACCESS, Tacurong, Kalamansig, Bagumbayan, Palimbang, Lutayan"
admin("schedules", "Exam schedules", f"""<div class="head"><span class="muted">SY 2027–2028 · 4 schedules</span>{btn("New school year", "setup-1.html", "primary")}</div>
{ptabs([("current", "This school year"), ("years", "All school years")])}
<section class="pane" id="pane-current"><div class="panel list"><div class="head"><h2>SY 2027–2028</h2>{btn("Add schedule", "#round")}</div>
{table(["Schedule", "Where", "Registration", "Exam", "Results", "Applicants", "Status", ""], [
    ('<b class="ink">Schedule 1</b>', f'<a href="exam-slots.html" title="{CAMPS}">7 campuses · 12 slots</a>', '<span class="num">Jan 1 – Feb 28</span>', '<span class="num">Mar 14–15</span>', '<span class="num">Released Apr 20</span>', '<span class="num">9,733</span>', '<span class="st">Finished</span>', rowact("results.html", "#s1menu", ("Check-in", "checkin.html#live"))),
    ('<b class="ink">Schedule 2</b>', f'<a href="exam-slots.html" title="{CAMPS}">7 campuses · 8 slots</a>', '<span class="num">Mar 1 – Apr 10</span>', '<span class="num">Apr 25–26</span>', '<span class="num">Releases May 15</span>', '<span class="num">4,980</span>', '<span class="st live">Registration open</span>', rowact(None, "#s2menu", ("Edit", "#round"))),
    ('<b class="ink">Schedule 3</b>', '<span class="muted">No slots yet ·</span> <a href="exam-slots.html#add">Add</a>', '<span class="num">Apr 11 – May 15</span>', '<span class="num">May 30</span>', '<span class="num">Not set</span>', '<span class="num">0</span>', '<span class="st">Not published</span>', rowact(None, "#s3menu", ("Publish", "#publish"))),
    ('<b class="ink">Schedule 4</b> <span class="tag">Transferees</span>', '<span title="Testing Room, Guidance and Testing Center, SKSU ACCESS Campus">ACCESS · Testing Room</span>', '<span class="num">Nov 2 – Dec 3</span>', '<span class="num">Dec 12</span>', '<span class="num">Not set</span>', '<span class="num">0</span>', '<span class="st">Not published</span>', rowact(None, "#s3menu", ("Publish", "#publish")))])}
{menu("s1menu", [("Edit dates", "#round", "", "")])}{menu("s2menu", [("Unpublish", "#unpublish", "danger", "New applications stop")])}{menu("s3menu", [("Edit", "#round", "", "")])}
<div class="setrow"><span>Absent examinees can take a later schedule without paying again</span><a class="switch on" href="#" aria-label="Absent examinees can take a later schedule without paying again"></a></div>
<small class="muted">Students can apply only while a schedule is published and its registration is open.</small></div></section>
<section class="pane" id="years">{list_page(table(["School year", "Schedules", "Applicants", "Status", ""], [
    ('<b class="ink">SY 2027–2028</b>', "4 · Mar 14 – Dec 12", '<span class="num">14,713</span>', '<span class="st live">Current</span>', btn("Edit", "#edit-sy")),
    ('<b class="ink">SY 2026–2027</b>', "1 · Mar 8", '<span class="num">10,214</span>', '<span class="st">Finished</span>', btn("View")),
    ('<b class="ink">SY 2025–2026</b>', "1 · Oct 25", '<span class="num">8,930</span>', '<span class="st">Finished</span>', btn("View"))]))}</section>""",
      overlays=modal("new", "info", "+", "New school year", '<div class="fld"><label for="s1">School year</label><select id="s1"><option>2028–2029</option><option>2029–2030</option></select></div><div class="two" style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="s2">Registration opens</label><input id="s2" type="date" value="2028-01-03"></div><div class="fld"><label for="s3">Closes</label><input id="s3" type="date" value="2028-02-26"></div></div><div class="fld"><label for="s4">Exam fee</label><span class="money"><span>₱</span><input id="s4" inputmode="decimal" value="275.00"></span></div><div class="fld"><label for="s5">Schedules</label><select id="s5"><option>3 schedules</option><option>2 schedules</option><option>1 schedule</option></select></div><label style="display:flex;gap:8px;font-size:14px"><input type="checkbox" checked>Copy campuses, programs, rooms and staff from SY 2027–2028</label>', btn("Cancel", "#") + btn("Create", "#open-conflict", "primary"))
      + modal("open-conflict", "warn", WARN, "SY 2027–2028 is still open", '<p class="muted" style="margin:0">Finish SY 2027–2028 first, or save SY 2028–2029 to publish later.</p>', btn("Save for later", "#created") + btn("Finish 2027–2028 and open 2028–2029", "#", "danger"))
      + modal("edit-sy", "info", "✎", "SY 2027–2028", '<div class="fld"><label for="ef">Exam fee</label><span class="money"><span>₱</span><input id="ef" inputmode="decimal" value="275.00"></span></div><h3 style="margin:8px 0 0;font-size:15px">Examinee numbers</h3><div class="kv"><span>Pattern</span><span>6 digits, no prefix, counting up by 1 <span class="muted">(locked: numbers already given)</span></span><span>Started at</span><span class="mono">500001</span><span>Next number</span><span class="mono">509734</span></div><div class="fld"><label for="en">Skip ahead to (optional)</label><input id="en" inputmode="numeric" maxlength="6" placeholder="e.g. 510001"></div><small class="hint">Numbers already given never change. You can only move the next number forward, never back, so no number is used twice.</small><h3 style="margin:8px 0 0;font-size:15px">Payment methods</h3><div class="setrow"><span>At an SKSU cashier</span><span class="muted">Always on</span></div><div class="setrow"><span>Online, with receipt upload</span><a class="switch" href="#" aria-label="Online payment with receipt upload"></a></div><small class="hint">Turn on when the office has a GCash or bank account. Students then upload a receipt and an admin checks it in Payment review.</small>', btn("Cancel", "#") + btn("Save", "#sy-saved", "primary"))
      + toast("sy-saved", "ok", OK, "Saved", "Applicants see the change on the payment step.")
      + toast("created", "ok", OK, "SY 2028–2029 saved, not published", "Students can’t see it until you publish Schedule 1.")
      + modal("round", "info", "+", "Schedule 3 · SY 2027–2028", '<div class="fld"><label>Who is this schedule for?</label><label class="chkrow"><input type="radio" name="for" checked> Freshmen</label><label class="chkrow"><input type="radio" name="for"> Transferees (2nd semester)</label></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="r1">Registration opens</label><input id="r1" type="date" value="2027-04-11"></div><div class="fld"><label for="r2">Closes</label><input id="r2" type="date" value="2027-05-15"></div><div class="fld"><label for="r3">Exam day(s)</label><input id="r3" type="date" value="2027-05-30"></div><div class="fld err"><label for="r4">Results release</label><input id="r4" type="date" value="2027-05-20"><span class="errmsg">Must be after the exam day.</span></div></div>' + WHERE_FORM + '<h4 class="fsec">Exam day</h4><div class="setrow"><span>Check-in at the door<small>Proctors scan permits. Off: absences come from the score import.</small></span><a class="switch" href="#" aria-label="Check-in at the door"></a></div>', btn("Cancel", "#") + btn("Save schedule", "#round-saved", "primary"))
      + toast("round-saved", "ok", OK, "Schedule 3 saved, not published", "Students can't see it until you publish it.")
      + modal("cal", "info", "", "Registration dates · Schedule 3", '<div class="two" style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="c1">Opens</label><input id="c1" type="date" value="2027-04-11"></div><div class="fld"><label for="c2">Closes</label><input id="c2" type="date" value="2027-05-15"></div></div>' + calendar("April 2027", 4, 30, 11, 30, today=29) + '<p class="muted" style="margin:0">Pick the first day, then the last. Apr 11 – May 15 · 35 days.</p>', btn("Cancel", "#round") + btn("Use these dates", "#round", "primary"))
      + modal("sched-t", "info", "+", "Schedule 4 · Transferees", '<div class="fld"><label>Who is this schedule for?</label><label class="chkrow"><input type="radio" name="for2"> Freshmen</label><label class="chkrow"><input type="radio" name="for2" checked> Transferees (2nd semester)</label></div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="t1">Registration opens</label><input id="t1" type="date" value="2027-11-02"></div><div class="fld"><label for="t2">Closes</label><input id="t2" type="date" value="2027-12-03"></div>'
        '<div class="fld"><label for="t3">Exam day</label><input id="t3" type="date" value="2027-12-12"></div><div class="fld"><label for="t4">Fee</label><span class="money"><span>₱</span><input id="t4" inputmode="decimal" value="275.00"></span></div>'
        '<div class="fld"><label for="t5">Report by (guide)</label><input id="t5" type="time" value="07:30"></div><div class="fld"><label for="t6">Exam starts (guide)</label><input id="t6" type="time" value="08:00"></div></div>'
        '<h4 class="fsec">Where</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="t8">Campus</label><select id="t8"><option>ACCESS, Tacurong</option><option>Isulan</option></select></div>'
        '<div class="fld"><label for="t7">Room</label><select id="t7"><option>Testing Room, Guidance and Testing Center · 60 seats</option><option>CTE · Room 12 · 50 seats</option></select></div></div>'
        + hint("Applicants pick 2 programs and upload their grades. The program chairperson approves before they can pay at the cashier."), btn("Cancel", "#") + btn("Save schedule", "#round-saved", "primary"))
      + modal("publish", "info", "", "Publish Schedule 3?", '<p class="muted" style="margin:0">Students see the Apply button from <b class="ink">Apr 11</b>, when registration opens. Until then the home page says “Schedule 3 opens Apr 11”.</p><div class="kv"><span>Exam days</span><span>May 30 · 4 campuses</span><span>Seats</span><span>2,000</span><span>Fee</span><span>₱275.00</span></div>', btn("Cancel", "#") + btn("Publish", "#published", "primary"))
      + toast("published", "ok", OK, "Schedule 3 published", "Registration opens Apr 11. You can unpublish it any time.")
      + modal("unpublish", "warn", WARN, "Unpublish Schedule 2?", '<p class="muted" style="margin:0">Students can’t start or submit new applications. Anyone who already submitted or paid keeps their progress and seat.</p><div class="fld"><label for="up1">Message on the home page (optional)</label><input id="up1" placeholder="Registration is paused. Please check back on Mar 20."></div>', btn("Cancel", "#") + btn("Unpublish", "#unpublished", "danger"))
      + toast("unpublished", "ok", OK, "Schedule 2 unpublished", "Students can’t apply until you publish it again."),
      states=[("years", "All school years tab"), ("edit-sy", "Edit school year · payment methods"), ("sy-saved", "School year saved"), ("publish", "Publish schedule"), ("published", "Published"), ("unpublish", "Unpublish schedule"), ("unpublished", "Unpublished"), ("s2menu", "··· menu"), ("new", "New school year form"), ("open-conflict", "Conflict warning"), ("created", "Created"), ("round", "Schedule form with error"), ("cal", "Calendar open"), ("round-saved", "Schedule saved"), ("sched-t", "Transferee schedule form")])

SETUP_STEPS = [("Basics", "School year and fee", "setup-1.html"), ("Schedules", "One or more, with dates", "setup-2.html"), ("Campuses and programs", "What is offered", "setup-3.html"),
               ("Exam slots and rooms", "Where and when", "setup-4.html"), ("Review and publish", "Nothing is public before this", "setup-5.html")]


def setup(n, body, nxt):
    back = btn("Back", f"setup-{n - 1}.html") if n > 1 else btn("Cancel", "schedules.html")
    admin(f"setup-{n}", "New school year · 2028–2029", f"""{rail(SETUP_STEPS, n, f'<div class="panel formpage"><div class="scrollx">{body}</div></div><div class="formfoot">{back}<span class="muted" style="margin-left:auto;font-size:13px">Saved as a draft as you go</span>{btn("Save draft", "schedules.html#created")}{nxt}</div>')}""", active="schedules",
          crumb='<a href="schedules.html" class="muted">← Exam schedules</a>',
          overlays=modal("open", "info", "", "Publish Schedule 1 of SY 2028–2029?", '<p class="muted" style="margin:0">Students see the Apply button from <b class="ink">Jan 3, 2028</b>, when registration opens. You can unpublish it any time from Exam schedules.</p>', btn("Cancel", "#") + btn("Publish", "schedules.html#published", "primary")) if n == 5 else "",
          states=[("rail-min", "Steps hidden")] + ([("open", "Publish confirm")] if n == 5 else []))


setup(1, f"""<h2>Basics</h2>{hint("You add its exam schedules (1st, 2nd, 3rd) on the next step.")}
<div class="formgrid"><div class="fld"><label for="n2">School year</label><select id="n2"><option>2028–2029</option><option>2029–2030</option></select>{hint("Shown to applicants as “SKSU TPT · SY 2028–2029”.")}</div>
<div class="fld"><label for="n3">Exam fee</label><span class="money"><span>₱</span><input id="n3" inputmode="decimal" value="275.00"></span>{hint("Applicants see this on the payment step.")}</div>
<div class="fld" style="grid-column:1/-1"><label>Examinee number pattern</label><div class="pattern"><span><small>Prefix (optional)</small><input aria-label="Prefix" maxlength="4" placeholder="none"></span><span><small>Digits</small><select aria-label="Digits"><option>5</option><option selected>6</option><option>7</option><option>8</option></select></span><span><small>Start at</small><input aria-label="Start at" inputmode="numeric" value="600001"></span></div>{hint("Preview: 600001, 600002, 600003 … Last school year: 500001 to 509733. The pattern locks once the first number is given; next school year can use a new one.")}</div>
</div><h3 style="margin:8px 0 0;font-size:15px">Payment methods</h3><div class="setrow"><span>At an SKSU cashier</span><span class="muted">Always on</span></div><div class="setrow"><span>Online, with receipt upload</span><a class="switch" href="#" aria-label="Online payment with receipt upload"></a></div><small class="hint">Turn on when the office has a GCash or bank account. Students then upload a receipt and an admin checks it in Payment review.</small>
<label class="check"><input type="checkbox" checked>Copy campuses, programs, rooms, staff and message templates from SY 2027–2028</label>""", btn("Next: schedules", "setup-2.html", "primary"))
setup(2, f"""<h2>Schedules</h2>
{table(["Schedule", "Where", "Registration opens", "Closes", "Exam day", "Results", ""], [(f"<b>Schedule {i}</b>", '<a href="schedules.html#round" title="Isulan, ACCESS, Tacurong, Kalamansig, Bagumbayan, Palimbang, Lutayan">7 campuses</a>', f'<input type="date" value="{o}">', f'<input type="date" value="{c}">', f'<input type="date" value="{e}">', f'<input type="date" value="{r}">', btn("Remove", "#")) for i, o, c, e, r in [(1, "2028-01-03", "2028-02-26", "2028-03-11", "2028-04-14"), (2, "2028-02-27", "2028-04-08", "2028-04-22", "2028-05-12"), (3, "2028-04-09", "2028-05-13", "2028-05-27", "2028-06-16")]])}
<a class="btn" href="#" style="align-self:flex-start">+ Add a schedule</a>
<div class="alertbox info">Dates can overlap only between registration of one schedule and the exam of the schedule before.</div>""", btn("Next: campuses", "setup-3.html", "primary"))
setup(3, f"""<h2>Campuses and programs</h2>{hint("Copied from SY 2027–2028. Switch off a campus that won’t hold the exam.")}
{table(["Campus", "Programs offered", "Test center", ""], [(c, f"{p} of {p}", '<a class="switch on" href="#"></a>', btn("Edit programs", "campuses.html")) for c, p in [("ACCESS, Tacurong", 22), ("Isulan", 14), ("Tacurong", 9), ("Kalamansig", 5), ("Bagumbayan", 2), ("Palimbang", 2), ("Lutayan", 2)]])}""", btn("Next: exam slots", "setup-4.html", "primary"))
setup(4, f"""<h2>Exam slots and rooms</h2>
{table(["Campus", "Rooms", "Seats per exam day", "Schedule 1 · Mar 11", "Schedule 2 · Apr 22", "Schedule 3 · May 27", ""], [(f'<span class="ink">{c}</span>', f'<span class="num">{r}</span>', f'<span class="num">{n:,}</span>', "✓", "✓", '<span class="muted">—</span>', btn("Rooms", "rooms.html", "sm")) for c, r, n in EXAM_CAMPUSES])}
<small class="muted">✓ = an exam slot on that day. Schedule 1 and 2: 7 exam slots · 2,950 seats each.</small>
<div class="alertbox warn">Schedule 3 has no exam slots yet. You can open the school year and add them later.</div>""", btn("Next: review", "setup-5.html", "primary"))
setup(5, f"""<h2>Review and publish</h2>
<div class="kv"><span>School year</span><span class="ink">SY 2028–2029</span><span>Exam fee</span><span>₱275.00</span><span>Schedules</span><span>3 · Mar 11, Apr 22, May 27</span><span>Campuses</span><span>7 · 56 programs</span><span>Seats</span><span>Schedule 1: 2,950 at 7 campuses · Schedule 2: 2,950 at 7 campuses · Schedule 3: none yet</span><span>Staff</span><span>5 copied from SY 2027–2028</span></div>
<div class="alertbox ok">Everything needed for Schedule 1 is ready. Nothing is public yet: students can’t see SY 2028–2029 until you publish.</div>""", btn("Publish Schedule 1", "#open", "primary"))

ses = SLOTS2
srows = []
for i, (c, w, r, t, st) in enumerate(ses):
    cap = r * 50
    srows.append((f'<span class="ink">{c}</span>', w, f'<span class="num">{r}</span>',
                  f'<div class="meter"><div class="t"><span class="{"full" if t >= cap else ""}" style="width:{round(t / cap * 100)}%"></span></div><span class="num">{t:,} of {cap:,}</span></div>',
                  f'<span class="st{" bad" if st == "Full" else (" live" if st == "Open" else "")}">{st}</span>', rowact(None, "#slotmenu", ("Add rooms", "#addrooms") if st == "Full" else ("Seat plan", "../docs/seat-plan.html"))))
admin("exam-slots", "Exam slots", f"""{rounds_bar(2)}<div class="head"><span class="muted"></span>{btn("···", "#pagemenu")}{btn("Add exam slot", "#add", "primary")}</div>
<p class="guideline">8 exam slots · 4,150 seats · report by 7:30 AM, exam starts 8:00 AM</p>
{menu("pagemenu", [("Assign rooms and seats", "#auto", "", "For approved applicants without a slot"), ("Guide times", "#times", "", "Report and start time"), ("Check-in settings", "schedules.html#round", "", "Off for Schedule 2")])}
{list_page(stabs([("Both days", "8"), ("Sat, Apr 25", "5"), ("Sun, Apr 26", "3")]) + '', filters("Campus or room", [("Campus", ["Any campus", "ACCESS, Tacurong", "Isulan", "Tacurong", "Kalamansig", "Bagumbayan", "Palimbang", "Lutayan"])]),
table(["Campus", "Date", "Rooms", "Seats taken", "Status", ""], srows, sortable=("Campus", "Date", "Seats taken"), active=("Date", "asc")))}
{menu("slotmenu", [("Add rooms", "#addrooms", "", "More seats for this day"), ("Seat plan", "../docs/seat-plan.html", "", ""), ("Close this exam slot", "#toggle", "", "People keep their seats")])}""",
      overlays=modal("add", "info", "+", "Add an exam slot", f'<p class="muted" style="margin:0">Schedule 2 · registration open</p><div class="fld"><label for="a1">Campus</label><select id="a1"><option>Isulan</option><option>ACCESS, Tacurong</option><option>Tacurong</option><option>Kalamansig</option><option>Bagumbayan</option><option>Palimbang</option><option>Lutayan</option></select></div><div class="fld"><label for="a2">Exam day</label><select id="a2"><option>Sun, Apr 26</option><option>Sat, Apr 25 (Isulan already has a slot)</option></select>{hint('Only the exam days of Schedule 2. Add another day in Edit schedule.')}</div><div class="fld"><label>Rooms</label><div class="roomlist"><label class="chkrow roomrow"><input type="checkbox" checked> <b>All rooms</b><span class="muted num">235 seats</span></label><label class="chkrow roomrow"><input type="checkbox" checked> <span>Main Building · Room 1</span><span class="muted num">50 seats</span></label><label class="chkrow roomrow"><input type="checkbox" checked> <span>Main Building · Room 2</span><span class="muted num">50 seats</span></label><label class="chkrow roomrow"><input type="checkbox" checked> <span>Main Building · Room 4</span><span class="muted num">50 seats</span></label><label class="chkrow roomrow"><input type="checkbox" checked> <span>Engineering · ENG 201</span><span class="muted num">45 seats</span></label><label class="chkrow roomrow"><input type="checkbox"> <span>Engineering · ENG 202</span><span class="muted num">40 seats</span></label></div></div><p style="margin:0"><b>4 rooms · 195 seats</b> <span class="muted">· report by 7:30 AM (from the schedule)</span></p>', btn("Cancel", "#") + btn("Add exam slot", "#added", "primary"))
      + modal("add-err", "info", "+", "Add an exam slot", '<div class="fld"><label for="ae1">Campus</label><select id="ae1"><option>Isulan</option></select></div><div class="fld err"><label>Rooms</label><div class="roomlist"><label class="chkrow roomrow"><input type="checkbox"> <span>Main Building · Room 1</span><span class="muted num">50 seats</span></label></div><span class="errmsg">Pick at least 1 room.</span></div><div class="alertbox warn"><div>Isulan already has an exam slot on Sat, Apr 25. Edit that one instead.</div></div>', btn("Cancel", "#") + btn("Add exam slot", "#", "primary"))
      + modal("addrooms", "info", "+", "Add rooms · Isulan, Sat Apr 25", '<p class="muted" style="margin:0">Full: 200 of 200. 41 approved applicants from Isulan have no exam slot yet.</p><div class="fld"><label>Rooms not used on this day</label><div class="roomlist"><label class="chkrow roomrow"><input type="checkbox" checked> <span>Engineering · ENG 201</span><span class="muted num">45 seats</span></label><label class="chkrow roomrow"><input type="checkbox"> <span>Engineering · ENG 202</span><span class="muted num">40 seats</span></label></div></div><p style="margin:0"><b>+45 seats</b> <span class="muted">· a room missing? Add it on the Rooms page first.</span></p>', btn("Cancel", "#") + btn("Add rooms", "#roomsadded", "primary"))
      + toast("roomsadded", "ok", OK, "45 seats added", "Isulan, Sat Apr 25 is open again. The 41 waiting applicants were told by email and in the app.")
      + toast("added", "ok", OK, "Exam slot added", "Isulan · Sun, Apr 26 · 200 seats. 41 waiting applicants were emailed.")
      + modal("toggle", "warn", WARN, "Close Isulan, Sun Apr 26?", '<p class="muted" style="margin:0">162 people keep their seats. Nobody new can pick it.</p>', btn("Cancel", "#") + btn("Close exam slot", "#", "primary"))
      + modal("times", "info", "", "Guide times for Schedule 2", f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div class="fld"><label for="g1">Report by</label><input id="g1" type="time" value="07:30"></div><div class="fld"><label for="g2">Exam starts</label><input id="g2" type="time" value="08:00"></div></div>{hint("A guide only; nobody books a time. Changing it updates every permit and sends one text to everyone scheduled.")}', btn("Cancel", "#") + btn("Save and notify", "#", "primary"))
      + modal("auto", "info", "⇄", "Assign rooms and seats · Schedule 2", f'{hint("For approved applicants who haven’t picked an exam slot. Nobody who already picked is moved.")}<div class="fld"><label for="au1">Rule</label><select id="au1"><option>Campus of their 1st choice, earliest exam slot first</option><option>Nearest campus with room</option></select></div><div class="kv"><span>Applicants</span><span>627</span><span>Will get a seat</span><span>586</span><span>No room left</span><span>41 (Isulan) · add an exam slot first</span></div>', btn("Cancel", "#") + btn("Assign 586 applicants", "#assigned", "primary"))
      + toast("assigned", "ok", OK, "586 applicants assigned", "Each applicant got an email with their room and seat."),
      states=[("pagemenu", "Page ··· menu"), ("slotmenu", "Row ··· menu"), ("times", "Guide times"), ("add", "Add exam slot"), ("add-err", "Add exam slot, errors"), ("addrooms", "Full: add rooms"), ("roomsadded", "Rooms added"), ("added", "Added"), ("toggle", "Close exam slot confirm"), ("auto", "Assign rooms and seats"), ("assigned", "Assigned")])

rooms = [("ACCESS · Room 1", "J. Ampatuan", 47, 2, 1, B("ok", "Synced")), ("ACCESS · Room 2", "R. Sinsuat", 45, 3, 2, B("ok", "Synced")), ("ACCESS · Room 3", "M. Usman", 31, 0, 19, B("warn", "3 queued, offline")), ("Isulan · Room 4", "L. Cabañero", 48, 2, 0, B("ok", "Closed")), ("Tacurong · Room 2", "E. Mangelen", 0, 0, 50, B("bad", "Not seen for 40 min")), ("Kalamansig · Room 1", "A. Bagundang", 46, 4, 0, B("ok", "Synced"))]
CHECKIN_LIVE = f'''<div class="kpis"><div class="kpi"><span>Expected today</span><b>4,212</b></div><div class="kpi"><span>Here</span><b>3,904</b></div><div class="kpi"><span>Noted not here</span><b>121</b></div><div class="kpi"><span>Not scanned yet</span><b>187</b></div><div class="kpi"><span>Proctor phones</span><b>88 / 91 synced</b></div></div>
{table(["Room", "Proctor", "Here", "Not here", "Pending", "Phone", ""], [(f'<span class="ink">{r[0]}</span>', r[1], f'<span class="num">{r[2]}</span>', f'<span class="num">{r[3]}</span>', f'<span class="num">{r[4]}</span>', r[5], btn("Call proctor", "#call") if "Not seen" in r[5] else "") for r in rooms])}
<a href="../proctor/checkin.html">See the proctor’s phone screen →</a>'''
admin("checkin", "Check-in", f"""{rounds_bar(1)}<div class="panel" style="align-items:flex-start;gap:10px"><h2>Check-in is off</h2>
<p class="muted" style="margin:0">Absences come from the score import: anyone with an exam slot but no score is marked absent. Turn this on only if proctors will scan permits at the door.</p>
<div style="display:flex;gap:8px">{btn("Turn it on in Edit schedule", "schedules.html#round")}{btn("See the live monitor (when on)", "#live")}</div></div>""", active="schedules", crumb='<a href="schedules.html" class="muted">← Exam schedules</a>',
      overlays=modal("call", "warn", WARN, "Tacurong Room 2 hasn’t synced", '<div class="kv"><span>Proctor</span><span>E. Mangelen</span><span>Mobile</span><span>0918 555 0142</span><span>Last seen</span><span>7:21 AM</span></div>', btn("Close", "#") + btn("Assign another proctor", "#", "primary"))
      + inmain("live", '<h2>Live check-in · Sat, Mar 14</h2>' + CHECKIN_LIVE),
      states=[("live", "Check-in on: live monitor"), ("call", "Offline proctor dialog")])

SUBJECTS = ["english", "science", "math", "filipino", "social_studies", "esm", "overall"]
TEMPLATE_COLS = ["examinee_no", "name"] + [f"{x}_{k}" for x in SUBJECTS for k in ("ss", "stanine")]
SCORE_STEPS = [("Upload file", "The Testing Center Excel", "#uploading"), ("Match columns", "Checked once, remembered", "#map"), ("Check rows", "Problems listed, nothing saved", "#"), ("Approve", "Saved, still hidden", "#commit"), ("Publish", "On the Results page", "results.html")]
admin("scores", "Import scores", f"""{rounds_bar(1)}{rail(SCORE_STEPS, 3, f'''<div class="panel"><div class="head"><h2>SKSU TPT RESULT 2027.xlsx</h2><span class="muted" style="font-size:13px">Sheet “Result” · Apr 18, 3:40 PM</span></div>
<span class="hint">Upload the Testing Center’s Excel as it is. Scores are saved exactly as given. {btn("Download the Excel template", "../docs/tpt-scores-template.xlsx", "sm")}</span>
<div class="kpis"><div class="kpi"><span>Rows in file</span><b>9,104</b></div><div class="kpi"><span>Ready</span><b>9,088</b></div><div class="kpi"><span>Not registered</span><b class="neg">4</b></div><div class="kpi"><span>Duplicates or invalid</span><b class="neg">12</b></div><div class="kpi"><span>No score (absent)</span><b>635</b></div></div></div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>Needs a look · 16</h2>{btn("Download these rows", "#")}</div>
{table(["Row", "Examinee no.", "Problem", "What to do"], [("212", '<span class="mono">500912</span>', B("bad", "Not registered this schedule"), "Check the number with the Testing Center"), ("1,044", '<span class="mono">50O233</span>', B("bad", "Letter O instead of zero"), "Fix in the file and upload again"), ("2,871", '<span class="mono">500655</span>', B("bad", "Appears twice"), "Keep one row"), ("5,002", '<span class="mono">502460</span>', B("bad", "Overall 910 is above 800"), "Ask the Testing Center"), ("6,310", '<span class="mono">501990</span>', B("warn", "Stanine 9 but score 512"), "Ask the Testing Center"), ("—", '<span class="mono">501877</span>', B("warn", "Has a slot, no score in file"), "Marked absent on approve; if they took the exam, ask the Testing Center")])}</div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>What changes if you approve</h2></div>
{table(["", "Examinees", "Example"], [(B("ok", "New"), '<span class="mono">9,080</span>', "500214 · Overall 584 · stanine 7"), (B("warn", "Changed"), '<span class="mono">8</span>', "500176 · Overall 498 → 512"), (B("gray", "Unchanged"), '<span class="mono">0</span>', "—")])}</div>
<div class="panel"><h2>Files for this schedule</h2>{table(["File", "Uploaded", "By", "Status", ""], [("SKSU TPT RESULT 2027.xlsx", "Apr 18, 3:40 PM", "Testing Center", B("warn", "Checking"), ""), ("SKSU TPT RESULT 2027 draft.xlsx", "Apr 17, 10:12 AM", "Testing Center", B("gray", "Replaced"), btn("Download original"))])}</div>
<div class="formfoot" style="max-width:none">{btn("Upload a fixed file", "#uploading")}<span style="margin-left:auto" class="muted">The 16 rows stay out until fixed; the rest can be approved now.</span>{btn("Approve 9,088 scores", "#commit", "primary")}</div>''')}""",
      overlays=modal("uploading", "info", '<span class="spin"></span>', "Reading SKSU TPT RESULT 2027.xlsx… 41%", '<div class="progress"><span style="width:41%"></span></div><p class="muted" style="margin:0">3,732 of 9,104 rows checked.</p>', btn("Cancel", "#"))
      + modal("checking", "info", '<span class="spin"></span>', "Checking rows… 6,410 of 9,104", '<div class="progress"><span style="width:70%"></span></div><p class="muted" style="margin:0">Matching examinee numbers with who has an exam slot. 12 problems so far.</p>', btn("Run in background", "#bg", "primary"))
      + toast("bg", "info", INFO, "Import runs in the background", "You can leave this page. We’ll notify you when it’s done (bell, top right).")
      + modal("summary", "info", "", "Import finished", '<div class="kpis"><div class="kpi"><span>Ready to approve</span><b>9,088</b></div><div class="kpi"><span>Skipped</span><b>0</b></div><div class="kpi"><span>Problems</span><b class="neg">16</b></div></div>' + hint("Took 38 seconds. Nothing is visible to students yet."), btn("Download problem rows") + btn("Review and approve", "#", "primary"))
      + modal("map", "info", "", "Match the columns", '<div class="fld"><label for="sh">Sheet</label><select id="sh"><option>Result (picked: has the examinee numbers)</option><option>Sheet1</option><option>Sheet2</option><option>Sheet3</option><option>Sheet5</option></select></div><p class="muted" style="margin:0">Two header rows found (subject, then score type), so they are read together. Guessed from the headers. Fix any that are wrong; it is remembered for next year.</p>' + table(["In the file", "Means"], [("Examinee Number", "<select><option>Examinee no.</option></select>"), ("Name of Examinee", "<select><option>Name (only to double-check)</option></select>"), ("English · Standard Score", "<select><option>English · standard score</option></select>"), ("English · Stanine", "<select><option>English · stanine</option></select>"), ("Qualitative Interpretation", "<select><option>Ignore (worked out from stanine)</option></select>"), ("Preferred Program", "<select><option>Ignore (already on the application)</option></select>"), ("Columns 32–33 · no header", "<select><option>Ignore (a second list beside the table)</option></select>")]), btn("Cancel", "#") + btn("Use these columns", "#", "primary"))
      + modal("missing", "bad", BAD, "No examinee number column found", '<p class="muted" style="margin:0">Nothing was saved. Every score needs an examinee number to find its student. Pick the column in Match columns, or ask the Testing Center for a file that has it.</p>', btn("Download the Excel template", "../docs/tpt-scores-template.xlsx") + btn("Match columns", "#map", "primary"))
      + modal("commit", "warn", WARN, "Approve 9,088 scores?", '<p class="muted" style="margin:0">They are saved exactly as in the file. Students cannot see them until you publish. The file and your approval go in the activity log.</p>', btn("Cancel", "#") + btn("Approve", "results.html#committed", "primary")),
      states=[("rail-min", "Steps hidden"), ("uploading", "Uploading"), ("checking", "Checking rows"), ("bg", "Running in background"), ("summary", "Import summary"), ("map", "Match columns"), ("missing", "Required column missing"), ("commit", "Approve confirm")])

RESULTS_BAR = ('<div class="setrow"><span style="display:flex;gap:10px;align-items:center"><span class="st">Not released</span><label for="rel">Release on</label><input id="rel" type="datetime-local" value="2027-04-20T09:00"></span>'
               '<span style="display:flex;gap:8px">' + btn("Save date", "#date-ok") + btn("Publish now", "#release", "primary") + '</span></div>')
admin("results", "Results", f"""{rounds_bar(1)}<div class="kpis"><div class="kpi"><span>Scored</span><b>9,088</b></div><div class="kpi"><span>Absent</span><b>635</b></div></div>
{RESULTS_BAR}
{list_page(stabs([("All scored", "9,088"), ("Qualified for 1st choice", "6,214"), ("Not qualified", "2,874"), ("Absent", "635")]), filters("Name or examinee no.", [("Campus", ["Any campus", "Isulan", "ACCESS, Tacurong"]), ("Program", ["Any program (type to search)", "BS Civil Engineering", "BS Nursing"])], more=True, right=btn("Export (Excel)", "exports.html#queued"), showing="Showing <b>412</b> · Qualified for 1st choice · BS Civil Engineering"),
table(["Examinee", "1st choice", "Overall standard score", "Stanine", ""], [(two(f'<span class="ink">{nm}</span>', no), two(pr, cp), f'<span class="num">{sc}</span>', stn, rowact("result-detail.html", "")) for no, nm, pr, cp, sc, stn in [
    ("500214", "Maria S. Dela Cruz", "BS Civil Engineering", "Isulan", "584", "7"), ("500176", "Datu R. Mamalinta", "BS Fisheries", "Palimbang", "512", "6"),
    ("500198", "Princess A. Lumabao", "BS Accountancy", "ACCESS, Tacurong", "661", "9"), ("500231", "Abdul R. Kanakan", "BS Information Technology", "ACCESS, Tacurong", "—", "Absent")]],
    sortable=("Examinee", "Overall standard score"), active=("Overall standard score", "desc")),
pager(1, 25, "9,088"))}""",
      overlays=inmain("none", empty("list", "No scores for Schedule 2 yet", "Import the Testing Center Excel after exam day.", btn("Import scores", "scores.html", "primary")))
      + toast("committed", "ok", OK, "9,088 scores approved", "Release is set for Apr 20, 9:00 AM.")
      + toast("date-ok", "ok", OK, "Release date saved", "Results go out by themselves on Apr 20, 9:00 AM.")
      + inmain("live", '<div class="setrow"><span style="display:flex;gap:10px;align-items:center"><span class="st live">Published</span>Released Apr 20, 9:00 AM · 9,088 examinees can see their scores</span>' + btn("Hide results", "#hide") + '</div>')
      + modal("release", "warn", WARN, "Publish results to 9,088 examinees now?", '<p class="muted" style="margin:0">They get an email and a text and can see scores at once. You can hide the results again here, but sent emails and texts stay sent.</p>', btn("Cancel", "#") + btn("Publish now", "#releasing", "primary"))
      + modal("hide", "warn", WARN, "Hide Schedule 1 results?", '<p class="muted" style="margin:0">Students stop seeing scores in the app, and the verify page says “not available”. Emails and texts already sent can’t be unsent.</p>', btn("Cancel", "#") + btn("Hide results", "#hidden", "danger"))
      + toast("hidden", "ok", OK, "Results hidden", "Publish them again from this page when ready.")
      + modal("releasing", "info", '<span class="spin"></span>', "Sending 9,088 emails… 2,310 sent", '<div class="progress"><span style="width:25%"></span></div><p class="muted" style="margin:0">Safe to close. This keeps going in the background.</p>', btn("Close", "#released"))
      + toast("released", "ok", OK, "Results released", "Emails and texts are going out. See the delivery report.")
      + modal("report", "info", "", "Results released · delivery", '<div class="kpis"><div class="kpi"><span>In app</span><b>9,088</b></div><div class="kpi"><span>Email delivered</span><b>9,051</b></div><div class="kpi"><span>Text delivered</span><b>8,967</b></div></div><div class="kv"><span>Email bounced</span><span>37 · mailbox full or wrong address</span><span>Text failed</span><span>121 · number not in service</span></div>' + hint("Failed ones can be fixed and resent from Messages."), btn("Open send log", "email.html") + btn("Done", "#", "primary")),
      states=[("live", "Published"), ("date-ok", "Date saved"), ("none", "Empty: no scores yet"), ("report", "Delivery report"), ("committed", "After approve"), ("release", "Publish confirm"), ("hide", "Hide results"), ("hidden", "Hidden"), ("releasing", "Sending progress"), ("released", "Released")])

admin("result-detail", "Result · 500214 Maria S. Dela Cruz", table(["Subject", "Raw", "Standard score", "Stanine"], [(n, '<span class="mono">' + str(r) + "</span>", f'<span class="mono">{s}</span>', t) for (n, s, t), r in zip(subj, [44, 29, 28, 43, 29, 26])]) + f'<div style="display:flex;gap:8px">{btn("Result PDF", "../docs/result-pdf.html")}{btn("Correct a score", "#fix")}</div>',
      active="results", crumb='<a href="results.html" class="muted">← Results</a>',
      overlays=modal("fix", "warn", WARN, "Correct a score", '<div class="fld"><label for="f1">Science raw</label><input id="f1" value="31"></div><div class="fld"><label for="f2">Reason</label><input id="f2" value="Answer sheet re-checked by testing center"></div><p class="muted" style="margin:0">The standard score is recomputed. Old and new values stay in the history.</p>', btn("Cancel", "#") + btn("Save", "#", "primary")),
      states=[("fix", "Correction dialog")])

EVENTS = [("Account created", "✓", "", "", "Welcome"), ("Application submitted", "✓", "✓", "", "Next: pay at a cashier, with the code"), ("Sent back with remarks", "✓", "✓", "✓", "What to fix, then send again"),
          ("Payment recorded at the cashier", "✓", "✓", "✓", "OR no., examinee no., pick an exam slot"), ("Exam slot booked · permit ready", "✓", "✓", "✓", "Date, report time, room, seat, permit link"),
          ("Exam slot changed", "✓", "✓", "✓", "New date, report time, room and seat"), ("Exam reminder (day before, 5 PM)", "✓", "✓", "✓", "Report time, room, what to bring"), ("Marked absent", "✓", "✓", "", "Move to next schedule"),
          ("Results released", "✓", "✓", "✓", "Link to result"), ("Receipt received · approved (online payment only)", "✓", "✓", "", "Only when online payment is turned on")]
admin("messages", "Announcements", f"""<div class="row"><div class="panel" style="max-width:560px;flex:1"><h2>Send an announcement</h2>
<div class="fld"><label for="m1">To</label><select id="m1"><option>Schedule 2 · approved, no exam slot (627)</option><option>Schedule 1 · absent (121)</option></select></div>
<div class="fld"><label for="m2">Template</label><select id="m2"><option>Pick your exam slot</option></select></div>
<div class="preview">Hi {{{{first_name}}}}, your payment is approved but you haven’t picked an exam slot yet. Pick one before Apr 11: sksu-tpt.com/slot</div>
<div class="fld"><label for="m3">Send</label><select id="m3"><option>Now</option><option>Schedule…</option></select>{hint("627 emails + 627 texts. Texts cost about ₱313.")}</div>
{btn("Send to 627", "#confirm", "primary lg")}</div></div>""",
      overlays=modal("confirm", "warn", WARN, "Send to 627 applicants now?", '<p class="muted" style="margin:0">Messages can’t be recalled once sent.</p>', btn("Cancel", "#") + btn("Send now", "#sending", "primary"))
      + modal("sending", "info", '<span class="spin"></span>', "Sending… 212 of 627", '<div class="progress"><span style="width:34%"></span></div>', btn("Run in background", "#sent"))
      + toast("sent", "ok", OK, "Blast sent", "627 emails, 627 texts. 3 numbers bounced; see Recent.")
      + BELL_POP,
      states=[("q-open", "Bell dropdown"), ("confirm", "Send confirm"), ("sending", "Sending"), ("sent", "Sent")])

TICKETS = [("#1046", "Rhea L. Sumagka", "Change my details", "Isulan", "Open", "12 min ago", "—"),
           ("#1045", "Jomar P. Abdullah", "Exam slot", "ACCESS, Tacurong", "Open", "1 h ago", "Ana R."),
           ("#1044", "Farida M. Ampatuan", "Payment", "Tacurong", "Open", "3 h ago", "—"),
           ("#1042", "Maria S. Dela Cruz", "Payment", "Isulan", "Answered", "Jan 12", "Ana R."),
           ("#0977", "Maria S. Dela Cruz", "Application", "Isulan", "Closed", "Jan 5", "Ben T.")]
admin("support", "Support", f"""{list_page(stabs([("Open", "3"), ("Answered", "41"), ("Closed", "812"), ("All", "856")]), filters("Request no. (#1046), name or examinee no.", [("Topic", ["Any topic", "Payment", "Application", "Change my details", "Exam slot", "Result", "Privacy request", "Other"]), ("Assigned", ["Anyone", "Assigned to me"])], showing="Showing <b>2</b> · Open · Change my details"),
table(["No.", "Student", "Topic", "Campus", "Status", "Last update", "Assigned", ""], [(f'<span class="mono">{n}</span>', st, t, c, f'<span class="st{" live" if s_ == "Open" else ""}">{s_}</span>', u, a, rowact("support-ticket.html", "", ("Reply", "support-ticket.html") if s_ == "Open" else None)) for n, st, t, c, s_, u, a in TICKETS], sortable=("No.", "Last update"), active=("Last update", "asc")),
pager(1, 5, 856), count="856 requests this school year")}
<div class="setrow"><span>Limits: 1 open request per student, 5 per school year, 1 reply a minute</span>{btn("Edit limits", "#limits", "sm")}</div>""",
      overlays=modal("limits", "info", "✎", "Support limits", '<div class="formgrid"><div class="fld"><label for="l1">Requests per student per school year</label><input id="l1" type="number" min="1" value="5"></div><div class="fld"><label for="l2">Open requests at a time</label><input id="l2" type="number" min="1" value="1" disabled></div><div class="fld"><label for="l3">Replies per request per day</label><input id="l3" type="number" min="1" value="20"></div><div class="fld"><label for="l4">Close after no reply (days)</label><input id="l4" type="number" min="1" value="7"></div></div>' + hint("Also fixed: one reply a minute, 10–1,000 characters, one photo up to 2 MB (JPG or PNG), links shown as plain text."), btn("Cancel", "#") + btn("Save", "#limits-ok", "primary"))
      + toast("limits-ok", "ok", OK, "Saved", "The new limits apply from now on. The change is in the activity log.")
      + BELL_POP,
      states=[("limits", "Support limits"), ("limits-ok", "Limits saved")])

admin("support-ticket", "#1046 · Change my details", f"""<div class="row"><div class="grow" style="display:flex;flex-direction:column;gap:16px;min-width:0">
<div class="thread"><div class="msg"><p>My birth date is wrong. It should be March 3, 2008, not March 8.</p><small>Rhea L. Sumagka · 12 min ago</small></div></div>
<div class="fld"><label for="ar">Reply (goes to her app and email)</label><textarea id="ar" rows="4" style="border:1px solid var(--line);border-radius:6px;padding:10px;font:14px var(--sans)">We corrected your birth date to March 3, 2008. Your permit shows the new date.</textarea></div>
<div style="display:flex;gap:8px;flex-wrap:wrap">{btn("Change details", "#change")}{btn("···", "#tmenu")}<span style="margin-left:auto"></span>{btn("Send reply", "#replied", "primary")}</div>
{menu("tmenu", [("Assign to me", "#", "", ""), ("Close as duplicate", "#dup", "", "Links it to #1031"), ("Close", "#closed", "", ""), ("-", "", "", ""), ("Pause support for this student", "#mute", "danger", "7 days, with a reason")])}</div>
<div style="width:340px;flex-shrink:0"><h2 style="font-size:15px;margin:0 0 8px">Rhea L. Sumagka</h2><div class="kv"><span>Status</span><span>Exam slot picked</span><span>Examinee no.</span><span class="mono">500233</span><span>Birth date</span><span>Mar 8, 2008</span><span>Campus</span><span>Isulan · Sat, Apr 25</span><span>Requests</span><span>2 of 5 this school year</span></div><a href="applicant.html">Open full record →</a></div></div>""",
      active="support", crumb='<a href="support.html" class="muted">← Support</a>',
      overlays=modal("change", "info", "✎", "Change details", '<p class="muted" style="margin:0">Requested by the student · request #1046</p><div class="fld"><label for="cb">Birth date</label><input id="cb" type="date" value="2008-03-03"></div><div class="fld"><label for="cr">Reason (goes in the history)</label><input id="cr" value="Student request #1046; matches PSA birth certificate"></div>', btn("Cancel", "#") + btn("Save", "#changed", "primary"))
      + toast("changed", "ok", OK, "Details changed", "In her history and the activity log, linked to #1046.")
      + toast("replied", "ok", OK, "Reply sent", "Rhea sees it in her app and by email. Status: Answered.")
      + modal("dup", "info", "", "Close as duplicate?", '<div class="fld"><label for="dd">Same as request</label><input id="dd" value="#1031"></div>', btn("Cancel", "#") + btn("Close as duplicate", "#closed", "primary"))
      + toast("closed", "ok", OK, "Request closed", "The student can open a new request.")
      + modal("mute", "warn", WARN, "Pause support for Rhea?", '<div class="fld"><label for="mr">Reason (logged, shown to the student)</label><input id="mr" value="Repeated messages with links"></div><p class="muted" style="margin:0">For 7 days she can’t open requests or reply. She is told to visit or call the office.</p>', btn("Cancel", "#") + btn("Pause for 7 days", "#muted", "danger"))
      + toast("muted", "ok", OK, "Support paused until Jan 19", "The reason is in the activity log.")
      + BELL_POP,
      states=[("change", "Change details (requested)"), ("changed", "Changed"), ("replied", "Reply sent"), ("dup", "Close as duplicate"), ("closed", "Closed"), ("mute", "Pause support"), ("muted", "Paused")])

admin("email", "Email and SMS", f"""{ptabs([("sender", "Sender"), ("auto", "Automatic messages"), ("templates", "Templates"), ("log", "Send log")])}
<section class="pane" id="pane-sender"><div class="panel"><div class="head"><h2>Official email</h2>{btn("Edit", "#mail", "sm")}</div><div class="kv">
<span>Sends from</span><span class="ink">SKSU Admission Office &lt;admission@sksu.edu.ph&gt; {B("ok", "Verified")}</span>
<span>Replies go to</span><span>admission@sksu.edu.ph</span>
<span>Footer</span><span class="muted">Sultan Kudarat State University · Admission Office · (064) 201-0000</span></div>
</div></section>
<section class="pane" id="auto"><div class="panel"><div class="head"><h2>Automatic notifications to students</h2></div>
{table(["Event", "In app", "Email", "Text", "Says", ""], [(f'<span class="ink">{e}</span>', i, m, t, f'<span class="muted">{w}</span>', btn("Edit", "#tpl")) for e, i, m, t, w in EVENTS])}
<a href="../docs/sms.html">See every text message →</a></div></section>
<section class="pane" id="templates"><div class="panel"><div class="head"><h2>Templates</h2>{btn("New template", "#tpl")}</div>
{table(["Template", "Sent when", "Channel", ""], [("Payment approved", "The admin approves, or a cashier records a payment", "Email", btn("Edit", "#tpl")), ("Sent back", "The admin sends it back, with remarks", "Email + SMS", btn("Edit", "#tpl")), ("Pick your exam slot", "Reminder, sent by you", "Email + SMS", btn("Edit", "#tpl")), ("Exam tomorrow", "Day before exam, 5:00 PM", "SMS", btn("Edit", "#tpl")), ("Results are out", "On release", "Email", btn("Edit", "#tpl"))])}</div>
</section>
<section class="pane" id="log"><div class="panel"><div class="head"><h2>Send log</h2><span class="seg"><span class="on">All</span><span>Failed · 4</span></span></div>{table(["When", "Student", "Message", "Channel", "Status", ""], [
    ('<span class="mono muted">9:05 AM</span>', "Jomar P. Abdullah", "Payment approved", "Email + text", B("ok", "Delivered"), ""),
    ('<span class="mono muted">8:00 AM</span>', "Rhea L. Sumagka", "Pick your exam slot (blast)", "Text", B("bad", "Failed · number not in service"), btn("Fix number and resend", "#resend")),
    ('<span class="mono muted">8:00 AM</span>', "Kevin D. Alonto", "Pick your exam slot (blast)", "Email", B("warn", "Bounced · mailbox full"), btn("Resend", "#resend")),
    ('<span class="mono muted">Yesterday</span>', "Maria S. Dela Cruz", "Exam slot booked", "Email + text", B("ok", "Delivered"), "")])}</div></section>""",
      overlays=modal("mail", "info", "✎", "Official email", '<div class="fld"><label for="mf1">Sender name</label><input id="mf1" value="SKSU Admission Office"></div><div class="fld"><label for="mf2">Sends from</label><input id="mf2" type="email" value="admission@sksu.edu.ph"></div><div class="fld"><label for="mf3">Replies go to</label><input id="mf3" type="email" value="admission@sksu.edu.ph"></div><div class="fld"><label for="mf4">Footer</label><input id="mf4" value="Sultan Kudarat State University · Admission Office · (064) 201-0000"></div>' + hint("A new address must be verified first: we send it a link. Until then, emails keep the old sender."), btn("Send a test email", "#mail-test") + btn("Cancel", "#") + btn("Save", "#mail-ok", "primary"))
      + toast("mail-test", "info", INFO, "Test email sent", "Check admission@sksu.edu.ph. It should arrive within a minute.")
      + toast("mail-ok", "ok", OK, "Saved", "New emails use this sender. The change is in the activity log.")
      + modal("tpl", "info", "✎", "Edit template · Pick your exam slot", f'<div class="fld"><label for="t1">Subject</label><input id="t1" value="Pick your exam slot"></div><div class="fld"><label for="t2">Message</label><textarea id="t2" rows="4" style="border:1px solid var(--line);border-radius:6px;padding:10px;font:14px var(--sans)">Hi {{{{first_name}}}}, your payment is approved…</textarea>{hint("Fields: {{{{first_name}}}}, {{{{examinee_no}}}}, {{{{exam slot}}}}, {{{{seat}}}}. SMS is cut at 160 characters.")}</div>', btn("Cancel", "#") + btn("Save", "#", "primary"))
      + modal("resend", "info", "", "Resend to Rhea L. Sumagka", '<div class="fld"><label for="rn">Mobile number</label><input id="rn" value="0917 555 0199"></div>' + hint("The number on her account is updated too."), btn("Cancel", "#") + btn("Resend", "#resent", "primary"))
      + toast("resent", "ok", OK, "Resent", "Delivered to 0917 555 0199."),
      states=[("auto", "Automatic messages tab"), ("templates", "Templates tab"), ("log", "Send log tab"), ("mail", "Official email"), ("mail-test", "Test email"), ("mail-ok", "Email saved"), ("tpl", "Edit template"), ("resend", "Resend a failed one"), ("resent", "Resent")])

admin("system", "System status", f"""<div class="kpis">
<div class="kpi"><span>Website</span><b>Working</b><small>Answering in 0.2 s</small></div>
<div class="kpi"><span>People online now</span><b>1,240</b><small>Can handle about 10,000</small></div>
<div class="kpi"><span>Emails today</span><b>1,420</b><small>of 2,000 a day</small></div>
<div class="kpi"><span>SMS credits left</span><b>18,600</b><small>About 30 days at this rate</small></div></div>
<div class="panel"><div class="head"><h2>Server</h2></div>{table(["", "Now", "Limit", ""], [("Processor", "34%", "100%", B("ok", "OK")), ("Memory", "5.1 GB", "8 GB", B("ok", "OK")), ("Storage (uploads)", "41 GB", "160 GB", B("ok", "OK")), ("Jobs waiting (emails, imports)", "12", "—", B("ok", "OK"))])}</div>
<div class="panel" id="maint"><div class="head"><h2>Maintenance</h2><span class="muted">Super admin only · every pause and resume goes in the activity log</span></div>
<div class="setrow"><span><b>Pause the student app</b><small>Students and the landing page see a maintenance screen. Staff can still sign in.</small></span><a class="switch" href="#pause-app" aria-label="Pause the student app"></a></div>
<div class="setrow"><span><b>Pause new applications</b><small>People who already applied can still pay, pick a slot and see results.</small></span><a class="switch" href="#pause-apps" aria-label="Pause new applications"></a></div>
<div class="setrow"><span><b>Pause cashier payments</b><small>Paused by Ana R. at 9:40 AM · cashiers see a notice</small></span><a class="switch on" href="#pause-one" aria-label="Pause cashier payments"></a></div>
<div class="setrow"><span><b>Hide results</b><small>Students stop seeing their results until you publish again. Controlled on the Results page.</small></span>{btn("Open Results", "results.html", "sm")}</div>
<div class="setrow"><span><b>Schedule maintenance</b><small>Sat, Apr 18 · 10:00 PM – 11:30 PM · students see a notice on Home from Apr 16.</small></span>{btn("Change", "#maint-plan", "sm")}</div></div>
<div class="setrow"><span>Data retention: applications older than [RETENTION PERIOD] are deleted or made anonymous. Next clean-up: Jul 1, 2027.</span>{btn("Privacy notice", "../public/privacy.html", "sm")}</div>
<div class="panel"><div class="head"><h2>Backups</h2></div>{table(["When", "What", "Size", ""], [("Today 2:00 AM", "Database and uploads", "6.2 GB", B("ok", "Done")), ("Yesterday 2:00 AM", "Database and uploads", "6.1 GB", B("ok", "Done"))])}</div>""",
      overlays=BELL_POP
      + modal("pause-app", "warn", WARN, "Pause the student app?", '<div class="fld"><label for="pm">Message students see</label><input id="pm" value="SKSU TPT is under maintenance. Your application is saved."></div><div class="fld"><label for="pb">Back by (optional)</label><input id="pb" type="time" value="15:00"></div><div class="fld"><label for="pr">Reason (only staff see it)</label><input id="pr" value="Fixing slow exam slot booking"></div>' + '<div class="kv"><span>Stops</span><span>Students and the landing page see the maintenance screen.</span><span>Still works</span><span>Staff sign in and work as usual. Permits saved on phones still open offline. Nothing typed or saved is lost.</span></div>', btn("Cancel", "#") + btn("Pause the student app", "#paused", "danger"))
      + modal("pause-one", "warn", WARN, "Pause cashier payments?", '<div class="fld"><label for="po">Reason (only staff see it)</label><input id="po" value="OR booklet mix-up at Isulan; checking the numbers"></div>' + '<div class="kv"><span>Stops</span><span>The counter can’t record payments. Cashiers see “Payments paused by Ana R. at 2:10 PM”.</span><span>Still works</span><span>Students can apply, see their code and wait. Payments already recorded stay.</span></div>', btn("Cancel", "#") + btn("Pause", "#", "danger"))
      + modal("pause-apps", "warn", WARN, "Pause new applications?", '<div class="fld"><label for="pa">Reason (only staff see it)</label><input id="pa" value="Exam slots full at every campus"></div><div class="kv"><span>Stops</span><span>Nobody can start or submit an application.</span><span>Still works</span><span>Applicants see their status, permit and results; cashiers can record payments.</span></div>', btn("Cancel", "#") + btn("Pause", "#", "danger"))
      + modal("maint-plan", "info", "", "Schedule maintenance", '<div class="formgrid"><div class="fld"><label for="md">Date</label><input id="md" type="date" value="2027-04-18"></div><div class="fld"><label for="mt">From – to</label><span class="range"><input type="time" value="22:00"> – <input type="time" value="23:30"></span></div></div><div class="fld"><label for="mm">Notice on the student Home</label><input id="mm" value="SKSU TPT will be down Sat, Apr 18, 10:00–11:30 PM for maintenance."></div><div class="fld"><label for="mf">Show the notice from</label><input id="mf" type="date" value="2027-04-16"></div>', btn("Cancel", "#") + btn("Save", "#", "primary"))
      + '<div class="pausedline" id="paused">Student app paused by Ana R. at 1:12 PM · back by 3:00 PM <a href="#">Resume</a></div>',
      states=[("pause-app", "Confirm pause"), ("paused", "Paused banner"), ("pause-apps", "Pause new applications"), ("pause-one", "Pause cashier payments"), ("maint-plan", "Schedule maintenance")])

reps = [("Registrations by day", "Sign-ups and submissions per day, by campus"), ("Applicant list", "Every field, filterable, for the registrar"), ("Program demand", "1st, 2nd and 3rd choices per campus and program"), ("Payments", "Approved, rejected and waiting, with reviewer and time"), ("Seat plan per room", "Printable list for proctors, by exam slot and room"), ("Attendance", "Scored and absent per exam slot, from the score import"), ("Score distribution", "Standard scores and stanines per subject"), ("Ranking per program", "Examinees ranked within each program choice"), ("Qualified students", "Who meets each program cut-off"), ("Survey answers", "The 10 exam statements: counts per answer, comments; Excel in the office format"), ("Applicants by home town", "Province and municipality or city, by schedule and campus")]
admin("reports", "Reports", f"""<div class="row"><div class="panel grow"><div class="head"><h2>Where applicants drop off · Schedule 1</h2></div>
{funnel([("Signed up", 16408), ("Submitted", 12287), ("Paid and approved", 9471), ("Picked an exam slot", 8844), ("Took the exam", 8990 - 146), ("Scored", 8844 - 6)])}</div>
<div class="panel grow"><div class="head"><h2>Most wanted programs · 1st choice</h2><a href="report-view.html" style="font-size:13px">All 56 →</a></div>
{hbars([(n, c, v) for n, c, v in prog])}</div></div>
<div class="panel"><div class="head"><h2>Overall score distribution · Schedule 1</h2><span class="muted" style="font-size:13px">9,088 examinees · each bar is 50 points, one stanine band</span></div>{histogram()}</div>
""" + table(["Report", "What it shows", ""], [(f'<span class="ink">{r[0]}</span>', r[1], f'<span class="act">{btn("View", {"Survey answers": "survey-results.html", "Applicants by home town": "report-hometown.html"}.get(r[0], "report-view.html"))} {btn("Excel", "exports.html#queued")}</span>') for r in reps]))

HOMETOWNS = [('Isulan', 1260), ('Tacurong City', 1105), ('Lambayong', 512), ('Esperanza', 430), ('President Quirino', 388), ('Bagumbayan', 341), ('Kalamansig', 296), ('Lebak', 270), ('Columbio', 155), ('Lutayan', 142)]
admin("report-hometown", "Applicants by home town", f"""<div class="head"><span class="muted">SY 2027–2028 · Schedule 2 · 4,980 applicants</span>{btn("Export (Excel)", "exports.html#queued")}</div>
{list_page(filters("Municipality or city", [("Schedule", ["Schedule 2", "Schedule 1", "All schedules"]), ("Campus", ["Any campus", "Isulan", "ACCESS, Tacurong"])], extra='<select aria-label="Province"><option>Sultan Kudarat</option><option>Cotabato</option><option>South Cotabato</option><option>Maguindanao del Sur</option><option>All provinces</option></select>'),
hbars([(t, "", n) for t, n in HOMETOWNS]),
table(["Municipality or city", "Province", "Applicants", "Share"], [(t, "Sultan Kudarat", f'<span class="num">{n:,}</span>', f'<span class="num">{n / 4980:.0%}</span>') for t, n in HOMETOWNS], sortable=("Municipality or city", "Applicants"), active=("Applicants", "desc")),
pager(1, 10, "24 municipalities and cities"))}""", active="reports", crumb='<a href="reports.html" class="muted">← Reports</a>')

admin("report-view", "Ranking per program", f"""<div class="filters"><select><option>BS Civil Engineering · Isulan</option></select><select><option>1st choice only</option></select><span style="margin-left:auto;display:flex;gap:6px">{btn("Print")}{btn("Excel", "exports.html#queued")}</span></div>
{table(["Rank", "Examinee no.", "Name", "Overall standard score", "Stanine", "Qualified"], [("1", '<span class="mono">500891</span>', "Rhea L. Sumagka", '<span class="mono">742</span>', "9", B("ok", "Yes")), ("2", '<span class="mono">500433</span>', "Kevin D. Alonto", '<span class="mono">701</span>', "9", B("ok", "Yes")), ("41", '<span class="mono">500214</span>', "Maria S. Dela Cruz", '<span class="mono">584</span>', "7", B("ok", "Yes")), ("180", '<span class="mono">501120</span>', "Joel P. Kamid", '<span class="mono">402</span>', "3", B("gray", "No"))])}""",
      active="reports", crumb='<a href="reports.html" class="muted">← Reports</a>')

SURVEY_ROWS = [f'<tr><td class="drag" aria-label="Drag to reorder">⋮⋮</td><td class="mono muted">{i}</td><td class="ink">{q}</td><td><a class="switch on" href="#" aria-label="Question {i} on"></a></td><td>{btn("Edit", "#q-edit")}</td></tr>'
               for i, q in enumerate(SURVEY_QS, 1)]
SURVEY_ROWS.append('<tr><td></td><td class="mono muted">—</td><td class="ink">Comments and suggestions <span class="muted">(optional, free text)</span></td><td><a class="switch on" href="#" aria-label="Comments on"></a></td><td></td></tr>')
admin("survey", "Survey", f"""<div class="head"><span class="muted"></span>{btn("Results", "survey-results.html")}{btn("Add question", "#q-add", "primary")}</div>
<div class="sline"><label class="fdd"><small>School year</small><select aria-label="School year"><option>SY 2027–2028 · version 1</option><option>SY 2026–2027</option></select></label><span class="muted">1,204 answers so far · defaults from tptv3</span></div>
<div class="setrow"><span>Required before choosing a program</span><a class="switch on" href="#" aria-label="Required before choosing a program"></a></div>
<div class="setrow"><span>Answer scale</span><span class="muted">{" · ".join(SURVEY_SCALE)}</span></div>
{table(["", "No.", "Statement", "On", ""], SURVEY_ROWS)}
<small class="muted">Changing questions applies to new answers only; answers already given keep the question they answered.</small>""",
      overlays=modal("q-edit", "info", "✎", "Edit statement 3", '<div class="fld"><label for="qe">Statement</label><textarea id="qe" rows="3">The signages in the testing site are visible and easy to follow.</textarea></div><div class="setrow"><span>Shown to students</span><a class="switch on" href="#" aria-label="Shown"></a></div>', btn("Cancel", "#") + btn("Save", "#q-locked", "primary"))
      + modal("q-add", "info", "+", "Add a statement", '<div class="fld"><label for="qa">Statement</label><textarea id="qa" rows="3">The permit and exam-day instructions were clear.</textarea></div><small class="muted">It uses the same five-point scale and goes at the end. Drag it to move it.</small>', btn("Cancel", "#") + btn("Add", "#q-locked", "primary"))
      + modal("q-locked", "warn", WARN, "1,204 students already answered this school year", '<p class="muted" style="margin:0">Saving starts version 2. Students who answer from now on see the new questions; the 1,204 answers keep version 1, and results show each version separately.</p>', btn("Cancel", "#") + btn("Save as version 2", "#q-saved", "primary"))
      + toast("q-saved", "ok", OK, "Saved as version 2", "New answers use it. The change is in the activity log.") + BELL_POP,
      states=[("q-edit", "Edit statement"), ("q-add", "Add statement"), ("q-locked", "Questions locked"), ("q-saved", "Saved")])


def likert_bar(counts):
    """Agree to disagree as one thin bar: two greens, grey for neutral, two reds."""
    total = sum(counts)
    return '<span class="lk">' + "".join(f'<i class="k{j}" style="width:{c / total * 100:.1f}%" title="{SURVEY_SCALE[j]}: {c:,}"></i>' for j, c in enumerate(counts)) + "</span>"


def likert_avg(counts):
    avg = sum((j + 1) * c for j, c in enumerate(counts)) / sum(counts)
    return f"{avg:.2f} · {SURVEY_SCALE[round(avg) - 1]}"


admin("survey-results", "Survey results", f"""<div class="head"><span class="muted"></span>{btn("Excel (office format)", "exports.html#queued", "primary")}</div>
{filters("Words in comments", [("Schedule", ["All schedules", "Schedule 1", "Schedule 2"]), ("Campus", ["Any campus", "Isulan", "ACCESS, Tacurong"])], more=True)}
<div class="kpis"><div class="kpi"><span>Answers</span><b>1,204</b><small>of 1,298 with a result</small></div><div class="kpi"><span>With a comment</span><b>213</b></div></div>
<div class="lklegend">""" + "".join(f'<span><i class="k{j}"></i>{o}</span>' for j, o in enumerate(SURVEY_SCALE)) + f"""</div>
{table(["No.", "Statement", "Answers", "SA", "A", "N", "D", "SD", "Average (1 = Strongly Agree)"], [(f'<span class="mono muted">{i}</span>', f'<span class="ink">{q}</span>', likert_bar(c), *[f"{v:,}" for v in c], likert_avg(c)) for i, (q, c) in enumerate(zip(SURVEY_QS, SURVEY_COUNTS), 1)])}
<small class="muted">The Excel has one row per statement with the count for each answer, the format the office submits.</small>
<h2 style="margin:8px 0 0;font-size:16px">Comments</h2>
{table(["When", "Campus", "Comment"], [('<span class="muted">Mar 14</span>', "Isulan", "The room was hot in the afternoon; please open the windows."), ('<span class="muted">Mar 14</span>', "ACCESS, Tacurong", "Clear instructions from the proctor. Thank you."), ('<span class="muted">Mar 15</span>', "Kalamansig", "The signs to the testing rooms were hard to find.")])}
{pager(1, 3, 213)}""", active="reports", crumb='<a href="reports.html" class="muted">← Reports</a>')

admin("exports", "Downloads", table(["File", "Asked by", "Status", ""], [
    ("applicants-2027.xlsx", "Admission Office · now", '<div class="meter"><div class="t"><span style="width:62%"></span></div><span class="mono">62%</span></div>', '<span class="spin"></span>'),
    ("ranking-civil-eng-isulan.xlsx", "Admission Office · 10 min ago", B("ok", "Ready · 84 KB"), btn("Download", "#")),
    ("payments-jan.xlsx", "Cashier 1 · yesterday", B("ok", "Ready · 1.2 MB"), btn("Download", "#")),
    ("attendance-mar14.xlsx", "Testing Center · Mar 14", B("bad", "Failed · timed out"), btn("Try again", "#retry"))]) + '<span class="muted">Files are kept for 7 days.</span>',
      overlays=inmain("empty", empty("file", "No downloads yet", "Exports you start from any list land here and stay for 7 days.", btn("Go to reports", "reports.html"))) + toast("queued", "info", INFO, "Building your file", "It will appear here in a minute. You can keep working.") + toast("retry", "info", INFO, "Trying again", "attendance-mar14.xlsx is back in the queue."),
      states=[("queued", "Export queued"), ("retry", "Retry"), ("empty", "Empty")])

camp = [("ACCESS, Tacurong", 22, "4,343"), ("Isulan", 14, "1,884"), ("Tacurong", 9, "1,663"), ("Kalamansig", 5, "731"), ("Bagumbayan", 2, "128"), ("Palimbang", 2, "94"), ("Lutayan", 2, "93")]
admin("rooms", "Rooms", f"""{list_page(filters("Building or room", [("Campus", ["Isulan", "ACCESS, Tacurong", "Tacurong", "Kalamansig", "Bagumbayan", "Palimbang", "Lutayan"])]),
table(["Building", "Room", "Seats", "Exam use", "Used in", ""], [("Main Building", "Room 1", '<span class=\"num\">50</span>', '<a class=\"switch on" href="#"></a>', "Schedule 1 · Schedule 2", btn("Edit", "#room")), ("Main Building", "Room 4", '<span class=\"num\">50</span>', '<a class=\"switch on" href="#"></a>', "Schedule 1 · Schedule 2", btn("Edit", "#room")), ("Engineering", "ENG 201", '<span class=\"num\">45</span>', '<a class=\"switch on" href="#"></a>', "Schedule 1", btn("Edit", "#room")), ("Engineering", "ENG 202", '<span class=\"num\">45</span>', '<a class=\"switch" href="#"></a>', "—", btn("Edit", "#room")), ("Library", "AVR", '<span class=\"num\">80</span>', '<a class=\"switch on" href="#"></a>', "Schedule 2", btn("Edit", "#room"))], sortable=("Building", "Room", "Seats"), active=("Building", "asc")), count="5 rooms at Isulan · 225 exam seats", actions=btn("Add room", "#room", "primary"))}
""",
      overlays=modal("room", "info", "+", "Add a room · Isulan", f'<div class="fld"><label for="ro1">Building</label><input id="ro1" value="Engineering"></div><div class="fld"><label for="ro2">Room name</label><input id="ro2" value="ENG 203"></div><div class="fld"><label for="ro3">Seats for an exam</label><input id="ro3" type="number" min="1" inputmode="numeric" value="45">{hint("Count the chairs with one seat gap between examinees, not the room’s class size.")}</div>', btn("Cancel", "#") + btn("Add room", "#added", "primary"))
      + toast("added", "ok", OK, "Room added", "ENG 203 · 45 seats. Pick it when you add an exam slot."),
      states=[("room", "Add room form"), ("added", "Added")])

ISULAN = [("BS Civil Engineering", "BSCE", True, 530, 412, True), ("BS Criminology", "BSCrim", True, 530, 884, True), ("BS Electrical Engineering", "BSEE", True, 530, 166, True),
          ("BS Computer Engineering", "BSCpE", True, 530, 121, True), ("BS Nursing", "BSN", True, 600, 318, True), ("BS Information Technology", "BSIT", False, 480, 247, True),
          ("Associate in Computer Technology", "ACT", False, 450, 54, True), ("BS Midwifery", "BSM", True, 530, 0, False)]


def prog_row(name, short, board, cutoff, picks, offered):
    return (f'<b class="ink">{name}</b><span class="sub mono">{short}</span>', B("gray", "Board") if board else '<span class="muted">—</span>',
            f'<span class="mono">{cutoff}</span>', f'<span class="mono">{picks:,}</span>' if offered else '<span class="muted">—</span>',
            f'<a class="switch{" on" if offered else ""}" href="{"#off" if offered else "#on"}" aria-label="Offered in SY 2027–2028"></a>',
            '<span class="act">' + btn("Edit", "#program") + "</span>")


PROGRAM_FORM = ('<div class="fld"><label for="p1">Campus</label><select id="p1"><option>Isulan</option><option>ACCESS, Tacurong</option></select></div>'
                '<div style="display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:10px"><div class="fld"><label for="p2">Program name</label><input id="p2" value="BS Information Technology"></div>'
                '<div class="fld"><label for="p3">Short name</label><input id="p3" value="BSIT" maxlength="10"></div></div>'
                '<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:10px"><div class="fld"><label for="p4">Cut-off score</label><input id="p4" type="number" min="200" max="800" inputmode="numeric" value="480">'
                + hint("Lowest overall score that qualifies.") + '</div><div class="fld"><label for="p5">Board program</label><select id="p5"><option>No</option><option>Yes, has a licensure exam</option></select></div></div>'
                '<label class="chkrow"><input type="checkbox" checked> Offered in SY 2027–2028</label>')

admin("campuses", "Campuses and programs", f"""<div class="head"><span class="muted"></span><span style="display:flex;gap:8px">{btn("Add campus", "#campus")}{btn("Add program", "#program", "primary")}</span></div>
<div class="cards">{''.join(f'<a class="tile ctile{" on" if c == "Isulan" else ""}" href="#"><span class="ct">{c}</span><span class="muted">{p} programs offered</span><span><span class="cn">{d}</span> <span class="muted">1st-choice picks</span></span></a>' for c, p, d in camp)}</div>
<div class="head" style="margin-top:8px"><h2 style="margin:0">Isulan · 14 programs</h2><span style="display:flex;gap:8px;align-items:center"><input class="search" aria-label="Search programs" placeholder="Search programs" style="width:240px"><span class="seg"><span class="on">All · 14</span><span>Offered · 13</span><span>Not offered · 1</span></span></span></div>
{table(["Program", "Board", "Cut-off score", "1st-choice picks", "Offered in SY 2027–2028", ""], [prog_row(*r) for r in ISULAN], sortable=("Program", "Cut-off score", "1st-choice picks"), active=("Program", "asc"))}
<div class="head"><span class="muted">1–8 of 14</span><span style="display:flex;gap:6px">{btn("Previous", "#", "sm")}{btn("Next", "#", "sm")}</span></div>""",
      overlays=modal("program", "info", "+", "Add a program", PROGRAM_FORM, btn("Cancel", "#") + btn("Add program", "#added", "primary"))
      + modal("campus", "info", "+", "Add a campus", '<div class="fld"><label for="c1">Campus name</label><input id="c1" placeholder="Kalamansig"></div><div class="fld"><label for="c2">Address (on the permit)</label><input id="c2" placeholder="Poblacion, Kalamansig, Sultan Kudarat"></div><label class="chkrow"><input type="checkbox" checked> Test center (exams are held here)</label>', btn("Cancel", "#") + btn("Add campus", "#added", "primary"))
      + toast("added", "ok", OK, "Program added", "BS Information Technology · Isulan, offered in 2027.")
      + modal("off", "warn", WARN, "Stop offering BS Criminology in Isulan?", '<p class="muted" style="margin:0">884 applicants picked it. They keep their choice; new applicants can’t pick it.</p>', btn("Cancel", "#") + btn("Stop offering", "#", "danger"))
      + modal("on", "info", "", "Offer BS Midwifery in Isulan again?", '<p class="muted" style="margin:0">New applicants can pick it from now on. Cut-off stays 530.</p>', btn("Cancel", "#") + btn("Offer it", "#", "primary")),
      states=[("program", "Add program"), ("campus", "Add campus"), ("added", "Added"), ("off", "Turn off warning"), ("on", "Turn on")])

# name, email, role, scope (campus or program), last active ("" = invite pending)
staff = [("Admission Office", "sksutpt@gmail.com", "Admin", "All campuses", "Now"), ("Ana R.", "ana.r@sksu.edu.ph", "Admin", "All campuses", "10 min ago"),
         ("Cashier 1", "cashier1@sksu.edu.ph", "Cashier", "Isulan counter 1", "5 min ago"), ("Cashier 2", "cashier2@sksu.edu.ph", "Cashier", "Isulan counter 2", "1 h ago"),
         ("Isulan proctor", "isulan.tpt@sksu.edu.ph", "Proctor", "Isulan rooms", "Mar 14"), ("Engr. R. Dalanda", "bsit.chair@sksu.edu.ph", "Program chair / Dean", "Chair · BS Information Technology", "Yesterday"),
         ("Dr. L. Mangansakan", "ceit.dean@sksu.edu.ph", "Program chair / Dean", "Dean · College of Engineering (BSCE, BSEE, BSCpE, BSIT)", "Today"),
         ("cashier3@sksu.edu.ph", "invited Jan 10", "Cashier", "ACCESS counter 1", "")]
PERMS = [("See applicants", "✓", "Waiting for payment", "Own rooms", "Own program’s transferees"), ("Approve or send back payments", "✓", "", "", ""), ("Record counter payments", "✓", "✓", "", ""), ("Approve transferees", "✓", "", "", "✓"), ("Edit applicants", "✓", "", "", ""), ("Exam schedules and slots", "✓", "", "", ""), ("Check-in (if turned on)", "✓", "", "✓", ""), ("Import scores, publish results", "✓", "", "", ""), ("Messages", "✓", "", "", ""), ("Staff, settings, System", "✓", "", "", "")]
def app_preview(src, label):
    """A phone preview of the real student app (euphoria's device frame), shown beside the form being edited."""
    return (f'<aside class="apppreview"><span class="muted">Preview · {label}</span><div class="device"><i class="cam"></i>'
            f'<iframe src="{src}" title="Student app preview: {label}" loading="lazy" tabindex="-1"></iframe><i class="home"></i></div></aside>')


ROWS_EDIT = lambda items, target: "".join(f'<div class="setrow"><span>{t}</span>{btn("Edit", target, "sm")}</div>' for t in items)

admin("landing", "Student app", f"""<div class="head"><span class="muted">What students see in the app and on the landing page</span>{btn("Save", "#landing-ok", "primary")}</div>
{ptabs([("home", "Home"), ("info", "Info"), ("settings", "Settings")])}
<section class="pane" id="pane-home"><div class="appedit"><div class="appform">
<div class="panel"><div class="head"><h2>Announcement</h2><a class="switch on" href="#announce" aria-label="Show the announcement"></a></div>
<div class="fld"><label for="l1">Shown at the top of the student Home and the landing page</label><input id="l1" value="Schedule 2 registration is open until Apr 10."></div>
<small class="muted">Up to 120 characters. Leave it off when there is nothing new.</small></div>
<div class="panel"><h2>Filled in by the system</h2><div class="kv">
<span>Registration</span><span>Open · Schedule 2 · until Apr 10 (from Exam schedules)</span>
<span>Exam fee</span><span>₱275.00 (from the school year)</span>
<span>Campuses</span><span>7 campuses, 56 programs (from Campuses and programs)</span></div></div></div>
{app_preview("../applicant/home.html", "Home")}</div></section>
<section class="pane" id="info"><div class="appedit"><div class="appform">
<div class="panel"><div class="head"><h2>To apply</h2>{btn("Add", "#req", "sm")}</div>{ROWS_EDIT(["2×2 ID photo, white background", "Application code, shown at the cashier"], "#req")}</div>
<div class="panel"><div class="head"><h2>On exam day, bring</h2>{btn("Add", "#req", "sm")}</div>{ROWS_EDIT(["Pencil No. 2 with eraser", "Permit", "School ID or any valid ID", "Official receipt"], "#req")}</div>
<div class="panel"><div class="head"><h2>Questions and answers</h2>{btn("Add", "#faq", "sm")}</div>{ROWS_EDIT(["Can I take the test again if I was absent?", "Where do I pay the exam fee?", "When are results released?"], "#faq")}</div>
<div class="panel"><div class="head"><h2>Cashier offices and hours</h2>{btn("Add", "#req", "sm")}</div>{ROWS_EDIT(["Isulan · Cashier, Admin Building · Mon–Fri 8:00 AM – 5:00 PM", "ACCESS, Tacurong · Cashier, Main Gate · Mon–Sat 8:00 AM – 12:00 noon"], "#req")}</div>
<div class="panel"><h2>Contact</h2><div class="formgrid"><div class="fld"><label for="l0">Office</label><input id="l0" value="Guidance and Testing Center, SKSU ACCESS Campus, EJC Montilla, Tacurong City"></div>
<div class="fld"><label for="l2">Phone</label><input id="l2" type="tel" value="0997 780 1758"></div><div class="fld"><label for="l3">Email</label><input id="l3" type="email" value="admission@sksu.edu.ph"></div>
<div class="fld"><label for="l5">Facebook page</label><input id="l5" value="SKSU Guidance and Testing Center"></div></div></div></div>
{app_preview("../public/landing.html", "Info")}</div></section>
<section class="pane" id="settings"><div class="appedit"><div class="appform">
<div class="panel"><h2>Install the app</h2><div class="fld"><label for="i1">Button text</label><input id="i1" value="Install the app"></div>
<div class="fld"><label for="i2">iPhone steps</label><input id="i2" value="Tap Share, then Add to Home Screen, then Add."></div></div>
<div class="panel"><h2>Survey</h2><div class="setrow"><span>Ask the survey after the result, before choosing a program</span><a class="switch on" href="#" aria-label="Survey before choosing a program"></a></div>
<a href="survey.html">Edit the survey statements →</a></div>
<div class="panel"><h2>Support</h2><div class="setrow"><span>1 open request at a time · 5 per school year · 1 reply a minute</span>{btn("Edit limits", "support.html#limits", "sm")}</div></div></div>
{app_preview("../public/landing.html#install", "Landing page")}</div></section>""",
      overlays=modal("req", "info", "✎", "Edit line", '<div class="fld"><label for="r1">Text</label><input id="r1" value="2×2 ID photo, white background"></div>', btn("Remove", "#", "danger") + btn("Cancel", "#") + btn("Save", "#landing-ok", "primary"))
      + modal("faq", "info", "✎", "Question and answer", '<div class="fld"><label for="f1">Question</label><input id="f1" value="Can I take the test again if I was absent?"></div><div class="fld"><label for="f2">Answer</label><textarea id="f2" rows="3">Yes. Apply again in the next schedule. Your details are filled in from last time.</textarea></div>', btn("Remove", "#", "danger") + btn("Cancel", "#") + btn("Save", "#landing-ok", "primary"))
      + modal("announce", "info", "✎", "Edit the announcement", '<div class="fld"><label for="an">Announcement</label><input id="an" value="Schedule 3 registration opens Apr 11. Cashiers are open on Saturday this week."></div><small class="muted">The preview updates as you type.</small>', btn("Cancel", "#") + btn("Save", "#landing-ok", "primary"))
      + toast("landing-ok", "ok", OK, "Saved", "Students see the change the next time they open the app.") + BELL_POP,
      states=[("info", "Info tab"), ("settings", "Settings tab"), ("announce", "Editing the announcement"), ("req", "Edit a line"), ("faq", "Edit a question"), ("landing-ok", "Saved")])

CHAIR_ROWS = [("Kenneth L. Abo", "Notre Dame of Tacurong College", "BS Computer Science · 2nd year", "grades-1st-sem.pdf", "Waiting"),
              ("Aiza M. Pendatun", "Cotabato State University", "BS Information Systems · 1st year", "tor.pdf", "Waiting"),
              ("Ronnie T. Sabdani", "STI College Koronadal", "BS Computer Science · 1st year", "", "Approved"),
              ("Mae C. Lumabao", "Notre Dame of Marbel University", "BS Accountancy · 2nd year", "grades.pdf", "Declined")]
CHAIR_ST = {"Waiting": '<span class="st">Waiting</span>', "Approved": '<span class="st live">Approved</span>', "Declined": '<span class="st bad">Declined</span>'}
CHAIR_PROGRAMS = [("BS Information Technology", 6, 20), ("BS Computer Engineering", 3, 15), ("BS Civil Engineering", 0, 10)]
admin("chair", "Transferee applicants", f"""<div class="head"><span class="muted">College of Engineering and Information Technology · you approve as Dean</span></div>
<div class="kpis"><div class="kpi"><span>Waiting for you</span><b>2</b></div><div class="kpi"><span>Approved</span><b>14</b></div></div>
{table(["Program", "Slots left this semester", ""], [(f'<span class="ink">{pr}</span>', f'<span class="num">{left} of {cap}</span>', '<span class="muted">Full</span>' if left == 0 else "") for pr, left, cap in CHAIR_PROGRAMS])}
{list_page(stabs([("Waiting", "2"), ("Approved", "14"), ("Declined", "3"), ("All", "19")]), filters("Name or application code", [("Program", ["All my programs"] + [pr for pr, *_ in CHAIR_PROGRAMS])]),
table(["Applicant", "Current school and course", "Grades", "Status", ""], [(two(f'<span class="ink">{n}</span>', "1st choice: BS Information Technology"), two(sch, crs), f'<a href="#grades">{g}</a>' if g else '<span class="muted">Evaluated in person</span>', CHAIR_ST[st],
      rowact("#grades", "", ("Review", "#grades")) if st == "Waiting" else rowact("#grades", "")) for n, sch, crs, g, st in CHAIR_ROWS]))}""",
      nav=CHAIR_NAV, user=("Dr. L. Mangansakan", "College dean"), side_note="Program chairs and deans see only this page: chairs for one program, deans for every program in their college.",
      overlays=modal("grades", "info", "", "Kenneth L. Abo · BS Computer Science, 2nd year", '<div class="thumb" style="height:220px">grades-1st-sem.pdf</div><div class="kv"><span>School</span><span>Notre Dame of Tacurong College</span><span>2nd choice</span><span>BS Computer Engineering · Isulan</span></div>', btn("Decline", "#decline", "danger") + btn("Evaluated in person", "#in-person") + btn("Approve", "#approved", "primary"))
      + modal("in-person", "info", "", "Evaluated in person", '<p class="muted" style="margin:0">Use this when the student brought their transcript or certificate of grades to your office. No upload is needed.</p><div class="fld"><label for="ip">Decision</label><select id="ip"><option>Approve</option><option>Decline</option></select></div><div class="fld"><label for="ipn">Note (optional)</label><input id="ipn" value="Transcript checked at the CEIT office, Nov 6."></div>', btn("Cancel", "#") + btn("Save", "#approved", "primary"))
      + modal("decline", "warn", WARN, "Decline Kenneth for BS Information Technology?", '<div class="fld"><label for="dr">Reason (sent to the applicant)</label><select id="dr"><option>No slots left this semester</option><option>Grades do not meet the program’s requirement</option><option>Other</option></select></div><div class="fld"><label for="dm">Remarks (optional)</label><textarea id="dm" rows="2">No slots left for 2nd year transferees this semester.</textarea></div>' + hint("His 2nd choice goes to that program’s chairperson next."), btn("Cancel", "#") + btn("Decline", "#declined", "danger"))
      + toast("approved", "ok", OK, "Approved by Dr. L. Mangansakan, Dean", "Kenneth can now pay ₱275.00 at the cashier. He was told by app and email.")
      + toast("declined", "ok", OK, "Declined", "Kenneth was told the reason. His 2nd choice is next."),
      states=[("grades", "Review grades"), ("in-person", "Evaluated in person"), ("decline", "Decline with reason"), ("approved", "Approved"), ("declined", "Declined")])

def setup_rows(steps, nxt):
    return "".join(f'<div class="srow {"done" if d else ("next" if i == nxt else "")}"><i>{"✓" if d else i + 1}</i><span class="grow"><b>{label}</b><small>{"Done" if d else ("Next" if i == nxt else "To do")}</small></span>{btn("Open", href, "sm")}</div>'
                   for i, (label, href, d) in enumerate(steps))


admin("setup", "Setup", f"""<div class="head"><span class="muted">SY 2028–2029 · 2 of 7 done</span>{btn("Continue: Campuses and programs", "campuses.html", "primary")}</div>
<div class="panel"><div class="srows">{setup_rows(SETUP_STEPS_ALL, 2)}</div></div>
<h2 style="margin:8px 0 0;font-size:16px">Optional</h2>
<div class="panel"><div class="srows">{setup_rows(SETUP_OPTIONAL, -1)}</div></div>
<small class="muted">The line under each page title disappears once everything above is done. Hide it any time from its ··· menu.</small>""")


STAFF_MENU = menu("staffmenu", [("Resend invite", "#invited", "", ""), ("-", "", "", ""), ("Deactivate", "#last-admin", "danger", "They can no longer sign in")])
admin("staff", "Staff and roles", f"""{ptabs([("staff", "Staff"), ("roles", "Roles")])}
<section class="pane" id="pane-staff">{list_page(stabs([("All", "8"), ("Admin", "2"), ("Cashier", "3"), ("Proctor", "1"), ("Program chair / Dean", "2")]), filters("Name or email"),
table(["Staff", "Role", "Campus or program", "Last active", ""], [(two(f'<span class="ink">{n}</span>', e), f'<span class="st">{r}</span>', sc,
      w if w else '<span class="muted">Invite pending</span>', rowact(None, "#staffmenu", ("Resend invite", "#invited") if not w else ("Change role", "#role"))) for n, e, r, sc, w in staff],
      sortable=("Staff", "Role", "Last active"), active=("Staff", "asc")), actions=btn("Invite staff", "#invite", "primary"))}{STAFF_MENU}</section>
<section class="pane" id="roles">{table(["What they can do", "Admin", "Cashier", "Proctor", "Program chair / Dean"], PERMS)}</section>""",
      overlays=modal("invite", "info", "+", "Invite staff", '<div class="fld"><label for="i1">Email</label><input id="i1" type="email" value="proctor.kalamansig@sksu.edu.ph"></div><div class="fld"><label for="i2">Role</label><select id="i2"><option>Proctor</option><option>Cashier</option><option>Program chair (one program)</option><option>College dean (every program in the college)</option><option>Admin</option></select></div>', btn("Cancel", "#") + btn("Send invite", "#invited", "primary"))
      + toast("invited", "ok", OK, "Invite sent", "proctor.kalamansig@sksu.edu.ph can sign in within 7 days.")
      + modal("role", "warn", WARN, "Change Cashier 2’s role?", '<select><option>Cashier</option><option>Proctor</option><option>No access</option></select><p class="muted" style="margin:0">Takes effect on their next click.</p>', btn("Cancel", "#") + btn("Save", "#", "primary"))
      + modal("last-admin", "bad", BAD, "You can’t remove the last admin", '<p class="muted" style="margin:0">Make someone else an admin first.</p>', btn("OK", "#")),
      states=[("roles", "Roles tab"), ("invite", "Invite form"), ("invited", "Invited"), ("role", "Change role"), ("last-admin", "Guard error")])

audit = [("Today 9:05", "Cashier 1", "Recorded Jomar P. Abdullah’s payment (OR 0048190) and issued 500215"), ("Today 8:58", "Ana R. (admin)", "Sent back Noel B. Guiamal: reference already used"), ("Jan 13 2:10 PM", "Admission Office", "Closed exam slot Isulan, Sat Apr 25 (full)"), ("Jan 13 9:42 AM", "Maria S. Dela Cruz", "Booked Isulan, Room 4 seat 27"), ("Jan 12 4:30 PM", "Ana R. (admin)", "Approved Maria S. Dela Cruz’s payment and issued 500214"), ("Jan 10 8:30 AM", "Admission Office", "Invited Ana R. as Admin"), ("Jan 2 7:00 AM", "System", "Nightly backup: database 31 MB, files 412 MB, copied off-site"), ("Jan 1 12:00 AM", "Admission Office", "Opened SY 2027–2028")]
admin("audit", "Activity log", list_page(filters("Name, examinee no. or OR no.", [("Who", ["Anyone", "Admins", "Cashiers", "Applicants"]), ("Action", ["Any action", "Payments", "Approvals and send-backs", "Exam slots", "Results", "Settings"])], extra='<span class="range"><input type="date" aria-label="From" value="2027-01-01"><span class="muted">to</span><input type="date" aria-label="To" value="2027-01-13"></span>'),
      table(["When", "Who", "What"], [(f'<span class="muted">{a[0]}</span>', f'<span class="ink">{a[1]}</span>', a[2]) for a in audit], sortable=("When", "Who"), active=("When", "desc")), pager(1, 25, "48,210"), count="48,210 entries"))

admin("account", "My account", f"""<div class="panel" style="max-width:640px"><div class="kv"><span>Name</span><span class="ink">Admission Office</span><span>Email</span><span>sksutpt@gmail.com</span><span>Role</span><span>{B("gray", "Admin")}</span><span>Signed in on</span><span>This PC · Chrome · since 7:58 AM</span></div>
<div style="display:flex;gap:8px">{btn("Sign out other devices", "#others")}{btn("Sign out", "../public/staff-login.html")}</div></div>
<div class="panel" id="guides" style="max-width:640px"><h2>Guides</h2>
<div class="setrow"><span>Show the setup line under page titles</span><a class="switch on" href="#" aria-label="Show the setup line"></a></div>
<div class="setrow"><span>Show steps on long forms</span><a class="switch on" href="#" aria-label="Show steps on long forms"></a></div>
<div class="setrow"><span>Hints you closed stay closed. Guide buttons never open by themselves.</span>{btn("Show all hints again", "#hints-back", "sm")}</div></div>""",
      active="", overlays=toast("others", "ok", OK, "Signed out 2 other devices", "Only this PC stays signed in.") + toast("hints-back", "ok", OK, "Hints are back", "Closed hints will show again once."), states=[("guides", "Guide settings"), ("others", "Signed out others"), ("hints-back", "Hints back")])

doc("docs/seat-plan.html", "Seat plan", f"""<div class="crumbs" style="text-align:center;padding-top:12px"><a href="../index.html">All pages</a> | <a href="../admin/exam-slots.html">Back to exam slots</a></div>
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
        out, run = "", []
        for f in full + [None]:  # keep the given order; a new row starts when the frame kind changes
            if run and (f is None or f[0] != run[0][0]):
                out += f'<div class="frames f-{run[0][0]}">' + "".join(frame(*g, pre=pre) for g in run) + "</div>"
                run = []
            if f:
                run.append(f)
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
          (D, "public/landing.html", "1", "Public home", "What the test is, the four steps and the school year dates. One green button."),
          (P, "public/landing.html", "1b", "Public home on a phone", "Same page at phone width; the menu folds away.", True),
          (P, "public/login.html", "2", "Sign in", "Continue with Google, as in tptv3."),
          (P, "public/login.html#loading", "2a", "Signing in", "Shown while Google answers.", True),
          (P, "public/login.html#google-error", "2b", "Sign-in failed", "Nothing saved; one Try again button.", True),
          (P, "public/login.html#closed", "2c", "Registration closed", "Per schedule; can still sign in to see a permit or result.", True)]),
       ("Apply", [
          (P, "applicant/home.html#not-started", "3", "Home: first time", "The four steps and the closing date. One button: Start."),
          (P, "applicant/home.html#draft", "3b", "Home: draft", "Where they stopped; Continue.", True),
          (P, "applicant/home.html#offline", "3a", "Offline", "Typing is kept and saved when the signal is back.", True),
          (P, "applicant/apply-personal.html", "4", "About you", "Name, birth date, contact and a 2×2 photo made smaller on the phone."),
          (P, "applicant/apply-personal.html#photo-bad", "4a", "Photo rejected", "No face found or too dark; choose another.", True),
          (P, "applicant/apply-personal.html#upload-failed", "4b", "Upload failed", "Signal dropped; tap to retry.", True),
          (P, "applicant/apply-personal.html#saved", "4c", "Autosaved", "A quiet confirmation, no button to press.", True),
          (P, "applicant/apply-personal.html#age", "4d", "Birth date error", "Says what is wrong and how to fix it.", True),
          (P, "applicant/apply-school.html", "5", "School", "Type, school, year, GWA, strand and documents."),
          (P, "applicant/apply-programs.html", "6", "Programs", "Three choices in order; a nudge to add the third."),
          (P, "applicant/apply-programs.html#picker", "6a", "Program picker", "Campus first, then program.", True),
          (P, "applicant/apply-programs.html#dup", "6b", "Duplicate choice", "Can’t pick the same program twice.", True),
          (P, "applicant/apply-review.html", "7", "Review", "Everything on one screen with Edit links."),
          (P, "applicant/apply-review.html#confirm", "7a", "Submit?", "Says what can and can’t change after.", True),
          (P, "applicant/apply-review.html#submitting", "7b", "Submitting", "Don’t close the page.", True),
          (P, "applicant/apply-review.html#missing", "7c", "Something missing", "Names exactly what is missing.", True)]),
       ("Pay", [
          (P, "applicant/home.html", "8", "Home: submitted", "The code to show the cashier, office hours, Show my code."),
          (P, "applicant/home.html#chair", "8b", "Home: waiting for chairperson", "Transferees only.", True),
          (P, "applicant/home.html#sent-back", "8c", "Home: sent back", "What to fix; Fix and send again.", True),
          (P, "applicant/payment.html#submitted", "8d", "Pay at an SKSU cashier", "A code to show, where to pay, office hours. Nothing to upload."),
          (P, "applicant/payment.html#online", "8a", "Later: online payment", "Only when the office turns it on.", True),
          (P, "applicant/payment-waiting.html#sent", "9", "Later: receipt sent", "Online payment only.", True),
          (P, "applicant/payment-rejected.html", "10", "Sent back: please fix", "Photo or details, the office’s remarks, Send again."),
          (P, "applicant/payment-rejected.html#voided", "10a", "Payment cancelled", "An admin voided it; the reason, then pay again.", True),
          (P, "applicant/payment-rejected.html#closed-out", "10b", "Too late for this schedule", "Apply for the next schedule, details filled in.", True),
          (D, "docs/email-approved.html", "11", "Email: payment recorded", "OR no., examinee number and one button: pick an exam slot."),
          (D, "docs/email-rejected.html", "12", "Email: sent back", "What to fix and a link straight back.")]),
       ("Exam slot and permit", [
          (P, "applicant/home.html#approved", "12b", "Home: paid", "Examinee number; Pick exam slot by Mar 1."),
          (P, "applicant/seat.html#approved", "13", "Pick an exam slot", "Live seats left per exam slot; full ones are greyed."),
          (P, "applicant/seat.html#loading", "13a", "Loading exam slots", "Skeleton rows, never a blank screen.", True),
          (P, "applicant/seat.html#confirm", "13b", "Confirm exam slot", "One change allowed until Mar 1.", True),
          (P, "applicant/seat.html#taken", "13c", "Exam slot just filled", "Someone booked the last seat first.", True),
          (P, "applicant/home.html#booked", "13d", "Home: exam slot booked", "Date, campus, room and seat, report time; View permit.", True),
          (P, "applicant/permit.html#booked", "14", "Permit", "QR, number, room and seat. Works offline once opened."),
          (P, "applicant/permit.html#making", "14a", "Making the PDF", "Built once, saved for next time.", True),
          (D, "docs/permit-pdf.html", "15", "Permit PDF", "A4 with letterhead, photo and verify QR.")]),
       ("After exam day", [
          (P, "applicant/home.html#exam-done", "16", "Home: waiting for results", "Release date."),
          (P, "applicant/home.html#absent", "16b", "Home: absent", "Apply for Schedule 2 without paying again.", True),
          (P, "applicant/result-pending.html", "16c", "Waiting for results (detail)", "Release date and the exam taken.", True),
          (P, "applicant/result-pending.html#absent", "16a", "Marked absent", "No score in the file; apply for the next schedule or ask the office.", True),
          (D, "docs/email-results.html", "18", "Email: results out", "One button to the result."),
          (P, "applicant/home.html#result-out", "18b", "Home: result out", "Overall score and stanine; See result."),
          (P, "applicant/result.html", "19", "Result", "Overall score, stanine, plain meaning, each subject."),
          (P, "applicant/result.html#cutoffs", "19a", "Program cut-offs", "Qualified or not per choice.", True),
          (P, "applicant/survey.html", "19b", "Exam survey", "The 10 tptv3 statements; needed before choosing.", True),
          (P, "applicant/survey.html#missing", "19c", "Survey: missing answer", "All 10 are required; comments optional.", True),
          (P, "applicant/result.html#choose", "19d", "Choose a program", "Only programs they qualify for.", True),
          (P, "applicant/result.html#chosen", "19e", "Program chosen", "The registrar contacts them.", True),
          (P, "applicant/home.html#chosen", "19d", "Home: program chosen", "Done; result PDF.", True),
          (D, "docs/result-pdf.html", "20", "Result PDF", "Official copy with verify link.")]),
       ("Notifications and support", [
          (P, "applicant/notifications.html", "21", "Notifications", "Every update in one list, newest first."),
          (P, "applicant/support.html#new", "21a", "New support request", "Topic, message, optional photo.", True),
          (P, "applicant/support-ticket.html", "21b", "Office reply", "A thread; reply or mark as solved.", True),
          (P, "applicant/support.html#one-open", "21c", "Limit reached", "One open request; 5 per school year.", True),
          (D, "docs/sms.html", "22", "Text messages", "Every SMS, under 160 characters.")]),
       ("Account", [
          (P, "applicant/profile.html", "23", "My account", "Details locked after approval; request a change through Support."),
          (P, "applicant/profile.html#photo", "23a", "Change photo", "", True),
          (P, "applicant/profile.html#history", "23b", "My history", "Every step with its date.", True),
          (D, "public/error.html", "24", "Error pages", "404, busy queue and server error, each with a next step.")])],
      [("Few words, one action", "System font, 16 px text, 48 px tap targets, one main button per screen."), ("Never lose work", "Autosave, offline typing, retry on upload."),
       ("Say what happens next", "Every success says the next step; every error says how to fix it."), ("Safe answer first", "Dialogs put Cancel or Back below the main action."),
       ("Status in words", "Colour never carries meaning alone."), ("Phone first", "Every applicant screen is drawn at 390 px.")])

admin_pages = [("dashboard", "", "Dashboard", "Today’s numbers, sign-ups, demand and what needs attention."),
               ("applications", "", "Applications", "Search, filter, export; status in words."),
               ("applications", "rowmenu", "Row actions", "Open, resend permit, move, cancel."),
               ("applications", "loading", "Searching", "Skeleton while 16k rows are searched."),
               ("applications", "empty", "No results", "Empty state with Clear search."),
               ("applicant", "", "Applicant record", "Everything about one applicant plus the full history."),
               ("applicant", "edit", "Edit details", "Form with a date error; a reason is required."),
               ("applicant", "move", "Move exam slot", ""), ("applicant", "cancel", "Cancel application", "Type CANCEL to confirm."),
               ("payments", "", "Payment review", "Queue, receipt and decision side by side; keyboard keys."),
               ("payments", "approve", "Reused reference warning", ""), ("payments", "approved", "Approved", "Number issued, next one opens."),
               ("payments", "reject", "Send back with remarks", "What to fix, reason and remarks."), ("payments", "conflict", "Two reviewers", "Someone else decided first."),
               ("payments", "empty", "All caught up", ""),
               ("schedules", "", "Exam schedules", "Publish or unpublish each schedule."), ("schedules", "new", "New school year form", ""), ("schedules", "open-conflict", "School year conflict", ""),
               ("exam-slots", "", "Exam slots", "Seats taken per campus and date."), ("exam-slots", "add", "Add exam slot form", "With a rooms error."),
               ("exam-slots", "added", "Exam slot added", "Waiting applicants are emailed."), ("exam-slots", "toggle", "Close exam slot", ""),
               ("checkin", "", "Check-in (optional)", "Off by default; absences come from the score import."), ("checkin", "live", "Live check-in", "Only when turned on."), ("checkin", "call", "Proctor offline", ""),
               ("scores", "", "Import scores", "The Testing Center Excel as it is; problem rows listed."), ("scores", "uploading", "Reading the file", ""),
               ("scores", "missing", "Required column missing", ""), ("scores", "commit", "Approve confirm", ""),
               ("results", "", "Results", "Release date or Publish now; search results."), ("results", "release", "Publish confirm", "Can be hidden again; emails stay sent."),
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
    ("2 · Set up the school year", [
        ("admin/schedules.html", "School years and schedules", "A school year holds one or more exam schedules, for Freshmen or Transferees."),
        ("admin/setup-1.html", "New school year · step 1 Basics", "A stepper, because each step needs the one before."),
        ("admin/setup-2.html", "Step 2 Schedules", ""),
        ("admin/setup-3.html", "Step 3 Campuses and programs", ""),
        ("admin/setup-4.html", "Step 4 Exam slots and rooms", ""),
        ("admin/setup-5.html", "Step 5 Review and open", ""),
        ("admin/setup-5.html#open", "Open registration", ""),
        ("admin/schedules.html#open-conflict", "Another school year is open", "Save as draft, or close the old one first."),
        ("admin/schedules.html#created", "School year saved", ""),
        ("admin/schedules.html#round", "Add or edit a schedule", "Each schedule has its own registration, exam day and release; date error shown."),
        ("admin/schedules.html#round-saved", "Schedule saved", ""),
        ("admin/campuses.html", "Campuses and programs", "Seven campuses; each program is switched on per school year."),
        ("admin/campuses.html#program", "Add program form", ""),
        ("admin/campuses.html#campus", "Add campus form", ""),
        ("admin/campuses.html#off", "Stop offering a program", "Says how many applicants already picked it."),
        ("admin/staff.html", "Staff and roles", "Cashiers, proctors and the testing center, by role."),
        ("admin/staff.html#invite", "Invite staff form", ""),
        ("admin/staff.html#invited", "Invite sent", ""),
        ("admin/staff.html#role", "Change a role", ""),
        ("admin/staff.html#last-admin", "Last admin guard", "The system refuses, instead of warning.")]),
    ("3 · Exam schedule and rooms", [
        ("admin/rooms.html", "Rooms", "Buildings, rooms and exam seats per campus, reused every school year."),
        ("admin/rooms.html#room", "Add a room", "With a hint on how to count seats."),
        ("admin/exam-slots.html", "Exam slots", "Campus and date only; report and start times are a guide on the permit."),
        ("admin/exam-slots.html#times", "Guide times", ""),
        ("admin/exam-slots.html#add", "Add exam slot form", "Shown with a validation error on rooms."),
        ("admin/exam-slots.html#added", "Exam slot added", "Waiting applicants are emailed by themselves."),
        ("admin/exam-slots.html#toggle", "Close an exam slot", "People already booked keep their seats."),
        ("admin/exam-slots.html#auto", "Auto-assign seats", "Preview who gets a seat before it happens."),
        ("admin/exam-slots.html#assigned", "Seats assigned", "Undo for one hour."),
        ("docs/seat-plan.html", "Seat plan printout", "One sheet per room for the proctor and the door.")]),
    ("4 · Registration is running", [
        ("admin/dashboard.html", "Dashboard", "Only what needs action: payments to review, approved with no seat, seats left, then the attention list."),
        ("admin/dashboard.html#loading", "Loading", "Skeleton, never a blank page."),
        ("admin/applications.html", "Applications", "16k applicants, filters, export; status in words."),
        ("admin/applications.html#loading", "Searching", ""),
        ("admin/applications.html#empty", "No match", ""),
        ("admin/applications.html#view", "View: quick look", "A drawer on the right keeps the list in place."),
        ("admin/applications.html#menu", "··· menu", "Every row action, with the destructive one last and red."),
        ("admin/applications.html#bulk", "Bulk actions", "Tick rows, then remind, assign rooms and seats, or export."),
        ("admin/applications.html#bulk-remind", "Bulk reminder", "Template preview and cost before sending."),
        ("admin/applications.html#dupes", "Duplicate applicants", "Side by side; merge or mark not the same."),
        ("admin/search.html", "Global search", "Press / anywhere: names, numbers, references."),
        ("admin/applications.html#resent", "Permit email resent", ""),
        ("admin/messages.html", "Messages", "Templates, blasts and delivery."),
        ("admin/email.html#tpl", "Edit a template", ""),
        ("admin/messages.html#confirm", "Send a blast", ""),
        ("admin/messages.html#sent", "Blast sent", ""),
        ("admin/email.html#resend", "Resend a failed message", "Fix the number, resend, see it delivered."),
        ("admin/applicant.html", "One applicant", "Full record and every change with who and when."),
        ("admin/applicant.html#edit", "Edit details form", "Date error shown; a reason is required."),
        ("admin/applicant.html#saved", "Saved with reason", ""),
        ("admin/applicant.html#move", "Move to another exam slot", ""),
        ("admin/applicant.html#moved", "Moved, email sent", ""),
        ("admin/applicant.html#cancel", "Cancel application", "Type CANCEL; the exam slot is freed."),
        ("admin/applicant.html#photo", "Review an upload", "Ask for a new photo without losing the exam slot."),
        ("admin/applicant.html#sendback", "Send back with remarks", "Photo or details; the applicant fixes it and sends it again."),
        ("admin/applicant.html#void", "Void a payment", "Reason required; exam slot released; applicant told and can pay again.")]),
    ("5 · Payments, numbers and permits", [
        ("cashier/console.html", "Cashier console", "Its own role and screen: search, fixed fee, OR no., Enter."),
        ("admin/cashier.html", "Cashier counters", "Every counter’s payments and voids."),
        ("docs/email-approved.html", "What the applicant gets: approved", ""),
        ("docs/email-rejected.html", "What the applicant gets: sent back", ""),
        ("docs/permit-pdf.html", "Permit issued", "After the applicant picks an exam slot; QR links to the verify page.")]),
    ("5b · When online payment is turned on (later)", [
        ("admin/payments.html", "Payment review", "Queue, receipt and decision side by side; A and R keys."),
        ("admin/payments.html#approve", "Reused reference warning", "Caught before a double approval."),
        ("admin/payments.html#approved", "Approved, number issued", "Examinee no. comes from the school year counter; next one opens."),
        ("admin/payments.html#reject", "Send back with remarks", "What to fix, a reason and remarks go to the applicant."),
        ("admin/payments.html#rejected", "Sent back", ""),
        ("admin/payments.html#conflict", "Two admins, one receipt", "Whoever is second is told and moved on."),
        ("admin/payments.html#empty", "All caught up", "")]),
    ("6 · Exam day", [
        ("admin/checkin.html", "Check-in monitor", "Every room live: present, absent, pending, phone sync."),
        ("admin/checkin.html#call", "A proctor is offline", "Name, number, and assign someone else."),
        ("proctor/checkin.html", "What the proctor sees", "Their phone at the door, scanning permits."),
        ("proctor/summary.html#closed", "Room closed", "Counts arrive on the monitor.")]),
    ("7 · Scores", [
        ("admin/scores.html", "Import scores", "Upload the Testing Center Excel, match columns, see problem rows and what changes, approve."),
        ("admin/scores.html#uploading", "Uploading the Excel", "Progress while the file goes up."),
        ("admin/scores.html#checking", "Checking rows", "A row counter and problems found so far."),
        ("admin/scores.html#bg", "Running in the background", "Leave the page; the bell tells you when it’s done."),
        ("admin/scores.html#summary", "Import summary", "Ready, skipped, problems; download the problem rows."),
        ("admin/scores.html#map", "Match columns", "Remembered for next time."),
        ("admin/scores.html#map", "Match columns", "The sheet, two header rows and extra columns, checked once and remembered."),
        ("admin/scores.html#commit", "Approve confirm", "Scores are saved exactly as in the file, not yet visible.")]),
    ("8 · Review and publish results", [
        ("admin/results.html#committed", "Results", "Release date set; scored and absent counted."),
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
        ("admin/account.html", "My account", ""),
        ("admin/account.html#others", "Signed out other devices", "")]),
]
ADMIN_PHONE = ["admin/dashboard.html", "admin/applications.html", "admin/applicant.html", "admin/payments.html", "admin/payments.html#approved",
               "admin/exam-slots.html", "admin/exam-slots.html#add", "admin/checkin.html", "admin/results.html#release", "admin/staff.html#invite"]

sections = [(name, numbered(D, items)) for name, items in ADMIN_CYCLE]
sections.append(("10 · The same pages on a phone", numbered(P, [(src, "Phone: " + next(t for _, its in ADMIN_CYCLE for s2, t, _c in its if s2 == src), "") for src in ADMIN_PHONE])))
board("ADMIN-JOURNEY-MOCKUP.html", "Admin: the full school year",
      "Everything the admission office does in one school year, in order: sign in, set up the school year, build the exam schedule, run registration, "
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
    tabs = "".join(f'<a href="{h}" class="{"on" if t == tab else ""}">{label}</a>' for t, label, h in [("counter", "Counter", "console.html"), ("paid", "Paid", "paid.html"), ("info", "Info", "info.html")])
    doc(f"cashier/{key}.html", title, f"""<div class="strip"><strong>SKSU TPT · CASHIER MOCKUP</strong><span class="muted">sample data</span><a class="sp" href="../index.html">All pages</a></div>
<div class="cshell"><header class="ctop"><img src="../assets/sksu-seal.png" alt="SKSU seal"><b>Cashier</b><nav>{tabs}</nav>
{GUIDE_BTN if key in GUIDES else ""}<span class="ctally">Today: 36 · ₱9,900</span><span class="cwho"><span class="dot"></span>Cashier 1 · Isulan counter 1</span></header>
<main class="cmain">{body}</main></div>{overlays}{guide_modal(key) if key in GUIDES else ""}""", states=([("guide", "Guide")] if key in GUIDES else []) + list(states or []))


RECENT = [("9:41", "Ricky P. Ulangkaya", "0048213", "Cash"), ("9:12", "Joy M. Dalumpines", "0048212", "Cash"), ("8:47", "Norhana P. Sali", "0048211", "GCash at counter")]

WAITING = [("APP-27-10422", "Lea M. Sampulna", "BSEd Mathematics", "Kalamansig", "Mar 3", "12 days"), ("APP-27-10431", "Arnel D. Kamid", "BS Criminology", "Isulan", "Mar 4", "11 days"),
           ("APP-27-10437", "Jasmine O. Kusain", "BS Information Technology", "ACCESS, Tacurong", "Mar 6", "9 days"), ("APP-27-10440", "Rodel A. Sangki", "BS Agriculture", "Tacurong", "Mar 9", "6 days"),
           ("APP-27-10452", "Hanna S. Mamalo", "BS Nursing", "ACCESS, Tacurong", "Mar 12", "3 days"), ("APP-27-10466", "Mark J. Tayuan", "BS Civil Engineering", "Isulan", "Today", ""),
           ("APP-27-20418", "Kenneth L. Abo", 'BS Information Technology <span class="tag">Transferee · chairperson approved</span>', "ACCESS, Tacurong", "Today", "")]

QUICK_CASH = [(275, "Exact"), (300, "₱300"), (500, "₱500"), (1000, "₱1,000")]


def cnotice(nid, kind, title, text, acts=""):
    """An error or warning shown inline at the top of the payment panel (picked from the states bar)."""
    return f'<div class="cnotice {kind}" id="{nid}"><b>{title}</b><span>{text}</span>{acts}</div>'


cashier("console", "Counter", f"""<section class="cleft"><div class="cfind"><input id="find" type="search" aria-label="Find the applicant" placeholder="Name, application code or examinee no.   ( / )" autofocus></div>
<div class="clist"><div class="clisthead"><b>Waiting for payment <span class="muted">790 · oldest first</span></b><select aria-label="Campus"><option>All campuses</option><option>Isulan</option><option>ACCESS, Tacurong</option><option>Kalamansig</option></select></div>""" + "".join(
    f'<a class="crow{" on" if i == 0 else ""}" href="#"><span><b>{n}</b><span class="mono sub">{a}</span></span><span class="sub">{prg}<br>{c}</span></a>' for i, (a, n, prg, c, d, age) in enumerate(WAITING)) + f"""</div></section>
<section class="cright">
{cnotice("paid", "warn", "Already paid", "Jomar P. Abdullah paid today at 9:05 · OR 0048190 · Isulan counter 2. Don’t take another payment.", btn("Reprint that receipt", "#", "sm"))}
{cnotice("orused", "bad", "OR 0048213 is already used", "It was recorded at 9:41 for Ricky P. Ulangkaya. Check your booklet and type the next number.")}
{cnotice("notfound", "info", "No one found for “Lea Sampolna”", "Check the spelling, or ask for the application code on their phone (Home screen). Walk-ins apply online first, then pay.")}
{cnotice("round", "warn", "Applied for Schedule 3, not open yet", "Schedule 3 payments start Apr 11. Ask them to come back then, or move to Schedule 2 in their app.")}
{cnotice("cpaused", "bad", "Payments paused by Ana R. at 2:10 PM", "You can’t record payments right now. Ask the admission office before taking any money.")}
{cnotice("waived", "info", "Fee waived", "Hanna S. Mamalo’s fee was waived by the admission office. Nothing to collect.")}
<div class="cform"><span class="clabel">Payment for</span>
<div class="cperson"><div class="thumb cphoto">2×2 photo</div><div><b>Lea M. Sampulna</b><span class="mono">APP-27-10422</span><span>BSEd Mathematics · Kalamansig</span><span class="muted">Schedule 2 · Freshman</span></div></div>
<div class="camount"><span>Amount</span><b>₱275.00</b></div>
<div class="fld"><label for="rcv">Received</label><div class="money"><span>₱</span><input id="rcv" inputmode="decimal" value="500.00"></div>
<div class="quick">""" + "".join(f'<a class="btn sm{" on" if v == 500 else ""}" href="#">{t}</a>' for v, t in QUICK_CASH) + f"""</div></div>
<div class="cchange"><span>Change</span><b>₱225.00</b></div>
<div class="fld"><label for="or">Official receipt no.</label><input id="or" class="orno" inputmode="numeric" value="0048214"><small class="muted">Next in your booklet</small></div>
<div class="fld"><label>Paid with</label><div class="seg"><span class="on">Cash</span><span>Other (GCash at the counter)</span></div></div>
<a class="btn primary xl" href="#done">Record payment <kbd>Enter</kbd></a></div>
<div class="cdone" id="done"><span class="clabel">Paid · Lea M. Sampulna</span>
<div class="camount"><span>Examinee no.</span><b class="mono">500231</b></div>
<div class="kv"><span>OR no.</span><b class="mono">0048214</b><span>Received</span><b>₱500.00 cash · change ₱225.00</b></div>
<p class="ctell">Tell the student: check the app for your exam slot.</p>
<div class="cdone-acts">{btn("Print receipt copy", "#")}<a class="btn primary" href="#">Next person <kbd>Esc</kbd></a></div></div>
</section>""",
        states=[("done", "Recorded"), ("paid", "Already paid"), ("orused", "OR already used"), ("notfound", "Not found"), ("round", "Wrong schedule"), ("waived", "Fee waived"), ("cpaused", "Payments paused")])

PAID = [("APP-27-10398", "Ricky P. Ulangkaya", "0048213", "Cash", "Today 9:41", "Isulan counter 1", "500230"), ("APP-27-10377", "Joy M. Dalumpines", "0048212", "Cash", "Today 9:12", "Isulan counter 1", "500229"),
        ("APP-27-10361", "Norhana P. Sali", "0048211", "GCash at counter", "Today 8:47", "Isulan counter 1", "500228"), ("APP-27-10342", "Jomar P. Abdullah", "0048190", "Cash", "Today 9:05", "Isulan counter 2", "500215")]


PAID_TABLE = table(["Applicant", "OR no.", "Paid with", "When", "Where", "Examinee no.", ""], sortable=("Applicant", "OR no.", "When"), active=("When", "desc"), rows=[
    (two(n, a), f'<span class="mono">{o}</span>', m, w, c, f'<span class="mono">{e}</span>', '<span class="act">' + btn("Reprint receipt", "#") + "</span>") for a, n, o, m, w, c, e in PAID])

cashier("paid", "Paid", f"""<div class="pagehead"><div><h1>Paid</h1><p class="muted">36 today at Isulan counter 1 · ₱9,900</p></div><div class="pacts">{btn("Print list")}{btn("Export (Excel)", "../admin/exports.html#queued")}</div></div>
{list_page(stabs([("Today", "36"), ("This schedule", "3,976")]), filters("Name, OR no. or examinee no.", [("Paid with", ["Any way", "Cash", "GCash at counter", "Check"])]), PAID_TABLE, pager(1, 25, "36"))}""", tab="paid")

DAYS = [(w, c, r * 50, t) for c, w, r, t, st in SLOTS2 if st != "Closed"]
ROOMS = [("Isulan", "Sat, Apr 25", "Main Building · Room 1", 50, 50), ("Isulan", "Sat, Apr 25", "Main Building · Room 4", 50, 50), ("Isulan", "Sat, Apr 25", "Engineering · ENG 201", 45, 45), ("ACCESS, Tacurong", "Sat, Apr 25", "CTE · Room 12", 50, 46), ("ACCESS, Tacurong", "Sun, Apr 26", "CTE · Room 12", 50, 18)]
PROGS = [("BS Information Technology", "ACCESS, Tacurong", "Open"), ("BS Nursing", "ACCESS, Tacurong", "Open"), ("BS Civil Engineering", "Isulan", "Open"), ("BS Criminology", "Isulan", "Open"), ("BS Midwifery", "Isulan", "Not offered this school year"), ("BS Agriculture", "Tacurong", "Open"), ("BS Fisheries", "Palimbang", "Open")]
cashier("info", "Info", f"""<div class="pagehead"><div><h1>Info for applicants</h1><p>What people ask at the counter. Read-only.</p></div><div class="pacts"><input class="search" placeholder="Search programs, campuses, rooms" style="width:320px"></div></div>
<div class="kpis cstats"><div class="kpi"><span>Paid today, this counter</span><b>36</b><small>₱9,900</small></div><div class="kpi"><span>Paid this schedule</span><b>3,976</b></div><div class="kpi"><span>Waiting for payment</span><b>790</b></div><div class="kpi"><span>Seats left this schedule</span><b>801</b><small>Isulan Sat is full</small></div></div>
<div class="infogrid"><div class="panel"><h2>Key dates · Schedule 2</h2><div class="kv"><span>Registration</span><span>Mar 1 – Apr 10</span><span>Pay by</span><span>Apr 10</span><span>Exam days</span><span>Sat, Apr 25 and Sun, Apr 26</span><span>Report by</span><span>7:30 AM · exam starts 8:00 AM</span><span>Results</span><span>May 15</span><span>Next schedule</span><span>Schedule 3 · exam May 30</span></div></div>
<div class="panel"><h2>Fee and what to bring</h2><div class="kv"><span>Exam fee</span><span>₱275.00 (waivers only through the admission office)</span><span>To apply</span><span>Online at sksu-tpt.com: a 2×2 ID photo</span><span>Exam day</span><span>Pencil No. 2 with eraser, permit, school ID or any valid ID, official receipt if paid here</span></div></div></div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>Exam days and seats left</h2></div>{table(["Day", "Campus", "Seats", "Left", ""], [(d, c, f"{taken:,} of {cap:,}", f'<b class="mono">{cap - taken}</b>', B("bad", "Full") if cap == taken else (B("warn", "Nearly full") if cap - taken < 60 else "")) for d, c, cap, taken in DAYS])}</div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>Rooms</h2></div>{table(["Campus", "Day", "Room", "Seats", "Taken", "Left"], [(c, d, r, cap, t, f'<b class="mono">{cap - t}</b>') for c, d, r, cap, t in ROOMS])}</div>
<div class="panel" style="padding:0;gap:0"><div class="head" style="padding:12px 16px"><h2>Programs</h2></div>{table(["Program", "Campus", "This school year"], [(n, c, B("ok", st) if st == "Open" else B("gray", st)) for n, c, st in PROGS])}</div>""", tab="info")

board("CASHIER-JOURNEY-MOCKUP.html", "Cashier: one counter, one fee",
      "A cashier records that the exam fee was paid: OR number, amount, who and when. Cash handling and remittance stay in the university’s own accounting. Click any screen to open it.",
      [("Take a payment", [(D, "cashier/console.html", "2", "Counter", "Search, fixed fee, OR no., Enter."),
                           (D, "cashier/console.html#done", "2b", "Paid", "Print OR copy, next person.", True),
                           (D, "cashier/console.html#paid", "2c", "Already paid", "", True), (D, "cashier/console.html#orused", "2d", "OR already used", "", True),
                           (D, "cashier/console.html#notfound", "2e", "Not found", "", True), (D, "cashier/console.html#round", "2f", "Wrong schedule", "", True),
                           (D, "cashier/console.html#waived", "2g", "Fee waived", "", True)]),
       ("During the day", [(D, "cashier/info.html", "2i", "Info for applicants", "Programs, exam days, seats, rooms, dates, fee."), (D, "cashier/paid.html", "3", "Paid", "Today by default; reprint, export to match the OR booklet."), (D, "admin/cashier.html", "4", "Admin sees every counter", "")])],
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
    ("/admin/examinations", "admin/examinations, examination/*", "admin/schedules.html"),
    ("/admin/manage-examination/{id}/applications/slots", "manage-examination/slot, manage-slot", "admin/exam-slots.html · docs/seat-plan.html"),
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
    ("Cashier", ["cashier/console.html", "cashier/paid.html", "cashier/info.html"]),
    ("Public", ["public/landing.html", "public/login.html", "public/staff-login.html", "public/verify.html", "public/privacy.html", "public/error.html"]),
    ("Applicant (phone)", ["applicant/splash.html", "applicant/welcome-1.html", "applicant/welcome-2.html", "applicant/welcome-3.html"] + [f"applicant/{k}.html" for k, _ in FLOW]),
    ("Emails and printouts", ["docs/sms.html", "docs/email-approved.html", "docs/email-rejected.html", "docs/email-results.html", "docs/permit-pdf.html", "docs/result-pdf.html", "docs/seat-plan.html"]),
    ("Proctor (phone)", ["proctor/rooms.html", "proctor/checkin.html", "proctor/summary.html"]),
    ("Admin", [f"admin/{k}.html" for k in ["dashboard", "setup", "report-hometown", "search", "support", "support-ticket", "messages", "email", "system", "landing", "survey", "survey-results", "chair", "rooms", "cashier", "setup-1", "setup-2", "setup-3", "setup-4", "setup-5", "applications", "applicant", "payments", "schedules", "exam-slots", "checkin", "scores", "results", "result-detail", "reports", "report-view", "exports", "campuses", "staff", "audit", "account"]]),
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
<div class="toplinks"><a href="ADMIN-FLOW.html"><b>Admin flow diagram</b><span>Setup to results with arrows; click any step</span></a><a href="ADMIN-JOURNEY-MOCKUP.html"><b>Admin journey</b><span>The whole school year in order, every form and state</span></a><a href="APPLICANT-JOURNEY-MOCKUP.html"><b>Applicant journey</b><span>Public page to result, on a phone</span></a><a href="PROCTOR-JOURNEY-MOCKUP.html"><b>Proctor journey</b><span>Exam day at the door</span></a></div>
<section><h2 style="margin-bottom:10px">Walk a flow</h2><div style="display:flex;gap:8px;flex-wrap:wrap">{flow_links}</div></section>
{grid}
<section><h2 style="margin-bottom:10px">Coverage: every tptv3 route and view</h2><div class="mapt">{maptable}</div></section>
<section><h2 style="margin-bottom:10px">Interaction rules</h2>{table(["When you need to…", "Use", "Example"], [
    ("Look at one record without losing the list", "Side drawer", '<a href="admin/applications.html#view">View an applicant</a>'),
    ("Pick one of several actions on a row", "··· menu; destructive item last, in red", '<a href="admin/applications.html#menu">Row menu</a>'),
    ("Change 1 to 6 fields", "Modal", '<a href="admin/applicant.html#edit">Edit details</a>'),
    ("Fill a long form or several sections", "Full page", '<a href="admin/applicant.html">Applicant record</a>'),
    ("Do steps that depend on the one before", "Stepper", '<a href="admin/setup-1.html">New school year</a> · <a href="admin/scores.html">Scores</a> · applicant registration'),
    ("Delete, cancel, release or send to many", "Confirm dialog that says what happens", '<a href="admin/results.html#release">Release results</a>'),
    ("Confirm something worked", "Toast, 5 seconds", '<a href="admin/exam-slots.html#assigned">Seats assigned</a>'),
    ("Explain a field or step", "Grey hint under it; ? tooltip for rare cases", '<a href="admin/setup-1.html">School year basics</a>')])}</section>
<section><h2 style="margin-bottom:10px">Chart choices</h2>{table(["Question", "Chart", "Why", "Where"], [
    ("How are sign-ups going?", "Line with the area filled", "A trend over days; the line shows direction at a glance", '<a href="admin/dashboard.html">Dashboard</a>'),
    ("Where do applicants drop off?", "Funnel of horizontal bars", "Ordered stages; the drop between them is the point", '<a href="admin/reports.html">Reports</a>'),
    ("Which programs are most wanted?", "Horizontal bars, sorted", "Long names fit; easy to compare lengths", '<a href="admin/reports.html">Reports</a>'),
    ("How did scores spread?", "Histogram with the 500 line", "A distribution; bins match the 50-point stanine bands", '<a href="admin/reports.html">Reports</a>'),
    ("How many seats are left?", "Small progress meter per exam slot", "One share per row; a chart would be noise", '<a href="admin/exam-slots.html">Exam slots</a>'),
    ("Payments waiting, approved with no seat", "Plain number tile", "One number to act on; a chart adds nothing", '<a href="admin/dashboard.html">Dashboard</a>'),
    ("Pie charts", "Not used", "Hard to compare slices; bars say the same more clearly", "—")])}</section>
<section><h2 style="margin-bottom:10px">Admin features added</h2><div class="grid">{"".join(f'<a href="{h}"><b>{t}</b><span class="muted">{d}</span></a>' for t, d, h in [
    ("Global search", "Press / anywhere for names, numbers, references", "admin/search.html"),
    ("Bulk actions", "Remind, auto-seat or export many at once", "admin/applications.html#bulk"),
    ("Duplicate detector", "Same name + birth date or mobile; a flag only, no merge", "admin/applications.html#dupes"),
    ("Auto seat assignment", "Preview, then assign", "admin/exam-slots.html#auto"),
    ("Messages and blasts", "Templates, email + SMS, cost shown first", "admin/messages.html"),
    ("School year setup wizard", "Copy last school year, 5 steps", "admin/setup-1.html"),
    ("Score import checks", "Not registered, duplicate, out-of-range and missing rows before approval", "admin/scores.html"),
    ("Scheduled release", "Pre-built pages so release day stays fast", "admin/results.html"),
    ("Activity log", "Every change: who, what, when", "admin/audit.html"),
    ("Role permissions", "Fixed roles, clear matrix", "admin/staff.html"),
    ("Proctor offline check-in", "Phones work without signal", "proctor/checkin.html")])}</div></section>
<a href="design-system.html">Design system →</a></div>""")

doc("design-system.html", "Design system", f"""<div class="idx"><div class="crumbs"><a href="index.html">All pages</a></div>
<header><img src="assets/sksu-seal.png" alt="SKSU seal"><div><h1>SKSU TPT design system</h1><span class="muted">Colours from the SKSU seal (tptv3 public/images/sksu1.png). Layout rules follow our v2 admin and app patterns. Light mode.</span></div></header>
<section class="panel"><h2>Colour</h2><div class="sw">{''.join(f'<div><i style="background:{c}"></i><b class="ink">{n}</b><span class="mono muted">{c}</span><span class="muted">{u}</span></div>' for c, n, u in [("#009A3C", "SKSU green", "brand"), ("#007A30", "Button green", "white text 5.4:1"), ("#007CC2", "SKSU blue", "charts, links"), ("#FFFF00", "Seal yellow", "small accents only"), ("#DA251C", "Seal red", "reserved"), ("#F6F8F6", "Panel", "sidebar, table heads")])}</div>
<div style="display:flex;gap:6px;flex-wrap:wrap">{B("gray", "Draft")}{B("warn", "In review")}{B("ok", "Approved")}{B("info", "Exam slot picked")}{B("ok", "Present")}{B("warn", "Sent back")}{B("bad", "Absent")}{B("ok", "Scored")}</div></section>
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
# Empty the folder rather than delete it, so an open Explorer/VS Code window can't block the rebuild.
OUT.mkdir(exist_ok=True)
for item in OUT.iterdir():
    shutil.rmtree(item) if item.is_dir() else item.unlink()
(OUT / "assets").mkdir()
(OUT / "assets" / "style.css").write_text("".join((TOOLS / f).read_text(encoding="utf-8") for f in ("base.css", "theme.css", "theme-extra.css", "theme-app.css", "theme-admin.css", "theme-calm.css", "theme-clean.css", "theme-phone.css")), encoding="utf-8")
shutil.copyfile(TOOLS / "sksu-seal.png", OUT / "assets" / "sksu-seal.png")
(OUT / "docs").mkdir(parents=True, exist_ok=True)
shutil.copyfile(TOOLS / "tpt-scores-template.csv", OUT / "docs" / "tpt-scores-template.csv")
shutil.copyfile(TOOLS / "tpt-scores-template.xlsx", OUT / "docs" / "tpt-scores-template.xlsx")
for extra in ("seal-faint.png", "seal-white.png", "campus-duo.jpg"):
    shutil.copyfile(TOOLS / extra, OUT / "assets" / extra)
shutil.copyfile(TOOLS / "admin-flow.html", OUT / "ADMIN-FLOW.html")
for path, html in PAGES.items():
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")
print(f"wrote {len(PAGES)} pages to {OUT}")
