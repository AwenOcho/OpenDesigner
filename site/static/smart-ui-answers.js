// The Smart UI page's answer demo (site/smart_ui_answers.py writes the views, the parts and the recorded answers).
// Everything is recorded: no model and no network call runs here. A tab, a chip or a typed question runs one answer's build
// sequence: the outline, the sentence, the card, the check, ready, with the island's dots in step. "Try a state" shows slow data,
// no results, a data error and an approval. The stage keeps one height through all of it, so nothing on the page moves.
(() => {
  const dataEl = document.getElementById("sd-data");
  if (!dataEl) return;
  const DATA = JSON.parse(dataEl.textContent);
  const T = {}, P = {};
  document.querySelectorAll("template[data-sd-t]").forEach(t => { T[t.dataset.sdT] = t; });
  document.querySelectorAll("template[data-sd-p]").forEach(t => { P[t.dataset.sdP] = t; });
  const KEYS = Object.keys(DATA);
  const LAY = { canvas: 2, window: 1, single: 3 };
  const mq = matchMedia("(max-width: 820px)");
  const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fill = (view, key) => view.replaceChildren(T[key].content.cloneNode(true));
  const press = (group, b) => group.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));

  // ---------------------------------------------------------------- phones: one window height for every first answer
  function size(view, v, current) {
    view.style.removeProperty("--sd-win-h");
    if (!mq.matches || v !== 1 || !view.offsetParent) return;
    let win = 0;
    for (const k of KEYS) { fill(view, `${k}-1`); win = Math.max(win, view.querySelector(".sd-win").getBoundingClientRect().height); }
    view.style.setProperty("--sd-win-h", Math.ceil(win) + "px");
    fill(view, `${current}-1`);
  }

  // ---------------------------------------------------------------- the boxes (hero and section 2)
  const boxes = [...document.querySelectorAll(".sd[data-sd]")].map(el => ({
    el, name: el.dataset.sd, k: el.dataset.tab, id: "init", q: null, matched: "", st: "normal", tok: 0, lay: el.dataset.sd === "hero" ? 2 : 1, look: "blue",
  }));
  const views = box => [...box.el.querySelectorAll(".sd-view")];
  const live = box => box.el.querySelector("[data-live]");

  function chipsHTML(box) {
    const s = DATA[box.k];
    return s.order.filter(a => a !== box.id).map(a => `<button type="button" class="sd-chip" data-ask="${a}">${esc(s.answers[a].q)}</button>`).join("");
  }
  function lanes(box, ans, on) {
    const li = (xs, cls) => xs.map(x => `<li class="sd-step${cls}">${esc(x)}</li>`).join("");
    box.el.querySelectorAll('[data-lane="agent"]').forEach(u => { u.innerHTML = li(ans.agent, on ? " on" : ""); });
    box.el.querySelectorAll('[data-lane="ui"]').forEach(u => { u.innerHTML = li(ans.ui, on ? " on" : ""); });
    box.el.querySelectorAll('[data-lane="checks"]').forEach(u => { u.innerHTML = li(DATA[box.k].checks, on ? " on" : ""); });
    box.el.querySelectorAll("[data-ready]").forEach(b => { b.textContent = ans.ms; });
    box.el.querySelectorAll("[data-count]").forEach(b => { b.textContent = `${ans.ui.length} steps checked`; });
  }
  function dots(box) { return [...box.el.querySelectorAll('[data-lane="agent"] .sd-step, [data-lane="ui"] .sd-step, [data-lane="checks"] .sd-step')]; }

  // the parts an answer can end in
  function partFor(box, ans, initHTML) {
    if (ans.fallback) return `<p class="sd-note">No ready-made card fits, so Smart UI answers in text.</p>`;
    if (box.id === "init") return initHTML;
    return P[`${box.k}:${box.id}`].innerHTML;
  }
  function stateCard(box, kind) {
    const s = DATA[box.k];
    if (kind === "empty")
      return `<div class="sd-card sd-tcard sd-state"><div class="sd-cardh"><p class="sd-ct">${esc(s.empty[0])}</p><span class="sd-st info">No results</span></div>`
        + `<p class="sd-sub">${esc(s.empty[1])}</p><div class="sd-acts"><button type="button" class="sd-btn" data-ask="${s.order[1]}">${esc(s.answers[s.order[1]].q)}</button></div></div>`;
    if (kind === "error")
      return `<div class="sd-card sd-tcard sd-state"><div class="sd-cardh"><p class="sd-ct">Couldn't reach ${esc(s.source)}</p><span class="sd-st bad">Data error</span></div>`
        + `<p class="sd-sub">The data source didn't answer, so nothing is shown and nothing was changed.</p><div class="sd-acts"><button type="button" class="sd-btn" data-retry>Retry</button></div></div>`;
    const a = s.approval;
    return `<div class="sd-card sd-tcard sd-approve"><div class="sd-cardh"><p class="sd-ct">${esc(a.title)}</p><span class="sd-st warn">Needs your yes</span></div>`
      + `<dl class="sd-kv">${a.details.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl><p class="sd-warnl">${esc(a.warn)}</p>`
      + `<div class="sd-acts"><button type="button" class="sd-btn sd-sec" data-cancel>Cancel</button><button type="button" class="sd-btn" data-confirm>${esc(a.ok)}</button></div></div>`;
  }
  const SKEL = slow => `<div class="sd-skel" aria-hidden="true"><i></i><div class="sd-blocks"><i></i><i></i><i></i></div><i></i><i></i>${slow ? '<span class="sd-slow">Still fetching…</span>' : ""}</div>`;

  // the first answer's part as drawn for a view's layout, kept from when the view was filled
  const INIT = new WeakMap();
  function initHTML(view) {
    if (!INIT.has(view)) { const p = view.querySelector(".sd-part"); INIT.set(view, p ? p.innerHTML : ""); }
    return INIT.get(view);
  }

  // ---------------------------------------------------------------- one answer, built in order
  function answerOf(box) {
    const s = DATA[box.k];
    if (box.id === "fallback")
      return { q: box.q, a: "I can't answer that from this demo's recorded answers. Try one of the questions below.", title: "Answered in text", count: "",
               agent: ["Searched the recorded answers"], ui: ["No ready-made card", "Answered in text"], ms: "0.3 s", fallback: true };
    return s.answers[box.id];
  }

  function run(box, opts = {}) {
    const tok = ++box.tok;
    const ans = answerOf(box);
    const st = opts.state || box.st;
    const anim = !opts.instant && !still();
    const vs = views(box);
    const inits = vs.map(initHTML);
    box.el.querySelectorAll(".sd-island").forEach(i => i.classList.remove("sd-done", "sd-failed"));
    lanes(box, ans, !anim);
    vs.forEach(v => {
      v.querySelectorAll(".sd-q").forEach(q => { q.textContent = box.q || ans.q; });
      v.querySelectorAll(".sd-match").forEach(m => { m.textContent = box.matched; });
      v.querySelectorAll(".sd-qlist, .sd-compose").forEach(c => { c.innerHTML = chipsHTML(box); });
      v.querySelectorAll(".sd-ctitle b").forEach(b => { b.textContent = ans.title; });
      v.querySelectorAll(".sd-ctitle .kicker").forEach(b => { b.textContent = ans.count; });
      v.querySelectorAll(".sd-body").forEach(b => { b.scrollTop = 0; });
    });
    const sentence = st === "error" ? `I couldn't reach ${DATA[box.k].source} just now.` : st === "empty" ? "I found nothing that matches." : ans.a;
    const finalPart = i => (st === "error" || st === "empty") ? stateCard(box, st) : partFor(box, ans, inits[i]);
    const setA = (hide) => vs.forEach(v => v.querySelectorAll(".sd-a").forEach(a => { a.textContent = sentence; a.classList.toggle("sd-hide", hide); }));
    const setPart = html => vs.forEach((v, i) => v.querySelectorAll(".sd-part").forEach(p => { p.innerHTML = typeof html === "function" ? html(i) : html; }));
    const done = () => {
      box.el.querySelectorAll(".sd-island").forEach(i => i.classList.toggle(st === "error" ? "sd-failed" : "sd-done", true));
      box.el.classList.remove("sd-wait");
      box.el.querySelector(".sd-stage").setAttribute("aria-busy", "false");
      live(box).textContent = sentence;
      if (st === "approval" && !ans.fallback && box.k) setPart(() => stateCard(box, "approval"));
    };
    if (!anim) {
      setA(false);
      setPart(finalPart);
      if (st === "error") dots(box).slice(1).forEach(d => d.classList.replace("on", "bad"));
      done();
      return;
    }
    box.el.classList.add("sd-wait");
    box.el.querySelector(".sd-stage").setAttribute("aria-busy", "true");
    live(box).textContent = "";
    setA(true);
    setPart(SKEL(st === "slow"));
    const ds = dots(box);
    const nAgent = ans.agent.length;
    const at = (ms, f) => setTimeout(() => { if (box.tok === tok) f(); }, ms);
    const hold = st === "slow" ? 3000 : 0;
    ds.slice(0, nAgent).forEach((d, i) => at(120 + i * 120 + (i === nAgent - 1 ? hold : 0), () => d.classList.add(st === "error" && i > 0 ? "bad" : "on")));
    const t1 = 120 + nAgent * 120 + hold;
    at(t1, () => setA(false));
    at(t1 + 160, () => { setPart(finalPart); vs.forEach(v => v.querySelectorAll(".sd-part > *").forEach(e => e.classList.add("sd-fill"))); });
    ds.slice(nAgent).forEach((d, i) => at(t1 + 280 + i * 120, () => d.classList.add(st === "error" ? "bad" : "on")));
    at(t1 + 280 + (ds.length - nAgent) * 120 + 60, done);
  }

  // ---------------------------------------------------------------- matching a typed question to a recorded one
  function match(k, text) {
    const words = text.toLowerCase().replace(/[^a-z0-9£\- ]/g, " ").split(/\s+/).filter(w => w.length > 1);
    let best = null, score = 0;
    for (const id of DATA[k].order) {
      const keys = DATA[k].answers[id].keys;
      const s = words.reduce((n, w) => n + (keys.includes(w) ? 2 : keys.some(x => x.length > 3 && (x.startsWith(w) || w.startsWith(x))) ? 1 : 0), 0);
      if (s > score) { score = s; best = id; }
    }
    return score >= 2 ? best : null;
  }

  // ---------------------------------------------------------------- drawing a layout or a tab
  function drawBox(box, swap) {
    const vs = views(box);
    if (box.name === "any") {
      const v = mq.matches ? 1 : box.lay;
      box.el.className = `sd sd-any sd-lay-${v}`;
      box.el.querySelector(".sd-stage").className = `sd-stage sd-look-${box.look}`;
      vs[0].className = `sd-view sd-v${v}`;
      vs[0].dataset.v = v;
    }
    for (const view of vs) {
      const v = Number(view.dataset.v);
      fill(view, `${box.k}-${v}`);
      size(view, v, box.k);
      INIT.delete(view);
      initHTML(view);
      view.classList.toggle("sd-swap", !!swap);
    }
    fades();
  }

  function toast(box, text) {
    const wrap = box.el.querySelector(".sd-toasts");
    const t = document.createElement("div");
    t.className = "sd-toast";
    t.textContent = text;
    wrap.append(t);
    setTimeout(() => t.remove(), 3200);
  }

  // ---------------------------------------------------------------- events
  document.addEventListener("click", e => {
    const b = e.target.closest(".sd button, .sd-ctrls button");
    if (!b) return;
    const box = boxes.find(x => x.el.contains(b)) || boxes.find(x => x.name === "any");
    if (!box) return;
    if (b.dataset.k) {
      if (box.k === b.dataset.k) return;
      box.k = b.dataset.k; box.id = "init"; box.q = null; box.matched = "";
      press(b.parentElement, b);
      drawBox(box, true);
      run(box);
    } else if (b.dataset.l) {
      box.lay = LAY[b.dataset.l]; press(b.parentElement, b); drawBox(box, true); run(box, { instant: true });
    } else if (b.dataset.o) {
      box.look = b.dataset.o; press(b.parentElement, b); drawBox(box, false); run(box, { instant: true });
    } else if (b.dataset.s) {
      box.st = b.dataset.s; press(b.parentElement, b); run(box);
    } else if (b.dataset.ask) {
      box.id = b.dataset.ask; box.q = null; box.matched = ""; run(box);
    } else if (b.hasAttribute("data-retry")) {
      run(box, { state: "normal" });
    } else if (b.hasAttribute("data-act")) {
      box.tok++;  // an approval stops any build still running
      views(box).forEach(v => v.querySelectorAll(".sd-part").forEach(p => { p.innerHTML = stateCard(box, "approval"); }));
      const first = box.el.querySelector(".sd-view:not([hidden]) .sd-approve [data-confirm]");
      if (first && first.offsetParent) first.focus();
    } else if (b.hasAttribute("data-cancel")) {
      run(box, { instant: true, state: "normal" });
    } else if (b.hasAttribute("data-confirm")) {
      b.setAttribute("aria-busy", "true");
      const tok = ++box.tok;
      setTimeout(() => { if (box.tok !== tok) return; run(box, { instant: true, state: "normal" }); toast(box, DATA[box.k].approval.done); }, still() ? 0 : 600);
    }
  });

  document.addEventListener("submit", e => {
    const f = e.target.closest(".sd-ask");
    if (!f) return;
    e.preventDefault();
    const box = boxes.find(x => x.el.contains(f));
    const text = f.q.value.trim().slice(0, 80);
    if (!box || !text) return;
    const id = match(box.k, text);
    box.q = text;
    if (id) { box.id = id; box.matched = `Matched: ${DATA[box.k].answers[id].q}`; } else { box.id = "fallback"; box.matched = "No match"; }
    f.q.value = "";
    run(box);
  });

  // a sideways row (tabs, chips, the state and look pickers) fades at its end only while there is more of it to scroll to
  function fades() {
    document.querySelectorAll(".sd-seg, .sd-compose").forEach(el => el.classList.toggle("sd-fade", el.scrollWidth - el.clientWidth - el.scrollLeft > 2));
  }
  document.addEventListener("scroll", e => { if (e.target.matches && e.target.matches(".sd-seg, .sd-compose")) fades(); }, true);
  addEventListener("resize", fades);

  function redraw() { boxes.forEach(box => { drawBox(box, false); run(box, { instant: true }); }); }
  if (mq.matches) redraw();
  fades();
  mq.addEventListener("change", redraw);
  let lastW = 0;
  new ResizeObserver(([e]) => {
    const w = Math.round(e.contentRect.width);
    if (w !== lastW) { const first = !lastW; lastW = w; if (!first && mq.matches) redraw(); }
  }).observe(document.querySelector(".sd"));
  if (document.fonts) document.fonts.ready.then(() => { if (mq.matches) redraw(); });

  // a tab's photos load when a visitor points at or focuses its tab, not all on first load
  const warmed = new Set();
  document.addEventListener("pointerover", warm, { passive: true });
  document.addEventListener("focusin", warm);
  function warm(e) {
    const b = e.target.closest && e.target.closest(".sd [data-k]");
    if (!b || warmed.has(b.dataset.k)) return;
    warmed.add(b.dataset.k);
    const box = boxes.find(x => x.el.contains(b));
    const v = box && box.name === "any" && !mq.matches ? box.lay : 2;
    const t = T[`${b.dataset.k}-${mq.matches ? 1 : v}`];
    if (t) t.content.querySelectorAll("img").forEach(i => { const im = new Image(); im.sizes = i.sizes; im.srcset = i.srcset; im.src = i.src; });
  }
})();
