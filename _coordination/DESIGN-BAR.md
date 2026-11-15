# The design bar: read this before building anything people will see

Kunal's rules for every page, figure, demo, video and image in this project, in one place. They come from his reviews since October (`_coordination/OWNER-FEEDBACK.md`). Each one was given more than once because it lived only in one session's memory. Every session that builds something visual reads this file first and checks its work against it before showing anyone. A brief to another session links this file.

## Why first versions keep missing the bar (2026-11-16)
1. **Checks pass while the page looks wrong.** Tests, layout checks and the review measure overflow, contrast and tap size, not taste. Passing them was treated as done.
2. **The rules lived in memory, not in the briefs.** A new session never saw them, so Kunal had to say them again.
3. **The maker graded its own work.** It saw what it meant to build, not what was on screen.
4. **No picture before the build.** Pages were built from a written spec. The one page Kunal liked on the first try (the Smart UI vision sketch) started as a small, approved picture of the target.
5. **More was added than cut.** Every finished piece of work went onto the page, so pages grew cluttered.
6. **We judged the code, not the experience.** Work was checked the way it was built, file by file, never the way a visitor meets it: arriving, scrolling, clicking, waiting. The demo that grew and pushed the page away on every click passed every check (Kunal, 2026-11-16).

## The process
1. **Picture first, in two or three variants.** Before building a page or a section, make one rough screen of the target (static HTML is fine) and get Kunal's yes, or match one he already approved.
2. **Build against this file,** and cut before adding. Every section has to earn its place.
3. **Walk it as a viewer, frame by frame.** Open the built page as someone seeing it for the first time, at 1440 and 375 px, in WebKit. Capture a frame on load, then every 250 ms for 2 s after each scroll and each click on everything clickable. Then look at the frames in order and answer:
   - What do I see first? Where does my eye go?
   - Does anything jump, grow, shift or leave the view? (Note `scrollY` and the bounding boxes of the main blocks before and after each click; they shouldn't change unless the click means to.)
   - Can I read each screen at a glance, without stopping on any text?
   - Does every click answer within a moment, and is it clear what happened?
   - Is anything covered (a banner, a toast, a sticky header)?
   Put the contact sheet of frames in your report. A step that only reads the code doesn't count.
4. **Fresh-eyes visual audit.** Start a new agent with no context. Give it this file, the brief and the walkthrough's frames (never the code), and have it judge them as a first-time visitor. Sort its findings as `_coordination/PROTOCOL.md` section 7 says.
5. **The coordinator walks it too**, frame by frame, before Kunal does.
6. **Kunal sees it locally** before anything is pushed.

## How quality is judged (adapted from Contra Labs' Human Creativity Benchmark)
Source: [contralabs.com/research/human-creativity-benchmark](https://contralabs.com/research/human-creativity-benchmark), April 2026. Across 5,940 pairwise judgments by working designers, they found:
- Judges agree on failures: unreadable text, broken hierarchy, visual artifacts.
- Once those are cleared, disagreement is taste. Usability acted as a gate: outputs scored lowest on it reached the top two only 10% of the time.
- On desktop apps and landing pages, models fell short on the details: typography, spacing, component design, interaction patterns, icons and accessibility.

What we take from it:
1. **A gate, then taste.** The checks and the fresh-eyes audit are the gate: nothing broken, cut off, misaligned or unreadable. Passing the gate makes work showable, not good. Taste is judged next, by Kunal.
2. **Show two, not one.** For a new page, section or visual, show Kunal two or three real variants side by side (`skills/opendesigner/assets/picker.js`), not one first draft. People judge a pair more reliably than a single piece.
3. **Score three things apart:** prompt adherence (it does what the brief asked), usability (people can read it and use it), and visual appeal (taste). The fresh-eyes audit reports all three, each with its reasons.
4. **Polish where models fail.** Before showing anything, spend a refinement pass on exactly those details: type, spacing, component finish, interaction states, icons and accessibility.
5. **Use agreement as the signal.** When two fresh reviewers agree on a problem, it's a gate failure, so fix it. When they disagree, it's taste, so ask Kunal.
6. **Record why he picked.** When Kunal picks a variant, record his reason in `OWNER-FEEDBACK.md`, tagged by theme (layout, hierarchy, usability, colour, type, motion). Themes that recur become rules in this file.

## The rules

**Calm and minimal**
- One idea per section. Short headings, one line of copy, and let the visual carry it. If people would skip it, cut it.
- No explanatory paragraphs under demos or figures. At most one short line where honesty needs it ("Recorded answers"). Details go in alt text or `aria-describedby`. Photo credits go in one line at the foot of the page.
- No developer detail in reader-facing places: no mono component names, function names, timings in ms or debug logs. Fold them, or put them on Reference pages.
- One backdrop for a set of cards, tiles of one size, and one rhythm of section spacing. No big empty gaps.

**Shape and size**
- Corners follow one scale across the page (brand radii 6, 12, 16 and 24, capsule buttons). A demo frame uses the same radius as the cards around it, not a rounder one. Nested corners: inner equals outer minus the gap.
- Frames fit their content. No oversized containers, and no empty space inside a frame.
- **Preview components are drawn at their natural width and scaled down, never squeezed.** A toast, card or button in a thumbnail must look exactly as it does at full size: no text wrapping to three lines, no buttons stacking.
- Interactive demos don't jump. When content grows, the frame keeps a stable height and scrolls inside, or grows smoothly while keeping the new content in view. Never push the page out from under the reader.
- One shell width on every page.

**Type and colour**
- At most two fonts in a section. Sizes come from the type scale, never ad hoc. Titles needn't be bold.
- Strong tonal contrast; one accent on calm neutrals. No gradients, glows or glass frames unless Kunal asked for them. No purple gradients and no emoji icons.
- Status colours follow meaning (`build/status.json`): green for done, amber for needs a look, red for broken. Never colour alone.

**Visuals and motion**
- Demos are live HTML that animates in code, never video or screenshots of HTML. It should look like it's being built while you watch.
- Use real product screens and real Unsplash photos, not placeholders. Use Lucide icons, never hand-drawn ones.
- Motion is fast and confident (the `emil-design-eng` skill), and reduced motion gets the finished state.
- Inspiration: Linear, Stripe, Mercury and Midday: near-monochrome, one accent, real product shots. Use Mobbin generously.

**Words**
- Don't brag. Every claim must be true in the repo today. Use plain words first (`docs/COPY.md`, `tools/copy_check.py`). Sentence case.
- Name the thing in the person's words, not ours.

## Before you show anything
- Corners at 2x: siblings match, and nested corners are right.
- Each preview is at its natural width, with nothing wrapped or stacked that shouldn't be.
- Interactive demos keep their place on click.
- No paragraph explains a visual.
- 1440 and 375 px, in WebKit and Chromium: no sideways scroll, nothing cut off.
- The viewer walkthrough is done (contact sheet attached), and the fresh-eyes audit is done and sorted.
- `site/check_layout.py`, `site/post_change_audit.py` and `opendesigner-review` pass.
