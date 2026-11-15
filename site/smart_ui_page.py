"""The Smart UI page (/smart-ui/), its scripted demo, the home page's compact demo, and the renderer demo (/smart-ui/demo/).

Owner direction, 2026-11-14 (_coordination/plans/2026-11-13-smart-ui-spec.md, sections 10 and 11): a page that shows every kind
of answer and how it is built, with a demo that is scripted visuals only (no backend), ported from the approved sketch onto the
site's brand system. It must feel built live: the tool-call chip, the outline, values filling as the data lands, the sentence,
and the lanes beside it. The demo is site/static/smart-ui-live.js and smart-ui-live.css; this module writes its scenarios as
JSON next to it. The Fernhollow scenarios are read from examples/smart-ui-fernhollow (its data, its prepared parts, its recorded
answers and the consequences its server states), so the page cannot drift from the example. Every count is read from the
repository at build time. "Different products, different answers" reads evals/smart-ui/use-cases.json and draws nothing when it
is missing. The older renderer demo (examples/smart-ui-chat, the real <od-surface> in a same-origin iframe) is still built at
/smart-ui/demo/ and linked from the page; build.py's vercel_json() lets only it be framed, by this site.

build.py calls add() for the page and preview() for the home page's section.
"""
import datetime
import hashlib
import html
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC = ROOT / "site" / "static"
SKILL = ROOT / "skills" / "opendesigner-smart-ui"
EXAMPLE = ROOT / "examples" / "smart-ui-chat"
FERN = ROOT / "examples" / "smart-ui-fernhollow"
USE_CASES = ROOT / "evals" / "smart-ui" / "use-cases.json"
LIB = ROOT / "skills" / "opendesigner" / "assets" / "library" / "components"
DOCS = ROOT / "site" / "docs"
esc = html.escape
PATH = "/smart-ui/"
DEMO = PATH + "demo/"
TITLE = "Smart UI"
H1 = "Generative UI for your chatbot, in your own design system"
SEO_TITLE = H1
DESCRIPTION = ("Add generative UI to your chatbot with your own design system. Watch a recorded answer build: the outline first, "
               "then values as the data lands.")
# the questions on /docs/faq/ this page repeats (word for word, so the two never disagree)
FAQ = ["What is generative UI, and how do I make it match my design system?", "How do I add generative UI to a chatbot I already have?",
       "Does the model write the interface code for every answer?", "Can my chatbot answer with my own components instead of text?"]
VER = ""
# the systems the renderer demo can switch between: (file in the demo, label, source tokens.css)
SYSTEMS = [("orvell", "Orvell Travel", EXAMPLE / "opendesigner/build/css/tokens.css"),
           ("devtool-dense", "Devtool Dense", ROOT / "examples/devtool-dense/build/css/tokens.css"),
           ("consumer-playful", "Consumer Playful", ROOT / "examples/consumer-playful/build/css/tokens.css")]
TONE = {"warning": "warn", "success": "ok", "danger": "bad", "info": "info", "accent": "accent"}


def section(md, heading):
    """The body of one '## heading' section of a Markdown file."""
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    return m.group(1).strip() if m else ""


def table_rows(block):
    rows = [ln.strip().strip("|").split("|") for ln in block.splitlines() if ln.startswith("|")]
    return [[c.strip() for c in r] for r in rows[2:]]  # skip the header and the --- row


def lib_name(slug):
    return json.loads((LIB / slug / "meta.json").read_text())["name"]


def facts():
    s = json.loads((SKILL / "assets/set.json").read_text())
    groups = [g for g in s["groups"] if g != "domain"]
    cases = json.loads((SKILL / "assets/fixtures/validator/cases.json").read_text())["cases"]
    concept = (DOCS / "smart-ui.md").read_text()
    adapters = (DOCS / "smart-ui-adapters.md").read_text()
    steps = re.findall(r"^\d+\. \*\*(.+?)\.\*\* (.+)$", section(concept, "How an answer becomes interface"), re.M)
    rules = table_rows(section(concept, "The rules it keeps"))
    where = table_rows(adapters.split("\n## ")[0])
    untried = re.findall(r"^- (.+)$", section(adapters, "What we haven't tried"), re.M)
    assert len(steps) == 5 and rules and where and untried, "smart_ui_page: a docs section it reads has moved (site/docs/smart-ui*.md)"
    by_group = {g: [(c["slug"], lib_name(c["slug"]), c["as"]) for c in s["components"] if c["group"] == g] for g in s["groups"]}
    library = sum(1 for d in LIB.iterdir() if (d / "meta.json").exists())
    templates = json.loads((FERN / "opendesigner/smart-ui/templates.json").read_text())["templates"]
    return {"library": library, "parts": len(s["components"]), "groups": groups, "group_what": s["groups"], "by_group": by_group,
            "cases": len(cases), "steps": steps, "rules": rules, "where": where, "untried": untried, "templates": templates}


# ---------------------------------------------------------------- the scripted demo's scenarios
def day(iso, year=True):
    d = datetime.date.fromisoformat(iso)
    return f"{d:%A} {d.day} {d:%B}" + (f" {d.year}" if year else "")


def short(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%b} {d.year}"


def warns(fn):
    """The consequence the Fernhollow server states for one change (@warns above its def), so the demo says what the app says."""
    src = (FERN / "server.py").read_text()
    m = re.search(r'@warns\("([^"]+)"\)(?:\n@[^\n]+)*\ndef ' + fn + r"\(", src)
    assert m, f"smart_ui_page: no @warns for {fn} in examples/smart-ui-fernhollow/server.py"
    return m.group(1)


def lanes(data, ui, words, fallback=False):
    """The three lanes. fallback: no prepared part covers it, so the model writes the part (then it is checked like any other)."""
    return {"data": data, "ui": ui, "text": [["Writing the card and a sentence" if fallback else "Writing a sentence", words * 26 + (700 if fallback else 0)]]}


def fernhollow():
    d = json.loads((FERN / "data.json").read_text())
    rec = json.loads((FERN / "recorded.json").read_text())["turns"]
    f = next(x for x in d["fines"] if x["status"] == "Unpaid")
    card = d["resident"]["card"]
    pay = f["discounted_amount"] if d["today"] <= f["discount_until"] else f["amount"]
    say_fine = (f"You have one unpaid fine, {f['reference']}. If you pay by {day(f['discount_until'], False)}, it costs "
                f"{f['discounted_amount']} instead of {f['amount']}.")
    fine = {"q": "Do I have any fines?", "chip": "Fine card, ready-made", "part": "KeyFacts", "prepared": True, "say": say_fine,
            "lanes": lanes([["Fetching your fines", 420]], [["Matching a ready-made card", 1], ["Drawing its outline", 2], ["Filling it in", 4], ["Checking it", 4]], len(say_fine.split())),
            "view": {"kind": "facts", "title": "Unpaid parking fine", "sub": f"Vehicle {f['vehicle']}", "facts": [
                {"label": "Reference", "value": f["reference"], "w": "40%"},
                {"label": "Date", "value": f"{day(f['date'])}, {f['time']}"},
                {"label": "Place", "value": f["location"], "w": "80%"},
                {"label": "Reason", "value": f["contravention"], "w": "90%"},
                {"label": "Full amount", "value": f["amount"], "w": "30%"},
                {"label": f"Pay by {day(f['discount_until'], False)}", "value": f["discounted_amount"], "tone": "accent", "w": "30%",
                 "note": f"The lower amount ends on {day(f['discount_until'], False)}. After that it is {f['amount']}."},
                {"label": "Challenge by", "value": day(f["can_challenge_until"]), "w": "50%"},
                {"label": "Status", "value": f["status"], "tone": "warn", "w": "25%"}],
                "action": {"label": f"Pay {pay}", "after": "Paid", "approval": {
                    "kind": "approval", "title": f"Pay notice {f['reference']}", "details": [
                        {"label": "Amount", "value": pay}, {"label": "Paid with", "value": card}],
                    "warn": warns("pay_fine"), "cancel": "Not now", "approve": f"Pay {pay}", "pending": "Paying", "done": "Paid",
                    "toast": f"{pay} paid. Notice {f['reference']} is closed"}}}}
    a = rec["Where is my application?"]
    ps = a["answer"][0]["createSurface"]["components"][0]
    app = {"q": "Where is my application?", "chip": "Progress card, ready-made", "part": "ProgressStatus", "prepared": True, "say": a["text"],
           "lanes": lanes([["Fetching your application", 380]], [["Matching a ready-made card", 1], ["Drawing its outline", 2], ["Filling it in", 3], ["Checking it", 3]], len(a["text"].split())),
           "view": {"kind": "progress", "title": ps["title"], "status": ps["status"], "tone": TONE[ps["tone"]],
                    "steps": [{"label": s["label"], "state": s["state"], "time": s.get("time", "")} for s in ps["steps"]]}}
    r = rec["Renew my parking permit"]
    ap = r["answer"][0]["createSurface"]["components"][0]
    opt = d["renewal"]["options"][0]
    renew = {"q": "Renew my parking permit", "chip": "Approval card", "part": "ApprovalPrompt", "prepared": False, "say": r["text"],
             "lanes": lanes([["Fetching your permit", 260], ["Fetching the renewal price", 300]], [["Picking an approval card", 1], ["Drawing its outline", 2], ["Filling it in", 3], ["Checking it says what happens", 5]], len(r["text"].split()), fallback=True), "fallback": True,
             "view": {"kind": "approval", "title": ap["title"], "summary": ap.get("summary", ""),
                      "details": [{"label": x["label"], "value": x["value"]} for x in ap["details"]], "warn": warns("renew_permit"),
                      "cancel": ap["cancel"]["label"], "approve": ap["approve"]["label"], "pending": "Paying", "done": "Renewed",
                      "toast": f"Permit renewed for {opt['length']}"}}
    o = rec["When is the Hollow Lane office open?"]
    office = {"q": "When is the Hollow Lane office open?", "chip": "Answering in text", "part": None, "prepared": False, "say": o["text"],
              "lanes": lanes([["Fetching the office hours", 240]], [["No card needed: a sentence will do", 1]], len(o["text"].split()))}
    return {"id": "fernhollow", "label": "Fernhollow council", "tab": "Council services",
            "sub": "Recorded answers", "scenarios": [fine, app, renew, office]}


def design_review():
    """The sketch's design-review assistant (an invented product with invented numbers), on the brand system."""
    names = {"AuditFindings": "Findings card, ready-made", "KpiStrip + BarChart": "Numbers and bars, ready-made",
             "Recommendations": "Part suggestions, ready-made", "ApprovalPrompt": "Approval card", None: "Answering in text"}

    def sc(q, part, say, data, ui, view=None, prepared=True, fallback=False):
        return {"q": q, "chip": names[part], "part": part, "prepared": prepared, "fallback": fallback, "say": say, "lanes": lanes(data, ui, len(say.split()), fallback), **({"view": view} if view else {})}
    std = lambda fill: [["Matching a ready-made card", 1], ["Drawing its outline", 2], ["Filling it in", fill], ["Checking it", 4]]
    return {"id": "review", "label": "Design review assistant", "tab": "Design review",
            "sub": "Recorded answers", "scenarios": [
        sc("Review my pricing page", "AuditFindings",
           "Your pricing page follows the system in most places. Two things break it, and one is worth a look.",
           [["Reading 14 files", 260], ["Measuring colours and spacing", 420], ["Comparing with your tokens", 380]], std(3),
           {"kind": "findings", "title": "Pricing page, checked against your system", "summary": "5 checks: 3 pass, 1 to look at, 1 broken", "rows": [
               {"tone": "ok", "label": "Pass", "text": "Colours all come from tokens"},
               {"tone": "ok", "label": "Pass", "text": "Body text contrast is 7.2 to 1"},
               {"tone": "ok", "label": "Pass", "text": "Buttons use one corner radius"},
               {"tone": "warn", "label": "Look", "text": "Plan cards sit 14px apart; the scale has 12 and 16", "fix": "Use 16px"},
               {"tone": "bad", "label": "Broken", "text": "The “Most popular” label is cut off at 320px wide", "fix": "Let it wrap"}]}),
        sc("How much of my code uses the tokens?", "KpiStrip + BarChart",
           "About two thirds of your values come from tokens. Shadows are the weak spot.",
           [["Scanning 54 files", 340], ["Counting token uses", 300], ["Grouping by kind", 200]], std(4),
           {"kind": "metrics", "title": "Token use in your code", "kpis": [
               {"label": "Values checked", "value": "1,900"}, {"label": "From tokens", "value": "1,254"}, {"label": "Typed by hand", "value": "646"}],
            "bars": [{"label": "Colours", "pct": 82}, {"label": "Spacing", "pct": 71}, {"label": "Type sizes", "pct": 64},
                     {"label": "Corners", "pct": 58}, {"label": "Shadows", "pct": 19, "tone": "bad"}]}),
        sc("Which parts fit a settings page?", "Recommendations",
           "Three library parts fit a settings page. All three already use your tokens.",
           [["Searching the library", 300], ["Ranking by fit", 260]], std(2),
           {"kind": "cards", "title": "Parts for a settings page", "cards": [
               {"name": "Settings switches", "text": "On and off settings, each with a plain explanation."},
               {"name": "Member list", "text": "People, roles and pending invites."},
               {"name": "Save bar", "text": "Unsaved changes, with save and discard."}]}),
        sc("Make the corners rounder", "ApprovalPrompt",
           "I can raise the corner radius one step. This changes your system, so it needs your yes.",
           [["Reading your radius tokens", 160], ["Finding what would change", 320]],
           [["Picking an approval card", 1], ["Drawing its outline", 2], ["Filling it in", 2], ["Checking it says what happens", 4]],
           {"kind": "approval", "title": "Change the corner radius", "details": [
               {"label": "Controls", "value": "12px to 16px"}, {"label": "Containers", "value": "16px to 20px"}, {"label": "Affects", "value": "38 parts on 9 screens"}],
            "warn": "This changes every screen that uses these tokens.", "cancel": "Cancel", "approve": "Change corners",
            "pending": "Changing", "done": "Changed", "toast": "Corners changed in your system", "undo": "Change undone"}, prepared=False, fallback=True),
        sc("What is a design token?", None,
           "A design token is a named design value, such as “primary text colour” or “small gap”. Your code uses the name, so changing the value in one place changes it everywhere.",
           [["Looking up the glossary", 180]], [["No card needed: a sentence will do", 1]], prepared=False)]}


def demo_html(products, mini=False):
    """A compact chat window (about 720 px) with the lanes beside it; the product switch sits outside the chat as quiet tabs."""
    data = json.dumps({"products": products}, ensure_ascii=False).replace("</", "<\\/")
    did = "sl-about-mini" if mini else "sl-about"
    switch = "" if mini else ('<div class="sl-switch" role="group" aria-label="Example product">'
                              + "".join(f'<button type="button" data-product="{p["id"]}" aria-pressed="false">{esc(p["tab"])}</button>' for p in products) + "</div>")
    lane = lambda k, t: f'<div class="sl-lane"><h3>{t}</h3><ol data-lane="{k}"></ol></div>'
    behind = "" if mini else f"""<aside class="sl-behind" aria-label="Behind the answer">
<h2>Behind the answer</h2>
<div class="sl-lanes">{lane("data", "Your agent")}{lane("ui", "Smart UI")}</div>
<p class="sl-total"><span>Ready in</span><b data-t="full">–</b></p>
</aside>"""
    chat_extra = ('<button class="sl-btn sl-replay" type="button" data-replay>Play again</button>' if mini
                  else '<div class="sl-chips" data-chips role="group" aria-label="Questions to ask"></div>')
    about = ("A recorded demo. Each answer is played from a script in the order a real one runs: the tool call that picked a part, "
             "the part's outline, values as the data lands, then the sentence. No model runs on this page, and the timings are scripted. "
             "The council and its data are invented.")
    return f"""<div class="sl"{" data-mini" if mini else ""} data-sl>
<script type="application/json">{data}</script>
<p class="vh" id="{did}">{about}</p>
{switch}<div class="sl-grid">
<div class="sl-app" aria-describedby="{did}">
<div class="sl-top"><div class="sl-who"><span class="sl-avatar" aria-hidden="true"></span><div><h2 data-who></h2><p data-sub></p></div></div></div>
<section class="sl-chat" aria-label="Conversation"><div class="sl-logwrap"><div class="sl-log" data-log tabindex="0" aria-label="Answers"></div><div class="sl-toasts" data-toasts></div></div>{chat_extra}</section>
<p class="vh" data-live aria-live="polite"></p>
</div>{behind}
</div>
</div>"""


def asset_ver():
    return hashlib.sha256((STATIC / "smart-ui-live.css").read_bytes() + (STATIC / "smart-ui-live.js").read_bytes()).hexdigest()[:10]


def assets_html():
    v = asset_ver()
    return f'<link rel="stylesheet" href="/smart-ui-live.css?v={v}">\n<script src="/smart-ui-live.js?v={v}" defer></script>\n'


def preview(b):
    """The home page's compact demo: the Fernhollow chat alone, played once when it comes into view, with a replay button."""
    return assets_html() + f'<div class="su-frame-calm su-mini">{demo_html([fernhollow()], mini=True)}</div>', ""


# ---------------------------------------------------------------- page sections
def hero(b, f):
    return f"""
<section class="h-sec h-first su-hero">
<nav class="crumb" aria-label="Breadcrumb"><a href="/">{b.NAME}</a><span aria-hidden="true">/</span><span aria-current="page">Smart UI</span></nav>
<h1 class="su-title">{esc(H1)}</h1>
<p class="h-lede su-lede">Answers drawn from your own components, filled from your data, checked before they show.</p>
<p class="su-act"><a class="btn primary" href="/docs/smart-ui-quickstart/">Add it to your assistant</a></p>
<div class="su-demo">{demo_html([fernhollow(), design_review()])}</div>
</section>
"""


# ---------------------------------------------------------------- real library components, drawn on this page
def lib_components():
    import library_page  # site/, already loaded by build.py
    return {c["slug"]: c for c in library_page.components()}, library_page.quiet


def keyfacts(title, sub, rows, action=None):
    """The library's key-facts part, filled by hand from the Fernhollow data: rows of (label, value, tone, note)."""
    items = "".join(f'<div><dt>{esc(l)}</dt><dd><span class="odl-value" data-tone="{tone or "neutral"}">{esc(v)}</span>'
                    + (f'<span class="odl-note">{esc(n)}</span>' if n else "") + "</dd></div>" for l, v, tone, n in rows)
    act = f'<div class="odl-acts"><span class="odl-act">{esc(action)}</span></div>' if action else ""
    return (f'<section class="odl-key-facts"><div class="odl-card"><header><h3>{esc(title)}</h3><p class="odl-sub">{esc(sub)}</p></header>'
            f'<dl>{items}</dl>{act}</div></section>')


def fine_facts(short_=False):
    d = json.loads((FERN / "data.json").read_text())
    f = next(x for x in d["fines"] if x["status"] == "Unpaid")
    rows = [("Reference", f["reference"], "", ""), ("Place", f["location"], "", ""), ("Full amount", f["amount"], "", ""),
            (f"Pay by {day(f['discount_until'], False)}", f["discounted_amount"], "accent", "The lower amount ends then."),
            ("Status", f["status"], "warning", "")]
    if short_:
        rows = [rows[0], rows[2], rows[3], rows[4]]
    return keyfacts("Unpaid parking fine", f"Vehicle {f['vehicle']}", rows, f"Pay {f['discounted_amount']}"), f


def frame(inner, cls=""):
    return f'<div class="su-shot {cls}"><div class="su-shot-in">{inner}</div></div>'


def build_seq_section(b, n):
    _, f = fine_facts()
    q = '<div class="sl-me">Do I have any fines?</div>'
    chip = lambda done: f'<p class="sl-call num{" done" if done else ""}"><span class="sl-dot"></span><span>Fine card, ready-made</span></p>'
    labels = ["Reference", "Full amount", "Pay by Thursday", "Status"]
    outline = ('<div class="sl-part"><div class="sl-ph"><p class="sl-pt">Unpaid parking fine</p></div><dl class="sl-facts">'
               + "".join(f'<div class="sl-fact"><dt>{l}</dt><dd><span class="sl-sk" style="width:{w}"></span></dd></div>' for l, w in zip(labels, ["60%", "40%", "40%", "30%"])) + "</dl></div>")
    filled = ('<div class="sl-part"><div class="sl-ph"><p class="sl-pt">Unpaid parking fine</p></div><dl class="sl-facts">'
              f'<div class="sl-fact"><dt>Reference</dt><dd>{esc(f["reference"])}</dd></div><div class="sl-fact"><dt>Full amount</dt><dd>{esc(f["amount"])}</dd></div>'
              f'<div class="sl-fact"><dt>Pay by Thursday</dt><dd><span class="sl-strong">{esc(f["discounted_amount"])}</span></dd></div>'
              f'<div class="sl-fact"><dt>Status</dt><dd><span class="sl-tag warn">{esc(f["status"])}</span></dd></div></dl></div>')
    steps = [("The tool call", "A prepared part is matched. No model.", q + chip(False)),
             ("The outline", "Drawn at once, before the data arrives.", q + chip(False) + outline),
             ("The data", "Values land as your agent returns them.", q + chip(True) + filled)]
    cells = "".join(f'<li><span class="sq-n num">{i + 1}</span>{frame(art, "sq-shot")}<h3>{t}</h3><p>{d}</p></li>' for i, (t, d, art) in enumerate(steps))
    return f"""
<section class="h-sec" id="building">
<div class="h-head">{b.idx(n, "Built live")}<h2 class="h-h2">An answer, in the order it arrives.</h2></div>
<ol class="sq" aria-label="Three moments of one answer">{cells}</ol>
</section>
"""


def compare_section(b, n):
    rec = json.loads((FERN / "recorded.json").read_text())["turns"]["Do I have any fines?"]["text"]
    d = json.loads((FERN / "data.json").read_text())
    f = next(x for x in d["fines"] if x["status"] == "Unpaid")
    text = (f"{rec} It was issued on {day(f['date'])} at {f['time']} on {f['location']}, for this reason: {f['contravention'].lower()}. "
            f"You can challenge it until {day(f['can_challenge_until'])}. To pay, tell me and I'll take you through it.")
    card, _ = fine_facts()
    before = f'<div class="cmp-chat"><div class="sl-me">Do I have any fines?</div><p class="sl-say">{esc(text)}</p></div>'
    after = f'<div class="cmp-chat"><div class="sl-me">Do I have any fines?</div><div class="odl-sys-su-fernhollow cmp-part">{card}</div></div>'
    return f"""
<section class="h-sec" id="compare">
<div class="h-head">{b.idx(n, "Before and after")}<h2 class="h-h2">Text, or the answer itself.</h2></div>
<div class="cmp">
<figure class="cmp-side">{frame(before)}<figcaption><b>Text only</b> The same facts in a paragraph.</figcaption></figure>
<figure class="cmp-side">{frame(after)}<figcaption><b>Smart UI</b> The fine, its status and a Pay button that asks first.</figcaption></figure>
</div>
</section>
"""


def parts_section(b, f, n):
    import library_page
    comps, quiet = lib_components()
    slugs = [c[0] for g in f["groups"] for c in f["by_group"][g]] + [c[0] for c in f["by_group"].get("domain", [])]
    tiles = []
    for slug in slugs:
        c = comps.get(slug)
        if not c:
            continue
        w = library_page.FRAME_W[c["width"]]
        tiles.append(f'<li class="th"><div class="th-view lib-fit" data-fit="{w}" inert aria-hidden="true"><div class="th-zoom odl-sys-nordic" style="width:{w}px">{quiet(c["markup"])}</div></div>'
                     f'<a class="th-name" href="/library/{slug}/">{esc(c["name"])}</a><p class="th-line">{esc(library_page.short(c))}</p></li>')
    return f"""
<section class="h-sec" id="parts">
<div class="h-head h-head-row"><div>{b.idx(n, "Every part")}<h2 class="h-h2">{len(tiles)} parts an answer can use.</h2></div>
<a class="h-link" href="/library/">The whole library {b.ARROW}</a></div>
<ul class="ths">{"".join(tiles)}</ul>
</section>
"""


SYS3 = [("su-fernhollow", "Fernhollow council", FERN / "opendesigner/build/css/tokens.css"),
        ("su-opendesigner", "OpenDesigner", ROOT / "examples/smart-ui-opendesigner/opendesigner/build/css/tokens.css")]


def systems_section(b, n):
    card, _ = fine_facts(short_=True)
    cells = "".join(f'<figure class="sys">{frame(f"<div class=odl-sys-{k}>" + card + "</div>", "sys-shot")}<figcaption>{esc(name)}</figcaption></figure>' for k, name, _ in SYS3)
    return f"""
<section class="h-sec" id="systems">
<div class="h-head">{b.idx(n, "Two systems")}<h2 class="h-h2">Same question, two design systems.</h2></div>
<div class="syss">{cells}</div>
</section>
"""


def states_section(b, n):
    comps, quiet = lib_components()
    def tile(slug, label):
        inner = f'<div class="lib-fit st-fit" inert aria-hidden="true"><div class="odl-sys-nordic st-zoom">{quiet(comps[slug]["markup"])}</div></div>'
        return f'<figure class="st">{frame(inner)}<figcaption>{label}</figcaption></figure>'
    tones = ('<div class="tones"><p class="tones-h">The data picks the colour</p><ul>'
             '<li><span class="sl-tag ok">Paid</span><span>success</span></li><li><span class="sl-tag warn">Unpaid</span><span>warning</span></li>'
             '<li><span class="sl-tag bad">Overdue</span><span>danger</span></li><li><span class="sl-tag info">In review</span><span>info</span></li></ul></div>')
    return f"""
<section class="h-sec" id="states">
<div class="h-head">{b.idx(n, "States")}<h2 class="h-h2">Loading, empty, an error, a change undone.</h2></div>
<div class="sts">{tile("skeleton-card", "Loading")}{tile("empty-state", "Empty")}{tile("error-retry", "Error, with a retry")}{tile("toast-stack", "Toasts, one with Undo")}</div>
{tones}
</section>
"""


def real_section(b, n):
    shots = [("travel", "Travel", "Flights you can book.", 668), ("fernhollow", "Council", "Your parking fines.", 996),
             ("tallyhaus", "Billing", "API use this year.", 797), ("opendesigner", "Design review", "A page checked against its system.", 1574)]
    img = lambda k, name, cap, h: f'<img src="/img/smart-ui/{k}.webp" width="1000" height="{h}" loading="lazy" alt="{esc(name)} example app: {esc(cap)}">'
    cells = "".join(f'<li class="rs">{frame(img(k, name, cap, h), "rs-shot")}<p><b>{esc(name)}</b> {esc(cap)}</p></li>' for k, name, cap, h in shots)
    return f"""
<section class="h-sec" id="screens">
<div class="h-head">{b.idx(n, "Real screens")}<h2 class="h-h2">Four products, four kinds of answer.</h2></div>
<ul class="rss" aria-label="Example apps">{cells}</ul>
</section>
"""


def part_slugs(f):
    return {c[0] for g in f["by_group"].values() for c in g} | {"key-facts", "skeleton-card", "empty-state", "error-retry", "toast-undo"}


def parts_js(f):
    """The short scripts some parts draw themselves with (a chart from its table), each scoped to its own root class."""
    comps, _ = lib_components()
    return "\n".join(f"/* {s} */\n" + comps[s]["js"].strip() for s in sorted(part_slugs(f)) if s in comps and comps[s]["js"].strip()) + "\n"


def parts_css(f):
    """/smart-ui-parts.css: the Nordic look, the three example systems scoped to a class each, and the parts this page draws."""
    import library_systems
    comps, _ = lib_components()
    looks = (STATIC / "library-systems.css").read_text()
    m = re.search(r"\.odl-sys-nordic \{.*?\n\}", looks, re.S)
    out = [m.group(0)] + [f".odl-sys-nordic{{{inner}}}" for inner in []]
    for k, _n, src in SYS3:
        decls = re.findall(r"(--ds-[a-z0-9-]+\s*:[^;]+;)", library_systems.light_block(src.read_text()))
        out.append(f".odl-sys-{k} {{" + "".join(decls) + "}")
    out += [comps[s]["css"] for s in sorted(part_slugs(f)) if s in comps]
    return "\n".join(out)


def built_section(b, f, n):
    t = f["templates"]
    pick = [x for x in t if x["action"] in ("list_fines", "application_status", "renewal_quote")]
    seen, rows = set(), []
    for x in pick:
        if x["action"] not in seen:
            seen.add(x["action"])
            rows.append(f'<li><span>{esc(x["action"])}</span><b>{esc(x["part"]["component"])}</b></li>')
    vis = [
        f'<div class="sb-file"><p class="sb-fname num">templates.json</p><ul>{"".join(rows)}</ul><p class="sb-more">{len(t)} parts for Fernhollow</p></div>',
        '<div class="sb-match"><div class="sl-me">Do I have any fines?</div><p class="sl-call done num"><span class="sl-dot"></span><span>list_fines → KeyFacts</span></p><p class="sb-note">Under 0.2 ms, no model</p></div>',
        '<div class="sl-part sb-fill"><div class="sl-fact"><dt>Full amount</dt><dd>£70.00</dd></div><div class="sl-fact"><dt>Status</dt><dd><span class="sl-tag warn">Unpaid</span></dd></div><div class="sl-fact"><dt>Challenge by</dt><dd><span class="sl-sk" style="width:70%"></span></dd></div></div>',
        '<ul class="sb-checks"><li>Every value is in the data</li><li>Every colour is a token</li><li>The colour agrees with the data</li><li>A change asks first</li></ul>',
        '<div class="sb-draw"><p class="num">&lt;od-surface&gt;</p><div class="sl-part"><p class="sl-pt">Unpaid parking fine</p><span class="sl-btn primary">Pay £35.00</span></div><p class="num">+ your tokens.css</p></div>',
    ]
    who = ["Once, with you", "Smart UI", "Code, as data lands", "Smart UI", "Your page"]
    # one line each here; the full step is on /docs/smart-ui/ (the titles come from there, so the two keep the same steps)
    lines = ["Works out which answers your product needs and binds a part to each data source. You check them.",
             "Finds the prepared part for the question in under 0.2 ms, with no model.",
             "Code fills the part as your agent's data lands. The data picks the colours.",
             "Every part is validated before it renders, including one the model wrote.",
             "`<od-surface>` draws it with your tokens, in any framework."]
    cols = "".join(f'<li class="sb-step"><span class="sb-n num">0{i + 1}</span><h3>{esc(title)}</h3><p class="sb-who num">{who[i]}</p><div class="sb-vis" aria-hidden="true">{vis[i]}</div><p>{b.inline(lines[i])}</p></li>'
                   for i, (title, _desc) in enumerate(f["steps"]))
    return f"""
<section class="h-sec" id="built">
<div class="h-head">{b.idx(n, "How it's built")}<h2 class="h-h2">Prepare once. Then match, fill, check and draw.</h2>
<p class="h-lede">The model writes the sentence. The interface comes from parts you approved, so it can't drift from your system.</p></div>
<div class="sb">
<div class="sb-bands" aria-hidden="true"><span class="sb-band sb-ahead">Ahead of time</span><span class="sb-band sb-now">For every question, while your agent fetches the data</span></div>
<ol class="sb-steps">{cols}</ol>
</div>
<div class="sb-agents"><h3 class="h-h3">Your agents, your model</h3>
<ol class="flow3"><li><b>Your data agent</b><span>Your API, documents or database</span></li><li><b>Smart UI</b><span>Matches, fills and checks the part</span></li><li><b>The screen</b><span>Your components, your tokens</span></li></ol>
<a class="h-link" href="/docs/smart-ui-quickstart/#use-your-own-agents">Use your own agents {b.ARROW}</a></div>
<p class="su-more"><a href="/docs/smart-ui/">How it works</a><a href="/docs/smart-ui-quickstart/">Add it to your assistant</a><a href="/docs/smart-ui-adapters/">Where it runs</a><a href="/smart-ui/demo/">The renderer demo</a></p>
</section>
"""


def products_section(b, n):
    """Different products, different answers: evals/smart-ui/use-cases.json, or nothing when it isn't there (no invented data)."""
    if not USE_CASES.exists():
        return ""
    u = json.loads(USE_CASES.read_text())
    ps = u.get("products") or []
    if not ps:
        return ""
    cols = []
    for p in ps:
        # at most five, in plain words: the part names and the evidence stay in the Markdown copy and use-cases.json
        kinds = [a["type"][:1].upper() + a["type"][1:] for a in p["answer_types"] if not a.get("missing")][:5]
        cols.append(f'<div class="pr"><h3>{esc(p["name"])}</h3><ul class="pr-chips">{"".join(f"<li>{esc(k)}</li>" for k in kinds)}</ul></div>')
    return f"""
<section class="h-sec" id="products">
<div class="h-head">{b.idx(n, "Different products")}<h2 class="h-h2">Different products, different answers.</h2></div>
<div class="prs">{"".join(cols)}</div>
</section>
"""


def rules_section(b, f, n):
    rows = "".join(f'<li><h3>{b.inline(r)}</h3><div><p>{b.inline(m)}</p></div></li>' for r, m in f["rules"])
    return f"""
<section class="h-sec" id="rules">
<div class="h-head">{b.idx(n, "The rules")}<h2 class="h-h2">What every answer has to pass.</h2>
<p class="h-lede">A mistake goes back to the model as an error it can fix. Nothing half-checked reaches the screen.</p></div>
<ul class="su-rules">{rows}</ul>
</section>
"""


def tested_section(b, f, n):
    cards = "".join(f'<li class="su-where"><h3>{b.inline(w)}</h3><dl><dt>How</dt><dd>{b.inline(h)}</dd><dt>Tested</dt><dd>{b.inline(t)}</dd></dl></li>'
                    for w, h, t in f["where"])
    untried = "".join(f"<li>{b.inline(x)}</li>" for x in f["untried"])
    return f"""
<section class="h-sec" id="tested">
<div class="h-head h-head-row"><div>{b.idx(n, "Where it runs")}<h2 class="h-h2">What we ran, and what we haven't yet.</h2></div>
<a class="h-link" href="/docs/smart-ui-adapters/">Where Smart UI runs {b.ARROW}</a></div>
<ul class="su-wheres">{cards}</ul>
<div class="su-untried"><h3 class="h-h3">Not tried yet</h3><ul>{untried}</ul></div>
</section>
"""


def faq_section(b, items, n):
    qa = "".join(f'<details class="qa"><summary><h3>{esc(q)}</h3></summary><div class="ans">{b.md_to_html(a)}</div></details>' for q, a in items)
    return f"""
<section class="h-sec" id="faq">
<div class="h-head h-head-row"><div>{b.idx(n, "Questions")}<h2 class="h-h2">What people ask about generative UI.</h2></div>
<a class="h-link" href="/docs/faq/">All questions {b.ARROW}</a></div>
<div class="su-faq">{qa}</div>
</section>
"""


def end_section(b, n):
    links = [("Smart UI, explained", "What it does, the rules it keeps and what you get.", "/docs/smart-ui/", "Read the concept"),
             ("Add it to your assistant", "Scope your repo, confirm the parts, prepare them, then check each answer.", "/docs/smart-ui-quickstart/", "Open the quickstart"),
             ("Where it runs", "Your own product, A2UI v1.0, and MCP Apps hosts, with what was tested in each.", "/docs/smart-ui-adapters/", "See the adapters"),
             ("The renderer demo", "A travel assistant drawn by the real renderer, in three design systems. Send it a broken answer.", DEMO, "Open the renderer")]
    cards = "".join(f'<a class="who-card" href="{u}"><h3>{t}</h3><p>{d}</p><span class="more">{l} {b.CHEVRON}</span></a>' for t, d, u, l in links)
    return f"""
<section class="h-sec su-end" id="docs">
<div class="h-head">{b.idx(n, "Read more")}<h2 class="h-h2">Try it on your own assistant.</h2>
<p class="h-lede">It needs an OpenDesigner system first. The five-question sketch takes a few minutes.</p></div>
<div class="who su-docs">{cards}</div>
</section>
"""


def faq_items(b):
    faq = (DOCS / "faq.md").read_text()
    items = dict(b.faq_items(faq.split("\n---\n", 1)[-1]))
    missing = [q for q in FAQ if q not in items]
    assert not missing, f"smart_ui_page: these questions are no longer in site/docs/faq.md: {missing}"
    return [(q, items[q]) for q in FAQ]


def markdown(b, f, faq):
    steps = "\n".join(f"{i + 1}. **{t}.** {d}" for i, (t, d) in enumerate(f["steps"]))
    rules = "\n".join(f"- **{r}**: {m}" for r, m in f["rules"])
    where = "\n".join(f"- **{w}**: {h}. Tested: {t}" for w, h, t in f["where"])
    untried = "\n".join(f"- {x}" for x in f["untried"])
    uses = "\n".join(f"- **{g}** ({f['group_what'][g]}): " + ", ".join(f"[{n}]({b.SITE_URL}/library/{sl}/)" for sl, n, _ in f["by_group"][g]) for g in f["by_group"] if f["by_group"][g])
    prods = ""
    if USE_CASES.exists():
        u = json.loads(USE_CASES.read_text())
        prods = "\n\n## Different products, different answers\n\nWhat the scope step found for three example products (invented data), on " + u.get("date", "") + ":\n\n" + "\n".join(
            f"- **{p['name']}** ({p['kind'].replace('-', ' ')}): " + "; ".join(f"{a['type']} ({a['part'] if not a.get('missing') else 'no part yet'})" for a in p["answer_types"])
            for p in u.get("products", []))
    qa = "\n\n".join(f"### {q}\n\n{a}" for q, a in faq)
    return f"""# {H1}

{DESCRIPTION}

Your assistant answers with your own components: a fine with a Pay button, an application's progress, a table you can sort. The parts are made ahead of time from your library, filled from your data and checked before they show. It comes with OpenDesigner and stays off until you ask for it. You keep your own model and agents.

The page has a recorded demo, drawn live from scripted answers (no model runs on the page): a council assistant built on the Fernhollow example, and a design-review assistant. Each answer builds in the order a real one does: the tool call, the part's outline, values as the data lands, then the sentence, with the data agent, Smart UI and the model working side by side. A hosted playground comes later.

In numbers, read from the repository: {f["parts"]} parts in {len(f["groups"])} jobs ({", ".join(f["groups"])}); {len(f["templates"])} parts prepared ahead of time for the Fernhollow example; {f["cases"]} test cases the Python and browser checks must answer the same way. Measured on the examples: the outline is on screen 1 to 3 ms after the question, and a whole Fernhollow answer takes about 1.5 to 2 seconds with Gemini Flash Lite.

## Every kind of answer

{uses}

## How it's built

{steps}

Smart UI is the UI step beside your own agents. Your page draws what each event says: call, shell, part, text, lane, done.{prods}

## The rules

{rules}

## Where it runs

{where}

Not tried yet:

{untried}

## Questions

{qa}

Read more: {b.SITE_URL}/docs/smart-ui/ · Quickstart: {b.SITE_URL}/docs/smart-ui-quickstart/ · Adapters: {b.SITE_URL}/docs/smart-ui-adapters/
"""


def demo_files(b):
    """/smart-ui/demo/: the example chat with the site's paths, its renderer, catalog, recorded turns and three systems' tokens."""
    out = b.DIST / "smart-ui" / "demo"
    (out / "tokens").mkdir(parents=True, exist_ok=True)
    for name in ("od-validate.js", "od-surface.js", "od-surface.css"):
        shutil.copy(SKILL / "assets" / name, out / name)
    shutil.copy(EXAMPLE / "opendesigner/smart-ui/catalog.json", out / "catalog.json")
    shutil.copy(EXAMPLE / "opendesigner/smart-ui/od-components.js", out / "od-components.js")
    shutil.copy(EXAMPLE / "turns.json", out / "turns.json")
    for key, _label, src in SYSTEMS:
        shutil.copy(src, out / "tokens" / f"{key}.css")
    (out / "chat.css").write_text((EXAMPLE / "chat.css").read_text() + "\n" + (STATIC / "smart-ui-demo.css").read_text())
    (out / "chat.js").write_text((STATIC / "smart-ui-demo.js").read_text())
    ver = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file())).hexdigest()[:10]
    opts = "".join(f'<option value="{DEMO}tokens/{k}.css">{esc(label)}</option>' for k, label, _ in SYSTEMS)
    page = (EXAMPLE / "index.html").read_text()
    head = (f'<title>Smart UI demo: a travel assistant with recorded answers</title>\n'
            f'<meta name="description" content="A live Smart UI demo: recorded assistant answers, checked by the validator and drawn by the real renderer in three design systems.">\n'
            f'<meta name="robots" content="noindex">\n<link rel="canonical" href="{b.SITE_URL}{DEMO}">\n'
            f'<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">\n'
            f'<link id="tokens" rel="stylesheet" href="{DEMO}tokens/orvell.css">\n'
            f'<link rel="stylesheet" href="{DEMO}od-surface.css?v={ver}">\n<link rel="stylesheet" href="{DEMO}chat.css?v={ver}">\n'
            f'<script src="{DEMO}od-components.js?v={ver}"></script>\n')
    page = re.sub(r"<title>.*?<script src=\"opendesigner/smart-ui/od-components.js\"></script>\n", lambda m: head, page, flags=re.S)
    page = re.sub(r'(<select id="system"[^>]*>).*?(</select>)', lambda m: m[1] + opts + m[2], page, flags=re.S)
    # a heading for the conversation, so the answers' own h3 headings do not skip a level (seen hidden, read by screen readers)
    page = page.replace('<main id="log"', '<h2 class="vh">Conversation</h2>\n  <main id="log"', 1)
    page = page.replace('<script type="module" src="chat.js"></script>', f'<script type="module" src="{DEMO}chat.js?v={ver}"></script>')
    assert "opendesigner/" not in page.replace(b.SITE_URL, "").replace(DEMO, ""), "smart_ui_page: a demo path was not fixed for the site"
    (out / "index.html").write_text(page)


def add(b, files, mds, paths):
    """Write /smart-ui/, its Markdown copy, /smart-ui.css, the live demo's files and the renderer demo into the build."""
    global VER
    f = facts()
    faq = faq_items(b)
    css = b.minify_css(b.corners_match_levers(b.apple_tracking((STATIC / "smart-ui.css").read_text())))
    VER = hashlib.sha256(css.encode()).hexdigest()[:10]
    # six sections (Kunal, 2026-11-16: "about 5 or 6"); the rules, where it runs and the questions live on the docs pages
    secs = [lambda n: parts_section(b, f, n), lambda n: real_section(b, n), lambda n: compare_section(b, n),
            lambda n: systems_section(b, n), lambda n: products_section(b, n), lambda n: built_section(b, f, n)]
    body, i = hero(b, f), 1
    for s in secs:
        h = s(f"{i:02d}")
        if h:  # a section with nothing to show (no use-cases.json) takes no number
            body += h
            i += 1
    ld = [b.crumbs_ld([("Smart UI", PATH)]),
          {"@context": "https://schema.org", "@type": "WebPage", "name": SEO_TITLE, "url": b.SITE_URL + PATH,
           "description": DESCRIPTION, "inLanguage": "en", "dateModified": b.TODAY,
           "about": [{"@type": "Thing", "name": "Generative UI"}, {"@type": "Thing", "name": "Design system"}],
           "isPartOf": {"@type": "WebSite", "name": b.NAME, "url": b.SITE_URL + "/"},
           "mainEntity": {"@type": "SoftwareApplication", "name": "OpenDesigner Smart UI", "applicationCategory": "DeveloperApplication",
                          "operatingSystem": "Any", "isAccessibleForFree": True, "license": "https://opensource.org/licenses/MIT",
                          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                          "isPartOf": {"@type": "SoftwareApplication", "name": b.NAME, "url": b.SITE_URL + "/"},
                          "description": "Generative UI for an assistant, made from the product's own design system: parts prepared ahead of time, filled from the app's data and checked before they render."},
           "hasPart": [{"@type": "TechArticle", "name": t, "url": b.SITE_URL + u} for t, u in
                       (("Smart UI: answers that show your interface", "/docs/smart-ui/"), ("Add Smart UI to your assistant", "/docs/smart-ui-quickstart/"),
                        ("Where Smart UI runs", "/docs/smart-ui-adapters/"))]}]
    pv = hashlib.sha256(parts_css(f).encode()).hexdigest()[:10]
    pv = hashlib.sha256((parts_css(f) + parts_js(f)).encode()).hexdigest()[:10]
    body = (f'<link rel="stylesheet" href="/smart-ui-parts.css?v={pv}">\n<link rel="stylesheet" href="/smart-ui.css?v={VER}">\n'
            f'<script src="/smart-ui-parts.js?v={pv}" defer></script>\n' + assets_html() + body)
    og = "/og/smart-ui.jpg" if (b.CACHE / "og" / "smart-ui.jpg").exists() else "/og/home.jpg"
    files["smart-ui/index.html"] = b.shell(PATH, SEO_TITLE, DESCRIPTION, body, b.load_docs(), ld, og=og, home=True,
                                          og_alt=f"Smart UI: {H1}")
    mds["smart-ui/index.md"] = markdown(b, f, faq)
    paths.append(PATH)
    (b.DIST / "smart-ui.css").write_text(css)
    (b.DIST / "smart-ui-live.css").write_text(b.minify_css(b.corners_match_levers(b.apple_tracking((STATIC / "smart-ui-live.css").read_text()))))
    (b.DIST / "smart-ui-live.js").write_text((STATIC / "smart-ui-live.js").read_text())
    (b.DIST / "smart-ui-parts.css").write_text(b.minify_css(parts_css(f)))
    (b.DIST / "smart-ui-parts.js").write_text(parts_js(f))
    (b.DIST / "img" / "smart-ui").mkdir(parents=True, exist_ok=True)
    for img in (STATIC / "smart-ui").glob("*.webp"):  # screens of the example apps, captured from their recorded answers
        shutil.copy(img, b.DIST / "img" / "smart-ui" / img.name)
    demo_files(b)
