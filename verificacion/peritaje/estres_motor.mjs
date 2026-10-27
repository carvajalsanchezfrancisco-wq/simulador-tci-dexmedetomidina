// Peritaje · prueba de estrés del motor: configuraciones y secuencias de eventos aleatorias
// (cambios de objetivo, pausas, cambios de objetivo en pausa, reanudaciones) con comprobación de invariantes.
// Dependencias: las de ../../compilar (npm ci en esa carpeta)
const NM = new URL("../../compilar/node_modules/", import.meta.url);
const { build } = await import(new URL("esbuild/lib/main.js", NM));
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
const SRC = process.argv[2], OUT = process.argv[3], N = Number(process.argv[4] ?? 3000);
const tmp = OUT + ".jsx", bundle = OUT + ".mjs";
writeFileSync(tmp, readFileSync(SRC, "utf8") + "\nexport { buildPlan, safetyReview, validateDraft, draftToConfig, simulateWashout, rateHistory, SAFETY, PUMP_STEP_MLH, LOAD_SEC, APP_VERSION, PK_MODELS };\n");
await build({ entryPoints: [tmp], bundle: true, platform: "node", format: "esm", outfile: bundle, jsx: "automatic", logLevel: "warning", nodePaths: [fileURLToPath(NM)] });
const M = await import(pathToFileURL(bundle).href);

let seed = 20261012;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const pick = a => a[Math.floor(rnd() * a.length)];
const r1 = (a, b) => Math.round((a + rnd() * (b - a)) * 10) / 10;

const fails = [], stats = { casos: 0, invalidos: 0, duros: 0, eventos: 0, cargas: 0, errCargaMax: 0, errMantMax: 0, pausasConCambio: 0, limitadosPorResolucion: 0 };
// Tolerancias: ±1 % al final de la carga y ±5,5 % en mantenimiento, ampliadas con la resolución de la bomba
// (±0,05 mL/h sobre la tasa programada): con tasas de pocos mL/h el redondeo a 0,1 mL/h domina el error.
const fail = (id, msg, ctx) => { if (fails.length < 40) fails.push({ id, msg, ctx }); };

for (let k = 0; k < N; k++) {
  const induction = rnd() < 0.8 ? "load" : "none";
  const draft = {
    model: pick(Object.keys(M.PK_MODELS)), weight: String(pick([2, 3.5, 5, 8, 12.4, 15, 20, 25, 33, 40, 60, 80])),
    targetCp: String(r1(0.1, 4)), duration: String(pick([15, 30, 45, 60, 90, 120, 180, 240])), stock: pick([100, 200, 500]),
    conc: "auto", concCustom: "", induction, syringeMl: pick([10, 20, 50]),
    pumpMin: String(pick([0.1, 0.5, 1, 2])), pumpMax: String(pick([50, 100, 200, 999])),
    premed: induction === "none" ? String(pick([0, 0, 1, 3, 5, 10])) : "0",
  };
  const v = M.validateDraft(draft);
  if (!v.valid) { stats.invalidos++; continue; }
  const c = M.draftToConfig(draft, v);
  const total = c.durationMin * 60;
  // Secuencia de eventos como la genera la interfaz
  const changes = [];
  let t = 0, paused = false, target = c.targetCp;
  const nEv = Math.floor(rnd() * 6);
  for (let e = 0; e < nEv; e++) {
    t += 1 + Math.floor(rnd() * Math.max(2, total / 4));
    if (t >= total - 1) break;
    const roll = rnd();
    if (!paused && roll < 0.55) { target = r1(0.1, 4); if (target !== changes.at(-1)?.targetCp) changes.push({ sec: t, targetCp: target }); }
    else if (!paused) { changes.push({ sec: t, targetCp: target, pause: true }); paused = true; }
    else if (roll < 0.4) { target = r1(0.1, 4); changes.push({ sec: t, targetCp: target, pause: true }); stats.pausasConCambio++; }
    else { changes.push({ sec: t, targetCp: target }); paused = false; }
  }
  stats.casos++; stats.eventos += changes.length;
  const ctx = JSON.stringify({ draft, changes });
  let plan;
  try { plan = M.buildPlan(c, changes); } catch (err) { fail("EXC", String(err), ctx); continue; }
  const review = M.safetyReview(plan, c);
  if (review.hard.length) stats.duros++;
  const doseCap = (M.SAFETY.rateUgKgH.hard * c.weight) / c.conc + 1e-9;
  // I1: valores finitos y no negativos
  for (const [name, arr] of [["cp", plan.cp], ["c2", plan.c2], ["rateAt", plan.rateAt], ["deliveredMl", plan.deliveredMl]]) {
    if (arr.some(x => !Number.isFinite(x) || x < 0)) { fail("I1", `${name} no finito o negativo`, ctx); break; }
  }
  // I2: pasos ordenados, segundos únicos y tasas válidas
  for (let i = 0; i < plan.steps.length; i++) {
    const s = plan.steps[i];
    if (i && s.sec <= plan.steps[i - 1].sec) { fail("I2", `pasos desordenados o repetidos en ${s.sec}`, ctx); break; }
    if (Math.abs(s.rateMlH / M.PUMP_STEP_MLH - Math.round(s.rateMlH / M.PUMP_STEP_MLH)) > 1e-6) { fail("I2", `tasa no múltiplo de 0,1: ${s.rateMlH}`, ctx); break; }
    if (s.rateMlH > c.pumpMaxMlH + 1e-9) { fail("I2", `tasa ${s.rateMlH} > máximo de la bomba`, ctx); break; }
    if (s.rateMlH > doseCap) { fail("I2", `tasa ${s.rateMlH} mL/h > 30 µg/kg/h`, ctx); break; }
  }
  // I3: volumen = integral de la tasa; monótono
  let vol = 0, bad = false;
  for (let s = 0; s < plan.totalSec; s++) { vol += plan.rateAt[s] / 3600; if (Math.abs(plan.deliveredMl[s + 1] - vol) > 1e-6 * Math.max(1, vol)) { bad = true; break; } }
  if (bad) fail("I3", "volumen ≠ integral de la tasa", ctx);
  // I4: tasa 0 en pausa; objetivo = el del tramo
  const segs = [{ sec: 0, targetCp: c.targetCp }, ...changes];
  for (let i = 0; i < segs.length; i++) {
    const a = segs[i].sec, b = i + 1 < segs.length ? segs[i + 1].sec : plan.totalSec;
    for (let s = a; s < b; s++) {
      if (plan.target[s] !== segs[i].targetCp) { fail("I4", `objetivo ${plan.target[s]} ≠ ${segs[i].targetCp} en ${s}`, ctx); s = b; i = segs.length; }
      else if (segs[i].pause && plan.rateAt[s] !== 0) { fail("I4", `tasa ${plan.rateAt[s]} en pausa (s ${s})`, ctx); s = b; i = segs.length; }
    }
  }
  // I5 (TCI con carga): al final de cada carga no limitada la Cp = objetivo ±1 %; en mantenimiento ±5,5 %
  if (c.induction === "load") {
    for (let i = 0; i < plan.steps.length; i++) {
      const s = plan.steps[i];
      if (s.kind !== "load" || s.limited || s.doseLimited) continue;
      const end = s.sec + s.loadSec;
      const nextChange = segs.find(x => x.sec > s.sec)?.sec ?? plan.totalSec;
      if (end >= nextChange || end > plan.totalSec) continue;
      stats.cargas++;
      const err = Math.abs(plan.cp[end] - s.targetCp) / s.targetCp;
      stats.errCargaMax = Math.max(stats.errCargaMax, err);
      if (s.rateMlH >= 5) stats.errCargaMaxTasa5 = Math.max(stats.errCargaMaxTasa5 ?? 0, err);
      if (err > 0.01) stats.limitadosPorResolucion++;
      if (err > Math.max(0.01, 0.05 / s.rateMlH + 0.002)) fail("I5", `Cp al final de la carga ${plan.cp[end].toFixed(4)} vs ${s.targetCp} (${(err * 100).toFixed(2)} %, tasa ${s.rateMlH} mL/h)`, ctx);
    }
    for (let s = 0; s <= plan.totalSec; s++) {
      const st = plan.steps[[...plan.steps.keys()].findLast(j => plan.steps[j].sec <= s)];
      if (!["maintain", "adjust", "resume", "target"].includes(st.kind) || st.outOfRange || st.limited) continue;
      const err = Math.abs(plan.cp[s] - plan.target[s]) / plan.target[s];
      if (err > stats.errMantMax) { stats.errMantMax = err; stats.tasaEnErrMantMax = st.rateMlH; }
      if (st.rateMlH >= 5) stats.errMantMaxTasa5 = Math.max(stats.errMantMaxTasa5 ?? 0, err);
      if (err > 0.055 + 0.05 / st.rateMlH) { fail("I5", `mantenimiento ${(err * 100).toFixed(2)} % del objetivo en ${s} (tasa ${st.rateMlH} mL/h)`, ctx); break; }
    }
  }
  // I6: descenso tras la infusión en un instante aleatorio
  const endSec = Math.floor(rnd() * plan.totalSec);
  const w = M.simulateWashout(plan, endSec, 600);
  if (w.cp.some(x => !Number.isFinite(x) || x < 0) || Math.abs(w.cp[0] - plan.cp[endSec]) > 1e-12) fail("I6", "descenso tras la infusión inválido", ctx);
  if (plan.depot[endSec] === 0 && w.cp[600] > w.cp[0] + 1e-12) fail("I6", "la Cp sube tras detener la infusión sin depósito IM", ctx);
}
const res = { version: M.APP_VERSION, semilla: 20261012, ...stats, fallos: fails.length, detalle: fails };
writeFileSync(OUT + "_resultado.json", JSON.stringify(res, null, 1));
console.log(JSON.stringify({ ...res, detalle: fails.slice(0, 6) }, null, 1));
