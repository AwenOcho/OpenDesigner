#!/usr/bin/env python3
"""Fill every template in opendesigner/smart-ui/templates.json from its action's real output and check it.

  python3 examples/smart-ui-opendesigner/check_templates.py [--record]

Runs each read action in server.py with its defaults (review_page to its last check, and every partial result on the
way), fills each of its templates with smartui.bind, and validates the part with smartui.validate against the catalog,
the action's own data and the consequences the app's changes declare (@warns). Prints ok or fail for each, and exits 1
on any failure. Changes made while checking (preview_corners runs the engine) go to a temporary folder, not work/.

--record also writes recorded.json: the five suggested questions answered from the same data and templates, with a
sentence made from the data by code (no model), so the page answers with --provider recorded.
"""
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "skills" / "opendesigner-smart-ui" / "scripts"))
import server  # noqa: E402
import smartui  # noqa: E402

CATALOG = json.loads(server.CATALOG.read_text())
TEMPLATES = json.loads((server.CATALOG.parent / "templates.json").read_text())["templates"]
SAID = {name: a["consequences"] for name, a in server.ACTIONS.items() if a["changes"] and a["consequences"]}


def check(template, data):
    """(ok, message) for one template filled from one result."""
    if template.get("when") and not smartui._holds(template["when"], data):
        return None, "its condition does not hold for this data"
    part = smartui.bind(template["part"], data)
    if not isinstance(part, dict) or not part.get("component"):
        return False, "filled to nothing"
    r = smartui.validate(smartui.wrap(part), CATALOG, {"source": data, "copy": True, "consequences": SAID})
    if not r["ok"]:
        return False, "; ".join(f"{e['rule']} {e['path']}: {e['message']}" for e in r["errors"][:4])
    return True, part


def main():
    record = "--record" in sys.argv
    failed = 0
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        server.WORK = pathlib.Path(tmp) / "work"
        for name, a in server.ACTIONS.items():
            if a["changes"]:
                continue
            out = a["fn"]()
            steps = []
            if hasattr(out, "__next__"):
                steps = list(out)
                out = steps[-1]
            results[name] = out
            mine = [t for t in TEMPLATES if t["action"] == name]
            if not mine:
                print(f"--   {name}: no template (answered as a sentence)")
            for i, t in enumerate(mine):
                ok, msg = check(t, out)
                label = f"{name} #{i + 1} {t['part']['component']} ({t.get('intent', '')})"
                if ok:
                    print(f"ok   {label}")
                else:
                    failed += ok is False
                    print(f"{'FAIL' if ok is False else 'skip'} {label}: {msg}")
                for n, partial in enumerate(steps[:-1], 1):  # the part as it grows, one check at a time
                    pok, pmsg = check(t, partial)
                    if pok is False:
                        failed += 1
                        print(f"FAIL {label}, after {n} of {len(steps) - 1} results: {pmsg}")
                if steps:
                    shown = sum(1 for p in steps[:-1] if check(t, p)[0])
                    print(f"     and {shown} of {len(steps) - 1} partial results draw it as the data lands")
        if record:
            write_recorded(results)
    print("all templates pass" if not failed else f"{failed} failed")
    return 1 if failed else 0


def first_part(action, data):
    t = next(t for t in TEMPLATES if t["action"] == action)
    ok, part = check(t, data)
    return smartui.wrap(part) if ok else None


def write_recorded(r):
    rev, parts, use, term, corners = r["review_page"], r["suggest_parts"], r["token_use"], r["define"], r["preview_corners"]
    n = rev["counts"]
    worst = next((c for c in rev["checks"] if c["status"] == "broken"), None)
    weak = use["kinds"][0]
    turns = {
        "Review my pricing page": {
            "text": f"{n['pass']} of {len(rev['checks'])} checks pass. " + (f"{n['broken']} are broken, starting with {worst['title'].lower()}." if worst else "Nothing is broken."),
            "action": "review_page"},
        "Which parts fit a settings page?": {
            "text": f"{len(parts['parts'])} library parts fit a settings page" + (", and all of them use only your tokens." if all(p["tokens_only"] for p in parts["parts"]) else "."),
            "action": "suggest_parts"},
        "How much of my code uses the tokens?": {
            "text": f"{use['total']['share']}% of the values in your CSS come from tokens. {weak['kind']} is the weakest, at {weak['share']}%.",
            "action": "token_use"},
        "What is a design token?": {"text": f"{term['plain']} Change it in that one place, and every screen that uses it changes too.", "action": "define"},
        "Make the corners rounder": {
            "text": f"I can make the corners one step rounder. It changes your system, so it needs your yes.", "action": "preview_corners"},
    }
    out = {}
    for q, t in turns.items():
        data = {t["action"]: r[t["action"]]}
        ans = None if t["action"] == "define" else first_part(t["action"], r[t["action"]])
        if ans is not None and not smartui.validate(ans, CATALOG, {"source": data})["ok"]:
            ans = None
        out[q] = {"text": t["text"], "answer": ans, "data": data, "model": None}
    dest = HERE / "recorded.json"
    dest.write_text(json.dumps({"about": "Answers made by check_templates.py --record from this app's real data and its templates, with sentences written by code, not by a model, so the page works with no model key. Replace them with real model answers with live.py record.",
                                "turns": out}, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {dest.relative_to(HERE)} ({len(out)} turns)")


if __name__ == "__main__":
    sys.exit(main())
