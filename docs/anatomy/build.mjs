// Builds the interactive RAG bench: node build.mjs [--light] [--audit]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "./kit/iso-kit.mjs";
import { kitScript } from "./scripts/inline-kit.mjs";
import * as rig from "./rig.mjs";
import * as g from "./parts.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 800;
const HEIGHT = 410;
const { W } = g;

const P = k.fitProjection(
  [
    ...k.boxCorners(W.PLATE, -17, 0),
    [-31, 36, 116],
    [-7, -35, 104],
    [95, 43, 68],
    [-128, 0, 76],
    [-71, -15, 60],
    [150, 43, 4],
  ],
  WIDTH,
  HEIGHT,
  { pad: 26, azimuth: 62 },
);

const REST = 0.975; // the figure shown without script: the answer has just been delivered
const qi0 = 0;

function scene(u, qi) {
  const p = rig.pose(u, qi);
  const q = rig.QUESTIONS[qi];
  const flyCards = p.fly
    .filter((f) => f.shown && !f.inDrawer)
    .sort((a, b) => k.depthOf([a.x, a.y, 0], P) - k.depthOf([b.x, b.y, 0], P) || a.z - b.z)
    .map((f) => g.card(P, f.x, f.y, f.z, { op: f.op, tagged: true }))
    .join("");
  const beltCards = p.cards.map((c) => g.card(P, c.x, 0, c.z, { op: c.op, tagged: c.tagged })).join("") + g.card(P, p.q.x, p.q.y, 1.5, { op: p.q.op, tagged: p.q.tagged });
  const drawers = Array.from({ length: rig.DRAWERS }, (_, i) => {
    const s = p.open[i];
    const fl = p.fly.find((f) => f.drawer === i);
    const inside = !!fl && fl.inDrawer && s > 0.05;
    return `<g data-part="drawer${i}">${g.drawer(P, i, s, q.kw[i], q.vec[i], { card: inside, reveal: p.reveal[i] })}</g>`;
  });
  return [
    g.plate(P),
    g.feed(P),
    g.chunkerBack(P),
    `<g data-part="blade" transform="${k.translateAlong(P, [0, 0, -32.8 * p.blade])}">${g.blade(P)}</g>`,
    g.chunkerFront(P),
    g.belt(P),
    `<g data-part="cable" style="opacity:${p.cable}">${g.cableLine(P)}</g>`,
    `<g data-part="beltcards">${beltCards}</g>`,
    g.stampStatic(P),
    `<g data-part="head" transform="${k.translateAlong(P, [0, 0, -11 * p.stampDown])}">${g.stampHead(P, 0)}</g>`,
    g.stampArm(P, p.needle),
    g.mast(P),
    g.cableEnds(P),
    g.cabinet(P),
    ...drawers,
    `<g data-part="bar">${g.bar(P, p.barZ, p.loaded)}</g>`,
    g.pressColumn(P),
    g.trayBack(P),
    `<g data-part="fly">${flyCards}</g>`,
    `<g data-part="answer">${g.answer(P, p.answer)}</g>`,
    g.trayFront(P),
    `<g data-part="platen" transform="${k.translateAlong(P, [0, 0, -7.2 * p.press])}">${g.platen(P, 0)}</g>`,
    g.pressArm(P),
  ];
}

const svg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label:
    "A bench that works like the Azure AI RAG pipeline. Left: a stack of documents feeds a guillotine that cuts 500-character chunks with 50 characters of overlap, and a stamp prints each chunk's 1536-number vector before it goes into an eight-drawer index cabinet. A question takes the same stamp, a reader bar sweeps every drawer reading a keyword score and a vector score, the five best drawers open one at a time and hand their chunk to a prompt tray, a press squeezes the prompt into the chat model, and an answer card with its source tabs slides out.",
  body: scene(REST, qi0),
});

// ---- the live part ---------------------------------------------------------------------------------
const strip = (file) => readFileSync(join(HERE, file), "utf8").replace(/^export /gm, "").replace(/^import .*$/gm, "");
const kitNames = Object.keys(k).join(", ");

const live = `
const P = ${JSON.stringify(P)};
const REST = ${REST};
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const part = (name) => svg.querySelector('[data-part="' + name + '"]');
const E = { blade: part("blade"), belt: part("beltcards"), head: part("head"), cable: part("cable"), bar: part("bar"), fly: part("fly"), answer: part("answer"), platen: part("platen"), needle: part("needle"), drawers: Array.from({ length: DRAWERS }, (_, i) => part("drawer" + i)) };
const readout = document.querySelector("[data-readout]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const cache = {};
const put = (key, node, html) => { if (cache[key] !== html) { cache[key] = html; node.innerHTML = html; } };
let u = still.matches ? REST : 0, target = u, qi = 0, touring = !still.matches, frame = 0, last = 0, visible = false, idleTimer = 0;

function render() {
  const p = pose(u, qi);
  const q = QUESTIONS[qi];
  E.blade.setAttribute("transform", translateAlong(P, [0, 0, -32.8 * p.blade]));
  E.head.setAttribute("transform", translateAlong(P, [0, 0, -11 * p.stampDown]));
  E.platen.setAttribute("transform", translateAlong(P, [0, 0, -7.2 * p.press]));
  const a = p.needle * Math.PI * 2;
  E.needle.setAttribute("d", lineOnTop([-71, -15], [-71 + Math.sin(a) * 5.4, -15 - Math.cos(a) * 5.4], 58.2, P));
  E.cable.style.opacity = p.cable.toFixed(3);
  put("belt", E.belt, p.cards.map((c) => card(P, c.x, 0, c.z, { op: c.op, tagged: c.tagged })).join("") + card(P, p.q.x, p.q.y, 1.5, { op: p.q.op, tagged: p.q.tagged }));
  for (let i = 0; i < DRAWERS; i++) {
    const s = p.open[i];
    const fl = p.fly.find((f) => f.drawer === i);
    const inside = !!fl && fl.inDrawer && s > 0.05;
    const rv = Math.round(p.reveal[i] * 200) / 200;
    put("d" + i, E.drawers[i], drawer(P, i, Math.round(s * 20) / 20, q.kw[i], q.vec[i], { card: inside, reveal: rv }));
  }
  put("bar", E.bar, bar(P, Math.round(p.barZ * 20) / 20, Math.round(p.loaded * 50) / 50));
  put("fly", E.fly, p.fly.filter((f) => f.shown && !f.inDrawer).sort((x, y) => depthOf([x.x, x.y, 0], P) - depthOf([y.x, y.y, 0], P) || x.z - y.z).map((f) => card(P, f.x, f.y, f.z, { op: f.op, tagged: true })).join(""));
  put("answer", E.answer, answer(P, p.answer));
  const text = "Q" + (qi + 1) + " · " + describe(u, qi);
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", String(Math.round(u * 100)));
  stage.setAttribute("aria-valuetext", text);
}

function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  if (touring) {
    u += dt / CYCLE;
    if (u >= 1) { u -= 1; qi = (qi + 1) % QUESTIONS.length; }
    target = u;
  } else {
    u = still.matches ? target : u + (target - u) * (1 - Math.exp(-dt / 0.12));
    if (Math.abs(target - u) < 0.0004) u = target;
  }
  render();
  frame = visible && (touring || u !== target) ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
const hold = () => { touring = false; clearTimeout(idleTimer); idleTimer = setTimeout(() => { touring = !still.matches; run(); }, 3600); run(); };
const ask = (n) => { qi = ((n % QUESTIONS.length) + QUESTIONS.length) % QUESTIONS.length; u = target = T.askStart - 0.012; touring = !still.matches; if (still.matches) { u = target = REST; } clearTimeout(idleTimer); render(); run(); };

new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
stage.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  target = clamp(((event.clientX - box.left) / box.width - 0.06) / 0.88, 0, 0.995);
  hold();
});
stage.addEventListener("pointerleave", () => { clearTimeout(idleTimer); idleTimer = setTimeout(() => { touring = !still.matches; run(); }, 1200); });
stage.addEventListener("click", () => ask(qi + 1));
stage.addEventListener("keydown", (event) => {
  const key = event.key;
  if (key === "ArrowRight" || key === "ArrowUp") target = clamp(target + 0.03, 0, 0.995);
  else if (key === "ArrowLeft" || key === "ArrowDown") target = clamp(target - 0.03, 0, 0.995);
  else if (key === "Home") target = 0;
  else if (key === "End") target = REST;
  else if (key === "1" || key === "2" || key === "3") { event.preventDefault(); ask(Number(key) - 1); return; }
  else if (key === " " || key === "Enter") { event.preventDefault(); ask(qi + 1); return; }
  else return;
  event.preventDefault();
  hold();
});
window.__ragSet = (uu, qq) => { u = target = uu; qi = qq; touring = false; render(); };
render();
`;

const phone = `<style>@media (max-width:560px){.iso-plate-corner[data-corner="hint"]{display:none}.iso-plate-corner[data-corner="readout"]{left:0;right:0;white-space:normal;text-align:right;font-size:9.5px;line-height:1.35}}</style>`;
const body = phone + k.plateHtml({
  fig: "Fig 1",
  title: "RAG bench",
  hint: "Hover to scrub · click to ask the next question",
  readout: "Q1 · " + rig.describe(REST, qi0),
  keys: [
    { mark: "lit", label: "A chunk or an answer in motion" },
    { mark: "raised", label: "Drawer = one stored chunk; its two bars are the keyword (upper) and vector (lower) score" },
  ],
  caption:
    "The ingest side (left) cuts documents into 500-character chunks with 50 characters of overlap and stamps each with a 1536-number vector. A question takes the same stamp; the reader bar scores every chunk by keyword and by meaning, the five best drawers open in turn and fill the prompt tray, and the chat model's answer comes out with its source tabs. Chunk names and scores are sample data.",
  body: `<div class="iso-stage" tabindex="0" role="slider" aria-label="RAG bench: hover to scrub through ingest and a question, click or press 1, 2 or 3 to ask a question, arrow keys step through" aria-valuemin="0" aria-valuemax="100" aria-valuenow="97">${svg}</div>`,
});

const script = kitScript() + `\nconst k = { ${kitNames} };\n` + strip("rig.mjs") + "\n" + strip("parts.mjs") + "\n" + live;
const file = theme === "light" ? "rag-bench-light.html" : "rag-bench.html";
writeFileSync(join(HERE, file), k.pageHtml({ title: "RAG bench", theme, body, script, width: 860 }));
console.log("wrote", file);
