// The scripted Smart UI demo on /smart-ui/ and the home page (site/smart_ui_page.py writes the scenarios as JSON next to it).
// No model and no server: each answer is played in the order a real one runs (references/your-agents.md in the skill):
// the tool call that picked the part, the part's outline, values filling as the data lands, then the sentence. The data agent,
// the UI agent and the writer run side by side in the "Behind the answer" panel. Timings are scripted, and say so on the page.
// Any new question cancels the one playing (interruptible). With reduced motion the order stays and only opacity changes.
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function Cancel() {}

  function Demo(root) {
    this.root = root;
    this.data = JSON.parse(root.querySelector("script[type='application/json']").textContent);
    this.mini = root.hasAttribute("data-mini");
    this.log = root.querySelector("[data-log]");
    this.live = root.querySelector("[data-live]");
    this.chips = root.querySelector("[data-chips]");
    this.toasts = root.querySelector("[data-toasts]");
    this.run = 0;
    this.product = this.data.products[0];
    var self = this;
    root.querySelectorAll("[data-product]").forEach(function (b) {
      b.addEventListener("click", function () { self.pick(b.getAttribute("data-product"), true); });
    });
    var replay = root.querySelector("[data-replay]");
    if (replay) replay.addEventListener("click", function () { self.ask(self.product.scenarios[0]); });
    this.pick(this.product.id, false);
    // play the first question once the demo is on screen, never before
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (es) {
        if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); self.ask(self.product.scenarios[0]); }
      }, { threshold: 0.2 });
      io.observe(root);
    } else {
      this.ask(this.product.scenarios[0]);
    }
  }

  Demo.prototype.pick = function (id, play) {
    var self = this;
    this.product = this.data.products.filter(function (p) { return p.id === id; })[0];
    this.root.querySelectorAll("[data-product]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-product") === id)); });
    this.root.querySelectorAll("[data-who]").forEach(function (n) { n.textContent = self.product.label; });
    this.root.querySelectorAll("[data-sub]").forEach(function (n) { n.textContent = self.product.sub; });
    if (this.chips) {
      this.chips.replaceChildren();
      this.product.scenarios.forEach(function (s, i) {
        var b = el("button", "sl-chip", s.q);
        b.type = "button";
        b.setAttribute("aria-pressed", "false");
        b.addEventListener("click", function () { self.ask(s); });
        s._chip = b;
        self.chips.append(b);
      });
    }
    if (play) this.ask(this.product.scenarios[0]);
  };

  Demo.prototype.wait = function (ms, id) {
    var self = this;
    if (reduce.matches) ms = 0;  // reduced motion: the finished answer, with no build-up
    return new Promise(function (ok, no) {
      setTimeout(function () { if (id !== self.run) no(new Cancel()); else ok(); }, ms);
    });
  };

  Demo.prototype.toast = function (text, undo) {
    var t = el("div", "sl-toast", null);
    t.setAttribute("role", "status");
    t.append(el("span", null, text));
    var gone = function () { t.classList.add("out"); setTimeout(function () { t.remove(); }, 200); };
    if (undo) {
      var b = el("button", "sl-undo", "Undo");
      b.type = "button";
      b.addEventListener("click", function () { undo(); gone(); });
      t.append(b);
    }
    this.toasts.append(t);
    setTimeout(gone, 5000);
  };

  // ---------------------------------------------------------------- lanes
  // Two lanes: your agent (fetch the data, then write the sentence) and Smart UI (match, outline, fill, check).
  // Each step is a plain verb with a quiet dot: waiting, working, done. The writer's step sits in your agent's lane.
  Demo.prototype.lanes = function (s) {
    var out = {}, root = this.root;
    root.querySelectorAll("[data-lane]").forEach(function (box) { box.replaceChildren(); });
    ["data", "ui", "text"].forEach(function (k) {
      var box = root.querySelector("[data-lane='" + (k === "text" ? "data" : k) + "']");
      out[k] = (s.lanes[k] || []).map(function (st) {
        var row = el("li", "sl-step", null);
        row.append(el("span", "sl-pdot", null), el("span", "sl-step-t", st[0]));
        if (box) box.append(row);
        return { row: row, ms: st[1] };
      });
    });
    root.querySelectorAll("[data-t]").forEach(function (n) { n.textContent = "–"; });
    return out;
  };
  Demo.prototype.step = async function (st, id) {
    st.row.classList.add("run");
    await this.wait(st.ms, id);
    st.row.classList.remove("run");
    st.row.classList.add("done");
  };
  Demo.prototype.lane = async function (steps, id) { for (var i = 0; i < steps.length; i++) await this.step(steps[i], id); };
  Demo.prototype.time = function (key, t0) {
    var n = this.root.querySelector("[data-t='" + key + "']");
    if (!n) return;
    var ms = Math.round(performance.now() - t0);
    n.textContent = reduce.matches ? "–" : ms < 1000 ? ms + " ms" : (ms / 1000).toFixed(1) + " s";
  };

  // ---------------------------------------------------------------- one answer
  Demo.prototype.ask = async function (s) {
    var id = ++this.run;
    var self = this;
    var t0 = performance.now();
    if (this.chips) this.product.scenarios.forEach(function (x) { if (x._chip) x._chip.setAttribute("aria-pressed", String(x === s)); });
    this.root.setAttribute("data-state", "busy");
    var L = this.lanes(s);
    var turn = el("div", "sl-turn", null);
    turn.append(el("div", "sl-me", s.q));
    this.log.replaceChildren(turn);
    var say = el("p", "sl-say", null);
    var call = el("p", "sl-call num", null);
    call.append(el("span", "sl-dot", null), el("span", null, s.chip));
    var part = null;
    try {
      await this.wait(this.mini ? 220 : 120, id);
      turn.append(call);
      t0 = performance.now();  // timed from the moment the question is sent, as the evals time it
      // the data agent starts with the tool call and runs beside the UI agent; the fill waits for it
      var data = this.lane(L.data || [], id);
      data.catch(function () {});
      var ui = L.ui || [];
      // the UI agent: match a prepared part (or decide on text) and draw its outline at once
      if (ui[0]) await this.step(ui[0], id);
      if (s.view) {
        turn.append(say);
        part = this.build(s.view, true);
        if (ui[1]) await this.step(ui[1], id);
        turn.append(part.node);
        this.time("outline", t0);
      } else {
        turn.append(say);
      }
      await data;
      // no prepared part covers a change: the model writes the part first, then it fills and is checked like any other
      var w = (L.text || [])[0];
      if (s.fallback && w) { w.row.classList.add("run"); await this.wait(700, id); }
      if (s.view) {
        if (ui[2]) ui[2].row.classList.add("run");
        await part.fill(this, id);
        if (ui[2]) { ui[2].row.classList.remove("run"); ui[2].row.classList.add("done"); }
        if (ui[3]) await this.step(ui[3], id);
      }
      // the writer: one or two sentences, after the facts are in
      if (w) w.row.classList.add("run");
      await this.stream(say, s.say, id);
      if (w) { w.row.classList.remove("run"); w.row.classList.add("done"); }
      call.classList.add("done");
      if (s.view && !this.mini) turn.append(el("p", "sl-checked", "Checked before it showed."));
      this.time("full", t0);
      this.live.textContent = s.say;
      this.root.setAttribute("data-state", "done");
    } catch (e) {
      if (!(e instanceof Cancel)) throw e;
    }
  };

  Demo.prototype.stream = async function (node, text, id) {
    if (reduce.matches) { node.textContent = text; return; }
    var words = text.split(" ");
    node.classList.add("typing");
    for (var i = 0; i < words.length; i++) {
      node.textContent += (i ? " " : "") + words[i];
      await this.wait(18, id);
    }
    node.classList.remove("typing");
  };

  // ---------------------------------------------------------------- parts
  function sk(w) { var s = el("span", "sl-sk", null); s.style.width = w; return s; }
  function tag(tone, text) { return el("span", "sl-tag " + (tone || ""), text); }
  function head(view) {
    var h = el("header", "sl-ph", null);
    h.append(el("h3", "sl-pt", view.title));
    if (view.sub) h.append(el("p", "sl-psub", view.sub));
    return h;
  }
  function land(node) { node.classList.add("sl-land"); }
  function btn(text, primary) { var b = el("button", "sl-btn" + (primary ? " primary" : ""), text); b.type = "button"; return b; }

  Demo.prototype.build = function (view, outline) {
    return KINDS[view.kind].call(this, view);
  };

  // stagger: values land one after another, 60 ms apart (decorative; nothing waits on it for input)
  async function each(demo, items, id, fn) {
    for (var i = 0; i < items.length; i++) { fn(items[i], i); await demo.wait(45, id); }
  }

  var KINDS = {
    facts: function (v) {
      var demo = this;
      var a = el("article", "sl-part", null);
      a.append(head(v));
      var dl = el("dl", "sl-facts", null);
      var dds = v.facts.map(function (f) {
        var row = el("div", "sl-fact", null);
        var dd = el("dd", null, null);
        dd.append(sk(f.w || "60%"));
        row.append(el("dt", null, f.label), dd);
        dl.append(row);
        return dd;
      });
      a.append(dl);
      var acts = el("div", "sl-acts", null);
      a.append(acts);
      return { node: a, fill: async function (d, id) {
        await each(d, v.facts, id, function (f, i) {
          var dd = dds[i];
          dd.replaceChildren();
          if (f.tone && f.tone !== "accent") dd.append(tag(f.tone, f.value));
          else dd.append(el("span", f.tone === "accent" ? "sl-strong" : null, f.value));
          if (f.note) dd.append(el("small", null, f.note));
          land(dd);
          dd.setAttribute("data-k", f.label);
        });
        if (v.action) {
          var b = btn(v.action.label, true);
          b.addEventListener("click", function () { demo.approve(v.action.approval, a, b, function () {
            var st = a.querySelector("[data-k='Status']");
            if (st) { st.replaceChildren(tag("ok", v.action.after)); land(st); }
            b.remove();
          }); });
          acts.append(b);
          land(b);
        }
      } };
    },

    findings: function (v) {
      var demo = this;
      var a = el("article", "sl-part", null);
      a.append(head(v));
      var sum = el("p", "sl-psub", null);
      sum.append(sk("50%"));
      a.append(sum);
      var ul = el("ul", "sl-rows", null);
      var lis = v.rows.map(function () {
        var li = el("li", "sl-row", null);
        li.append(sk("52px"), sk("80%"));
        ul.append(li);
        return li;
      });
      a.append(ul);
      function draw(li, r) {
        li.replaceChildren(tag(r.tone, r.label), el("span", null, r.text));
        if (r.fix) {
          var b = btn(r.fix);
          b.addEventListener("click", function () {
            li.replaceChildren(tag("ok", "Fixed"), el("span", null, r.text));
            land(li);
            demo.toast("Fixed: " + r.fix.toLowerCase(), function () { draw(li, r); land(li); });
          });
          li.append(b);
        }
      }
      return { node: a, fill: async function (d, id) {
        sum.textContent = v.summary;
        land(sum);
        await each(d, v.rows, id, function (r, i) { draw(lis[i], r); land(lis[i]); });
      } };
    },

    cards: function (v) {
      var demo = this;
      var a = el("article", "sl-part", null);
      a.append(head(v));
      var grid = el("div", "sl-cards", null);
      var cs = v.cards.map(function () {
        var c = el("div", "sl-card", null);
        c.append(sk("70%"), sk("100%"), sk("40%"));
        grid.append(c);
        return c;
      });
      a.append(grid);
      return { node: a, fill: async function (d, id) {
        await each(d, v.cards, id, function (k, i) {
          var c = cs[i];
          var b = btn("Add to kit");
          c.replaceChildren(el("strong", null, k.name), el("span", null, k.text), b);
          b.addEventListener("click", function () {
            b.disabled = true;
            b.textContent = "In your kit";
            demo.toast(k.name + " added to your kit", function () { b.disabled = false; b.textContent = "Add to kit"; });
          });
          land(c);
        });
      } };
    },

    metrics: function (v) {
      var a = el("article", "sl-part", null);
      a.append(head(v));
      var kp = el("div", "sl-kpis", null);
      var ks = v.kpis.map(function (k) {
        var d = el("div", "sl-kpi", null);
        var b = el("b", "num", null);
        b.append(sk("60%"));
        d.append(b, el("span", null, k.label));
        kp.append(d);
        return b;
      });
      var bars = el("div", "sl-bars", null);
      var bs = v.bars.map(function (r) {
        var row = el("div", "sl-bar", null);
        var track = el("span", "sl-track", null);
        var fill = el("span", "sl-fill", null);
        track.append(fill);
        var pct = el("span", "num", "–");
        row.append(el("span", null, r.label), track, pct);
        bars.append(row);
        return { fill: fill, pct: pct };
      });
      a.append(kp, bars);
      return { node: a, fill: async function (d, id) {
        await each(d, v.kpis, id, function (k, i) { ks[i].textContent = k.value; land(ks[i]); });
        await each(d, v.bars, id, function (r, i) {
          bs[i].fill.style.transform = "scaleX(" + r.pct / 100 + ")";
          if (r.tone) bs[i].fill.classList.add(r.tone);
          bs[i].pct.textContent = r.pct + "%";
        });
      } };
    },

    approval: function (v) {
      var demo = this;
      var a = el("article", "sl-part", null);
      a.append(head(v));
      var p = el("p", "sl-psub", null);
      if (v.summary) { p.append(sk("90%")); a.append(p); }
      var dl = el("dl", "sl-facts", null);
      var dds = v.details.map(function (f) {
        var row = el("div", "sl-fact", null);
        var dd = el("dd", null, null);
        dd.append(sk("50%"));
        row.append(el("dt", null, f.label), dd);
        dl.append(row);
        return dd;
      });
      a.append(dl);
      var warn = el("p", "sl-warn", v.warn);
      var acts = el("div", "sl-acts", null);
      var no = btn(v.cancel), yes = btn(v.approve, true);
      no.disabled = yes.disabled = true;
      acts.append(no, yes);
      a.append(warn, acts);
      return { node: a, fill: async function (d, id) {
        if (v.summary) { p.textContent = v.summary; land(p); }
        await each(d, v.details, id, function (f, i) { dds[i].textContent = f.value; land(dds[i]); });
        no.disabled = yes.disabled = false;
        land(acts);
        demo.wire(v, no, yes);
      } };
    },

    progress: function (v) {
      var a = el("article", "sl-part", null);
      var h = head(v);
      var st = el("span", "sl-sk", null);
      st.style.width = "120px";
      h.append(st);
      a.append(h);
      var ol = el("ol", "sl-steps", null);
      var lis = v.steps.map(function (s) {
        var li = el("li", "sl-pstep", null);
        li.append(el("span", "sl-mark", null), el("span", "sl-pl", s.label), sk("40%"));
        ol.append(li);
        return li;
      });
      a.append(ol);
      return { node: a, fill: async function (d, id) {
        var t = tag(v.tone, v.status);
        st.replaceWith(t);
        land(t);
        await each(d, v.steps, id, function (s, i) {
          var li = lis[i];
          li.className = "sl-pstep " + s.state;
          li.replaceChildren(el("span", "sl-mark", null), el("span", "sl-pl", s.label), el("span", "sl-pt2", s.time || (s.state === "now" ? "Now" : "")));
          land(li);
        });
      } };
    }
  };

  // A change asks first: the approval states what the change does, and its buttons are the person's to press.
  Demo.prototype.wire = function (v, no, yes, done) {
    var demo = this;
    no.addEventListener("click", function () { no.disabled = yes.disabled = true; demo.toast("Nothing was changed"); });
    yes.addEventListener("click", function () {
      no.disabled = yes.disabled = true;
      var label = yes.textContent;
      yes.textContent = v.pending || "Working";
      yes.setAttribute("aria-busy", "true");
      setTimeout(function () {
        yes.removeAttribute("aria-busy");
        yes.textContent = v.done || "Done";
        if (done) done();
        demo.toast(v.toast, v.undo ? function () { yes.textContent = label; no.disabled = yes.disabled = false; demo.toast(v.undo); } : null);
      }, 700);
    });
  };

  // A button on a part that starts a change (Pay on a fine) shows the approval next, in the same turn.
  Demo.prototype.approve = function (ap, after, trigger, done) {
    trigger.disabled = true;
    var p = KINDS.approval.call(this, ap);
    after.after(p.node);
    var self = this;
    p.fill(this, this.run).then(function () {
      var yes = p.node.querySelector(".sl-btn.primary"), no = p.node.querySelector(".sl-btn:not(.primary)");
      var y2 = yes.cloneNode(true), n2 = no.cloneNode(true);
      yes.replaceWith(y2); no.replaceWith(n2);
      self.wire(ap, n2, y2, done);
      n2.addEventListener("click", function () { trigger.disabled = false; });
    }).catch(function () {});
  };

  function boot() { document.querySelectorAll("[data-sl]").forEach(function (r) { new Demo(r); }); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
