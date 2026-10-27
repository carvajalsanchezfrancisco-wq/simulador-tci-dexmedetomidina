// Verificación de la v1.4.0 (modelo «corregido»: V1, V2 y aclaramiento reajustados en anestesia).
//   REG-03  Los modelos «anestesiado» y «publicado» dan en la v1.4.0 exactamente el mismo programa, la misma Cp y
//           los mismos avisos que en la v1.3.0 (mismos casos aleatorios, con cambios de objetivo y pausas).
//   CSV     Escribe el CSV de cada caso, con los tres modelos, para `reconstruir_cp.py --verificar`, que recalcula
//           la Cp desde el registro de tasas con una implementación independiente (tolerancia 0,5 %).
//   TCI-C   Con el modelo «corregido»: la Cp al final de cada carga no limitada queda a ±1 % del objetivo y, en
//           mantenimiento, a ±5,5 % (ambas ampliadas con la resolución de la bomba, ±0,05 mL/h).
// Uso: node verificar_v140.mjs <jsx v1.4.0> <jsx v1.3.0> <carpeta de salida> [casos por modelo]
// Dependencias: las de ../../compilar (npm ci en esa carpeta)
const NM = new URL("../../compilar/node_modules/", import.meta.url);
const { build } = await import(new URL("esbuild/lib/main.js", NM));
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const [SRC_NEW, SRC_OLD, OUT, NARG] = process.argv.slice(2);
const N = Number(NARG ?? 100);
const EXPORTS = "\nexport { buildPlan, buildCaseCsv, safetyReview, validateDraft, draftToConfig, PK_MODELS, DEFAULT_MODEL, APP_VERSION, LOAD_SEC };\n";
async function load(src, name) {
  const tmp = `${OUT}/${name}.jsx`, bundle = `${OUT}/${name}.mjs`;
  writeFileSync(tmp, readFileSync(src, "utf8") + EXPORTS);
  await build({ entryPoints: [tmp], bundle: true, platform: "node", format: "esm", outfile: bundle, jsx: "automatic",
                logLevel: "warning", nodePaths: [fileURLToPath(NM)] });
  return import(pathToFileURL(bundle).href);
}
mkdirSync(OUT, { recursive: true });
rmSync(`${OUT}/csv`, { recursive: true, force: true });
mkdirSync(`${OUT}/csv`, { recursive: true });
const NEW = await load(SRC_NEW, "nuevo"), OLD = await load(SRC_OLD, "anterior");

let seed = 20261027;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const pick = a => a[Math.floor(rnd() * a.length)];
const r1 = (a, b) => Math.round((a + rnd() * (b - a)) * 10) / 10;
const strip = plan => JSON.stringify({ ...plan, pk: { ...plan.pk } });   // las funciones de pk no se serializan

const res = { version: NEW.APP_VERSION, anterior: OLD.APP_VERSION, modeloPorDefecto: NEW.DEFAULT_MODEL,
              casos: {}, invalidos: 0, reg: { comparados: 0, distintos: [] }, tci: { cargas: 0, mantenimiento: 0, fallos: [] } };
const models = Object.keys(NEW.PK_MODELS);
for (const model of models) {
  res.casos[model] = 0;
  for (let k = 0; k < N; k++) {
    const induction = rnd() < 0.8 ? "load" : "none";
    const draft = {
      model, weight: String(pick([2, 3.5, 5, 8, 12.4, 15, 20, 25, 33, 40, 60, 80])), targetCp: String(r1(0.1, 4)),
      duration: String(pick([15, 30, 45, 60, 90, 120, 180, 240])), stock: pick([100, 200, 500]), conc: "auto", concCustom: "",
      induction, syringeMl: pick([10, 20, 50]), pumpMin: String(pick([0.1, 0.5, 1])), pumpMax: String(pick([50, 100, 200, 999])),
      premed: induction === "none" ? String(pick([0, 0, 1, 3, 5])) : "0",
    };
    const v = NEW.validateDraft(draft);
    if (!v.valid) { res.invalidos++; continue; }
    const c = NEW.draftToConfig(draft, v);
    const total = c.durationMin * 60;
    const changes = [];
    let t = 0, paused = false, target = c.targetCp;
    for (let e = 0, n = Math.floor(rnd() * 5); e < n; e++) {
      t += 1 + Math.floor(rnd() * Math.max(2, total / 4));
      if (t >= total - 1) break;
      const roll = rnd();
      if (!paused && roll < 0.6) { target = r1(0.1, 4); if (target !== changes.at(-1)?.targetCp) changes.push({ sec: t, targetCp: target }); }
      else if (!paused) { changes.push({ sec: t, targetCp: target, pause: true }); paused = true; }
      else { changes.push({ sec: t, targetCp: target }); paused = false; }
    }
    const endSec = rnd() < 0.25 ? 60 + Math.floor(rnd() * Math.max(1, total - 60)) : null;
    const plan = NEW.buildPlan(c, changes);
    res.casos[model]++;
    const id = `${model}-${String(k).padStart(3, "0")}`;

    // REG-03: mismo resultado que la v1.3.0 con los modelos que ya existían
    if (model in OLD.PK_MODELS) {
      const vo = OLD.validateDraft(draft), co = OLD.draftToConfig(draft, vo);
      const po = OLD.buildPlan(co, changes);
      const same = JSON.stringify(c) === JSON.stringify(co) && strip(plan) === strip(po)
        && JSON.stringify(NEW.safetyReview(plan, c)) === JSON.stringify(OLD.safetyReview(po, co));
      res.reg.comparados++;
      if (!same && res.reg.distintos.length < 20) res.reg.distintos.push({ id, draft, changes });
    }

    // CSV para la reconstrucción independiente
    const until = endSec ?? plan.totalSec;
    writeFileSync(`${OUT}/csv/${id}.csv`, NEW.buildCaseCsv(c, plan, [], { endSec, untilSec: until, startMode: "" }));

  }
}

// TCI-C: precisión de la carga y del mantenimiento con el modelo «corregido» (programas sin cambios ni pausas, con carga)
for (let k = 0; k < 4 * N; k++) {
  const draft = {
    model: "corregido", weight: String(pick([3.5, 5, 8, 12.4, 15, 20, 25, 33, 40, 60])), targetCp: String(r1(0.2, 4)),
    duration: String(pick([30, 60, 90, 120, 180, 240])), stock: pick([100, 200, 500]), conc: "auto", concCustom: "",
    induction: "load", syringeMl: pick([20, 50]), pumpMin: String(pick([0.1, 0.5])), pumpMax: String(pick([100, 200, 999])), premed: "0",
  };
  const v = NEW.validateDraft(draft);
  if (!v.valid) { res.invalidos++; continue; }
  const c = NEW.draftToConfig(draft, v);
  const plan = NEW.buildPlan(c, []);
  const pumpTol = (0.05 * c.conc) / 60;                       // µg/min de error de redondeo de la bomba
  const load = plan.steps.find(s => s.kind === "load");
  if (!load || load.limited) continue;                        // carga limitada por la bomba: no alcanza el objetivo en el tiempo
  const endLoad = load.sec + load.loadSec, cp = plan.cp[endLoad];
  const tol = 0.01 + (pumpTol * (load.loadSec / 60)) / (plan.pk.V1 * c.targetCp);
  res.tci.cargas++;
  if (load.doseLimited) res.tci.cargasLimitadasPorDosis = (res.tci.cargasLimitadasPorDosis ?? 0) + 1;
  if (Math.abs(cp / c.targetCp - 1) > tol) res.tci.fallos.push({ id: `TCI-${k}`, tipo: "carga", cp, objetivo: c.targetCp, tol, draft });
  const maint = plan.steps.filter(s => s.kind !== "load" && s.sec >= endLoad);
  if (!maint.length || !maint.every(s => s.rateMlH >= c.pumpMinMlH && s.rateMlH < c.pumpMaxMlH)) continue;
  const tolM = 0.055 + pumpTol / (plan.pk.clAt(c.targetCp) * c.targetCp);
  let worst = 0;
  for (let s = endLoad; s <= plan.totalSec; s++) worst = Math.max(worst, Math.abs(plan.cp[s] / c.targetCp - 1));
  res.tci.mantenimiento++;
  res.tci.desviacionMaxMant = Math.max(res.tci.desviacionMaxMant ?? 0, worst);
  if (worst > tolM) res.tci.fallos.push({ id: `TCI-${k}`, tipo: "mantenimiento", desviacion: worst, tol: tolM, draft });
}
res.reg.pass = res.reg.distintos.length === 0 && res.reg.comparados > 0;
res.tci.pass = res.tci.fallos.length === 0 && res.tci.cargas > 0;
writeFileSync(`${OUT}/verificacion_v140.json`, JSON.stringify(res, null, 1));
console.log(`v${res.version} (por defecto «${res.modeloPorDefecto}») frente a v${res.anterior} · casos ${JSON.stringify(res.casos)} · inválidos ${res.invalidos}`);
console.log(`${res.reg.pass ? "✔" : "✘"} REG-03 modelos anteriores idénticos a la v${res.anterior}: ${res.reg.comparados - res.reg.distintos.length}/${res.reg.comparados}`);
console.log(`${res.tci.pass ? "✔" : "✘"} TCI-C modelo corregido: ${res.tci.cargas} cargas y ${res.tci.mantenimiento} mantenimientos dentro de tolerancia (${res.tci.fallos.length} fallos)`);
for (const f of res.tci.fallos.slice(0, 5)) console.log("   ", JSON.stringify(f));
console.log(`CSV escritos en ${OUT}/csv: reconstruir con python3 reconstruir_cp.py --verificar ${OUT}/csv`);
