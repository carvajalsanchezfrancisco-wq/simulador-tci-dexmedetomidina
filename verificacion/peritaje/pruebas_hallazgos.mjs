// Peritaje · pruebas de los hallazgos de la revisión (escenarios concretos de los revisores).
// Uso: node pruebas_hallazgos.mjs <jsx> <salida>
// Dependencias: las de ../../compilar (npm ci en esa carpeta)
const NM = new URL("../../compilar/node_modules/", import.meta.url);
const { build } = await import(new URL("esbuild/lib/main.js", NM));
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
const [SRC, OUT] = process.argv.slice(2);
writeFileSync(OUT + ".jsx", readFileSync(SRC, "utf8") + "\nexport { buildPlan, safetyReview, newOrWorse, confirmationCovers, asConfirmation, validateDraft, draftToConfig, SAFETY, APP_VERSION };\n");
await build({ entryPoints: [OUT + ".jsx"], bundle: true, platform: "node", format: "esm", outfile: OUT + ".mjs", jsx: "automatic", logLevel: "warning", nodePaths: [fileURLToPath(NM)] });
const M = await import(pathToFileURL(OUT + ".mjs").href);
const res = [];
const test = (id, desc, ok, ev) => { res.push({ id, desc, pass: !!ok, evidencia: ev }); console.log(`${ok ? "✔" : "✘"} ${id} ${desc} · ${ev}`); };
const cfg = (o = {}) => { const d = { model: "anestesiado", weight: "25", targetCp: "2.0", duration: "60", stock: 500, conc: "auto", concCustom: "", induction: "load", syringeMl: 50, pumpMin: "1", pumpMax: "100", premed: "0", ...o }; return M.draftToConfig(d, M.validateDraft(d)); };
const rev = (c, ch, timing = null) => M.safetyReview(M.buildPlan(c, ch, timing), c);
const val = (r, code) => r.items.find(i => i.code === code)?.value;

// H-01 · Cambio en pausa y «Reanudar» en el mismo segundo: el objetivo pendiente se toma de plan.target[sec]
{
  const c = cfg(); const ch = [{ sec: 900, targetCp: 2, pause: true }, { sec: 1000, targetCp: 3, pause: true }];
  const plan = M.buildPlan(c, ch);
  test("H-01", "Reanudar en el segundo del cambio en pausa usa el objetivo nuevo (plan.target[sec])", plan.target[1000] === 3 && plan.target[999] === 2, `target[999] ${plan.target[999]} · target[1000] ${plan.target[1000]}`);
}
// H-02 · Subida en pausa: al reanudar se pide la dosis en 60 min que empeora (6,2 → 9,6)
{
  const c = cfg();
  const baseline = rev(c, []).items;                                   // lo confirmado al pausar
  const plusTarget = [...baseline, { level: "soft", code: "target", value: 3.5 }];   // confirmado en pausa
  const cand = rev(c, [{ sec: 900, targetCp: 2, pause: true }, { sec: 940, targetCp: 3.5, pause: true }, { sec: 960, targetCp: 3.5 }]);
  const nw = M.newOrWorse(cand.items, plusTarget, "soft").map(i => i.code);
  test("H-02", "Objetivo subido en pausa: al reanudar se pide confirmar la dosis en 60 min que empeora, no el objetivo ya confirmado",
    nw.includes("hour") && !nw.includes("target"), `línea base hour ${val({ items: baseline }, "hour")?.toFixed(2)} → candidato ${val(cand, "hour")?.toFixed(2)} · nuevos/peores: ${nw.join(", ")}`);
}
// H-03 · Una confirmación no vale si los valores han subido desde que se mostró
{
  const shown = M.asConfirmation([{ code: "load", value: 3.47 }, { code: "rate", value: 20.8 }]);
  const later = [{ code: "load", value: 4.63 }, { code: "rate", value: 27.8 }];
  const same = [{ code: "load", value: 3.48 }, { code: "rate", value: 20.8 }];
  test("H-03", "Segundo clic con avisos peores que los mostrados: no se acepta; con los mismos (±2 %), sí",
    !M.confirmationCovers(shown, later) && M.confirmationCovers(shown, same), `peores ${M.confirmationCovers(shown, later)} · iguales ${M.confirmationCovers(shown, same)}`);
}
// H-04 · Bajar desde un límite duro ya registrado no pide confirmar el blando del mismo código
{
  const nw = M.newOrWorse([{ level: "soft", code: "hour", value: 10.01, text: "" }], [{ level: "hard", code: "hour", value: 14.55, text: "" }], "soft");
  test("H-04", "Bajar el objetivo desde una dosis en 60 min por encima del límite duro no pide confirmación", nw.length === 0, `nuevos/peores: ${nw.length}`);
}
// H-05 · Un objetivo fijado en pausa y sustituido antes de reanudar no cuenta como objetivo máximo
{
  const c = cfg({ weight: "15" });
  const r = rev(c, [{ sec: 900, targetCp: 2, pause: true }, { sec: 960, targetCp: 3, pause: true }, { sec: 1000, targetCp: 2.2, pause: true }, { sec: 1080, targetCp: 2.2 }]);
  test("H-05", "Objetivo de pausa sustituido (3,0 → 2,2) no genera «Cp objetivo 3.00 > 2.5»", !r.items.some(i => i.code === "target"), r.soft.join(" | ").slice(0, 120));
}
// H-06 · Comparación de la subida con margen: 1,2 → 2,2 no es «> 1 ng/mL»
{
  const pairs = []; for (let a = 1.1; a <= 3.0001; a += 0.1) { const x = Math.round(a * 10) / 10, y = Math.round((x + 1) * 10) / 10; if (y - x > M.SAFETY.targetStep.soft + 1e-9) pairs.push(`${x}→${y}`); }
  test("H-06", "Ninguna subida de exactamente 1,00 ng/mL (1,1–3,0 → +1) se considera > 1 ng/mL", pairs.length === 0, pairs.length ? pairs.join(", ") : "0 pares");
}
// H-07 · Pausa en modo manual con ajustes vencidos sin confirmar: la historia no se reescribe
{
  const c = cfg({ weight: "15" });
  const ch0 = [{ sec: 1201, targetCp: 1 }];
  const plan0 = M.buildPlan(c, ch0);
  const stopIdx = plan0.steps.findIndex(s => s.sec === 1201);
  const ackIdx = stopIdx - 1;
  const appliedAt = {}; for (let i = 1; i <= ackIdx; i++) appliedAt[i] = plan0.steps[i].sec;   // todo confirmado a tiempo salvo «Detener»
  const ch = [...ch0, { sec: 1501, targetCp: 1, pause: true }];
  const before = M.buildPlan(c, ch, { appliedAt, ackIdx, nowSec: 1500 });               // justo al pulsar Pausar
  const pauseIdx = before.steps.findIndex(s => s.kind === "pause");
  const fixed = { ...appliedAt }; for (let i = ackIdx + 1; i <= pauseIdx; i++) fixed[i] = 1501;
  const after = M.buildPlan(c, ch, { appliedAt: fixed, ackIdx: pauseIdx, nowSec: 1600 });  // corrección v1.3.0
  const buggy = M.buildPlan(c, ch, { appliedAt, ackIdx: pauseIdx, nowSec: 1600 });         // comportamiento anterior
  let dFix = 0, dBug = 0;
  for (let s = 0; s <= 1500; s++) { dFix = Math.max(dFix, Math.abs(after.cp[s] - before.cp[s])); dBug = Math.max(dBug, Math.abs(buggy.cp[s] - before.cp[s])); }
  test("H-07", "Modo manual: al pausar con «Detener» sin confirmar, la Cp registrada hasta la pausa no cambia",
    dFix < 1e-12 && dBug > 0.1, `diferencia máx. hasta 1500 s: corregido ${dFix.toExponential(1)} · sin corregir ${dBug.toFixed(3)} ng/mL (Cp a 1500 s ${before.cp[1500].toFixed(2)} vs ${buggy.cp[1500].toFixed(2)})`);
}
// H-08 · Atribución del límite: si se superan la bomba y la dosis, cuenta el menor
{
  const c = cfg({ weight: "80", targetCp: "0.1", conc: "custom", concCustom: "50", pumpMin: "0.1", pumpMax: "50" });
  const plan = M.buildPlan(c, [{ sec: 60, targetCp: 4 }]);
  const load = plan.steps.find(s => s.kind === "load" && s.sec === 60);
  const doseCap = Math.floor(30 * 80 / c.conc / 0.1 + 1e-9) * 0.1;
  test("H-08", "Carga que supera la bomba y el límite de dosis: se atribuye al límite que actúa", load && ((doseCap < 50 && load.doseLimited && !load.limited) || (doseCap >= 50 && load.limited && !load.doseLimited)),
    `conc ${c.conc} µg/mL · tope de dosis ${doseCap.toFixed(1)} mL/h · bomba 50 mL/h · pedida ${load?.requestedMlH} · programada ${load?.rateMlH} · limited ${load?.limited} · doseLimited ${load?.doseLimited}`);
}
// H-09 · «No alcanza el objetivo» solo para la carga del último tramo (no si la corta un cambio o una pausa)
{
  const c = cfg({ weight: "15", targetCp: "0.1", conc: "custom", concCustom: "10", pumpMin: "0.1", pumpMax: "60", duration: "120" });
  const r0 = rev(c, [{ sec: 1200, targetCp: 4 }]);
  const r1 = rev(c, [{ sec: 1200, targetCp: 4 }, { sec: 1400, targetCp: 1 }]);
  const r2 = rev(c, [{ sec: 1200, targetCp: 4 }, { sec: 1401, targetCp: 4, pause: true }]);
  test("H-09", "Carga limitada por dosis cortada por un cambio o una pausa: sin aviso de «no alcanza»",
    r0.items.some(i => i.code === "doseLimited") && !r1.items.some(i => i.code === "doseShort") && !r2.items.some(i => i.code === "doseShort"), `sin cortar: ${r0.items.map(i => i.code).join(",")} · cambio: ${r1.items.map(i => i.code).join(",")} · pausa: ${r2.items.map(i => i.code).join(",")}`);
}
writeFileSync(OUT + "_resultado.json", JSON.stringify({ version: M.APP_VERSION, results: res }, null, 1));
console.log(`${res.length} pruebas · ${res.filter(r => !r.pass).length} fallos`);
