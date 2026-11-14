# Orchestration: a data agent and a UI agent, side by side

An answer should start to appear before the facts are in. So a turn runs two lanes at the same time, and they meet when the data lands:

| Lane | What it does | In `live.py` |
|---|---|---|
| **Data agent** | Finds the facts: the app's own read actions, a search over documents (RAG), a database query | `Conversation.route` (by the question's words; a model only when it's unclear), then `Conversation.stream` on a worker thread |
| **UI agent** | Picks the part, announces it, draws its outline, fills it as data arrives, checks it | `Conversation._planned` (a part made ahead of time) and `smartui.pick_template`, then `smartui.validate` |
| **Writer** | One or two sentences about what matters | one model call, text only, streamed |

The orchestrator is `Conversation.answer`. It never waits for one lane before starting the other: the outline is on screen in a few milliseconds, while the data agent is still working.

## Parts made ahead of time

At scope time, each read action the assistant can call gets a part bound to its data, saved in `opendesigner/smart-ui/templates.json`:

```bash
python3 smartui.py templates --app server.py --write     # drafts, from the shape of each action's real result
```

A template is the part with placeholders: `{path}`, lists with `{"each": path, "item": {...}}`, conditions with `{"when": cond, "then": x}`, and tones set by the data with `{"tone": path, "map": {"Unpaid": "warning", "*": "success"}}`. Green for good and red for bad come from the system's tokens and the data's own values, never from a model's taste. The owner edits the drafts (titles, labels, which fields show). The full syntax is in `scripts/smartui.py` above `bind()`.

At run time the template fills by code from the data, so it can't be invalid for that data and needs no repair. The model writes only the sentence. A question with no template (or one that wants a different part, say a chart instead of the drafted table) falls back to a part the model writes, checked the same way.

## What the person sees, in order

The reference server streams one JSON object per line (`/api/chat` with `"stream": true`). `od-chat.js` draws them and also dispatches each as an `od-chat-event` on the page, so a "what runs behind the answer" panel can show the lanes.

1. `{"type": "call", "name": "show_ui", "intent", "part"}`: the tool call that picked the part, shown as a small chip.
2. `{"type": "shell", "part"}`: the part's outline, drawn from its own markup (loading blocks where values will go).
3. `{"type": "lane", "lane": "data" | "ui" | "text", "step", "status", "ms"}`: each step of each lane, with its time.
4. `{"type": "part", "answer", "data"}`: the part filled from the data. A read action that is a generator yields its result as it grows, and each yield fills the part further (one check, one row at a time).
5. `{"type": "text", "text"}`: the sentence, as it streams.
6. `{"type": "done", ...}`: the checked turn.

## Changes and feedback

- A change the person asks for gets an approval prompt that states its consequences (`@warns`, rule `R3-consequence`).
- A change that can be undone (`@reversible`), on a button the person was shown, such as Fix on an issue row or Undo in a toast, runs when it's pressed. The app's result carries `"toast"` and `"undo"`, and the page shows a toast with Undo, in the system's colours.
- A button that only starts a change ("Pay £35.00" on a fine card) asks for it: the approval comes next.

## Plugging in your own data agent

The data lane calls whatever the app registers as a read action. To answer from documents or a database, register an action that does that, with a plain description and its parameters:

```python
@app.get("/api/search")
@params(query="what to look for, in the person's words")
def search_docs(query):
    """Passages from the help centre that answer a question, each with its title and link."""
    for batch in retriever.stream(query):        # yield as results arrive: the part fills as they land
        yield {"results": batch}
```

Give it a template (a list of results, for example), and the person sees the list grow while the retriever works. The model sees the same data and cites only it (R6).

## The same pattern over MCP

In Claude or ChatGPT (MCP Apps), the host model is the orchestrator. It can run a data agent (a sub-agent with the app's read tools) and, at the same time, a UI agent that calls `show_ui`:

- `show_ui({"template": "list_fines", "data": <the data agent's result>})` fills the part made ahead of time and checks it. The model writes only its sentence.
- `show_ui({"answer": [...A2UI...]})` is the fallback, for a question no template covers. It is checked too, and errors come back for one repair.

Nothing changes data from `show_ui`. A pressed button comes back as `OD:action <name> <context>` for the host to confirm first.

## Measuring it

`tools/smartui_evals.py --live` logs, per turn: the time to the outline (`shell`), the time to the first data on screen (`first_data`), the time to the full answer, the model calls, the tokens, and whether a part made ahead of time served the turn (`template`). `evals/smart-ui/REPORT.md` has the numbers by model.
