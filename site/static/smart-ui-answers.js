// The Smart UI page's answer demo (site/smart_ui_page.py writes every view as a <template>; this only swaps them).
// Tabs pick the assistant; on the second stage, Layout and Look redraw the same answer. On phones (820 px or less) every layout is
// the window with the rail below, and the window and the view take the tallest answer's height, so nothing below moves on a click.
(() => {
  const T = {};
  document.querySelectorAll("template[data-sd-t]").forEach(t => { T[t.dataset.sdT] = t; });
  if (!Object.keys(T).length) return;
  const KEYS = ["shop", "places", "council", "review"];
  const LAY = { canvas: 2, window: 1, single: 3 };
  const mq = matchMedia("(max-width: 820px)");
  const fill = (view, key) => view.replaceChildren(T[key].content.cloneNode(true));
  const press = (group, b) => group.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));

  // phones: measure every answer in this view (synchronously, so nothing paints in between), then fix the heights
  function size(view, v, current) {
    view.style.removeProperty("--sd-win-h");
    view.style.removeProperty("--sd-view-h");
    if (!mq.matches || v !== 1 || !view.offsetParent) return;
    let win = 0, all = 0;
    for (const k of KEYS) { fill(view, `${k}-1`); win = Math.max(win, view.querySelector(".sd-win").getBoundingClientRect().height); }
    view.style.setProperty("--sd-win-h", Math.ceil(win) + "px");
    for (const k of KEYS) { fill(view, `${k}-1`); all = Math.max(all, view.getBoundingClientRect().height); }
    view.style.setProperty("--sd-view-h", Math.ceil(all) + "px");
    fill(view, `${current}-1`);
  }

  const hero = document.querySelector('[data-sd="hero"]');
  const any = document.querySelector('[data-sd="any"]');
  const state = { hero: hero && hero.dataset.tab, any: any && any.dataset.tab, lay: "window", look: "blue" };

  function drawHero(swap) {
    if (!hero) return;
    for (const view of hero.querySelectorAll(".sd-view")) {
      const v = Number(view.dataset.v);
      fill(view, `${state.hero}-${v}`);
      size(view, v, state.hero);
      view.classList.toggle("sd-swap", !!swap);
    }
  }
  function drawAny(swap) {
    if (!any) return;
    const v = mq.matches ? 1 : LAY[state.lay];
    const view = any.querySelector(".sd-view");
    any.className = `sd sd-any sd-lay-${v} sd-look-${state.look}`;
    view.className = `sd-view sd-v${v}`;
    view.dataset.v = v;
    fill(view, `${state.any}-${v}`);
    size(view, v, state.any);
    view.classList.toggle("sd-swap", !!swap);
  }

  document.addEventListener("click", e => {
    const b = e.target.closest(".sd button, .sd-ctrls button");
    if (!b) return;
    if (b.dataset.k) {
      const box = b.closest("[data-sd]");
      const which = box.dataset.sd;
      if (state[which] === b.dataset.k) return;
      state[which] = b.dataset.k;
      press(b.parentElement, b);
      which === "hero" ? drawHero(true) : drawAny(true);
    } else if (b.dataset.l) {
      state.lay = b.dataset.l; press(b.parentElement, b); drawAny(true);
    } else if (b.dataset.o) {
      state.look = b.dataset.o; press(b.parentElement, b); drawAny(true);
    }
  });

  const redraw = () => { drawHero(false); drawAny(false); };
  if (mq.matches) redraw();  // wide screens already show the finished answers the page was built with
  mq.addEventListener("change", redraw);
  // a new width on a phone changes how the answers wrap: measure again before the next paint (width only, so the heights
  // this sets never call it again)
  let lastW = 0;
  new ResizeObserver(([e]) => {
    const w = Math.round(e.contentRect.width);
    if (w !== lastW) { const first = !lastW; lastW = w; if (!first && mq.matches) redraw(); }
  }).observe(document.querySelector(".sd") || document.body);
  if (document.fonts) document.fonts.ready.then(() => { if (mq.matches) redraw(); });

  // warm the photos of the other answers once the page has loaded, so a tab shows its pictures at once
  addEventListener("load", () => {
    const seen = new Set();
    for (const t of Object.values(T)) t.content.querySelectorAll("img").forEach(i => { if (!seen.has(i.src)) { seen.add(i.src); new Image().src = i.src; } });
  });
})();
