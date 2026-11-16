# Smart UI evals

Made by `python3 tools/smartui_evals.py --report` from `evals/smart-ui/results/`. The cases: `cases.json` (20 that need a part, 5 that should stay text). The data in them is invented.

## The selector alone (no model)

Run 2026-11-16. Recall at 3 (the expected part is among the three sent to the model): **100.0%**. Held back on text-only questions: **100.0%**.

## Models

| Model | Date | Runs | Picked the right part | Valid first time | Held back on text-only | Over-triggered | Rendered | Floor findings |
|---|---|---|---|---|---|---|---|---|
| claude-sonnet-5-5 | 2026-11-13 | 75 (3 per case) | 80.0% | 98.0% | 100.0% | 0.0% | 48 | 0 |
| gemini-3.1-pro-preview | 2026-11-13 | 75 (3 per case) | 95.0% | 93.0% | 100.0% | 0.0% | 53 | 0 |

### What went wrong: claude-sonnet-5-5

- `bars-spend` run 1: showed text, wanted BarChart, LineChart, DataTable
- `bars-spend` run 2: showed text, wanted BarChart, LineChart, DataTable
- `bars-spend` run 3: showed text, wanted BarChart, LineChart, DataTable
- `donut-categories` run 1: showed text, wanted DonutBreakdown, DataTable, BarChart
- `donut-categories` run 2: showed text, wanted DonutBreakdown, DataTable, BarChart
- `donut-categories` run 3: showed text, wanted DonutBreakdown, DataTable, BarChart
- `receipt-seat` run 1: showed text, wanted Receipt, ProgressStatus
- `receipt-seat` run 2: showed text, wanted Receipt, ProgressStatus
- `receipt-seat` run 3: showed text, wanted Receipt, ProgressStatus
- `error-search` run 1: showed text, wanted ErrorRetry
- `error-search` run 2: showed text, wanted ErrorRetry
- `location-hotel` run 3: invalid: length /0/createSurface/components/0/distance text is 48 characters, the most is 40
- `file-invoice` run 3: showed ApprovalPrompt, wanted FileCard

### What went wrong: gemini-3.1-pro-preview

- `facts-hotel` run 2: invalid: root  one component needs id "root"
- `bars-spend` run 1: invalid: required /0/createSurface/components/0/months/0/forecast forecast is required; required /0/createSurface/components/0/months/1/forecast forecast is required
- `bars-spend` run 2: invalid: required /0/createSurface/components/0/months/0/forecast forecast is required; required /0/createSurface/components/0/months/1/forecast forecast is required
- `bars-spend` run 3: invalid: required /0/createSurface/components/0/budget budget is required
- `donut-categories` run 1: showed text, wanted DonutBreakdown, DataTable, BarChart
- `donut-categories` run 2: showed text, wanted DonutBreakdown, DataTable, BarChart
- `donut-categories` run 3: showed text, wanted DonutBreakdown, DataTable, BarChart

## Speed: before and after (billing app, live path)

Per turn, measured around each answer. **Before**: a model routed every turn, the model wrote the whole part as free text, it thought as long as it liked, and nothing showed until the end (one run of each case). **After**: the question's words pick the app's read action and a prepared part with no model, the part's outline shows at once and fills as the data lands, and one short model call writes the sentence (a part the model writes is the fallback). **First** is when something shows (the outline, the filled part or the first words); **full** is the checked answer. Models ran side by side, sharing the API.

| Model | Before: full, p50 / p95 | Calls a turn | After: first, p50 / p95 | After: full, p50 / p95 | Calls a turn | Tokens a turn | Right part, before → after | Approval, before → after |
|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | – / – | – | 5 ms / 9.0 s | 8.3 s / 16.3 s | 1.21 | 75,255 | –% → 82.6% | –% → 100.0% |
| claude-sonnet-5-5 | 15.3 s / 19.6 s | 2.03 | 5 ms / 9.8 s | 6.1 s / 14.9 s | 1.21 | 69,898 | 85.7% → 82.6% | 100.0% → 80.0% |
| gemini-3.1-flash-lite | 4.7 s / 5.7 s | 2.58 | 5 ms / 1.7 s | 1.8 s / 2.9 s | 1.21 | 1,626 | 85.7% → 91.3% | 60.0% → 100.0% |
| gemini-3.1-pro-preview | 21.0 s / 29.0 s | 2.45 | 5 ms / 7.4 s | 7.3 s / 14.5 s | 1.21 | 2,152 | 90.5% → 89.9% | 100.0% → 100.0% |
| gemini-3.8-flash | 14.0 s / 28.3 s | 2.23 | 6 ms / 4.5 s | 3.6 s / 7.3 s | 1.18 | 1,623 | 85.7% → 91.3% | 80.0% → 100.0% |
| gemini-4-argon | 18.0 s / 65.2 s | 2.26 | 5 ms / 7.9 s | 8.0 s / 27.4 s | 1.21 | 2,933 | 90.5% → 91.3% | 100.0% → 100.0% |
| gemini-4-hydrogen | 9.7 s / 15.6 s | 2.06 | 5 ms / 4.2 s | 4.4 s / 10.1 s | 1.21 | 3,229 | 90.5% → 87.0% | 100.0% → 100.0% |

The `claude` rows run through the `claude` command (no API key on this computer): each call starts a Claude Code process, which adds seconds and loads its own context (the tokens column). With an API key the same path uses the Messages API with a forced tool for the schema.

## Prepared parts: Fernhollow, a council service

**Outline** is the prepared part's outline on screen; **first data** is the part filled with the first data. **Turns**: filled from a prepared part by code / a prepared part with a small edit from the model (rows kept, ordered or filtered, details hidden, another variant) / a part the model wrote (the fallback) / text only.

| Model | Runs | Right part | Valid first time | After one repair | Held back (text-only) | Outline, p50 / p95 | First data, p50 / p95 | Full, p50 / p95 | Turns: filled / edited / written / text | Calls a turn |
|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 99 | 96.3% | 92.8% | 100.0% | 100.0% | 2 ms / 5 ms | 3 ms / 2.8 s | 1.5 s / 2.9 s | 38.0% / 20.4% / 25.0% / 16.7% | 1.09 |
| gemini-3.1-pro-preview | 99 | 93.8% | 97.4% | 100.0% | 100.0% | 2 ms / 5 ms | 3 ms / 12.2 s | 5.7 s / 12.0 s | 45.4% / 13.0% / 20.4% / 21.3% | 1.06 |
| gemini-3.8-flash | 99 | 100.0% | 95.1% | 100.0% | 100.0% | 2 ms / 4 ms | 3 ms / 6.5 s | 2.8 s / 6.5 s | 47.2% / 11.1% / 25.0% / 16.7% | 1.06 |
| gemini-4-argon | 99 | 100.0% | 91.7% | 100.0% | 100.0% | 3 ms / 4 ms | 4 ms / 11.9 s | 6.0 s / 14.9 s | 50.0% / 8.3% / 25.0% / 16.7% | 1.09 |
| gemini-4-hydrogen | 99 | 100.0% | 96.3% | 100.0% | 100.0% | 2 ms / 6 ms | 3 ms / 7.6 s | 3.0 s / 7.6 s | 47.2% / 11.1% / 25.0% / 16.7% | 1.06 |

### The fines question in ten wordings

`fh-fines-w01` to `w10` ask whether there is a fine in ten different ways ("have I got any parking fines?", "did I get a parking ticket?", "my penalty charge notice"...). Right means the fine card with its Pay button, the discount date and no payment prompt.

| Model | Runs | Card with Pay, every time | First answer passed | Repaired |
|---|---|---|---|---|
| gemini-3.1-flash-lite | 30 | 100.0% | 100.0% | 0.0% |
| gemini-3.1-pro-preview | 30 | 100.0% | 100.0% | 0.0% |
| gemini-3.8-flash | 30 | 100.0% | 100.0% | 0.0% |
| gemini-4-argon | 30 | 100.0% | 100.0% | 0.0% |
| gemini-4-hydrogen | 30 | 100.0% | 100.0% | 0.0% |

## Prepared parts: OpenDesigner on a sample app

**Outline** is the prepared part's outline on screen; **first data** is the part filled with the first data. **Turns**: filled from a prepared part by code / a prepared part with a small edit from the model (rows kept, ordered or filtered, details hidden, another variant) / a part the model wrote (the fallback) / text only.

| Model | Runs | Right part | Valid first time | After one repair | Held back (text-only) | Outline, p50 / p95 | First data, p50 / p95 | Full, p50 / p95 | Turns: filled / edited / written / text | Calls a turn |
|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 15 | 100.0% | 100.0% | 100.0% | 100.0% | 2 ms / 3 ms | 17 ms / 722 ms | 2.0 s / 2.4 s | 26.7% / 53.3% / 0.0% / 20.0% | 1.0 |
| gemini-3.1-pro-preview | 15 | 100.0% | 100.0% | 100.0% | 100.0% | 2 ms / 2 ms | 14 ms / 724 ms | 5.4 s / 7.1 s | 80.0% / 0.0% / 0.0% / 20.0% | 1.0 |
| gemini-3.8-flash | 15 | 100.0% | 100.0% | 100.0% | 100.0% | 2 ms / 2 ms | 16 ms / 759 ms | 3.1 s / 3.9 s | 80.0% / 0.0% / 0.0% / 20.0% | 1.0 |
| gemini-4-argon | 15 | 100.0% | 100.0% | 100.0% | 100.0% | 2 ms / 4 ms | 17 ms / 678 ms | 6.9 s / 10.2 s | 80.0% / 0.0% / 0.0% / 20.0% | 1.0 |
| gemini-4-hydrogen | 15 | 100.0% | 100.0% | 100.0% | 100.0% | 2 ms / 4 ms | 21 ms / 941 ms | 3.4 s / 4.2 s | 80.0% / 0.0% / 0.0% / 20.0% | 1.0 |

## Different products, different answers

`smartui.py usecases` on three example products, from each one's own data, actions, description and screens (none of the three has research files, which the step reports as a gap). Best first.

| Fernhollow council (public-service) | Tallyhaus billing (work-tool) | Orvell travel (travel) |
|---|---|---|
| table: DataTable | ask before a change: ApprovalPrompt | ask before a change: ApprovalPrompt |
| record details: KeyFacts | table: DataTable | table: DataTable |
| ask before a change: ApprovalPrompt | record details: KeyFacts | record details: KeyFacts |
| form: FormFields | chart over time: LineChart | compare options: Comparison |
| progress: ProgressStatus | headline numbers: KpiStrip | results to pick from: FlightResults |
| pick a time: TimeSlots | file: FileCard | pictures: ImageCard |
| place: LocationCard | compare options: Comparison | place: LocationCard |
| what happened: Receipt | what happened: Receipt | pick a time: TimeSlots |
| compare options: Comparison |  | what happened: Receipt |

## How the prepared part is found

- **Lexical first, measured.** A BM25-style index (`smartui.Matcher`) over each prepared part's intent and example phrasings (weighted most), its action's name and description, the data fields it binds, its title and the scope's phrases for that route. Words match on their stems and on a shared start of four letters. It runs in about 0.03 to 0.2 ms per question on these examples.
- **Why not embeddings.** The skill runs offline, from the standard library, wherever the person's agent runs: no packages, no network, no keys. On these products the questions use the app's own words (fines, permit, invoices), and the cases that missed were fixed by data the app owns (a description that says "also called a parking ticket"), not by meaning-matching. A product with a wide vocabulary can add its own embedding index beside `Matcher`; the interface is one call that returns ranked templates.
- **A model only when it's close.** When the router isn't sure (the best match needs a value the question doesn't give, "the refunded one") and the matcher's top two belong to different actions, a small model call routes. Otherwise no model runs before the sentence.

## Spend

Tokens counted from the provider's own usage figures in every result file here, priced per million tokens at November 2026 list prices (third-party pricing pages; Argon at its introductory rate). Runs that were stopped and rerun after a fix are not in these files, so the real total was higher.

| Model | Calls | Input tokens | Output tokens | Price in / out | Cost |
|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 333 | 393,457 | 43,939 | $0.25 / $1.50 | $0.16 |
| gemini-3.1-pro-preview | 325 | 381,466 | 198,105 | $2.00 / $12.00 | $3.14 |
| gemini-3.8-flash | 315 | 371,375 | 88,337 | $0.75 / $3.75 | $0.61 |
| gemini-4-argon | 526 | 814,796 | 100,116 | $2.00 / $10.00 | $2.63 |
| gemini-4-hydrogen | 502 | 759,536 | 265,155 | $1.50 / $7.50 | $3.13 |
| **Total** | | | | | **$9.67** |

Claude ran through the `claude` command on the owner's subscription: tokens, no API bill.

## The live path (examples/smart-ui-support)

A real model routes to the app's read actions, answers, and the answer is validated against the data it got, with one repair round. Cases come from `live-cases.json`: 21 that need a part (some are follow-ups that need the conversation, five are changes that must end in an approval prompt) and 5 that should stay text. Round 3 added `invoices-unpaid` (a table must name every column) and counts wording problems (Title Case, filler, a value shown twice) as failures of the first answer, so its "valid first time" is not comparable with rounds 1 and 2.

| Run | Model | Date | Runs | Selector recall | Right part | Valid first time | Valid after one repair | Held back (text-only) | Approval shown for changes | Changes the model ran | Rendered | Floor findings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| live-claude-haiku-5-5 | claude-haiku-5-5 | 2026-11-16 | 28 | 65.2% | 82.6% | 95.2% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |
| live-claude-round1 | claude-sonnet-5-5 | 2026-11-14 | 75 | 60.0% | 68.3% | 75.6% | 100.0% | 100.0% | 100.0% | 0 | 41 | 0 |
| live-claude-round2 | claude-sonnet-5-5 | 2026-11-14 | 75 | 85.0% | 80.0% | 93.9% | 98.0% | 100.0% | 80.0% | 0 | 48 | 0 |
| live-claude-round3 | claude-sonnet-5-5 | 2026-11-14 | 78 | 85.7% | 85.7% | 94.4% | 100.0% | 100.0% | 100.0% | 0 | 54 | 0 |
| live-claude-sonnet-5-5 | claude-sonnet-5-5 | 2026-11-16 | 28 | 65.2% | 82.6% | 95.2% | 100.0% | 100.0% | 80.0% | 0 | 0 | 0 |
| live-fernhollow-gemini-3.1-flash-lite | gemini-3.1-flash-lite | 2026-11-16 | 99 | 29.6% | 96.3% | 92.8% | 100.0% | 100.0% | 75.0% | 0 | 77 | 6 |
| live-fernhollow-gemini-3.1-pro-preview | gemini-3.1-pro-preview | 2026-11-16 | 99 | 29.6% | 93.8% | 97.4% | 100.0% | 100.0% | 91.7% | 0 | 72 | 2 |
| live-fernhollow-gemini-3.8-flash | gemini-3.8-flash | 2026-11-16 | 99 | 29.6% | 100.0% | 95.1% | 100.0% | 100.0% | 100.0% | 0 | 77 | 6 |
| live-fernhollow-gemini-4-argon | gemini-4-argon | 2026-11-16 | 99 | 29.6% | 100.0% | 91.7% | 100.0% | 100.0% | 100.0% | 0 | 77 | 6 |
| live-fernhollow-gemini-4-hydrogen | gemini-4-hydrogen | 2026-11-16 | 99 | 29.6% | 100.0% | 96.3% | 100.0% | 100.0% | 100.0% | 0 | 77 | 4 |
| live-gemini-3.1-flash-lite | gemini-3.1-flash-lite | 2026-11-16 | 84 | 65.2% | 91.3% | 95.7% | 100.0% | 100.0% | 100.0% | 0 | 67 | 3 |
| live-gemini-3.1-pro-preview | gemini-3.1-pro-preview | 2026-11-16 | 84 | 69.6% | 89.9% | 95.4% | 100.0% | 100.0% | 100.0% | 0 | 63 | 3 |
| live-gemini-3.8-flash | gemini-3.8-flash | 2026-11-16 | 84 | 65.2% | 91.3% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 67 | 3 |
| live-gemini-4-argon-round3 | gemini-4-argon | 2026-11-14 | 78 | 85.7% | 85.7% | 75.9% | 100.0% | 100.0% | 100.0% | 0 | 54 | 4 |
| live-gemini-4-argon | gemini-4-argon | 2026-11-16 | 84 | 65.2% | 91.3% | 95.7% | 100.0% | 100.0% | 100.0% | 0 | 67 | 4 |
| live-gemini-4-hydrogen-round3 | gemini-4-hydrogen | 2026-11-14 | 78 | 85.7% | 90.5% | 96.5% | 100.0% | 100.0% | 100.0% | 0 | 57 | 0 |
| live-gemini-4-hydrogen | gemini-4-hydrogen | 2026-11-16 | 84 | 65.2% | 87.0% | 95.5% | 100.0% | 100.0% | 100.0% | 0 | 64 | 3 |
| live-gemini-round1 | gemini-3.1-pro-preview | 2026-11-14 | 75 | 60.0% | 65.0% | 79.5% | 100.0% | 100.0% | 86.7% | 0 | 39 | 0 |
| live-gemini-round2 | gemini-3.1-pro-preview | 2026-11-14 | 75 | 80.0% | 88.3% | 84.9% | 100.0% | 100.0% | 93.3% | 0 | 53 | 0 |
| live-gemini-round3 | gemini-3.1-pro-preview | 2026-11-14 | 78 | 85.7% | 84.1% | 34.0% | 98.1% | 100.0% | 93.3% | 0 | 53 | 0 |
| live-opendesigner-gemini-3.1-flash-lite | gemini-3.1-flash-lite | 2026-11-16 | 15 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |
| live-opendesigner-gemini-3.1-pro-preview | gemini-3.1-pro-preview | 2026-11-16 | 15 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |
| live-opendesigner-gemini-3.8-flash | gemini-3.8-flash | 2026-11-16 | 15 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |
| live-opendesigner-gemini-4-argon | gemini-4-argon | 2026-11-16 | 15 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |
| live-opendesigner-gemini-4-hydrogen | gemini-4-hydrogen | 2026-11-16 | 15 | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 |

## Earlier rounds of the recorded-data path

| Round | Model | Right part | Valid first time | Held back |
|---|---|---|---|---|
| claude-round1 | claude-sonnet-5-5 | 33.3% | 37.3% | 100.0% |
| claude-round2 | claude-sonnet-5-5 | 80.0% | 98.0% | 100.0% |
| gemini-round1 | gemini-3.1-pro-preview | 95.0% | 93.0% | 100.0% |

## Not measured

- On the recorded-data path, a failed answer is not sent back to the model; the live path does one repair round.
- Round 2 of the live path ran while the billing catalog was regenerated once (optional fields, list item names); later cases used the new one.
- Round 3: both models answered `subscription` ("What plan are we on and when does it renew?") and `refund-followup` in text although the selector offered a part; it is not clear a part is better there.
- The selector's 100% on the recorded-data cases is on the same cases used to tune it; the live cases were written before its last changes.
- Streaming: every reply is scored whole.
- Copy quality inside the parts, and whether a person would prefer the part to text.
