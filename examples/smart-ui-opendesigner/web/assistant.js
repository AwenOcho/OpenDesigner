// The OpenDesigner assistant: Smart UI's reference chat client (od-chat.js), talking to this app's /api/chat (server.py),
// and a panel that shows what runs behind each answer, filled from the events the chat streams.
import "/opendesigner-smart-ui/od-chat.js";

const $ = (id) => document.getElementById(id);
const lanes = { data: $("lane-data"), ui: $("lane-ui") };
let t0 = 0, first = false, laneSeen = false;
const rows = new Map();

const ms = (n) => `${Math.round(n).toLocaleString("en")} ms`;

function reset() {
  t0 = performance.now();
  first = false;
  laneSeen = false;
  rows.clear();
  lanes.data.replaceChildren();
  lanes.ui.replaceChildren();
  $("t-first").textContent = "Waiting";
  $("t-full").textContent = "Waiting";
  $("behind-sub").textContent = "Both agents start at once.";
}

function step(lane, label, status, at) {
  const box = lanes[lane === "data" ? "data" : "ui"];  // writing the sentence is the UI agent's last step
  const key = `${lane}:${label}`;
  let row = rows.get(key);
  if (!row) {
    row = document.createElement("li");
    row.className = "step";
    const dot = document.createElement("span");
    dot.className = "dot";
    dot.setAttribute("aria-hidden", "true");
    const name = document.createElement("span");
    name.textContent = label;
    const time = document.createElement("span");
    time.className = "ms";
    time.textContent = "Running";
    row.append(dot, name, time);
    box.append(row);
    rows.set(key, row);
  }
  if (status === "done") {
    row.classList.add("is-done");
    row.lastElementChild.textContent = typeof at === "number" ? ms(at) : "Done";
  }
}

function seen() {
  if (first) return;
  first = true;
  $("t-first").textContent = ms(performance.now() - t0);
}

document.addEventListener("od-chat-event", (e) => {
  const ev = e.detail || {};
  switch (ev.type) {
    case "start": reset(); break;
    case "lane": laneSeen = true; step(ev.lane, ev.step, ev.status, ev.ms); break;
    case "call":
      if (!ev.part) step("ui", "No part: a sentence answers it", "done", undefined);
      break;
    case "shell": case "part": case "text": seen(); break;
    case "done":
      seen();
      $("t-full").textContent = ms(performance.now() - t0);
      if (!laneSeen) $("behind-sub").textContent = "A recorded answer: no agents ran for this one.";
      else $("behind-sub").textContent = "Done. Times are from when the question was sent.";
      break;
    case "error":
      $("t-full").textContent = "Stopped";
      $("behind-sub").textContent = "The answer stopped: " + (ev.error || "an error");
      break;
  }
});
