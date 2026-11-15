# Demo: status colours and feedback as rules

About four minutes, from a clean scratch folder. Run the commands from the repository's top folder. Nothing in this repository changes.

## 0. A clean scratch folder

```bash
export DEMO="$(mktemp -d)" HOME="$(mktemp -d)" && export OD_HOME="$HOME/.opendesigner" XDG_CONFIG_HOME="$HOME/.config" GIT_CONFIG_GLOBAL=/dev/null
```

```bash
export E="$PWD/skills/opendesigner/scripts/engine.py" && mkdir "$DEMO/app" && cp -R examples/devtool-dense "$DEMO/app/opendesigner" && cd "$DEMO/app" && mv opendesigner/DESIGN.md opendesigner/PRODUCT.md .
```

## 1. The status map

```bash
python3 "$E" build >/dev/null && python3 -m json.tool opendesigner/build/status.json | head -30
```

Each status (success, warning, danger, info, discovery) with what it means, when to use it, words and an icon, the token for text, background, border and icon, the CSS name of each, and the values in each mode. Then the rule "never colour alone" and how actions are confirmed.

## 2. The rules in DESIGN.md

```bash
sed -n '/^## Status and Feedback/,/^## Do/p' DESIGN.md
```

## 3. An answer changes the rules

```bash
python3 "$E" pick Q-form-04 toasts-widely --set-by assumed >/dev/null && python3 "$E" build >/dev/null && grep "Toasts:" DESIGN.md
```

Toasts close after 4 s, one with Undo or Retry stays until the person acts, and errors never close on their own.

## 4. What review asks a person to judge

```bash
printf '<style>\n.btn-primary{background:var(--ds-color-bg-success-bold)}\n</style>\n<span style="color:var(--ds-color-text-danger)">Payment</span>\n<form method="post"><button>Save</button></form>\n' > page.html
```

```bash
python3 "$E" review --project . | grep -A4 "For a person to judge"
```

You should see three notes, apart from the counted findings:
- a success colour on a primary button;
- a status shown by colour alone;
- a form with nothing shown back.

None of them changes review's verdict, because code alone cannot be sure.
