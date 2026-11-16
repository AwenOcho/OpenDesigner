"""The Smart UI page's answer demo: four example assistants that answer with picture-based parts, on a tinted stage.

Owner-approved prototype (2026-11-16, _coordination/plans/smart-ui-demo-variants/page.html), then the owner's rounds the same day:
an island under the panels shows the steps behind each answer; follow-up chips and a text field get real recorded answers; a
"Try a state" control shows slow data, no results, a data error and an approval; nothing on the page moves on a click.

Everything here is recorded: no model and no network call runs on the page except the Unsplash photos. smart_ui_page.py calls
answers_hero() and answers_section(); smart-ui-answers.js reads the JSON written here and runs each answer's build sequence
(outline, sentence, card, check, ready). The first paint is already a finished answer. Shops, cafés and names are invented; the
council answers come from examples/smart-ui-fernhollow (its data and recorded turns).
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FERN = ROOT / "examples" / "smart-ui-fernhollow"
STATIC = ROOT / "site" / "static"
esc = html.escape
NB = " "  # no-break space: a number never parts from its unit


# ---------------------------------------------------------------- photos: exact sizes, 2x in srcset, WebP or AVIF from Unsplash
def unsplash(pid, w, h):
    return f"https://images.unsplash.com/{pid}?w={w}&h={h}&q=60&auto=format&fit=crop&crop=entropy"


def img(pid, w, h, alt, first=False):
    """w x h is the box the photo is drawn in at 1440 px; the 2x file is in srcset. The hero's first row loads first."""
    load = 'fetchpriority="high"' if first else 'loading="lazy"'
    return (f'<img src="{unsplash(pid, w, h)}" srcset="{unsplash(pid, w, h)} {w}w, {unsplash(pid, 2 * w, 2 * h)} {2 * w}w" sizes="{w}px" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" decoding="async" {load}>')


# ---------------------------------------------------------------- recorded data
COATS = [  # photo, name, price, was, swatches, stock, arrives
    ("photo-1539533113208-f6df8cc8b543", "Camel single-breasted coat", 189, None, ["#b08a5e", "#2b2b2b"], ("ok", "In stock"), ("ok", "Arrives Friday")),
    ("photo-1591900947067-851789555ef3", "Red wool wrap coat", 149, 199, ["#a8322d", "#1f2a44"], ("warn", "2 left in M"), ("ok", "Arrives Friday")),
    ("photo-1550872199-63f4382fe925", "Belted brown coat", 172, None, ["#7a5a3c", "#c9b79c"], ("ok", "In stock"), ("ok", "Arrives Thursday")),
    ("photo-1707303294967-d0ccd0809cf2", "Black tailored coat", 195, None, ["#1d1d1f", "#6b6f78"], ("ok", "In stock"), ("warn", "Arrives Tuesday")),
    ("photo-1586081493946-c75071ee57c0", "Grey funnel-neck coat", 165, None, ["#9a9ea6", "#222222"], ("ok", "In stock"), ("ok", "Arrives Friday")),
    ("photo-1637102146291-c408b298e22b", "Classic trench", 158, 198, ["#c8b18e", "#1f2a44"], ("info", "Ships Friday"), ("warn", "Arrives Monday"))]
CAFES = [  # photo, name, rating, price, walk, why, hours, open status
    ("photo-1567880905822-56f8e06fe630", "The Reading Room", "4.8", "£", "6 min walk", "Quiet · sockets at every table", "Open until 20:00", ("ok", "Open now")),
    ("photo-1511081692775-05d0f180a065", "Kiln Coffee", "4.6", "£", "9 min walk", "Long tables · fast Wi-Fi", "Open until 22:00", ("warn", "Busy soon")),
    ("photo-1770739539412-d9e1021429cf", "Hollow Bean", "4.7", "££", "4 min walk", "Soft seating · no music", "Open until 18:00", ("ok", "Open now"))]
SHORT = {"shop": "Shop", "places": "Places", "council": "Council", "review": "Review"}  # tab labels on phones
LAYOUTS = [("canvas", "Canvas", 2), ("window", "Window and rail", 1), ("single", "Single window", 3)]
LOOKS = [("blue", "Your blue"), ("warm", "Warm"), ("dark", "Dark")]
STATES = [("normal", "Normal"), ("slow", "Slow data"), ("empty", "No results"), ("error", "Data error"), ("approval", "Needs approval")]


def fern():
    rec = json.loads((FERN / "recorded.json").read_text())["turns"]
    app = rec["Where is my application?"]
    renew = rec["Renew my parking permit"]
    return app["text"], app["answer"][0]["createSurface"]["components"][0], renew["text"], renew["answer"][0]["createSurface"]["components"][0]


def answers():
    """Every recorded answer: question, sentence, canvas title and count, the steps behind it, and words a typed question can match."""
    app_say, _, renew_say, _ = fern()
    A = lambda q, a, title, count, agent, ui, ms, keys, **kw: {"q": q, "a": a, "title": title, "count": count, "agent": agent, "ui": ui, "ms": ms, "keys": keys, **kw}
    text_ui = ["No ready-made card", "Answered in text"]
    return {
        "shop": {"tab": "Shopping", "who": "Wren & Loom assistant", "source": "the shop's stock",
                 "checks": ["Every photo has alt text", "Prices carry the £ sign", "Stock uses the status colours"],
                 "approval": {"title": "Order the camel coat in M for £189?", "details": [["Size", "M"], ["Delivery", "Friday"], ["Paid with", "Your saved card"]],
                              "warn": "Your card is charged when you press Order.", "ok": "Order for £189", "done": "Order placed. It arrives Friday."},
                 "empty": ["No coats match", "Try a higher price, or ask for sale coats."],
                 "answers": {
                     "init": A("Warm wool coats under £200, size M?", "Six coats fit. The camel single-breasted is the warmest under £200, and two are on sale this week.",
                               f"Wool coats under £200 · size{NB}M", "6 results", ["Searched 412 coats", "Filtered size M"], ["Matched the grid", "Filled 6", "Checked prices"], f"1.2{NB}s",
                               ["coat", "coats", "wool", "200", "size", "show"]),
                     "warmest": A("Which is warmest?", "The camel single-breasted coat is the warmest: 80% wool with a quilted lining.",
                                  "Warmest first", "4 coats", ["Read the fabrics", "Ranked by warmth"], ["Matched the grid", "Added a badge", "Checked it"], f"0.9{NB}s",
                                  ["warmest", "warm", "warmer", "warmth", "cold"]),
                     "sale": A("Show only sale coats", "Two coats are on sale: the red wool wrap at £149 and the classic trench at £158.",
                               "On sale", "2 results", ["Filtered sale prices"], ["Matched the grid", "Filled 2", "Checked prices"], f"0.8{NB}s",
                               ["sale", "discount", "cheap", "cheaper", "offer", "deal"]),
                     "friday": A("Will it arrive by Friday?", "Three of these four arrive by Friday if you order today. The black tailored coat arrives Tuesday.",
                                 "Delivery if you order today", "4 coats", ["Checked the couriers", "Read your address"], ["Matched delivery rows", "Filled 4", "Checked dates"], f"1.1{NB}s",
                                 ["arrive", "friday", "delivery", "deliver", "ship", "shipping", "when"])},
                 "order": ["init", "warmest", "sale", "friday"]},
        "places": {"tab": "Places", "who": "Fernhollow guide", "source": "opening hours",
                   "checks": ["Every photo has alt text", "Open now comes from live hours", "Ratings show one decimal"],
                   "approval": {"title": "Book a table at The Reading Room?", "details": [["Table", "For one"], ["Time", "Today, 14:00"], ["Cost", "Free"]],
                                "warn": "The café holds the table for 15 minutes.", "ok": "Book the table", "done": "Table booked for 14:00."},
                   "empty": ["No cafés match", "Try a wider area, or a later time."],
                   "answers": {
                       "init": A("A quiet café to work from near me?", "Three cafés within ten minutes are quiet and have sockets. The Reading Room stays open latest.",
                                 "Quiet cafés near Mill Street", "3 places", ["Found cafés within 1 km", "Read opening hours"], ["Matched place cards", "Filled 3", "Checked open now"], f"0.9{NB}s",
                                 ["cafe", "café", "quiet", "work", "near", "coffee"]),
                       "late": A("Somewhere open after 18:00?", "Two stay open after 18:00: Kiln Coffee until 22:00 and The Reading Room until 20:00.",
                                 f"Open after 18:00", "2 places", ["Read opening hours"], ["Matched place cards", "Filled 2", "Checked hours"], f"0.7{NB}s",
                                 ["open", "late", "after", "evening", "18", "night", "tonight"]),
                       "wifi": A("Which has the best Wi-Fi?", "Kiln Coffee has the fastest Wi-Fi, about 120 Mbps by visitors' tests.",
                                 "Best Wi-Fi", "3 places", ["Read visitor tests"], ["Matched place cards", "Marked the best", "Checked it"], f"0.8{NB}s",
                                 ["wifi", "wi-fi", "internet", "fast", "fastest", "signal"])},
                   "order": ["init", "late", "wifi"]},
        "council": {"tab": "Council", "who": "Fernhollow council", "source": "the council's records",
                    "checks": ["Dates in plain words", "Amounts carry the £ sign", "The pay button names the amount"],
                    "approval": {"title": "Pay £35.00 to Fernhollow council?", "details": [["Notice", "FH40018273"], ["Amount", "£35.00"], ["Paid with", "Debit card ending 2209"]],
                                 "warn": "This pays the notice now. It can't be undone.", "ok": "Pay £35.00", "done": "£35.00 paid. Notice FH40018273 is closed."},
                    "empty": ["No fines on your account", "Ask about permits or applications instead."],
                    "answers": {
                        "init": A("Do I have any fines?", "You have one unpaid fine. Pay by Thursday 19 November and it costs £35.00 instead of £70.00.",
                                  "Your fines", "1 unpaid", ["Fetched your fines", "Read the deadline"], ["Matched the fine card", "Filled it", "Checked amounts"], f"1.1{NB}s",
                                  ["fine", "fines", "penalty", "ticket", "parking", "owe", "pcn"]),
                        "application": A("Where is my application?", app_say, "Your application", "In progress", ["Fetched your application"],
                                         ["Matched the tracker", "Filled 5 steps", "Checked dates"], f"0.9{NB}s",
                                         ["application", "applied", "apply", "status", "progress", "where"]),
                        "renew": A("Renew my parking permit", renew_say, "Renew your permit", "£78.00", ["Fetched your permit", "Read the price"],
                                   ["Matched the renewal card", "Filled it", "Checked the price"], f"1.0{NB}s",
                                   ["renew", "permit", "renewal", "extend", "residents"])},
                    "order": ["init", "application", "renew"]},
        "review": {"tab": "Design review", "who": "Design review assistant", "source": "your repository",
                   "checks": ["Every finding has a status", "Colours come from your tokens", "The sentence matches the card"],
                   "approval": {"title": "Change the corner radius?", "details": [["Controls", f"12{NB}px to 16{NB}px"], ["Containers", f"16{NB}px to 20{NB}px"], ["Affects", "38 parts on 9 screens"]],
                                "warn": "This changes every screen that uses these tokens.", "ok": "Change corners", "done": "Corners changed in your system."},
                   "empty": ["Nothing to check", "Point it at a page or a folder with styles."],
                   "answers": {
                       "init": A("Review my pricing page", "Your pricing page follows the system in most places. Two things break it, and one is worth a look.",
                                 "Pricing page review", "5 checks", ["Read 14 files", "Measured colours"], ["Matched the findings", "Filled 5", "Checked it"], f"1.7{NB}s",
                                 ["review", "check", "pricing", "page", "audit"]),
                       "tokens": A("How much of my code uses tokens?", "About two thirds of your values come from tokens. Shadows are the weak spot.",
                                   "Token use in your code", "1,900 values", ["Scanned 54 files", "Counted token uses"], ["Matched the meter", "Filled 5 bars", "Checked it"], f"1.3{NB}s",
                                   ["tokens", "token", "how", "much", "code", "uses", "percent"]),
                       "corners": A("Make the corners rounder", "I can raise the corner radius one step. Here is a card and a button before and after.",
                                    "Corners, before and after", f"+4{NB}px", ["Read your radius tokens"], ["Matched before and after", "Drew both", "Checked it"], f"0.9{NB}s",
                                    ["corners", "corner", "rounder", "round", "radius"]),
                       "token": A("What is a design token?", "A design token is a named design value, such as “primary text colour” or “small gap”. Your code uses the name, so changing the value in one place changes it everywhere.",
                                  "Answered in text", "", ["Looked up the glossary"], text_ui, f"0.4{NB}s",
                                  ["what", "design", "token", "mean", "means", "definition", "explain"], text=True)},
                   "order": ["init", "tokens", "corners", "token"]}}


# ---------------------------------------------------------------- parts (the same parts every answer is built from)
def st(tone, text):
    return f'<span class="sd-st {tone}">{esc(text)}</span>'


def products(coats, w, h, first=False, badge=None):
    """A product grid. badge: (index, label) puts a highlight on one coat. first: the hero's first row loads first."""
    cells = []
    for i, (pid, name, p, was, sw, stock, _arr) in enumerate(coats):
        tag = st("info", badge[1]) if badge and badge[0] == i else st(*stock)
        cells.append(f'<li class="sd-pcard{" sd-hi" if badge and badge[0] == i else ""}"><div class="sd-ph">{img(pid, w, h, name, first and i < 4)}{tag}</div>'
                     f'<div><p class="sd-pname">{esc(name)}</p><p class="sd-prow"><span class="sd-price">£{p}' + (f'<s aria-label="was £{was}">£{was}</s>' if was else "") + "</span>"
                     f'<span class="sd-sw" role="img" aria-label="{len(sw)} colour{"s" if len(sw) > 1 else ""}">' + "".join(f'<i style="background:{c}"></i>' for c in sw) + "</span></p></div></li>")
    return f'<ul class="sd-pgrid sd-n{len(coats)}">{"".join(cells)}</ul>'


def place(c, w, h, hi=None):
    pid, n, r, pr, walk, why, hrs, s = c
    return (f'<li class="sd-place{" sd-hi" if hi else ""}"><div class="sd-ph">{img(pid, w, h, "Inside " + n)}' + (st("info", hi) if hi else "") + "</div>"
            f'<div class="sd-plb"><p class="sd-plt">{esc(n)}<span aria-label="rated {r} out of 5">★ {r}</span></p><p class="sd-plm">{pr} · {walk} · {hrs}</p>'
            f'<p class="sd-plw">{esc(why)}</p><p>{st(*s)}</p></div></li>')


def places(cafes, hi=None):
    return f'<ul class="sd-places sd-n{len(cafes)}">' + "".join(place(c, 280, 180, hi if c[1] == "Kiln Coffee" else None) for c in cafes) + "</ul>"


def a_map():
    """The fine's evidence photo, as a council's fine page shows one (checked by the coordinator, 2026-11-16: no number plate or
    readable badge anywhere in the frame). It flexes only in two columns; in one column it is 16:9."""
    pid = "photo-1792011452457-e795014a89b2"
    u = lambda w, h: f"https://images.unsplash.com/{pid}?w={w}&h={h}&q=60&auto=format&fit=crop&crop=focalpoint&fp-x=0.55&fp-y=0.72"
    return (f'<div class="sd-map sd-pic"><img src="{u(400, 300)}" srcset="{u(400, 300)} 400w, {u(800, 600)} 800w" sizes="400px" width="400" height="300" '
            'alt="Evidence photo: a car parked beside yellow no-parking lines on Mill Street" decoding="async" loading="lazy">'
            f'<span class="sd-maplbl" aria-hidden="true">Evidence photo · Fri{NB}6{NB}Nov, 10:42</span></div>')


def fine():
    rows = [("Reference", "FH40018273"), ("Date", f"Fri{NB}6{NB}Nov{NB}2026, 10:42"), ("Place", f"Mill Street, Zone{NB}B"), ("Reason", "Residents' bay, no permit"),
            ("Full amount", "£70.00"), (f"Pay by Thu{NB}19{NB}Nov", "<b>£35.00</b>"), ("Challenge by", f"Thu{NB}3{NB}Dec")]
    kv = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<div class="sd-card sd-tcard"><div class="sd-cardh"><div><p class="sd-ct">Unpaid parking fine</p><p class="sd-sub">Vehicle AB12 CDE</p></div>{st("warn", "Unpaid")}</div>'
            f'<dl class="sd-kv">{kv}</dl><button type="button" class="sd-btn" data-act>Pay £35.00</button></div>')


def council_init():
    opts = [("Pay £35.00 today", f"The lower amount ends Thursday 19{NB}November"), ("Challenge the fine", f"Send photos or a permit within 28{NB}days"),
            ("Ask for more time", f"Up to 14{NB}days if you ask before the 19th")]
    return (f'<div class="sd-duo">{fine()}<div class="sd-side2">{a_map()}<p class="kicker">What you can do</p>'
            + "".join(f'<div class="sd-opt"><b>{t}</b><span>{d}</span></div>' for t, d in opts) + "</div></div>")


def checks():
    rows = [("ok", "Pass", "Colours all come from tokens", "38 of 38 colours"), ("ok", "Pass", f"Body text contrast is 7.2{NB}to{NB}1", f"The floor is 4.5{NB}to{NB}1"),
            ("ok", "Pass", f"Spacing follows the 8{NB}px scale", "Every gap is on the scale"),
            ("warn", "Look", f"Two buttons use a 10{NB}px radius, the system says 12", f"Fix: use 12{NB}px"), ("bad", "Broken", f"Plan names are cut off at 375{NB}px", "Fix: let the name wrap")]
    return ('<div class="sd-card sd-tcard sd-findings"><p class="sd-ct">Pricing page, checked against your system</p><p class="sd-sub">5 checks: 3 pass, 1 to look at, 1 broken</p><ul class="sd-checks">'
            + "".join(f'<li>{st(t, l)}<span>{esc(x)}<small>{esc(d)}</small></span></li>' for t, l, x, d in rows) + "</ul></div>")


def mock():
    plan = lambda i: (f'<div class="sd-pl{" w" if i == 1 else ""}"><span class="nm">' + ('<span class="sd-pin bad">2</span>' if i == 0 else "")
                      + '</span><i class="pr"></i><i class="sh"></i><i></i><i></i><i></i><i></i><i class="sh"></i><span class="bt">' + ('<span class="sd-pin warn">1</span>' if i == 1 else "") + "</span></div>")
    return ('<div class="sd-side2"><p class="kicker">Where on the page</p>'
            '<div class="sd-mini sd-pic" role="img" aria-label="Sketch of the pricing page: marker 1 on the middle plan\'s button, whose corners are 10 px; marker 2 on the first plan\'s name, which is cut off">'
            '<div class="sd-mnav"><i class="lg"></i><i></i><i></i><i></i><i class="cta"></i></div><div class="sd-mhero"><i class="t"></i><i class="s"></i></div>'
            f'<div class="sd-plans">{plan(0)}{plan(1)}{plan(2)}</div><div class="sd-faq"><i class="t"></i><i></i><i></i><i></i></div></div></div>')


def delivery():
    rows = "".join(f'<li><span class="sd-thumb">{img(pid, 48, 48, name)}</span><span class="sd-dn">{esc(name)}<small>£{p}</small></span>{st(*arr)}</li>'
                   for pid, name, p, _w, _s, _st, arr in COATS[:4])
    return f'<div class="sd-card sd-tcard"><p class="sd-ct">If you order today</p><p class="sd-sub">Standard delivery to FH2 4QA</p><ul class="sd-rows">{rows}</ul></div>'


def tracker():
    _, ps, _, _ = fern()
    tone = {"warning": "warn", "success": "ok", "danger": "bad", "info": "info"}[ps["tone"]]
    steps = "".join(f'<li class="sd-{s["state"]}"><b>{esc(s["label"])}</b>' + (f'<small>{esc(s["time"])}</small>' if s.get("time") else "") + "</li>" for s in ps["steps"])
    return (f'<div class="sd-card sd-tcard"><div class="sd-cardh"><div><p class="sd-ct">{esc(ps["title"])}</p><p class="sd-sub">Residents\' parking permit</p></div>{st(tone, ps["status"])}</div>'
            f'<ol class="sd-track">{steps}</ol><button type="button" class="sd-btn sd-ghost" disabled>Upload your V5C</button></div>')


def renewal():
    _, _, _, ap = fern()
    keep = {"Zone", "Vehicle", "New permit", "Cost"}
    kv = "".join(f"<dt>{esc(d['label'])}</dt><dd>{esc(d['value']).replace(' to ', ' to' + NB) if d['label'] != 'Cost' else '<b>' + esc(d['value']) + '</b>'}</dd>"
                 for d in ap["details"] if d["label"] in keep)
    return (f'<div class="sd-card sd-tcard"><div class="sd-cardh"><div><p class="sd-ct">{esc(ap["title"])}</p><p class="sd-sub">12 months, from 1 December</p></div>{st("info", "Ends 30 Nov")}</div>'
            f'<dl class="sd-kv">{kv}</dl><button type="button" class="sd-btn" data-act>Continue</button></div>')


def meter():
    bars = [("Colours", 82, ""), ("Spacing", 71, ""), ("Type sizes", 64, ""), ("Corners", 58, ""), ("Shadows", 19, "bad")]
    rows = "".join(f'<li><span>{n}</span><i class="sd-bar {t}"><i style="width:{p}%"></i></i><b>{p}%</b></li>' for n, p, t in bars)
    return (f'<div class="sd-card sd-tcard"><div class="sd-meter"><b>66%</b><span>of 1,900 values come from tokens</span></div>'
            f'<i class="sd-bar big" role="img" aria-label="66 percent"><i style="width:66%"></i></i><ul class="sd-bars">{rows}</ul></div>')


def corners():
    side = lambda label, a, b: (f'<figure class="sd-ba" style="--ra:{a}px;--rb:{b}px"><figcaption class="kicker">{label}</figcaption>'
                                f'<div class="sd-bacard"><i class="t"></i><i></i><i></i><span class="sd-babtn">Save</span></div></figure>')
    return (f'<div class="sd-card sd-tcard"><div class="sd-bas">{side(f"Before · 12{NB}px", 12, 16)}{side(f"After · 16{NB}px", 16, 20)}</div>'
            f'<button type="button" class="sd-btn" data-act>Change corners</button></div>')


def note():
    return '<p class="sd-note">No ready-made card fits, so Smart UI answers in text.</p>'


def init_part(k, v, first=False):
    """The first answer of each assistant, drawn for its layout (1 window and rail, 2 canvas, 3 single window)."""
    if k == "shop":
        return products(COATS, 220, 180, first) if v == 2 else products(COATS, 200, 260) if v == 1 else products(COATS[:4], 200, 220)
    if k == "places":
        if v == 2:
            return (f'<div class="sd-feat"><ul class="sd-plist">{place(CAFES[0], 420, 300)}</ul>'
                    f'<ul class="sd-plist sd-side">{"".join(place(c, 160, 180) for c in CAFES[1:])}</ul></div>')
        return places(CAFES)
    if k == "council":
        return council_init()
    return f'<div class="sd-duo">{checks()}{mock()}</div>'


def follow_part(k, aid):
    """A follow-up answer's part, the same in every layout."""
    if k == "shop":
        if aid == "warmest":
            return products(COATS[:4], 200, 220, badge=(0, "Warmest"))
        if aid == "sale":
            return products([c for c in COATS if c[3]], 200, 220)
        return delivery()
    if k == "places":
        return places([CAFES[1], CAFES[0]]) if aid == "late" else places(CAFES, "Best Wi-Fi")
    if k == "council":
        return tracker() if aid == "application" else renewal()
    return {"tokens": meter, "corners": corners, "token": note}[aid]()


# ---------------------------------------------------------------- views
def head(s):
    return f'<div class="sd-winhead"><span class="sd-av" aria-hidden="true"></span><div><b>{esc(s["who"])}</b><span>Answers in your design system</span></div></div>'


def chips(s, current="init"):
    return "".join(f'<button type="button" class="sd-chip" data-ask="{a}">{esc(s["answers"][a]["q"])}</button>' for a in s["order"] if a != current)


ASK = ('<form class="sd-ask" autocomplete="off"><input type="text" name="q" maxlength="80" placeholder="Ask something…" aria-label="Ask the assistant">'
       '<button type="submit" aria-label="Send"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button></form>')


def qrow(s, a):
    return f'<div class="sd-qrow"><span class="sd-match" aria-live="off"></span><div class="sd-q">{esc(a["q"])}</div></div>'


def steps(xs, on=True):
    return "".join(f'<li class="sd-step{" on" if on else ""}">{esc(x)}</li>' for x in xs)


def view(k, v, first=False):
    """One assistant's first answer in one layout. JS fills the same hooks for every later answer."""
    s = ANSWERS[k]
    a = s["answers"]["init"]
    body = f'{qrow(s, a)}<p class="sd-a">{esc(a["a"])}</p>'
    foot = f'<div class="sd-foot">{ASK}<div class="sd-compose" aria-label="Other questions">{chips(s)}</div></div>'
    if v == 2:
        return (f'<div class="sd-win sd-chatcol">{head(s)}<div class="sd-body">{body}<div class="sd-qlist" aria-label="Other questions">{chips(s)}</div></div>'
                f'<div class="sd-foot">{ASK}</div></div>'
                f'<div class="sd-win sd-canvas"><div class="sd-body"><div class="sd-ctitle"><b>{esc(a["title"])}</b><span class="kicker">{a["count"]}</span></div>'
                f'<div class="sd-part">{init_part(k, 2, first)}</div></div></div>')
    win = f'<div class="sd-win">{head(s)}<div class="sd-body">{body}<div class="sd-part">{init_part(k, v)}</div></div>{foot}</div>'
    if v == 3:
        return win
    rail = (f'<aside class="sd-rail" aria-label="Behind the answer"><div class="sd-rtop"><p class="kicker">Behind the answer</p>'
            f'<div class="sd-lane"><p class="kicker">Your agent</p><ul class="sd-steps" data-lane="agent">{steps(a["agent"])}</ul></div>'
            f'<div class="sd-lane"><p class="kicker">Smart UI</p><ul class="sd-steps" data-lane="ui">{steps(a["ui"])}</ul></div>'
            f'<div class="sd-lane"><p class="kicker">Checked before it shows</p><ul class="sd-steps" data-lane="checks">{steps(s["checks"])}</ul></div></div>'
            f'<p class="sd-ready">Ready in <b data-ready>{a["ms"]}</b></p></aside>')
    return win + rail


def island(k):
    a = ANSWERS[k]["answers"]["init"]
    return (f'<div class="sd-island" aria-label="Behind the answer"><span class="kicker">Your agent</span><ul class="sd-isteps" data-lane="agent">{steps(a["agent"])}</ul>'
            f'<span class="sd-idiv"></span><span class="kicker">Smart UI</span><ul class="sd-isteps" data-lane="ui">{steps(a["ui"])}</ul>'
            f'<span class="sd-idiv"></span><span class="sd-iready">Ready in <b data-ready>{a["ms"]}</b></span>'
            f'<span class="sd-iphone"><span class="sd-idot"></span>Smart UI · <span data-count>3 steps checked</span> · <b data-ready>{a["ms"]}</b></span></div>')


def tabs(on):
    return ('<div class="sd-seg" role="group" aria-label="Example assistants">'
            + "".join(f'<button type="button" data-k="{k}" aria-pressed="{str(k == on).lower()}"><span class="sd-tl">{esc(s["tab"])}</span><span class="sd-ts">{SHORT[k]}</span></button>'
                      for k, s in ANSWERS.items()) + "</div>")


def states(name):
    return (f'<span class="sd-ctl sd-statewrap"><span class="sd-lbl" id="sd-st-{name}">Try a state</span><span class="sd-seg sd-states" role="group" aria-labelledby="sd-st-{name}">'
            + "".join(f'<button type="button" data-s="{k}" aria-pressed="{str(k == "normal").lower()}">{t}</button>' for k, t in STATES) + "</span></span>")


def stage(name, tab, views, cls, look=""):
    """look: a class on the stage itself, so the controls under it keep the page's own colours."""
    return (f'<div class="sd {cls}" data-sd="{name}" data-tab="{tab}"><div class="sd-stage{" " + look if look else ""}">'
            f'<div class="sd-bar">{tabs(tab)}<span class="sd-rec">Recorded answers</span></div>{views}{island(tab)}'
            f'<div class="sd-toasts" role="status" aria-live="polite"></div><p class="vh" data-live aria-live="polite"></p></div>'
            f'<div class="sd-under">{states(name)}</div></div>')


def data_json():
    out = {k: {kk: vv for kk, vv in s.items()} for k, s in ANSWERS.items()}
    return json.dumps(out, ensure_ascii=False).replace("</", "<\\/")


def templates():
    views = "".join(f'<template data-sd-t="{k}-{v}">{view(k, v)}</template>' for k in ANSWERS for v in (1, 2, 3))
    parts = "".join(f'<template data-sd-p="{k}:{a}">{follow_part(k, a)}</template>' for k, s in ANSWERS.items() for a in s["order"] if a != "init")
    return f'<script type="application/json" id="sd-data">{data_json()}</script>{views}{parts}'


ANSWERS = answers()


def answers_hero():
    """The hero's stage: chat and canvas on wide screens, the window on phones (both drawn; CSS shows one)."""
    views = (f'<div class="sd-view sd-v2 sd-desk" data-v="2">{view("shop", 2, first=True)}</div>'
             f'<div class="sd-view sd-v1 sd-phone" data-v="1">{view("shop", 1)}</div>')
    return stage("hero", "shop", views, "sd-hero sd-lay-2")


def answers_section(b, n):
    seg = lambda label, attr, items, on: (f'<span class="sd-ctl{" sd-laywrap" if attr == "l" else ""}"><span class="sd-lbl" id="sd-lbl-{attr}">{label}</span>'
                                          f'<span class="sd-seg" role="group" aria-labelledby="sd-lbl-{attr}">'
                                          + "".join(f'<button type="button" data-{attr}="{k}" aria-pressed="{str(k == on).lower()}">{t}</button>' for k, t, *_ in items) + "</span></span>")
    st_ = stage("any", "places", f'<div class="sd-view sd-v1" data-v="1">{view("places", 1)}</div>', "sd-any sd-lay-1", "sd-look-blue")
    return f"""
<section class="h-sec" id="any-look">
<div class="h-head">{b.idx(n, "Layouts and looks")}<h2 class="h-h2">One answer. Any layout, any look.</h2></div>
<div class="sd-ctrls">{seg("Layout", "l", LAYOUTS, "window")}{seg("Look", "o", LOOKS, "blue")}</div>
{st_}
<div hidden>{templates()}</div>
</section>
"""


def answers_assets():
    import hashlib
    v = hashlib.sha256((STATIC / "smart-ui-answers.css").read_bytes() + (STATIC / "smart-ui-answers.js").read_bytes()).hexdigest()[:10]
    return f'<link rel="stylesheet" href="/smart-ui-answers.css?v={v}">\n<script src="/smart-ui-answers.js?v={v}" defer></script>\n'
