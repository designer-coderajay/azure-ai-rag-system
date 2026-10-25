// The model behind the figure. Pure functions: the geometry, the motion and the readout all read from here.
// Facts that come from the project's code (src/): chunks of 500 characters with 50 overlap, 1536-dimension
// embeddings, hybrid search, top_k = 5. The chunk names and the scores below are illustrative sample data.

export const CHUNK_CHARS = 500;
export const OVERLAP_CHARS = 50;
export const DIMS = 1536;
export const TOP_K = 5;
export const DRAWERS = 8;
export const CYCLE = 28; // seconds for one full ingest + question

export const CHUNKS = [
  { src: "handbook.docx", page: null },
  { src: "policy.pdf", page: 1 },
  { src: "policy.pdf", page: 2 },
  { src: "faq.txt", page: null },
  { src: "expenses.pdf", page: 1 },
  { src: "expenses.pdf", page: 2 },
  { src: "leave.docx", page: null },
  { src: "security.pdf", page: 1 },
];

// Per question: a keyword score and a vector score for each of the eight chunks (0 to 1).
export const QUESTIONS = [
  { text: "remote work policy?", kw: [0.3, 0.9, 0.8, 0.35, 0.05, 0.05, 0.2, 0.1], vec: [0.5, 0.78, 0.92, 0.6, 0.1, 0.12, 0.42, 0.2] },
  { text: "travel expense limit?", kw: [0.1, 0.15, 0.1, 0.3, 0.88, 0.8, 0.05, 0.2], vec: [0.25, 0.4, 0.3, 0.55, 0.82, 0.93, 0.1, 0.3] },
  { text: "how much annual leave?", kw: [0.4, 0.2, 0.25, 0.45, 0.05, 0.1, 0.92, 0.05], vec: [0.55, 0.3, 0.5, 0.6, 0.08, 0.15, 0.95, 0.12] },
];

const rankOf = (scores) => {
  const order = scores.map((s, i) => [s, i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const rank = Array(scores.length).fill(0);
  order.forEach(([, i], r) => (rank[i] = r));
  return rank;
};

// Merge the two rankings with reciprocal-rank fusion (k = 60), then keep the best TOP_K.
export function fuse(question) {
  const kwRank = rankOf(question.kw);
  const vecRank = rankOf(question.vec);
  const merged = question.kw.map((_, i) => 1 / (60 + kwRank[i] + 1) + 1 / (60 + vecRank[i] + 1));
  const order = merged.map((s, i) => [s, i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]).map(([, i]) => i);
  return { merged, order, top: order.slice(0, TOP_K) };
}

export const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const seg = (u, a, b) => clamp((u - a) / (b - a));
export const ease = (t) => t * t * (3 - 2 * t);
export const wave = (u, a, b) => Math.sin(Math.PI * seg(u, a, b)); // 0 → 1 → 0 across [a, b]

// Where things are along the timeline u in [0, 1).
export const T = {
  chop: [0.02, 0.07, 0.12], // chunker strokes
  spawn: [0.035, 0.085, 0.135], // a chunk card leaves the bed after each stroke
  askStart: 0.26,
  qStamp: [0.33, 0.375],
  sweep: [0.46, 0.66],
  park: [0.66, 0.70],
  pickStart: 0.71,
  pickLen: 0.035,
  press: [0.89, 0.93],
  answer: [0.93, 0.975],
  fade: [0.985, 1.0],
};

export function pose(u, qi) {
  const q = QUESTIONS[qi];
  const f = fuse(q);
  const fadeOut = 1 - seg(u, T.fade[0], T.fade[1]);
  const p = { u, qi, top: f.top, order: f.order };

  // chunker blade and the three chunk cards
  p.blade = Math.max(...T.chop.map((c) => wave(u, c, c + 0.03)));
  p.cards = T.spawn.map((s, j) => {
    const a = s;
    const x = u < a + 0.03 ? -112 + 16 * ease(seg(u, a, a + 0.03)) : u < a + 0.055 ? -96 + 25 * ease(seg(u, a + 0.03, a + 0.045)) : -71 + 76 * ease(seg(u, a + 0.055, a + 0.09));
    const into = x > -4 ? 0 : 1;
    return { x, z: 3 - 1.5 * ease(seg(x, -104, -92)), op: seg(u, a, a + 0.008) * into * (u < a + 0.09 ? 1 : 0), tagged: u > a + 0.045, stamped: j };
  });
  p.stampDown = Math.max(...T.spawn.map((s) => wave(u, s + 0.036, s + 0.054)), wave(u, T.qStamp[0] + 0.01, T.qStamp[1]));
  p.needle = p.stampDown * 3;

  // the question card: down the chute, stamped, along the belt, into the cable
  const qa = T.askStart;
  const qy = 60 - 60 * ease(seg(u, qa, qa + 0.06));
  const qx = -71 + 41 * ease(seg(u, T.qStamp[1] + 0.005, T.qStamp[1] + 0.05));
  p.q = { x: qx, y: qy, op: seg(u, qa, qa + 0.01) * (1 - seg(u, 0.44, 0.465)), tagged: u > T.qStamp[0] + 0.03 };
  p.cable = seg(u, 0.425, 0.45) * (1 - seg(u, 0.46, 0.5)) * 0.9 + 0.1;
  p.loaded = seg(u, 0.45, 0.47) * (1 - seg(u, T.fade[0], T.fade[1]));

  // the reader bar sweeps the drawers, then parks above them
  const sw = seg(u, T.sweep[0], T.sweep[1]);
  p.sweep = sw;
  const zRow = (i) => 10 + 10.5 * i + 8.7;
  const up = zRow(0) + (zRow(DRAWERS - 1) - zRow(0)) * sw;
  p.barZ = u < T.park[0] ? up : zRow(DRAWERS - 1) + (106 - zRow(DRAWERS - 1)) * ease(seg(u, T.park[0], T.park[1])) + (zRow(0) - 106) * ease(seg(u, 0.935, 0.98)) * (u > 0.7 ? 1 : 0);
  p.reveal = Array.from({ length: DRAWERS }, (_, i) => ease(clamp(sw * DRAWERS - i + 0.4)) * fadeOut);

  // top five: one drawer at a time opens, gives up its card, closes
  p.open = Array(DRAWERS).fill(0);
  p.fly = []; // { drawer, rank, x, y, z, in: still in its drawer }
  f.top.forEach((d, r) => {
    const a = T.pickStart + T.pickLen * r;
    const s = 28 * ease(seg(u, a, a + 0.010)) * (1 - ease(seg(u, a + 0.024, a + 0.034)));
    p.open[d] = s;
    const w = seg(u, a + 0.008, a + 0.034);
    const zFloor = 10 + 10.5 * d + 1.6;
    const base = { x: 23, y: 27 + 28 * 0.5 + 0, z: zFloor };
    const hover = zFloor + 15;
    let x = base.x, y = base.y, z = base.z;
    if (w > 0) {
      const lift = ease(seg(w, 0, 0.2));
      const travel = ease(seg(w, 0.2, 0.55));
      const drop = ease(seg(w, 0.55, 0.75));
      const slide = ease(seg(w, 0.75, 0.9));
      const settle = ease(seg(w, 0.9, 1));
      z = base.z + (hover - base.z) * lift;
      x = base.x + (66 - base.x) * travel;
      y = base.y + (43 - base.y) * travel;
      z = z + (14 - hover) * drop;
      x = x + (95 - 66) * slide;
      z = z + (3 + 1.6 * r - 14) * settle;
    }
    const left = u >= a + 0.008; // card has left its drawer
    p.fly.push({ drawer: d, rank: r, x, y, z, inDrawer: !left, shown: u >= a + 0.004, op: fadeOut });
  });

  // press, answer card, citations
  p.press = wave(u, T.press[0], T.press[1]);
  p.answer = { x: 95 + 49 * ease(seg(u, T.answer[0], T.answer[1])), z: 11.2 - 8.8 * ease(seg(u, T.answer[0] + 0.02, T.answer[1])), op: seg(u, T.answer[0], T.answer[0] + 0.006) * fadeOut, tabs: Math.round(TOP_K * seg(u, T.answer[0] + 0.03, T.answer[1])) };
  p.pending = u < T.fade[0] ? 1 : fadeOut;
  p.fade = fadeOut;
  return p;
}

export function describe(u, qi) {
  const q = QUESTIONS[qi];
  const f = fuse(q);
  const p = pose(u, qi);
  const n = (i) => CHUNKS[i].src + (CHUNKS[i].page ? " p." + CHUNKS[i].page : "");
  if (u < 0.23) {
    const done = p.cards.filter((c) => u > T.spawn[c.stamped] + 0.045).length;
    return `ingest · ${done < 1 ? "cut into" : "stamped"} ${CHUNK_CHARS}-char chunks, ${OVERLAP_CHARS} shared`;
  }
  if (u < T.askStart) return `index holds ${DRAWERS} chunks · ${DIMS}-number vector each`;
  if (u < T.qStamp[0]) return `ask · "${q.text}"`;
  if (u < 0.43) return `embed question · same model, ${DIMS} numbers`;
  if (u < T.sweep[0]) return "query vector sent to the search";
  if (u < T.park[0]) {
    const i = Math.min(DRAWERS - 1, Math.floor(p.sweep * DRAWERS));
    return `hybrid search · chunk ${i + 1} · keyword ${q.kw[i].toFixed(2)} · vector ${q.vec[i].toFixed(2)}`;
  }
  if (u < T.pickStart) return "merge both rankings";
  if (u < T.press[0]) {
    const r = Math.min(TOP_K - 1, Math.floor((u - T.pickStart) / T.pickLen));
    return `top ${TOP_K} · #${r + 1} ${n(f.top[r])} → prompt`;
  }
  if (u < T.press[1]) return `prompt = rules + ${TOP_K} chunks + question → chat model`;
  if (u < T.fade[0]) return `answer from ${n(f.top[0])} +${TOP_K - 1} more, sources attached`;
  return "ready for the next question";
}
