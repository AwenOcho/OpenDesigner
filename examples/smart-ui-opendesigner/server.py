#!/usr/bin/env python3
"""The OpenDesigner assistant: Smart UI on OpenDesigner's own data, for the Smart UI example.

  python3 examples/smart-ui-opendesigner/server.py [--port 8030] [--provider gemini|claude-cli|anthropic|recorded]

Every answer comes from OpenDesigner itself, run on a small sample product (sample-app/, a pricing page on the brand's
tokens with three mistakes left in on purpose):
  review_page     engine.py review on the sample, plus checks measured from its CSS against the tokens (one check at a time)
  suggest_parts   the component library (skills/opendesigner/assets/library), ranked for a kind of page
  token_use       the sample's CSS: values that come from var(--ds-*) and values typed by hand, per kind
  define          the glossary (synthesis/glossary.json), plain voice
  change_corners  engine.py set dials.roundness, then generate, on a scratch copy of the system
  fix_check       one review fix, applied to a scratch copy of the sample
The GET routes are what the assistant may call to answer; the POST ones change something and only ever become buttons.
Nothing tracked is written at run time: changes go to work/ (git-ignored), made from opendesigner/ and sample-app/ on
first use. The chat itself is POST /api/chat, served by the Smart UI reference server
(skills/opendesigner-smart-ui/scripts/live.py). Standard library only; loopback only.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ENGINE = ROOT / "skills" / "opendesigner" / "scripts" / "engine.py"
LIBRARY = ROOT / "skills" / "opendesigner" / "scripts"
GLOSSARY = ROOT / "synthesis" / "glossary.json"
SAMPLE = HERE / "sample-app"
WORK = HERE / "work"

NAME = "OpenDesigner assistant"
CATALOG = HERE / "opendesigner" / "smart-ui" / "catalog.json"
TOKENS = HERE / "opendesigner" / "build" / "css" / "tokens.css"
WEB = HERE / "web"
ACTIONS = {}
SUGGESTIONS = ["Review my pricing page", "Which parts fit a settings page?", "How much of my code uses the tokens?",
               "What is a design token?", "Make the corners rounder"]


class App:
    """A tiny router in the style most Python web apps use. Each route is also an action the assistant knows about."""

    def _route(self, method, path, changes):
        def deco(fn):
            ACTIONS[fn.__name__] = {"description": (fn.__doc__ or "").strip(), "changes": changes, "fn": fn,
                                    "method": method, "path": path,
                                    "params": {k: v for k, v in getattr(fn, "params", {}).items()},
                                    "consequences": list(getattr(fn, "consequences", [])),
                                    "reversible": getattr(fn, "reversible", False),
                                    "view": getattr(fn, "view", None)}
            return fn
        return deco

    def get(self, path):
        return self._route("GET", path, False)

    def post(self, path):
        return self._route("POST", path, True)


app = App()


def params(**p):
    def deco(fn):
        fn.params = p
        return fn
    return deco


def warns(*lines):
    """What a change does that the person must read before saying yes. Smart UI's validator refuses an approval prompt
    for this action that leaves any of these out (R3)."""
    def deco(fn):
        fn.consequences = lines
        return fn
    return deco


def reversible(fn):
    """A change that can be taken back: it runs when the person presses its button, and the toast offers Undo."""
    fn.reversible = True
    return fn


# ------------------------------------------------------------------------------------------------ reading CSS and tokens

def _blocks(css):
    """Top-level rules as (selector, body); rules inside @media and other at-rules are left out."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, depth, start, sel = [], 0, 0, ""
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                sel, start = css[start:i].strip(), i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                if not sel.startswith("@"):
                    out.append((sel, css[start:i]))
                start = i + 1
    return out


def _decls(body):
    return [(m.group(1).strip().lower(), m.group(2).strip()) for m in re.finditer(r"([-\w]+)\s*:\s*([^;]+);?", body)]


def token_values(path=TOKENS):
    """The system's custom properties as the page sees them by default (the :root rules, later ones win)."""
    out = {}
    for sel, body in _blocks(pathlib.Path(path).read_text()):
        if ":root" in sel:
            for k, v in _decls(body):
                if k.startswith("--"):
                    out[k] = v
    return out


def resolve(value, toks, depth=0):
    """var(--a) -> its value, all the way down (12px, #222428)."""
    if depth > 12:
        return value
    return re.sub(r"var\((--[\w-]+)(?:,\s*([^)]+))?\)", lambda m: resolve(toks.get(m.group(1), m.group(2) or ""), toks, depth + 1), value)


def _rgb(hexv):
    h = hexv.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def contrast(a, b):
    def lum(c):
        r, g, bl = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in _rgb(c)]
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _px(v):
    m = re.fullmatch(r"\s*(-?[\d.]+)px\s*", v or "")
    return float(m.group(1)) if m else None


def sample_dir():
    """The sample as it is now: the scratch copy once a fix has been applied, else the original."""
    return WORK / "sample-app" if (WORK / "sample-app").is_dir() else SAMPLE


def sample_css(folder=None):
    folder = folder or sample_dir()
    return sorted(p for p in folder.glob("*.css"))


def rules(folder=None):
    """Every rule in the sample's own CSS: (file, line, selector, [(property, value)])."""
    out = []
    for f in sample_css(folder):
        text = f.read_text()
        clean = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", clean):
            sel = m.group(1).strip()
            if sel.startswith("@"):
                continue
            line = clean.count("\n", 0, m.start(2)) + 1
            out.append((f.name, line, sel, _decls(m.group(2))))
    return out


def _line_of(file, needle, folder=None):
    for i, l in enumerate(((folder or sample_dir()) / file).read_text().splitlines(), 1):
        if needle in l:
            return i
    return None


# ------------------------------------------------------------------------------------------------ 1. review a page

SCALE_NOTE = "use var(--ds-space-"


def _engine_review(folder):
    r = subprocess.run([sys.executable, str(ENGINE), "review", "--dir", str(folder / "opendesigner"), "--project", str(folder), "--json"],
                       cwd=folder, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"findings": [], "error": (r.stderr or r.stdout)[-200:]}


VERDICT = {"pass": "Passes", "look": "Look at this", "broken": "Broken"}


def _check(cid, status, title, result, detail, fix=None, where=None):
    """One check: its status (pass, look or broken) in words, a short result that is its own ("3.1 to 1"), and a detail."""
    return {"id": cid, "status": status, "verdict": VERDICT[status], "title": title, "result": result, "detail": detail,
            "fix": fix, "where": where}


def _measured_checks(folder, toks):
    """Checks read straight from the sample's CSS and HTML, each as soon as it is done."""
    rs = rules(folder)
    body_color = next((resolve(v, toks) for _, _, s, d in rs if s == "body" for k, v in d if k == "color"), "#000000")

    # text contrast: every rule that sets a background, with its own text colour or the body's
    worst = None
    color_of = {s: v for _, _, s, d in rs for k, v in d if k == "color"}
    for file, line, sel, d in rs:
        props = dict(d)
        bg = props.get("background") or props.get("background-color")
        if not bg:
            continue
        base = re.sub(r":[\w-]+(\([^)]*\))?", "", sel).strip()  # .button:hover takes its text colour from .button
        bgv, fg = resolve(bg, toks), resolve(props.get("color") or color_of.get(base) or body_color, toks)
        if not (re.fullmatch(r"#[0-9a-fA-F]{3,8}", bgv.strip()) and re.fullmatch(r"#[0-9a-fA-F]{3,8}", fg.strip())):
            continue
        ratio = contrast(fg.strip(), bgv.strip())
        if worst is None or ratio < worst[0]:
            worst = (ratio, sel, file, line)
    if worst and worst[0] < 4.5:
        yield _check("contrast", "broken", "Text contrast", f"{worst[0]:.1f} to 1", f"Text on {worst[1]} is under the 4.5 to 1 floor",
                     None, f"{worst[2]}:{worst[3]}")
    else:
        yield _check("contrast", "pass", "Text contrast", f"{worst[0]:.1f} to 1 at the lowest" if worst else "Nothing to measure",
                     "Every text and background pair is above the 4.5 to 1 floor")

    # corners: every border-radius from a radius token
    radii = [(f, l, v) for f, l, s, d in rs for k, v in d if k == "border-radius"]
    raw = [x for x in radii if "var(--ds-radius" not in x[2]]
    yield (_check("corners", "pass", "Corners come from tokens", f"{len(radii)} of {len(radii)} corners", "Every corner uses a radius token") if not raw else
           _check("corners", "look", "Corners come from tokens", f"{len(radii) - len(raw)} of {len(radii)} corners", "Some corner sizes are typed by hand", None, f"{raw[0][0]}:{raw[0][1]}"))

    # type: every font and font-size from a type token
    fonts = [(f, l, v) for f, l, s, d in rs for k, v in d if k in ("font", "font-size", "font-family")]
    raw = [x for x in fonts if "var(--ds-" not in x[2]]
    yield (_check("type", "pass", "Type comes from tokens", f"{len(fonts)} of {len(fonts)} text styles", "Every text style uses a type token") if not raw else
           _check("type", "look", "Type comes from tokens", f"{len(fonts) - len(raw)} of {len(fonts)} text styles", "Some text styles are typed by hand", None, f"{raw[0][0]}:{raw[0][1]}"))

    # focus: links and buttons show a focus ring
    ring = [s for _, _, s, d in rs if ":focus-visible" in s and any(k.startswith("outline") for k, _ in d)]
    yield (_check("focus", "pass", "Focus is visible", "A ring on links and buttons", "The ring's width, offset and colour come from your tokens") if ring else
           _check("focus", "broken", "Focus is visible", "No focus ring", "Nothing shows where the keyboard is"))

    # labels that cannot wrap: estimated width of the text against a 320 px phone
    html = "".join(p.read_text() for p in folder.glob("*.html"))
    found = None
    for file, line, sel, d in rs:
        props = dict(d)
        if props.get("white-space") != "nowrap" or not sel.startswith("."):
            continue
        m = re.search(rf'class="[^"]*\b{re.escape(sel[1:])}\b[^"]*">([^<]+)<', html)
        if not m:
            continue
        text = m.group(1).strip()
        fs = re.search(r"(\d+(?:\.\d+)?)px", resolve(props.get("font", props.get("font-size", "")), toks))
        size = float(fs.group(1)) if fs else 16
        pad = _px(resolve(props.get("padding", "0 0").split()[-1], toks)) or 0
        text_w = round(len(text) * 0.55 * size + 2 * pad)  # about 0.55 em a letter in the brand's text face
        page_pad = (_px(resolve("var(--ds-space-24)", toks)) or 24) + (_px(resolve("var(--ds-space-inset-lg)", toks)) or 20)
        needs = round(text_w + 2 * page_pad)
        found = (text, needs, file, _line_of(file, "white-space: nowrap", folder) or line)
        break
    if found and found[1] > 320:
        short = found[0] if len(found[0]) <= 22 else found[0][:20].rsplit(" ", 1)[0] + "…"
        yield _check("label-wrap", "broken", "Labels can wrap", f"Cut off below {found[1]}px wide", f"“{short}” can't wrap, so it spills out of its card on a phone",
                     "Let it wrap", f"{found[2]}:{found[3]}")
    else:
        yield _check("label-wrap", "pass", "Labels can wrap", "Fits at 320px wide", "Every label fits or wraps on a small phone")


def _engine_checks(folder, review):
    """The two checks engine.py review answers: colours and spacing typed by hand."""
    f = review.get("findings", [])
    colours = [x for x in f if x.get("kind") == "color"]
    sizes = [x for x in f if x.get("kind") == "size"]
    if colours:
        c = colours[0]
        yield _check("colour-tokens", "broken", "Colours come from tokens", f"{c['value']} typed by hand", f"Not one of your colours (found by engine.py review in {c['file']})",
                     "Use the accent token", f"{c['file']}:{c['line']}")
    else:
        yield _check("colour-tokens", "pass", "Colours come from tokens", "No colours by hand", "engine.py review finds every colour in your tokens")
    if sizes:
        s = sizes[0]
        step = re.search(r"var\(--ds-space-(\d+)\)", s.get("fix", ""))
        yield _check("spacing-scale", "look", "Spacing is on the scale", f"{s['value'].split(':')[-1].strip()} is off the scale",
                     f"A {s['value'].split(':')[0]} the scale doesn't have" + (f"; the nearest step is {step.group(1)}px" if step else ""),
                     f"Use {step.group(1)}px from the scale" if step else None, f"{s['file']}:{s['line']}")
    else:
        yield _check("spacing-scale", "pass", "Spacing is on the scale", "Every gap on a step", "engine.py review finds every gap and padding on your scale")


def _summary(page, checks, done):
    n = {s: sum(c["status"] == s for c in checks) for s in ("pass", "look", "broken")}
    nxt = next((c for s in ("broken", "look") for c in checks if c["status"] == s and c["fix"]), None)
    out = {"page": page, "page_name": page.capitalize(), "file": f"{page}.html", "checks": list(checks), "counts": n, "done": done,
           "summary": f"{len(checks)} checks: {n['pass']} pass, {n['look']} to look at, {n['broken']} broken"}
    if nxt:
        out["next_fix"] = {"id": nxt["id"], "label": nxt["fix"], "title": nxt["title"]}
    return out


@app.get("/api/pages/<page>/review")
@params(page="pricing (the one page in the sample app)")
def review_page(page="pricing"):
    """Check one page of the sample app against the design system: text contrast, corners, type, focus, labels that can't wrap, and engine.py review's hard-coded colours and spacing. Each check is pass, look or broken, with a short fix when there is one. Yields the result as each check lands."""
    folder = sample_dir()
    if not (folder / f"{page}.html").is_file():
        yield {"error": {"code": "not_found", "what": "page", "message": f"The sample app has no {page} page.",
                         "what_to_do": "Ask to review the pricing page."}}
        return
    toks = token_values(folder / "opendesigner" / "build" / "css" / "tokens.css")
    checks = []
    for c in _measured_checks(folder, toks):
        checks.append(c)
        yield _summary(page, checks, False)
    review = _engine_review(folder)
    for c in _engine_checks(folder, review):
        checks.append(c)
        yield _summary(page, checks, False)
    order = {"broken": 0, "look": 1, "pass": 2}
    yield _summary(page, sorted(checks, key=lambda c: order[c["status"]]), True)


# The edits behind each fix: (check id) -> (file, text now, text after). Read from the sample at the time of the fix.
def _fix_edit(cid, folder):
    css = "pricing.css"
    text = (folder / css).read_text()
    if cid == "spacing-scale":
        m = re.search(r"gap: (\d+)px;", text)
        if m:
            step = 4 * round(int(m.group(1)) / 4 - 0.01)  # the engine's nearest step on the 4px ladder (14 -> 12)
            return css, m.group(0), f"gap: var(--ds-space-{step});"
    if cid == "colour-tokens":
        m = re.search(r"background: (#[0-9a-fA-F]{3,8});", text)
        if m:
            return css, m.group(0), "background: var(--ds-color-bg-accent-bold);"
    if cid == "label-wrap" and " white-space: nowrap;" in text:
        return css, " white-space: nowrap;", ""
    return None


@app.post("/api/pages/<page>/fixes")
@reversible
@warns("This edits the sample app's CSS.")
@params(id="the check to fix: colour-tokens, spacing-scale or label-wrap", page="pricing")
def fix_check(id, page="pricing"):
    """Apply one review fix to the sample app (a scratch copy in work/): a hard-coded colour becomes a token, a gap moves onto the scale, or a label is allowed to wrap. Changes the page; Undo puts it back."""
    if not (WORK / "sample-app").is_dir():
        shutil.copytree(SAMPLE, WORK / "sample-app")
    folder = WORK / "sample-app"
    edit = _fix_edit(id, folder)
    if not edit:
        return {"error": {"code": "nothing_to_fix", "message": f"There is nothing to fix for {id} now. It may be fixed already."}}
    file, old, new = edit
    uid = f"fix-{int(time.time() * 1000)}"
    (WORK / "undo" / uid).mkdir(parents=True, exist_ok=True)
    shutil.copy2(folder / file, WORK / "undo" / uid / file)
    line = _line_of(file, old.strip(), folder)
    (folder / file).write_text((folder / file).read_text().replace(old, new, 1))
    label = {"colour-tokens": "the colour uses the accent token", "spacing-scale": "the gap is on the scale",
             "label-wrap": "the label can wrap"}[id]
    return {"fixed": {"id": id, "file": file, "line": line, "before": old.strip(), "after": new.strip() or "(removed)"},
            "toast": f"Fixed: {label}", "undo": {"name": "undo_fix", "context": {"change": uid}}}


@app.post("/api/pages/<page>/fixes/undo")
@reversible
@params(change="the change to take back, from the fix's toast")
def undo_fix(change):
    """Take back one fix to the sample app: its CSS goes back to what it was before."""
    snap = WORK / "undo" / str(change)
    if not re.fullmatch(r"fix-\d+", str(change)) or not snap.is_dir():
        return {"error": {"code": "not_found", "message": "That fix can't be undone any more."}}
    for f in snap.iterdir():
        shutil.copy2(f, WORK / "sample-app" / f.name)
    shutil.rmtree(snap)
    return {"undone": {"change": change}, "toast": "Fix undone"}


# ------------------------------------------------------------------------------------------------ 2. library parts for a page

PAGE_WORDS = {
    "settings": ["settings", "preferences", "toggle", "switch", "members", "roles", "invite", "notifications", "account", "security"],
    "pricing": ["pricing", "plans", "plan", "billing", "compare", "upgrade"],
    "dashboard": ["dashboard", "metrics", "kpi", "chart", "overview", "stats"],
    "sign-in": ["sign in", "login", "password", "code", "verification", "auth"],
}


def _library():
    sys.path.insert(0, str(LIBRARY))
    import library  # noqa: E402  the component library's own reader
    return library


@app.get("/api/library/suggest")
@params(page="the kind of page: settings, pricing, dashboard or sign-in")
def suggest_parts(page="settings"):
    """The component library's best parts for one kind of page (3 to 5): name, what each is for, its kind and style, and whether it uses only your design tokens."""
    lib = _library()
    words = PAGE_WORDS.get(str(page).lower().strip(), [str(page).lower().strip()])
    toks = set(token_values())
    ranked = []
    comps = lib.components()
    for c in comps:
        keys = [k.lower() for k in c.get("tags", {}).get("keywords", [])] if isinstance(c.get("tags"), dict) else [str(t).lower() for t in c.get("tags", [])]
        use = " ".join(c.get("spec", {}).get("use_when", []) if isinstance(c.get("spec"), dict) else []).lower() + " " + str(c.get("use", "")).lower()
        about = (c.get("name", "") + " " + c.get("summary", "")).lower()
        has = lambda w, t: bool(re.search(rf"\b{re.escape(w)}\b", t))
        score = sum(3 * (w in keys) + 2 * has(w, use) + has(w, about) for w in words)
        if score >= 6:
            ranked.append((score, c))
    ranked.sort(key=lambda x: (-x[0], x[1]["slug"]))
    parts = []
    for score, c in ranked[:4]:
        src = (lib.LIB / c["slug"] / "component.html").read_text()
        used = lib.used_vars(src)
        missing = sorted(used - toks)
        hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", "".join(re.findall(r"<style>(.*?)</style>", src, re.S)))
        summary = c.get("summary", "")
        first = re.split(r"(?<=[.!?])\s", summary)[0]
        while len(first) > 110 and "," in first:  # a long first sentence ends at its last clause that fits
            first = first.rsplit(",", 1)[0]
        parts.append({"id": c["slug"], "name": c.get("name", c["slug"]), "for": first.rstrip(".") + ".",
                      "kind": f"{c.get('type', 'part').capitalize()} part, {c.get('style', 'any')} style",
                      "tokens_used": len(used), "tokens_only": not missing and not hexes, "missing_tokens": missing[:5], "fit": score})
    return {"page": page, "searched": len(comps), "parts": parts,
            "note": f"{len(parts)} of {len(comps)} library parts fit a {page} page"}


@app.post("/api/kit")
@reversible
@params(id="a library part's id, such as settings-toggles")
def add_part(id):
    """Add one library part to the project's kit (a scratch folder in work/kit): its HTML, ready to use with your tokens. Undo removes it."""
    if not re.fullmatch(r"[a-z0-9-]+", str(id)) or not (_library().LIB / str(id) / "component.html").is_file():
        return {"error": {"code": "not_found", "message": f"There is no library part called {id}."}}
    kit = WORK / "kit"
    r = subprocess.run([sys.executable, str(LIBRARY / "library.py"), "add", str(id), "--into", str(kit), "--tokens", str(TOKENS)],
                       capture_output=True, text=True, timeout=60)
    if r.returncode:
        return {"error": {"code": "add_failed", "message": (r.stderr or r.stdout).strip()[-160:] or "The part couldn't be added."}}
    name = json.loads((_library().LIB / str(id) / "meta.json").read_text()).get("name", id)
    return {"added": {"id": id, "name": name, "into": "work/kit"}, "toast": f"{name} added to your kit",
            "undo": {"name": "remove_part", "context": {"id": id}}}


@app.post("/api/kit/remove")
@reversible
@params(id="the part to take out of the kit")
def remove_part(id):
    """Take one part back out of the kit."""
    removed = False
    if re.fullmatch(r"[a-z0-9-]+", str(id)):
        for p in (WORK / "kit").glob(f"{id}*"):
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            removed = True
    if not removed:
        return {"error": {"code": "not_found", "message": f"{id} is not in the kit."}}
    return {"removed": {"id": id}, "toast": "Taken out of your kit"}


# ------------------------------------------------------------------------------------------------ 3. token use

KINDS = [("Colour", r"^(color|background(-color)?|border(-[a-z]+)?-color|outline-color|fill|stroke|accent-color)$", "--ds-color-"),
         ("Spacing", r"^(padding|margin|gap|row-gap|column-gap|inset)(-[a-z-]+)?$", "--ds-space-"),
         ("Corners", r"^border(-[a-z-]+)?-radius$", "--ds-radius-"),
         ("Type", r"^(font|font-size|font-family|font-weight|line-height|letter-spacing)$", ("--ds-text-", "--ds-font-")),
         ("Shadows", r"^box-shadow$", ("--ds-elevation-", "--ds-shadow-"))]
LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)|(?<![\w-])-?\d*\.?\d+(px|rem|em)\b")


def _kind_of_var(name):
    for kind, _, prefix in KINDS:
        if name.startswith(prefix):
            return kind
    return None


@app.get("/api/tokens/use")
def token_use():
    """How much of the sample app's CSS uses the design tokens: values that come from var(--ds-*) and values typed by hand, in total and per kind (colour, spacing, corners, type, shadows), as counts and percentages, with each value typed by hand and where it is."""
    counts = {k: {"from_tokens": 0, "by_hand": 0} for k, _, _ in KINDS}
    hand = []
    files = sample_css()
    for file, line, sel, d in rules():
        for prop, value in d:
            for v in re.findall(r"var\((--ds-[\w-]+)", value):
                k = _kind_of_var(v)
                if k:
                    counts[k]["from_tokens"] += 1
            pk = next((k for k, pat, _ in KINDS if re.match(pat, prop)), None)
            if prop.startswith(("border", "outline")) and not pk:
                pk = "Colour"  # a border or outline shorthand: only its colour counts here
                literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)", value)
            else:
                literals = [m.group(0) for m in LITERAL.finditer(re.sub(r"var\([^)]*\)", "", value))] if pk else []
            for lit in literals:
                if re.fullmatch(r"-?0+(\.0+)?(px|rem|em)?", lit):
                    continue  # zero is zero in every system
                counts[pk]["by_hand"] += 1
                hand.append({"kind": pk, "value": lit, "property": prop, "file": file,
                             "line": _line_of(file, f"{prop}: {value}"[:40]) or line})
    kinds = []
    for k, c in counts.items():
        n = c["from_tokens"] + c["by_hand"]
        if n:
            kinds.append({"kind": k, "values": n, **c, "share": round(100 * c["from_tokens"] / n)})
    kinds.sort(key=lambda x: (x["share"], -x["values"]))  # the weakest first
    tf, tb = sum(k["from_tokens"] for k in kinds), sum(k["by_hand"] for k in kinds)
    total = {"values": tf + tb, "from_tokens": tf, "by_hand": tb, "share": round(100 * tf / (tf + tb)) if tf + tb else 0}
    return {"files": [f.name for f in files], "total": total, "kinds": kinds, "by_hand_values": hand,
            "weakest": kinds[0]["kind"] if kinds and kinds[0]["share"] < 100 else None}


# ------------------------------------------------------------------------------------------------ 4. a glossary fact

@app.get("/api/glossary/<term>")
@params(term="a design-system word, such as design token, semantic token, accent colour or spacing scale")
def define(term="design token"):
    """What one design-system word means, in plain words, from OpenDesigner's glossary: the definition, other names for it, and what designers and code call it."""
    q = re.sub(r"^(what\s+(is|are)\s+)?(an?|the)\s+", "", str(term).lower().strip(" ?.")).replace("colour", "color")
    glossary = json.loads(GLOSSARY.read_text())
    def names(t):
        return [t["term"].lower(), *[a.lower() for a in t.get("aliases") or []], t["id"].split(".", 1)[-1].replace("-", " ")]
    hit = next((t for t in glossary if q in names(t)), None) or next((t for t in glossary if q.rstrip("s") in names(t)), None)
    if not hit:
        close = [t["term"] for t in glossary if q and any(w in t["term"].lower() for w in q.split())][:5]
        return {"error": {"code": "not_found", "what": "term", "message": f"The glossary has no entry for {term}.",
                          "what_to_do": "Try one of: " + ", ".join(close) if close else "Ask about a word such as design token or spacing scale."}}
    return {"term": hit["term"], "plain": hit["plain"], "also_called": hit.get("aliases") or [],
            "designers_say": hit.get("designer_says"), "in_code": hit.get("code_name"), "from": "OpenDesigner's glossary",
            "terms_in_glossary": len(glossary)}


# ------------------------------------------------------------------------------------------------ 5. a change to the system

ROLES = [("--ds-radius-detail", "Small details"), ("--ds-radius-control-sm", "Small buttons"), ("--ds-radius-control", "Buttons and fields"),
         ("--ds-radius-container", "Cards and panels"), ("--ds-radius-overlay", "Dialogs and menus")]
STEP = 10  # one step of the roundness dial; 90 is the roundest before buttons turn into pills


def _system():
    """The scratch copy of the system that changes are made to (work/system/opendesigner), made on first use."""
    d = WORK / "system" / "opendesigner"
    if not d.is_dir():
        shutil.copytree(HERE / "opendesigner", d, ignore=shutil.ignore_patterns("smart-ui"))
    return d


def _radii(system):
    toks = token_values(system / "build" / "css" / "tokens.css")
    return {name: resolve(f"var({name})", toks).strip() for name, _ in ROLES}


def _roundness(system):
    return json.loads((system / "state.json").read_text())["dials"]["roundness"]["value"]


def _engine(system, *args):
    r = subprocess.run([sys.executable, str(ENGINE), "--dir", str(system), *args], cwd=system.parent, capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[-200:])
    return r.stdout


def _set_roundness(system, value):
    _engine(system, "set", "dials.roundness", str(value), "--set-by", "delegated", "--no-doc",
            "--why", "The person asked the assistant to change the corners and said yes to it")
    _engine(system, "generate")
    _engine(system, "export", "--format", "css")


def _uses(names):
    """How many places use these radius tokens: the sample app's CSS and the component library's parts."""
    pat = re.compile(r"var\((" + "|".join(re.escape(n) for n in names) + r")\)") if names else None
    app_n = sum(len(pat.findall(f.read_text())) for f in sample_css()) if pat else 0
    lib = _library().LIB
    parts = [d.name for d in lib.iterdir() if d.is_dir() and pat and (d / "component.html").is_file() and pat.search((d / "component.html").read_text())]
    lib_n = sum(len(pat.findall((lib / p / "component.html").read_text())) for p in parts) if pat else 0
    return {"total": app_n + lib_n, "in_sample_app": app_n, "in_library": lib_n, "library_parts": len(parts)}


def _corners(step, run):
    system = _system()
    now = _roundness(system)
    up = str(step).lower().strip() not in ("down", "less", "smaller", "sharper")
    to = max(0, min(90, now + (STEP if up else -STEP)))
    if to == now:
        return None, {"error": {"code": "at_the_end", "message": f"The corners are already as {'round' if up else 'sharp'} as this step allows.",
                                "what_to_do": f"Ask to make them {'sharper' if up else 'rounder'} instead."}}
    before = _radii(system)
    target = run(system, to)
    after = _radii(target)
    rows = [{"token": n, "role": label, "before": before[n], "after": after[n], "change": f"{before[n]} to {after[n]}"}
            for n, label in ROLES if before[n] != after[n]]
    return target, {"step": "up" if up else "down", "dial": {"name": "roundness", "from": now, "to": to}, "radius": rows,
                    "places": _uses([r["token"] for r in rows])}


@app.get("/api/system/corners/preview")
@params(step="up (rounder) or down (sharper)")
def preview_corners(step="up"):
    """What changing the corner radius one step would do, without changing anything: each radius token before and after, and how many places use them."""
    def trial(system, to):
        t = WORK / "trial" / "opendesigner"
        shutil.rmtree(t.parent, ignore_errors=True)
        shutil.copytree(system, t)
        _set_roundness(t, to)
        return t
    target, out = _corners(step, trial)
    shutil.rmtree(WORK / "trial", ignore_errors=True)
    return out


@app.post("/api/system/corners")
@warns("This changes every screen that uses these radius tokens.")
@params(step="up (rounder) or down (sharper)")
def change_corners(step="up"):
    """Change the design system's corner radius one step (rounder or sharper) with the engine, on the scratch copy of the system: every radius token moves together. Changes the system; Undo puts it back."""
    uid = f"corners-{int(time.time() * 1000)}"

    def apply(system, to):
        snap = WORK / "undo" / uid
        shutil.rmtree(snap, ignore_errors=True)
        shutil.copytree(system, snap)
        _set_roundness(system, to)
        return system
    target, out = _corners(step, apply)
    if target is None:
        return out
    return {**out, "toast": "Corners changed in your system", "undo": {"name": "undo_corners", "context": {"change": uid}}}


@app.post("/api/system/corners/undo")
@reversible
@params(change="the change to take back, from the toast")
def undo_corners(change):
    """Take back a corner change: the system's state and tokens go back to what they were before it."""
    snap = WORK / "undo" / str(change)
    if not re.fullmatch(r"corners-\d+", str(change)) or not snap.is_dir():
        return {"error": {"code": "not_found", "message": "That change can't be undone any more."}}
    system = WORK / "system" / "opendesigner"
    shutil.rmtree(system)
    shutil.copytree(snap, system)
    shutil.rmtree(snap)
    return {"undone": {"change": change, "roundness": _roundness(system)}, "radius": _radii(system), "toast": "Corner change undone"}


def run_to_end(value):
    """A read action's whole result: a generator (review_page) is run to its last yield."""
    if hasattr(value, "__next__"):
        last = None
        for last in value:
            pass
        return last
    return value


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "skills" / "opendesigner-smart-ui" / "scripts"))
    import live
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8030)
    ap.add_argument("--provider", choices=["anthropic", "claude-cli", "gemini", "recorded"])
    a = ap.parse_args()
    live.serve(__file__, a.port, a.provider)
