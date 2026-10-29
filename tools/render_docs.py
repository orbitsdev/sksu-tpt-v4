"""Render docs/*.md to readable HTML pages (Markdown and Mermaid rendered in the browser)."""
import json
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · SKSU TPT v4</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@500&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#f4f8f5;color:#27302b;font:16px/1.65 Geist,"Segoe UI",system-ui,sans-serif}}
header{{background:linear-gradient(135deg,#062e19,#0b4d2c 45%,#006b34);color:#fff;padding:28px 24px;box-shadow:inset 0 -3px 0 #f2c200}}
header div{{max-width:920px;margin:0 auto;display:flex;gap:14px;align-items:center}}header img{{width:52px;height:52px;background:#fff;border-radius:99px}}
header a{{color:#f2c200;font-size:14px}}
nav.toc{{max-width:920px;margin:20px auto 0;padding:0 24px;font-size:14px}}nav.toc a{{color:#006b34;margin-right:12px;white-space:nowrap}}
main{{max-width:920px;margin:20px auto 60px;background:#fff;border:1px solid #e3ebe6;border-radius:14px;padding:32px 40px}}
h1{{font-size:30px;margin:0 0 8px}}h2{{margin-top:44px;padding-top:12px;border-top:1px solid #e3ebe6;color:#0b4d2c}}h3{{color:#13261b}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0;display:block;overflow-x:auto}}th,td{{border:1px solid #e3ebe6;padding:8px 10px;text-align:left;vertical-align:top}}th{{background:#f6f9f7}}
code{{font:13px "Geist Mono",monospace;background:#f1f5f2;padding:1px 5px;border-radius:4px}}pre{{background:#f6f9f7;padding:14px;border-radius:10px;overflow-x:auto}}
.mermaid{{background:#fff;text-align:center;margin:16px 0}}
@media (max-width:700px){{main{{padding:20px}}}}
</style>
</head>
<body>
<header><div><img src="../assets/brand/sksu_seal.png" alt="SKSU seal"><div><b>SKSU TPT v4 · {title}</b><br><a href="PRD.html">PRD and flows</a> · <a href="SCOPE-CHECK.html">Scope check</a> · <a href="FORMS-AND-PAYMENTS.html">Forms and payments</a> · <a href="RESULTS-IMPORT.html">Results import</a> · <a href="../mockups/index.html">Mockups</a></div></div></header>
<nav class="toc" id="toc"></nav>
<main id="doc"></main>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs";
const md = {md};
const doc = document.getElementById("doc");
doc.replaceChildren(...new DOMParser().parseFromString(DOMPurify.sanitize(marked.parse(md)), "text/html").body.childNodes);
doc.querySelectorAll("pre code.language-mermaid").forEach(c => {{ const d = document.createElement("div"); d.className = "mermaid"; d.textContent = c.textContent; c.parentElement.replaceWith(d); }});
const toc = document.getElementById("toc");
doc.querySelectorAll("h2").forEach((h, i) => {{ h.id = "s" + i; const a = document.createElement("a"); a.href = "#s" + i; a.textContent = h.textContent; toc.appendChild(a); }});
mermaid.initialize({{ startOnLoad: false, theme: "neutral" }});
await mermaid.run({{ querySelector: ".mermaid" }});
</script>
</body>
</html>
"""

for name, title in [("PRD", "PRD and flows"), ("SCOPE-CHECK", "Scope check"), ("FORMS-AND-PAYMENTS", "Forms and payments"), ("RESULTS-IMPORT", "Results import"), ("UI-RULES", "UI rules"), ("CHANGES", "Changes"), ("RESULTS-RELEASE", "Results release plan")]:
    md = (DOCS / f"{name}.md").read_text(encoding="utf-8")
    (DOCS / f"{name}.html").write_text(PAGE.format(title=title, md=json.dumps(md).replace("</", "<\\/")), encoding="utf-8")
print("rendered")
