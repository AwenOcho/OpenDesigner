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
SEO_TITLE = "Smart UI: generative UI made from your own design system"
DESCRIPTION = ("Generative UI with your own components. Watch an assistant build its answer: the part's outline first, "
               "then values as the data lands, checked before it shows.")
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
    return {"data": data, "ui": ui, "text": [["Write the part and the sentence" if fallback else "Write the sentence", words * 26 + (700 if fallback else 0)]]}


def fernhollow():
    d = json.loads((FERN / "data.json").read_text())
    rec = json.loads((FERN / "recorded.json").read_text())["turns"]
    f = next(x for x in d["fines"] if x["status"] == "Unpaid")
    card = d["resident"]["card"]
    pay = f["discounted_amount"] if d["today"] <= f["discount_until"] else f["amount"]
    say_fine = (f"You have one unpaid fine, {f['reference']}. If you pay by {day(f['discount_until'], False)}, it costs "
                f"{f['discounted_amount']} instead of {f['amount']}.")
    fine = {"q": "Do I have any fines?", "part": "KeyFacts", "prepared": True, "say": say_fine,
            "lanes": lanes([["list_fines", 420]], [["Match a prepared part", 1], ["Draw the outline", 2], ["Fill as the data lands", 4], ["Check the part", 4]], len(say_fine.split())),
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
    app = {"q": "Where is my application?", "part": "ProgressStatus", "prepared": True, "say": a["text"],
           "lanes": lanes([["application_status", 380]], [["Match a prepared part", 1], ["Draw the outline", 2], ["Fill as the data lands", 3], ["Check the part", 3]], len(a["text"].split())),
           "view": {"kind": "progress", "title": ps["title"], "status": ps["status"], "tone": TONE[ps["tone"]],
                    "steps": [{"label": s["label"], "state": s["state"], "time": s.get("time", "")} for s in ps["steps"]]}}
    r = rec["Renew my parking permit"]
    ap = r["answer"][0]["createSurface"]["components"][0]
    opt = d["renewal"]["options"][0]
    renew = {"q": "Renew my parking permit", "part": "ApprovalPrompt", "prepared": False, "say": r["text"],
             "lanes": lanes([["get_permit", 260], ["renewal_quote", 300]], [["Pick a part for the change (no model)", 1], ["Draw the outline", 2], ["Fill from the model's answer", 3], ["Check: it names the consequence", 5]], len(r["text"].split()), fallback=True), "fallback": True,
             "view": {"kind": "approval", "title": ap["title"], "summary": ap.get("summary", ""),
                      "details": [{"label": x["label"], "value": x["value"]} for x in ap["details"]], "warn": warns("renew_permit"),
                      "cancel": ap["cancel"]["label"], "approve": ap["approve"]["label"], "pending": "Paying", "done": "Renewed",
                      "toast": f"Permit renewed for {opt['length']}"}}
    o = rec["When is the Hollow Lane office open?"]
    office = {"q": "When is the Hollow Lane office open?", "part": None, "prepared": False, "say": o["text"],
              "lanes": lanes([["office_details", 240]], [["No part: a sentence answers it", 1]], len(o["text"].split()))}
    return {"id": "fernhollow", "label": "Fernhollow council", "tab": "Council services",
            "sub": "Recorded demo. An invented council and its invented data.", "scenarios": [fine, app, renew, office]}


def design_review():
    """The sketch's design-review assistant (an invented product with invented numbers), on the brand system."""
    def sc(q, part, say, data, ui, view=None, prepared=True, fallback=False):
        return {"q": q, "part": part, "prepared": prepared, "fallback": fallback, "say": say, "lanes": lanes(data, ui, len(say.split()), fallback), **({"view": view} if view else {})}
    std = lambda fill: [["Match a prepared part", 1], ["Draw the outline", 2], ["Fill from the data", fill], ["Check the part", 4]]
    return {"id": "review", "label": "Design review assistant", "tab": "Design review",
            "sub": "Recorded demo. An invented app and its invented numbers.", "scenarios": [
        sc("Review my pricing page", "AuditFindings",
           "Your pricing page follows the system in most places. Two things break it, and one is worth a look.",
           [["Read 14 files", 260], ["Measure colours and spacing", 420], ["Compare with the tokens", 380]], std(3),
           {"kind": "findings", "title": "Pricing page, checked against your system", "summary": "5 checks: 3 pass, 1 to look at, 1 broken", "rows": [
               {"tone": "ok", "label": "Pass", "text": "Colours all come from tokens"},
               {"tone": "ok", "label": "Pass", "text": "Body text contrast is 7.2 to 1"},
               {"tone": "ok", "label": "Pass", "text": "Buttons use one corner radius"},
               {"tone": "warn", "label": "Look", "text": "Plan cards sit 14px apart; the scale has 12 and 16", "fix": "Use 16px"},
               {"tone": "bad", "label": "Broken", "text": "The “Most popular” label is cut off at 320px wide", "fix": "Let it wrap"}]}),
        sc("How much of my code uses the tokens?", "KpiStrip + BarChart",
           "About two thirds of your values come from tokens. Shadows are the weak spot.",
           [["Scan 54 files", 340], ["Count token uses", 300], ["Group by kind", 200]], std(4),
           {"kind": "metrics", "title": "Token use in your code", "kpis": [
               {"label": "Values checked", "value": "1,900"}, {"label": "From tokens", "value": "1,254"}, {"label": "Typed by hand", "value": "646"}],
            "bars": [{"label": "Colours", "pct": 82}, {"label": "Spacing", "pct": 71}, {"label": "Type sizes", "pct": 64},
                     {"label": "Corners", "pct": 58}, {"label": "Shadows", "pct": 19, "tone": "bad"}]}),
        sc("Which parts fit a settings page?", "Recommendations",
           "Three library parts fit a settings page. All three already use your tokens.",
           [["Search the library", 300], ["Rank by fit", 260]], std(2),
           {"kind": "cards", "title": "Parts for a settings page", "cards": [
               {"name": "Settings switches", "text": "On and off settings, each with a plain explanation."},
               {"name": "Member list", "text": "People, roles and pending invites."},
               {"name": "Save bar", "text": "Unsaved changes, with save and discard."}]}),
        sc("Make the corners rounder", "ApprovalPrompt",
           "I can raise the corner radius one step. This changes your system, so it needs your yes.",
           [["Read the radius tokens", 160], ["Find what would change", 320]],
           [["Pick a part for the change (no model)", 1], ["Draw the outline", 2], ["Fill from the model's answer", 2], ["Check: it names the consequence", 4]],
           {"kind": "approval", "title": "Change the corner radius", "details": [
               {"label": "Controls", "value": "12px to 16px"}, {"label": "Containers", "value": "16px to 20px"}, {"label": "Affects", "value": "38 parts on 9 screens"}],
            "warn": "This changes every screen that uses these tokens.", "cancel": "Cancel", "approve": "Change corners",
            "pending": "Changing", "done": "Changed", "toast": "Corners changed in your system", "undo": "Change undone"}, prepared=False, fallback=True),
        sc("What is a design token?", None,
           "A design token is a named design value, such as “primary text colour” or “small gap”. Your code uses the name, so changing the value in one place changes it everywhere.",
           [["Look up the glossary", 180]], [["No part: a sentence answers it", 1]], prepared=False)]}


def demo_html(products, mini=False):
    data = json.dumps({"products": products}, ensure_ascii=False).replace("</", "<\\/")
    switch = "" if mini else ('<div class="sl-switch" role="group" aria-label="Example product">'
                              + "".join(f'<button type="button" data-product="{p["id"]}" aria-pressed="false">{esc(p["tab"])}</button>' for p in products) + "</div>")
    lane = lambda k, t: f'<div class="sl-lane"><h3>{t}</h3><ol data-lane="{k}"></ol></div>'
    behind = "" if mini else f"""<aside class="sl-behind" aria-label="Behind the answer">
<h2>Behind the answer</h2>
<p>Three lanes start together. The part is on screen before the data arrives.</p>
<div class="sl-lanes">{lane("data", "Your data agent")}{lane("ui", "Smart UI")}{lane("text", "Your model")}</div>
<div class="sl-totals"><p class="sl-total"><span>Outline on screen</span><b data-t="outline">–</b></p><p class="sl-total"><span>Answer complete</span><b data-t="full">–</b></p></div>
<p class="sl-fineprint">Timings here are scripted to show the order. No model runs on this page.</p>
</aside>"""
    chat_extra = ('<button class="sl-btn sl-replay" type="button" data-replay>Play it again</button>' if mini
                  else '<div class="sl-chips" data-chips role="group" aria-label="Questions to ask"></div>')
    return f"""<div class="sl"{" data-mini" if mini else ""} data-sl>
<script type="application/json">{data}</script>
<div class="sl-app">
<div class="sl-top"><div class="sl-who"><span class="sl-avatar" aria-hidden="true"></span><div><h2 data-who></h2><p data-sub></p></div></div>{switch}</div>
<div class="sl-body"><section class="sl-chat" aria-label="Conversation"><div class="sl-log" data-log></div>{chat_extra}</section>{behind}</div>
<p class="vh" data-live aria-live="polite"></p>
<div class="sl-toasts" data-toasts></div>
</div>
</div>"""


def asset_ver():
    return hashlib.sha256((STATIC / "smart-ui-live.css").read_bytes() + (STATIC / "smart-ui-live.js").read_bytes()).hexdigest()[:10]


def assets_html():
    v = asset_ver()
    return f'<link rel="stylesheet" href="/smart-ui-live.css?v={v}">\n<script src="/smart-ui-live.js?v={v}" defer></script>\n'


def preview(b):
    """The home page's compact demo: the Fernhollow chat alone, played once when it comes into view, with a replay button."""
    st, credit = b.stage("blue-soft", demo_html([fernhollow()], mini=True), "su-stage su-mini")
    return assets_html() + st, credit


# ---------------------------------------------------------------- page sections
def hero(b, f):
    st, credit = b.stage("blue-soft", demo_html([fernhollow(), design_review()]), "su-stage")
    jobs = ", ".join(f["groups"][:-1]) + " and " + f["groups"][-1]
    stats = [(f["parts"], "parts an answer can use, each one a component in the library."),
             (len(f["groups"]), f"jobs they do: {jobs}."),
             (len(f["templates"]), "parts prepared ahead of time for the Fernhollow example, one per read action."),
             (f["cases"], "shared test cases. The Python and browser checks must answer each one the same way.")]
    stat_html = "".join(f'<div class="su-stat"><p class="su-big num">{n}</p><p>{esc(t)}</p></div>' for n, t in stats)
    return f"""
<section class="h-sec h-first su-hero">
<nav class="crumb" aria-label="Breadcrumb"><a href="/">{b.NAME}</a><span aria-hidden="true">/</span><span aria-current="page">Smart UI</span></nav>
<p class="kicker su-eyebrow">Generative UI, from your own design system</p>
<h1 class="su-title">Answers that show your interface</h1>
<p class="h-lede su-lede">Your assistant answers with your own components: a fine with a Pay button, an application's progress, a table you can sort. The parts are made ahead of time from your library, filled from your data and checked before they show.</p>
<p class="su-note">It comes with OpenDesigner and stays off until you ask for it. You keep your own model and agents.</p>
<p class="su-act"><a class="btn primary" href="/docs/smart-ui-quickstart/">Add it to your assistant</a><a class="h-link" href="#built">How it's built {b.ARROW}</a></p>
<figure class="su-demo">
{st}
<figcaption>A recorded demo, drawn live in this page from scripted answers. Pick a question, press Pay or Fix, try the other product. A hosted playground you can type into comes later. Photo: {credit} on Unsplash.</figcaption>
</figure>
<div class="su-stats">{stat_html}</div>
<p class="h-fine">Counted from the repository when this page was built.</p>
</section>
"""


def mini_facts(title, rows, sub=""):
    """A small static key-facts part for the use-case screens: rows of (label, value, tone or '')."""
    dd = lambda v, t: f'<span class="sl-tag {t}">{esc(v)}</span>' if t else esc(v)
    return (f'<div class="sl-part"><div class="sl-ph"><p class="sl-pt">{esc(title)}</p>{f"<p class=sl-psub>{esc(sub)}</p>" if sub else ""}</div>'
            f'<dl class="sl-facts">' + "".join(f'<div class="sl-fact"><dt>{esc(l)}</dt><dd>{dd(v, t)}</dd></div>' for l, v, t in rows) + "</dl></div>")


def screens(f):
    """One small screen per kind of answer, drawn with the demo's part styles and the Fernhollow data."""
    d = json.loads((FERN / "data.json").read_text())
    rec = json.loads((FERN / "recorded.json").read_text())["turns"]
    fine = next(x for x in d["fines"] if x["status"] == "Unpaid")
    office = rec["When is the Hollow Lane office open?"]["text"]
    ps = rec["Where is my application?"]["answer"][0]["createSurface"]["components"][0]
    steps = "".join(f'<li class="sl-pstep {s["state"]}"><span class="sl-mark"></span><span class="sl-pl">{esc(s["label"])}</span></li>' for s in ps["steps"][:4])
    opts = d["renewal"]["options"]
    docs = d["applications"][0]["documents"]
    hl = d["offices"][0]
    return [
        ("text", "Text, when text is enough", "A short fact or a “when” question. Most questions end here, with no part.",
         f'<div class="uc-chat"><p class="sl-me">When is the Hollow Lane office open?</p><p class="sl-say">{esc(office)}</p></div>', []),
        ("answer", "Answer", "A record with its facts: one fine, one booking, one office.",
         mini_facts("Hollow Lane office", [("Today", hl["open_today"], "ok"), ("Closure", "Friday 27 November", "warn"), ("Phone", hl["phone"], "")]), f["by_group"]["answer"]),
        ("data", "Data", "Where something stands, numbers and trends. The data picks the colour.",
         f'<div class="sl-part"><div class="sl-ph"><p class="sl-pt">{esc(ps["title"])}</p><span class="sl-tag {TONE[ps["tone"]]}">{esc(ps["status"])}</span></div><ol class="sl-steps">{steps}</ol></div>', f["by_group"]["data"]),
        ("choose", "Choose", "Two or three options side by side, so the person can pick.",
         '<div class="uc-cmp">' + "".join(f'<div class="sl-card"><strong>{esc(o["length"])}</strong><span class="uc-price">{esc(o["price"])}</span><span>{esc(short(o["from"]))} to {esc(short(o["to"]))}</span></div>' for o in opts) + "</div>", f["by_group"]["choose"]),
        ("act", "Act", "A change the person makes. It says what will happen and waits for their press.",
         f'<div class="sl-part"><p class="sl-pt">Pay notice {esc(fine["reference"])}</p><p class="sl-warn">{esc(warns("pay_fine"))}</p><div class="sl-acts"><span class="sl-btn">Not now</span><span class="sl-btn primary">Pay {esc(fine["discounted_amount"])}</span></div></div>', f["by_group"]["act"]),
        ("confirm", "Confirm", "What happened, with Undo when the change can be undone.",
         mini_facts("Payment received", [("Notice", fine["reference"], ""), ("Amount", fine["discounted_amount"], ""), ("Status", "Closed", "ok")])
         + '<div class="sl-toast uc-toast"><span>Corners changed in your system</span><span class="sl-undo">Undo</span></div>', f["by_group"]["confirm"]),
        ("media", "Media", "A file, a place, a picture or code, from hosts you allow.",
         '<div class="sl-part"><p class="sl-pt">Your documents</p><ul class="uc-files">' + "".join(
             f'<li><span class="uc-file" aria-hidden="true"></span><span><strong>{esc(x["document"])}</strong><small>{esc(x["file"] or "Still needed")}</small></span>'
             f'<span class="sl-tag {"ok" if x["file"] else "warn"}">{"Uploaded" if x["file"] else "Needed"}</span></li>' for x in docs) + "</ul></div>", f["by_group"]["media"]),
        ("states", "Every state", "Loading, empty, an error with a retry, data that may be old. Every part handles each one.",
         '<div class="uc-stategrid"><div class="sl-part"><span class="sl-sk" style="width:60%"></span><span class="sl-sk" style="width:90%"></span><span class="sl-sk" style="width:40%"></span></div>'
         '<div class="sl-part uc-empty"><p>Nothing to show yet.</p></div>'
         '<div class="sl-part"><p class="uc-err">We couldn’t load your fines.</p><span class="sl-btn">Try again</span></div>'
         '<div class="sl-part"><p class="uc-stale">Updated 10:42. It may have changed since.</p></div></div>', []),
    ]


def uses_section(b, f):
    cards = []
    for key, name, use, art, parts in screens(f):
        links = ", ".join(f'<a href="/library/{slug}/">{esc(n)}</a>' for slug, n, _ in parts)
        cards.append(f'<li class="uc uc-{key}"><div class="uc-screen" aria-hidden="true">{art}</div><h3>{esc(name)}</h3><p>{esc(use)}</p>'
                     + (f'<p class="uc-parts">{links}</p>' if links else "") + "</li>")
    rest = f["library"] - f["parts"]
    return f"""
<section class="h-sec" id="parts">
<div class="h-head h-head-row"><div>{b.idx("01", "Every kind of answer")}<h2 class="h-h2">One screen for each job an answer does.</h2>
<p class="h-lede">Each part is a component in the library, so it works in your product with or without the assistant. Your scope step keeps only the ones you need.</p></div>
<a class="h-link" href="/library/">The other {rest} components {b.ARROW}</a></div>
<ul class="ucs">{"".join(cards)}</ul>
<p class="h-fine">Drawn with the Fernhollow example's invented data. The parts also come in flight results, made for travel products.</p>
</section>
"""


def built_section(b, f):
    t = f["templates"]
    pick = [x for x in t if x["action"] in ("list_fines", "application_status", "renewal_quote")]
    seen, rows = set(), []
    for x in pick:
        if x["action"] not in seen:
            seen.add(x["action"])
            rows.append(f'<li><span>{esc(x["action"])}</span><b>{esc(x["part"]["component"])}</b></li>')
    vis = [
        f'<div class="sb-file"><p class="sb-fname num">templates.json</p><ul>{"".join(rows)}</ul><p class="sb-more">{len(t)} parts for Fernhollow</p></div>',
        '<div class="sb-match"><p class="sl-me">Do I have any fines?</p><p class="sl-call done num"><span class="sl-dot"></span><span>list_fines → KeyFacts</span></p><p class="sb-note">Under 0.2 ms, no model</p></div>',
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
    events = ["call", "shell", "part", "text", "lane", "done"]
    return f"""
<section class="h-sec" id="built">
<div class="h-head">{b.idx("02", "How it's built")}<h2 class="h-h2">Prepare once. Then match, fill, check and draw.</h2>
<p class="h-lede">The model writes the sentence. The interface comes from parts you approved, so it can't drift from your system.</p></div>
<div class="sb">
<div class="sb-bands" aria-hidden="true"><span class="sb-band sb-ahead">Ahead of time</span><span class="sb-band sb-now">For every question, while your agent fetches the data</span></div>
<ol class="sb-steps">{cols}</ol>
</div>
<div class="sb-agents"><div><h3 class="h-h3">Your agents, your model</h3>
<p>Smart UI is the UI step beside your agents. Your data agent can be your API, a search over documents or a database. Your page draws what each event says.</p></div>
<ul class="sb-events">{"".join(f"<li><code>{e}</code></li>" for e in events)}</ul>
<a class="h-link" href="/docs/smart-ui-quickstart/#use-your-own-agents">Use your own agents {b.ARROW}</a></div>
<p class="h-fine">Measured on the examples in this repository: the outline is on screen 1 to 3 ms after the question, and with Gemini Flash Lite the whole answer takes about 1.5 to 2 seconds on Fernhollow.</p>
</section>
"""


def products_section(b):
    """Different products, different answers: evals/smart-ui/use-cases.json, or nothing when it isn't there (no invented data)."""
    if not USE_CASES.exists():
        return ""
    u = json.loads(USE_CASES.read_text())
    ps = u.get("products") or []
    if not ps:
        return ""
    cols = []
    for p in ps:
        lis = "".join(f'<li class="{"pr-missing" if a.get("missing") else ""}"><span class="pr-type">{esc(a["type"])}</span>'
                      f'<span class="pr-part num">{esc(a["part"]) if a.get("part") and not a.get("missing") else "no part yet"}</span>'
                      f'<span class="pr-why">{esc(a["reason"])}</span></li>' for a in p["answer_types"])
        cols.append(f'<div class="pr"><h3>{esc(p["name"])}</h3><p class="pr-kind num">{esc(p["kind"].replace("-", " "))}</p><ol>{lis}</ol></div>')
    return f"""
<section class="h-sec" id="products">
<div class="h-head">{b.idx("03", "Different products")}<h2 class="h-h2">Different products, different answers.</h2>
<p class="h-lede">There's no fixed list. The scope step reads each product's data, actions and screens, and proposes the answers it needs. You confirm them.</p></div>
<div class="prs">{"".join(cols)}</div>
<p class="h-fine">What the scope step found for three example products in this repository, on {esc(u.get("date", ""))}. Their data is invented. None of them has user research yet, which would change the list.</p>
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
    uses = "\n".join(f"- **{name}**: {use}" + (" Parts: " + ", ".join(f"[{n}]({b.SITE_URL}/library/{sl}/)" for sl, n, _ in parts) + "." if parts else "")
                     for _k, name, use, _a, parts in screens(f))
    prods = ""
    if USE_CASES.exists():
        u = json.loads(USE_CASES.read_text())
        prods = "\n\n## Different products, different answers\n\nWhat the scope step found for three example products (invented data), on " + u.get("date", "") + ":\n\n" + "\n".join(
            f"- **{p['name']}** ({p['kind'].replace('-', ' ')}): " + "; ".join(f"{a['type']} ({a['part'] if not a.get('missing') else 'no part yet'})" for a in p["answer_types"])
            for p in u.get("products", []))
    qa = "\n\n".join(f"### {q}\n\n{a}" for q, a in faq)
    return f"""# Smart UI: generative UI made from your own design system

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
    prods = products_section(b)
    n = 4 if prods else 3
    num = lambda i: f"0{i}"
    body = (hero(b, f) + uses_section(b, f) + built_section(b, f) + prods + rules_section(b, f, num(n)) + tested_section(b, f, num(n + 1))
            + faq_section(b, faq, num(n + 2)) + end_section(b, num(n + 3)))
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
    body = f'<link rel="stylesheet" href="/smart-ui.css?v={VER}">\n' + assets_html() + body
    files["smart-ui/index.html"] = b.shell(PATH, SEO_TITLE, DESCRIPTION, body, b.load_docs(), ld, home=True)
    mds["smart-ui/index.md"] = markdown(b, f, faq)
    paths.append(PATH)
    (b.DIST / "smart-ui.css").write_text(css)
    (b.DIST / "smart-ui-live.css").write_text(b.minify_css(b.corners_match_levers(b.apple_tracking((STATIC / "smart-ui-live.css").read_text()))))
    (b.DIST / "smart-ui-live.js").write_text((STATIC / "smart-ui-live.js").read_text())
    demo_files(b)
