---
title: Smart UI: answers that show your interface
seo_title: "Generative UI from your own design system components"
description: Generative UI with your own design system. Your assistant answers with parts made from your components, filled from your data and checked before they show.
section: Concepts
order: 8
updated: 2026-11-14
---

Smart UI makes your assistant answer by showing your own components instead of plain text. Ask a council's assistant "Do I have any fines?" and it can show the unpaid fine with a Pay button, not three paragraphs. Smart UI comes with OpenDesigner and does this with your own design system: your components, your colours, your type, in any framework. There's nothing separate to install. It stays off until you ask for it, or until OpenDesigner sees an assistant or chat in your product, offers it once, and you say yes.

The model writes the sentence. The interface comes from parts made ahead of time and filled from your data by code, so the model never picks a colour, a size or a link. Every answer is checked before anything shows, and anything that books, pays, sends or deletes waits for the person to press a button.

## How an answer becomes interface

1. **Prepare.** Once, ahead of time. It reads your repo to work out what the product is, who uses it and which kinds of answer it needs: a council needs a fine with a Pay button and an application's progress, a finance app needs charts. Each of your app's read actions gets a part bound to its data (`templates.json`). You check the list and the labels. What it can't find says "not known".
2. **Match.** For each question, a matcher finds the prepared part that fits in under 0.2 ms, with no model. Your agent starts fetching the data at the same moment, so the part's outline is on screen before the data arrives. A short question gets a sentence and no part.
3. **Fill.** The data lands and code fills the part, a row or a value at a time. The data decides the colours through your status tokens: paid is green, overdue is red. Then the model writes one or two sentences about what matters.
4. **Check.** Every part is validated before it renders. A question no prepared part covers falls back to a part the model writes, checked the same way; a mistake goes back to the model once as an error it can fix.
5. **Draw.** `<od-surface>`, a plain HTML element, draws the part from your library and your `tokens.css`. It works in React, Vue, Svelte or plain HTML.

## The rules it keeps

| Rule | What it means |
|---|---|
| Text when text is enough | "When does check-in open?" gets a sentence, not a card. |
| One part per answer | Unless the person asked for more. |
| Changes wait for a tap | Book, pay, send and delete are buttons. Pressing one asks first and says what will happen ("Paying closes the notice"). The model can't press it. |
| The data picks the colour | Green for good and red for bad come from your status tokens and the data's own values. A colour the data contradicts is refused. |
| Nothing off-system | No colours, sizes, styles, HTML or links outside your allow-list. Unknown parts are refused, not dropped. |
| Accessibility floors | AA contrast, 24 px targets (44 px for actions that change data), visible focus, one polite announcement, reduced motion, and no two buttons with the same name. |
| Honest numbers | A number shown must be in the data the assistant was given. Missing stays missing. |
| Your look wins | Inside Claude or ChatGPT, the host's look applies only if you turn it on. |

## What you get

- 26 parts in six jobs: answer, data, choose, act, confirm, and media. They're all in the [component library](/library/), so they work in your product with or without the assistant. The full list, by job, is on the [Smart UI page](/smart-ui/#parts).
- A catalog in the A2UI v1.0 format, an MCP Apps view for Claude and ChatGPT, and a plain-text version for anywhere that shows no interface. See [where it runs](/docs/smart-ui-adapters/).
- An audit of every part in every state (phone and desktop sizes, 200% text, dark mode, right to left) against the accessibility floors, and evals of how Claude and Gemini use it.
- Toasts with Undo for changes that can be undone, in your system's colours.

## Plug in your own agents

You bring your own agents and your own model. Smart UI is the UI step beside them: it gives the parts, the matcher, the checks and a stream of events to draw: the tool call, the outline, each step of each lane, the filled part, the sentence, done. Your data agent can be your API, a search over documents (RAG) or a database query: register it as a read action, and the part fills as its results arrive. The full contract is in the skill's [guide to using your own agents](https://github.com/ckryptickunal/OpenDesigner/blob/main/skills/opendesigner-smart-ui/references/your-agents.md).

## What has been tested

We say what we ran. The parts, the checks and the renderer are tested in Chromium, in two different systems. The catalog and messages pass A2UI's own v1.0 schemas. The MCP Apps view is tested against a simulated host that speaks the protocol. It hasn't been tried yet inside Claude Desktop, claude.ai or ChatGPT. The [evals](/docs/evals/) report how often each model picked the right part, how often its answer passed the first time, and how often it showed a part where text was enough.

[Add it to your assistant](/docs/smart-ui-quickstart/)
