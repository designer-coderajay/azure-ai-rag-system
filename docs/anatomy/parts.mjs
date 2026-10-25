// Geometry for the RAG bench. Every function takes the projection P and returns SVG text.
// The same file is used by build.mjs (first frame) and inlined into the page (live frames).
import * as k from "./kit/iso-kit.mjs";

export const W = {
  PLATE: { x: -236, y: -76, w: 424, d: 152, r: 9 },
  PLATE_H: 12,
  FOOT_H: 5,
  // cabinet
  CAB: { x: -5, y: -33, w: 56, d: 60, r: 3 },
  FACE: 27, // y of the cabinet's front face
  DRAWER_Z: (i) => 10 + 10.5 * i,
  DRAWER_H: 8.6,
  DRAWER_W: 46,
  TOP: 98,
  // reader mast
  MAST: { x: -31, y: 36, w: 6, d: 6, r: 1.2 },
  // prompt tray and press
  TRAY: { x: 78, y: 28, w: 34, d: 30, r: 2 },
  PRESS_XY: [95, 43],
  OUT: { x: 112, y: 28, w: 66, d: 30, r: 3 },
};

const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const at = (P, p) => k.iso(p, P);
const byDepth = (P, points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const opaque = (svg, op) => (op >= 0.999 ? svg : `<g opacity="${Math.max(0, op).toFixed(3)}">${svg}</g>`);
const rect = (P, x0, x1, y, z0, z1) => k.pathOf([at(P, [x0, y, z0]), at(P, [x1, y, z0]), at(P, [x1, y, z1]), at(P, [x0, y, z1])], true);
const screws = (P, plan, z, inset = 3, size = 0.45) => D(k.corners(plan, inset).map(([x, y]) => at(P, [x, y, z])), { size });

// ---------------------------------------------------------------- base
export function plate(P) {
  const { PLATE, PLATE_H, FOOT_H } = W;
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(P, [...k.corners(PLATE, 22), [0, PLATE.y + 22], [0, PLATE.y + PLATE.d - 22]])) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const corner = k.corners(PLATE, 10);
  out.push(L(corner.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(corner.map(([x, y]) => at(P, [x, y, 0])), { size: 0.5 }));
  // ruler strip along the near edge: one tick per 10 characters of a chunk's worth of bench
  const strip = { x: -222, y: PLATE.y + PLATE.d - 15, w: 396, d: 7, r: 1 };
  out.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 5, 5, strip.y + 0.8, 0.6, [2, 3.6], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  out.push(D([at(P, [strip.x + 2, strip.y + 3.5, 0.6]), at(P, [strip.x + strip.w - 2, strip.y + 3.5, 0.6])], { size: 0.45 }));
  return out.join("");
}

// ---------------------------------------------------------------- 1 · feed: a stack of documents
export function feed(P) {
  const out = [];
  const riser = { x: -218, y: -28, w: 52, d: 56, r: 3 };
  out.push(`<path class="iso-halo" d="${k.haloOf(riser, 0, 6, P)}" style="filter:blur(4px)"/>`);
  out.push(S(k.slabOf(riser, 0, 6, P, 5, 0.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(riser, 2.6), 6, P, 5), { tone: "faint" }));
  out.push(screws(P, riser, 6, 5));
  // back stop and far guide, then the stack, then two corner posts in front
  out.push(S(k.slabOf({ x: -217, y: -27, w: 2.4, d: 54, r: 0.8 }, 6, 14, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -217, y: -27, w: 50, d: 2.4, r: 0.8 }, 6, 14, P, 3, 0.4), { tone: "mid" }));
  for (let i = 0; i < 8; i++) {
    const jx = i % 2 ? 0.7 : -0.5;
    const jy = i % 3 ? -0.4 : 0.6;
    const sheet = { x: -213 + jx, y: -22 + jy, w: 40, d: 44, r: 0.8 };
    out.push(S(k.slabOf(sheet, 6 + i * 1.15, 1.05, P, 3, 0.2), { tone: "hi", crease: "lo" }));
  }
  const top = 6 + 8 * 1.15;
  out.push(L(k.lineOnTop([-206, -12], [-186, -12], top, P) + k.lineOnTop([-206, -5], [-180, -5], top, P) + k.lineOnTop([-206, 2], [-190, 2], top, P), { tone: "lo", free: true }));
  for (const [x, y] of [[-168.6, -26], [-168.6, 25]]) out.push(S(k.cylinder(x, y, 1.7, 6, 15, P, 16), { tone: "mid" }));
  // hand wheel on the near edge of the riser
  out.push(S(k.cylinder(-200, 29.4, 3, 0, 5, P, 20), { tone: "mid" }));
  out.push(L(k.knurl(-200, 29.4, 3, 0, 5, 18, P), { tone: "lo" }));
  // short ramp from the stack to the cutting bed
  out.push(S(k.slabOf({ x: -166, y: -18, w: 18, d: 36, r: 1 }, 0, 3, P, 3, 0.4), { tone: "lo" }));
  return out.join("");
}

// ---------------------------------------------------------------- 2 · chunker: guillotine and bed
const BED = { x: -150, y: -24, w: 50, d: 48, r: 3 };
export function chunkerBack(P) {
  const out = [`<path class="iso-halo" d="${k.haloOf(BED, 0, 3, P)}" style="filter:blur(4px)"/>`];
  out.push(S(k.slabOf(BED, 0, 3, P, 5, 0.5), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BED, 3), 3, P, 5), { tone: "faint" }));
  out.push(L(k.planOutline({ x: -129.4, y: -21.5, w: 4.2, d: 43, r: 1 }, 3, P, 3), { tone: "lo" })); // blade slot
  out.push(screws(P, BED, 3, 6));
  // far post
  out.push(S(k.slabOf({ x: -133, y: -31, w: 9, d: 7, r: 1.4 }, 0, 70, P, 3, 0.5), { tone: "mid" }));
  return out.join("");
}
export function blade(P) {
  const out = [];
  out.push(S(k.slabOf({ x: -128.4, y: -21.2, w: 2.4, d: 42.4, r: 0.4 }, 36, 30, P, 2, 0.3), { tone: "hi", lit: true }));
  return out.join("");
}
export function chunkerFront(P) {
  const out = [];
  // near post, then the cross beam with its knob and the engraved label plate on the bed
  out.push(S(k.slabOf({ x: -133, y: 24, w: 9, d: 7, r: 1.4 }, 0, 70, P, 3, 0.5), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -135, y: -32, w: 14, d: 66, r: 2 }, 62, 8, P, 4, 0.6), { tone: "mid" }));
  out.push(D([at(P, [-128, -27, 70]), at(P, [-128, 29, 70])], { size: 0.5 }));
  out.push(S(k.cylinder(-128, 0, 5.4, 70, 4, P, 28), { tone: "mid" }));
  out.push(L(k.knurl(-128, 0, 5.4, 70, 74, 32, P), { tone: "lo" }));
  out.push(L(k.lineOnTop([-131, 0], [-123.4, 0], 74, P), { tone: "hi" }));
  out.push(D([at(P, [-128, 0, 74])], { size: 0.5, tone: "hi" }));
  const label = { x: -146, y: 14, w: 22, d: 6, r: 1 };
  out.push(S(k.slabOf(label, 3, 0.8, P, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(label, 1), 3.8, P, 3), { tone: "faint" }));
  out.push(k.faceTextSvg(k.topMatrix([-145, 18.3], 3.8, P, "x"), "500 | 50", { size: 3.2, tone: "mid" }));
  // ruler on the bed's near edge
  const strip = { x: -146, y: 8, w: 42, d: 5, r: 0.6 };
  out.push(S(k.slabOf(strip, 3, 0.5, P, 2), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 2, strip.x + strip.w - 2, 2, 5, strip.y + 0.5, 3.5, [1.6, 3], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  return out.join("");
}

// ---------------------------------------------------------------- belt, chute, stamp
export function belt(P) {
  const out = [];
  out.push(S(k.slabOf({ x: -100, y: -9, w: 94, d: 18, r: 1 }, 0, 1.5, P, 3, 0.2), { tone: "lo" }));
  // belt cross-lines end on the belt's own edges
  const t = k.topTicks(-98, -8, 6, 5, 9, 1.5, [-2, -3.4], P);
  out.push(L(t.minor, { tone: "faint" }), L(t.major, { tone: "lo" }));
  out.push(S(k.slabOf({ x: -100, y: -13, w: 94, d: 4, r: 0.8 }, 0, 3, P, 3, 0.4), { tone: "mid" }));
  // chute for the question card, crossing the near rail
  out.push(S(k.slabOf({ x: -79, y: 9, w: 18, d: 54, r: 1 }, 0, 1.5, P, 3, 0.2), { tone: "lo" }));
  out.push(S(k.slabOf({ x: -81.2, y: 13, w: 2, d: 50, r: 0.6 }, 0, 3, P, 3, 0.3), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -61, y: 13, w: 2, d: 50, r: 0.6 }, 0, 3, P, 3, 0.3), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -100, y: 9, w: 19, d: 4, r: 0.8 }, 0, 3, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -59.4, y: 9, w: 53.4, d: 4, r: 0.8 }, 0, 3, P, 3, 0.4), { tone: "mid" }));
  return out.join("");
}

export function cableLine(P) {
  // a cable lying on the plate from the belt's near rail to the reader's foot
  const a = at(P, [-30, 11, 3]);
  const via = [at(P, [-30, 14, 0.7]), at(P, [-27, 27, 0.7]), at(P, [-27, 29.6, 0.7])];
  const end = at(P, [-27, 34, 4]);
  return `<g class="rag-cable">${L(k.pathOf([a, ...via, end]), { tone: "mid", dashed: true, flow: true })}</g>`;
}
export function cableEnds(P) {
  return D([at(P, [-30, 11, 3]), at(P, [-27, 34, 4])], { size: 1.2, tone: "mid" });
}

export function stampStatic(P) {
  const out = [];
  out.push(S(k.slabOf({ x: -76, y: -30, w: 10, d: 10, r: 2 }, 0, 56, P, 4, 0.6), { tone: "mid" }));
  return out.join("");
}
export function stampHead(P, down) {
  const dz = -11 * down;
  const out = [];
  const g = [];
  g.push(S(k.cylinder(-71, 0, 2.4, 17, 23, P, 18), { tone: "hi", crease: "none" }));
  g.push(S(k.cylinder(-71, 0, 6, 14, 3, P, 28, 0.4), { tone: "hi", lit: true, crease: "lo" }));
  g.push(L(k.ring(-71, 0, 4, 17, P, 20), { tone: "lo" }));
  out.push(`<g transform="${k.translateAlong(P, [0, 0, dz])}">${g.join("")}</g>`);
  return out.join("");
}
export function stampArm(P, needle) {
  const out = [];
  out.push(S(k.cylinder(-71, 0, 4.4, 38, 8, P, 24), { tone: "mid" })); // sleeve under the arm, hidden at its top by the arm
  out.push(L(k.sideArc(-71, 0, 4.4, 42, P, 12), { tone: "faint" }));
  out.push(S(k.slabOf({ x: -80, y: -30, w: 18, d: 42, r: 2.4 }, 46, 8, P, 4, 0.6), { tone: "mid" }));
  // embedding dial on top of the arm: 36 marks, a needle that spins while it stamps
  const dial = [-71, -15];
  out.push(S(k.cylinder(dial[0], dial[1], 8.4, 54, 4, P, 40, 0.5), { tone: "hi", crease: "lo" }));
  out.push(L(k.knurl(dial[0], dial[1], 8.4, 54, 56, 48, P, 0.3), { tone: "lo" }));
  out.push(L(k.ring(dial[0], dial[1], 6.2, 58, P, 36), { tone: "lo" }));
  const t = k.radialTicks(dial[0], dial[1], 6, 36, 6, 58, [0.9, 1.9], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  const a = needle * Math.PI * 2;
  out.push(`<path data-part="needle" class="iso-line" data-tone="lit" d="${k.lineOnTop([dial[0], dial[1]], [dial[0] + Math.sin(a) * 5.4, dial[1] - Math.cos(a) * 5.4], 58.2, P)}" style="stroke-width:1.1"/>`);
  out.push(L(k.ring(dial[0], dial[1], 1.2, 58, P, 12), { tone: "mid" }));
  out.push(D([at(P, [-77, 4, 54]), at(P, [-65, 4, 54])], { size: 0.45 }));
  out.push(k.faceTextSvg(k.sideMatrix([-77.6, 12], 47.2, P, "left"), "1536", { size: 4, tone: "mid" }));
  return out.join("");
}

// ---------------------------------------------------------------- cards
const CARD = { w: 20, d: 14 };
export function card(P, x, y, z, { op = 1, tagged = false, lit = true } = {}) {
  if (op <= 0.003) return "";
  const plan = { x: x - CARD.w / 2, y: y - CARD.d / 2, w: CARD.w, d: CARD.d, r: 1 };
  const out = [S(k.slabOf(plan, z, 1.2, P, 4, 0.3), { tone: "hi", lit, crease: "lo" })];
  // the 50 characters shared with the next chunk are a tenth of its length
  out.push(L(k.lineOnTop([x + CARD.w / 2 - 2, y - CARD.d / 2], [x + CARD.w / 2 - 2, y + CARD.d / 2], z + 1.2, P), { tone: "lo" }));
  out.push(L(k.lineOnTop([x - CARD.w / 2 + 2.4, y - 2.4], [x + CARD.w / 2 - 5, y - 2.4], z + 1.2, P), { tone: "faint", free: true }));
  out.push(L(k.lineOnTop([x - CARD.w / 2 + 2.4, y + 0.4], [x + CARD.w / 2 - 7, y + 0.4], z + 1.2, P), { tone: "faint", free: true }));
  if (tagged) out.push(D([-6, -3, 0, 3, 6].map((dx) => at(P, [x + dx - 1, y + 4.2, z + 1.2])), { size: 0.55, tone: "hi" }));
  return opaque(out.join(""), op);
}

// ---------------------------------------------------------------- 3 · the index cabinet
export function cabinet(P) {
  const { CAB, FACE, TOP } = W;
  const out = [`<path class="iso-halo" d="${k.haloOf(CAB, 0, TOP + 5, P)}"/>`];
  out.push(S(k.slabOf({ x: -7, y: -35, w: 60, d: 64, r: 3 }, 0, 8, P, 5, 0.8), { tone: "lo" })); // plinth
  out.push(S(k.slabOf(CAB, 8, TOP - 8, P, 5, 0.8), { tone: "mid", inner: L(k.sideSeam(CAB, 8 + 1, P, 5), { tone: "faint" }) }));
  out.push(S(k.slabOf({ x: -7, y: -35, w: 60, d: 64, r: 3 }, TOP, 5, P, 5, 0.8), { tone: "lo" })); // cap
  out.push(L(k.planOutline({ x: -3, y: -31, w: 52, d: 56, r: 2 }, TOP + 5, P, 5), { tone: "faint" }));
  out.push(screws(P, { x: -7, y: -35, w: 60, d: 64 }, TOP + 5, 4));
  // recess frames round every drawer on the front
  for (let i = 0; i < 8; i++) {
    const z = W.DRAWER_Z(i);
    out.push(L(rect(P, -1.2, 47.2, FACE, z - 1, z + W.DRAWER_H + 0.8), { tone: "faint" }));
  }
  return out.join("");
}

// one drawer: closed front panel, or a tray that slid out by s with its card inside
export function drawer(P, i, s, kw, vec, { card: inside = false, reveal = 1 } = {}) {
  const { FACE, DRAWER_H } = W;
  const z = W.DRAWER_Z(i);
  const out = [];
  if (s > 0.05) {
    out.push(S(k.slabOf({ x: 1.2, y: FACE, w: 43.6, d: s, r: 0.4 }, z + 0.4, 0.8, P, 2, 0.2), { tone: "lo" }));
    out.push(S(k.slabOf({ x: 1.2, y: FACE, w: 1.2, d: s, r: 0.3 }, z + 1.2, 6, P, 2, 0.2), { tone: "mid" }));
    if (inside) out.push(card(P, 23, FACE + s * 0.5, z + 1.2, { lit: true, tagged: true }));
    out.push(S(k.slabOf({ x: 43.6, y: FACE, w: 1.2, d: s, r: 0.3 }, z + 1.2, 6, P, 2, 0.2), { tone: "mid" }));
  }
  const y = FACE + s;
  out.push(S(k.slabOf({ x: 0, y, w: W.DRAWER_W, d: 2.4, r: 0.8 }, z, DRAWER_H, P, 3, 0.5), { tone: "mid" }));
  const f = y + 2.4;
  // label holder, two score bars (keyword above, vector below) and a pull
  out.push(S(k.slabOf({ x: 3, y: f, w: 10, d: 0.6, r: 0.3 }, z + 2, 4.6, P, 2, 0.15), { tone: "lo", crease: "none" }));
  out.push(D([at(P, [4.2, f + 0.6, z + 3.2]), at(P, [11.8, f + 0.6, z + 3.2])], { size: 0.35, tone: "mid" }));
  if (kw * reveal > 0.02) out.push(S(k.slabOf({ x: 16, y: f, w: Math.max(0.8, 24 * kw * reveal), d: 0.7, r: 0.3 }, z + 5.2, 1.5, P, 2, 0.1), { tone: "mid", crease: "none" }));
  if (vec * reveal > 0.02) out.push(S(k.slabOf({ x: 16, y: f, w: Math.max(0.8, 24 * vec * reveal), d: 0.7, r: 0.3 }, z + 1.7, 1.5, P, 2, 0.1), { tone: "hi", crease: "none" }));
  out.push(S(k.slabOf({ x: 41.2, y: f, w: 3.2, d: 1.8, r: 0.6 }, z + 1.8, 5, P, 2, 0.2), { tone: "mid" }));
  return out.join("");
}

// ---------------------------------------------------------------- 4 · reader: mast and sweeping bar
export function mast(P) {
  const out = [];
  out.push(S(k.slabOf({ x: -37, y: 30, w: 18, d: 20, r: 2 }, 0, 4, P, 4, 0.6), { tone: "lo" }));
  out.push(D(k.corners({ x: -37, y: 30, w: 18, d: 20 }, 3).map(([x, y]) => at(P, [x, y, 4])), { size: 0.45 }));
  out.push(S(k.slabOf(W.MAST, 4, 108, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: -33, y: 34, w: 10, d: 10, r: 1.6 }, 112, 3, P, 3, 0.4), { tone: "lo" }));
  return out.join("");
}
export function bar(P, z, loaded) {
  const out = [];
  out.push(S(k.slabOf({ x: -36, y: 32, w: 16, d: 14, r: 1.6 }, z - 3, 9, P, 3, 0.5), { tone: "mid" })); // carriage round the mast
  out.push(D([at(P, [-33, 45, z + 3]), at(P, [-23, 45, z + 3])], { size: 0.4 }));
  out.push(S(k.slabOf({ x: -20, y: 34, w: 74, d: 3.6, r: 0.8 }, z, 1.8, P, 3, 0.3), { tone: "mid" }));
  out.push(L(k.lineOnTop([-18, 35.8], [52, 35.8], z + 1.8, P), { tone: "faint" }));
  for (const x of [8, 38]) {
    out.push(S(k.cylinder(x, 35.8, 1.7, z + 1.8, 1.8, P, 16), { tone: "mid" }));
    if (loaded > 0.01) out.push(opaque(S(k.cylinder(x, 35.8, 1.7, z + 1.8, 1.8, P, 16), { tone: "hi", lit: true }), loaded));
  }
  return out.join("");
}

// ---------------------------------------------------------------- 5 · prompt tray, press, answer
export function pressColumn(P) {
  const out = [];
  out.push(S(k.slabOf({ x: 86, y: 8, w: 18, d: 8, r: 2 }, 0, 60, P, 4, 0.6), { tone: "mid" }));
  out.push(k.faceTextSvg(k.sideMatrix([89.4, 16], 26, P, "left"), "LLM", { size: 4, tone: "mid" }));
  return out.join("");
}
export function trayBack(P) {
  const { TRAY, OUT } = W;
  const out = [`<path class="iso-halo" d="${k.haloOf(TRAY, 0, 3, P)}" style="filter:blur(4px)"/>`];
  out.push(S(k.slabOf(TRAY, 0, 3, P, 4, 0.5), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(TRAY, 2.4), 3, P, 4), { tone: "faint" }));
  out.push(S(k.slabOf(OUT, 0, 2.4, P, 5, 0.5), { tone: "lo" }));
  out.push(L(k.planOutline(k.insetPlan(OUT, 3), 2.4, P, 5), { tone: "faint" }));
  const t = k.topTicks(OUT.x + 6, OUT.x + OUT.w - 6, 4, 5, OUT.y + OUT.d - 3, 2.4, [-1.6, -3], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  for (const [x, y] of [[80, 30], [110, 30]]) out.push(S(k.cylinder(x, y, 1.5, 3, 9, P, 16), { tone: "mid" }));
  return out.join("");
}
export function trayFront(P) {
  return [[80, 56], [110, 56]].map(([x, y]) => S(k.cylinder(x, y, 1.5, 3, 9, P, 16), { tone: "mid" })).join("");
}
export function platen(P, down) {
  const dz = -7.2 * down;
  const [x, y] = W.PRESS_XY;
  const g = [];
  g.push(S(k.cylinder(x, y, 2.4, 20.5, 24, P, 18), { tone: "hi", crease: "none" }));
  g.push(S(k.cylinder(x, y, 11, 18, 2.5, P, 36, 0.4), { tone: "hi", crease: "lo" }));
  g.push(L(k.ring(x, y, 8, 20.5, P, 28), { tone: "lo" }));
  return `<g transform="${k.translateAlong(P, [0, 0, dz])}">${g.join("")}</g>`;
}
export function pressArm(P) {
  const [x, y] = W.PRESS_XY;
  const out = [];
  out.push(S(k.cylinder(x, y, 4.2, 40, 12, P, 24), { tone: "mid" })); // sleeve, hidden at its top by the arm
  out.push(L(k.sideArc(x, y, 4.2, 46, P, 12), { tone: "faint" }));
  out.push(S(k.slabOf({ x: 88, y: 8, w: 14, d: 50, r: 2 }, 52, 8, P, 4, 0.6), { tone: "mid" }));
  out.push(D([at(P, [95, 12, 60]), at(P, [95, 54, 60])], { size: 0.5 }));
  out.push(S(k.cylinder(x, y, 3, 60, 6, P, 20), { tone: "mid" }));
  out.push(L(k.knurl(x, y, 3, 60, 66, 14, P), { tone: "lo" }));
  return out.join("");
}
export function answer(P, a) {
  if (a.op <= 0.003) return "";
  const { x, z, tabs } = a;
  const plan = { x: x - 14, y: 43 - 9, w: 28, d: 18, r: 1.2 };
  const out = [S(k.slabOf(plan, z, 1.4, P, 4, 0.3), { tone: "hi", lit: true, crease: "lo" })];
  for (const dy of [-4.6, -1.4, 1.8]) out.push(L(k.lineOnTop([x - 11, 43 + dy], [x + 8 - (dy > 0 ? 8 : 0), 43 + dy], z + 1.4, P), { tone: "faint", free: true }));
  for (let j = 0; j < 5; j++) {
    const px = x - 11 + j * 5;
    const tab = S(k.slabOf({ x: px, y: 43 + 9, w: 3.4, d: 1.6, r: 0.4 }, z, 1.4, P, 2, 0.1), { tone: j < tabs ? "hi" : "lo", lit: j < tabs, crease: "none" });
    out.push(tab);
  }
  return opaque(out.join(""), a.op);
}
