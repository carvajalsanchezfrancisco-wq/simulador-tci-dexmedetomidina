import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

// ═══════════════════════════════════════════════════════════════════════════════
// Simulador TCI de dexmedetomidina en perros
// Autor: Francisco Carvajal Sánchez
// © 2026 Francisco Carvajal Sánchez. Todos los derechos reservados.
// ═══════════════════════════════════════════════════════════════════════════════
const AUTHOR = "Francisco Carvajal Sánchez";
const APP_VERSION = "1.2.1";   // mostrar en pantalla y en el CSV: identifica la versión evaluada
const COPYRIGHT_YEAR = 2026;

// ═══════════════════════════════════════════════════════════════════════════════
// MODELOS FARMACOCINÉTICOS
//
// Base: Levionnois et al. 2022, "Enantiospecific pharmacokinetics of intravenous
// dexmedetomidine in beagles", J Vet Pharmacol Ther. 2022;45:366-372. DOI: 10.1111/jvp.13063
// Modelo bicompartimental mamilar (popPK, NLME) — 8 Beagles adultos sanos,
// bolo IV único de 10 µg/kg, muestreo hasta 120 min.
//
// Estimaciones finales (Tabla 2, "final population compartmental analysis"):
//   V1  = 1.03 L/kg     Volumen compartimento central
//   V2  = 0.41 L/kg     Volumen compartimento periférico   (Vss = 1.45 L/kg)
//   Cl1 = 1.16 L/h/kg   Aclaramiento sistémico
//   Cl2 = 1.87 L/h/kg   Aclaramiento intercompartimental
//
// Comprobación: con estos valores se reproducen t½ = 0.91 h (publicado 0.92),
// AUC(10 µg/kg) = 8.62 h·ng/mL (8.65) y MRT = 1.24 h (1.25).
//
// Modelo «anestesiado» (por defecto desde la v1.2.0): misma estructura, V1, V2 y Cl2,
// con un aclaramiento que aumenta cuando la concentración es baja:
//   Cl(C) = Cl∞ + (Cl0 − Cl∞)·C50/(C50 + C),   Cl∞ = 1.16 L/h/kg (el publicado)
// Cl0 = 3.15 L/h/kg y C50 = 0.92 ng/mL, ajustados a las concentraciones medidas en
// perros anestesiados con isoflurano o propofol durante infusiones de 0,5–3 µg/kg/h
// (Pascoe 2006, Lin 2008), en los que el modelo publicado predecía el doble de lo
// medido. Calibración y validación: validacion_fase1/modelo_corregido.py (Fase 1).
// A concentraciones altas coincide con el publicado. Con las curvas completas de los
// dos estudios (Fase 1, v4) el reajuste da 3.21/0.95 (dosis +2 %): se mantienen 3.15/0.92.
// Limitación conocida: en anestesia la Cp medida sube durante 2–3 h pese a la carga, y
// este modelo no lo reproduce (posible volumen central mayor; pendiente de la Fase 3).
//
//   k10 = Cl/V1 · k12 = Cl2/V1 · k21 = Cl2/V2   [min⁻¹]
//
// Unidades: Cp en ng/mL ≡ µg/L · V en L · cantidades en µg · tiempo en min
// ═══════════════════════════════════════════════════════════════════════════════
const PK_MODELS = {
  anestesiado: {
    label: "Perro anestesiado (corregido)",
    short: "corregido para anestesia",
    reference: "Levionnois 2022 con aclaramiento corregido (Pascoe 2006, Lin 2008)",
    V1: 1.03, V2: 0.41, Cl2: 1.87, clInf: 1.16, cl0: 3.15, c50: 0.92,   // L/kg, L/h/kg, ng/mL
  },
  publicado: {
    label: "Publicado (Levionnois 2022)",
    short: "publicado",
    reference: "Levionnois et al. 2022",
    V1: 1.03, V2: 0.41, Cl2: 1.87, clInf: 1.16, cl0: 1.16, c50: null,   // aclaramiento constante
  },
};
const DEFAULT_MODEL = "anestesiado";

// ── Límites de seguridad (bomba inteligente) ─────────────────────────────────
// Blando: aviso que exige confirmación explícita. Duro: bloqueo.
// Anclados a la Cp de equilibrio del modelo publicado (Cp = dosis horaria / 1,16 L/h/kg),
// para que cuadren con las CRI publicadas en perros (0,5–3 µg/kg/h). Son los mismos con
// los dos modelos: limitan la dosis, no la Cp predicha. PROPUESTA
// para validar con el equipo clínico antes de uso en pacientes.
const SAFETY = {
  targetCp:    { soft: 2.5, hard: 4.0 },   // ng/mL (2,5 ≈ equilibrio de 3 µg/kg/h)
  loadUgKg:    { soft: 3 },                // µg/kg por carga
  rateUgKgH:   { soft: 20, hard: 30 },     // tasa instantánea; el duro limita la bomba (máx. 5 µg/kg en 10 min)
  hourUgKg:    { soft: 6, hard: 12 },      // dosis en cualquier ventana de 60 min
  targetStep:  { soft: 1.0 },              // ng/mL de subida por cambio de objetivo
  durationMin: { soft: 120 },              // más allá del muestreo del estudio (120 min)
  premedUgKg:  { soft: 5 },
};

// ── Límites de entrada ───────────────────────────────────────────────────────
const LIMITS = {
  weight:   { min: 2,   max: 80,  unit: "kg" },
  targetCp: { min: 0.1, max: SAFETY.targetCp.hard, unit: "ng/mL" },   // límite duro
  duration: { min: 15,  max: 240, unit: "min", integer: true },   // ≥ duración de la carga + mantenimiento
  pumpMin:  { min: 0.1, max: 5,    unit: "mL/h" },
  pumpMax:  { min: 1,   max: 1200, unit: "mL/h" },
  premed:   { min: 0,   max: 20,   unit: "µg/kg" },
};
const CUSTOM_CONC_MIN = 0.1;     // µg/mL; el máximo es la propia presentación comercial
const MIN_MEASURABLE_ML = 0.1;   // volumen mínimo de fármaco que se mide con precisión al preparar la jeringa

// ── Preparación y bomba ──────────────────────────────────────────────────────
const STOCK_OPTIONS    = [100, 200, 500];              // µg/mL
const DILUTION_OPTIONS = [0.5, 1, 2, 4, 5, 10, 20, 50]; // µg/mL
const SYRINGE_OPTIONS  = [10, 20, 50];                // mL
const PUMP_MIN_MLH     = 1.0;    // tasa mínima operable por defecto (modificable en el formulario)
const PUMP_MAX_MLH     = 100;    // tasa máxima por defecto (modificable), para carga y mantenimiento
const PUMP_STEP_MLH    = 0.1;    // resolución de programación de la bomba
const PREFERRED_END_MLH = 2.5;   // tasa final preferida al elegir concentración
const ADJUST_BAND      = 0.10;   // anchura total de la banda de ajuste (±5 % en torno a la tasa ideal)
const LOAD_SEC         = 600;    // la dosis de carga se infunde en 10 min (evita la respuesta
                                 // hipertensiva y la bradicardia refleja de la inyección rápida)

// ── Premedicación IM (solo en inicio sin carga) ──────────────────────────────
// SUPUESTOS, no proceden de Levionnois 2022 (estudio solo IV): absorción IM de
// primer orden con biodisponibilidad completa y t½ de absorción de 3 min, que con
// este modelo sitúa el pico plasmático a los ~10 min de la inyección. La bomba se
// inicia IM_PREMED.delayMin después de la inyección. Sustituir por datos caninos
// de dexmedetomidina IM cuando estén disponibles.
const IM_PREMED = { delayMin: 10, F: 1, absHalfMin: 3 };

// ── Simulación / interfaz ────────────────────────────────────────────────────
const CHART_SAMPLE_SEC = 30;
const SPEED_OPTIONS    = [1, 10, 60];
const TICK_MS          = 200;
const PREALERT_SEC     = 30;     // pre-aviso (tiempo simulado) antes de cada ajuste
const TARGET_TOLERANCE = 0.01;   // diferencia mínima con la Cp actual para cargar o detener
const MILESTONE_PRESETS = ["Inducción", "Intubación", "Incisión", "Fin de cirugía", "Extubación", "Recuperación"];

// ── Fin de la infusión ───────────────────────────────────────────────────────
const WASHOUT_MAX_MIN = 120;    // la Cp se sigue calculando hasta 120 min tras detener la infusión


// Validación externa (Fase 1) del modelo publicado: con objetivos bajos la Cp medida en otros estudios fue menor
// que la predicha, alrededor de un 20 % en perros despiertos (van Oostrom 2011: −37 % con 1 µg/kg/h, −18 % con
// 3 µg/kg/h) y un 50 % en perros anestesiados (Pascoe 2006, Lin 2008). Con el modelo publicado se avisa al usuario;
// el modelo «anestesiado» corrige ese sesgo.
const EXTERNAL_BIAS_NOTE_MAX_CP = 2;   // ng/mL: por debajo o igual, se muestra el aviso junto al objetivo

// Rango de peso habitual del Beagle adulto, población en la que se obtuvo el modelo.
// El texto del artículo no publica el rango exacto de pesos: confirmarlo con los autores.
const MODEL_WEIGHT_KG = { min: 8, max: 20 };

const STATUS_LABEL = {
  idle:     "EN ESPERA",
  running:  "INFUNDIENDO",
  paused:   "EN PAUSA",
  washout:  "POST-INFUSIÓN",   // bomba detenida; la Cp se sigue calculando
  finished: "FINALIZADO",
};

const INDUCTION_LABEL = {
  load: `Carga en ${LOAD_SEC / 60} min (TCI)`,
  none: "Sin carga · infusión continua",
};

const DEFAULT_DRAFT = {
  model: DEFAULT_MODEL,
  weight: "25", targetCp: "2.0", duration: "60", stock: 500, conc: "auto", concCustom: "",
  induction: "load", syringeMl: 50, pumpMin: String(PUMP_MIN_MLH), pumpMax: String(PUMP_MAX_MLH), premed: "0",
};

// ═══════════════════════════════════════════════════════════════════════════════
// MOTOR TCI
//
// Algoritmo de Shafer & Gregg (1992) para Cp-TCI, ajustado a una bomba de
// jeringa convencional con tasa fija por tramos. El objetivo puede cambiarse en
// cualquier momento de la infusión, como en las bombas TCI de uso humano:
//
//   · Objetivo mayor que la Cp actual → carga a tasa constante durante LOAD_SEC
//     (10 min), calculada para que la Cp llegue exactamente al objetivo al final:
//       A1(T) = A1ss(R) + [descenso libre de (A1₀ − A1ss, A2₀ − A2ss)](T),
//       A1ss = R/k10, A2ss = k12·A1ss/k21  → lineal en R, se despeja R
//   · Objetivo menor que la Cp actual → bomba detenida (0 mL/h) hasta que la Cp,
//     en descenso libre, alcanza el nuevo objetivo
//   · Mantenimiento con A1 = Cp_obj·V1 constante:
//       R(τ)  = A1·(k10+k12) − k21·A2(τ)                    [µg/min]
//       A2(τ) = A2ss + (A2₀ − A2ss)·e^(−k21·τ),  A2ss = k12·A1/k21
//
// La bomba no sigue R(τ) de forma continua: cada tasa programada se centra en
// una banda ±ADJUST_BAND/2 alrededor de la tasa ideal y se reprograma cuando la
// ideal sale de la banda, de modo que el error se reparte a ambos lados del
// objetivo. La Cp resultante del esquema escalonado se simula con Euler (dt = 1 s).
//
// Con el modelo «anestesiado» (aclaramiento dependiente de la Cp) el sistema no es
// lineal: el descenso libre, la respuesta a una tasa constante y la tasa de carga se
// calculan por integración numérica (Runge-Kutta 4, paso de 1 s) y la carga se
// resuelve por el método de la secante. El mantenimiento sigue siendo exacto, porque
// con la Cp fija en el objetivo el aclaramiento es constante (k10 = Cl(objetivo)/V1).
//
// Descenso libre (sin infusión), solución analítica bicompartimental:
//   A1(t) = cα·e^(−αt) + cβ·e^(−βt)
//   cα = (A1₀·(k21−α) + k21·A2₀)/(β−α),  cβ = (A1₀·(k21−β) + k21·A2₀)/(α−β)
//   A2(t) = (A1′(t) + (k10+k12)·A1(t)) / k21
// ═══════════════════════════════════════════════════════════════════════════════
/** Aclaramiento (L/h/kg) del modelo con la Cp `c` (ng/mL). */
function clearanceKgH(modelId, c) {
  const m = PK_MODELS[modelId];
  return m.cl0 === m.clInf ? m.clInf : m.clInf + ((m.cl0 - m.clInf) * m.c50) / (m.c50 + Math.max(0, c));
}

function buildPK(weightKg, modelId = DEFAULT_MODEL) {
  const m   = PK_MODELS[modelId];
  const V1  = m.V1  * weightKg;
  const V2  = m.V2  * weightKg;
  const Cl1 = (m.clInf / 60) * weightKg;     // aclaramiento a concentración alta (el publicado)
  const Cl2 = (m.Cl2 / 60) * weightKg;
  const k10 = Cl1 / V1, k12 = Cl2 / V1, k21 = Cl2 / V2;
  const sum = k10 + k12 + k21;
  const root = Math.sqrt(sum * sum - 4 * k10 * k21);
  const linear = m.cl0 === m.clInf;
  /** Aclaramiento (L/min) con la Cp `c` (ng/mL); en el modelo lineal, siempre Cl1. */
  const clAt  = linear ? () => Cl1 : c => (clearanceKgH(modelId, c) / 60) * weightKg;
  /** Constante de eliminación (min⁻¹) con la Cp `c`; en el modelo lineal, siempre k10. */
  const k10At = linear ? () => k10 : c => clAt(c) / V1;
  /**
   * Sensibilidad de la Cp de equilibrio a la tasa, d ln(Cp·Cl) / d ln Cp: un error del x % en la tasa da
   * un error del x/e % en la Cp. Es 1 en el modelo lineal y < 1 en el corregido (el aclaramiento baja al subir la Cp).
   */
  const elasticity = linear ? () => 1 : c => 1 - ((m.cl0 - m.clInf) * m.c50 * c) / ((m.c50 + c) ** 2 * clearanceKgH(modelId, c));
  return {
    model: modelId, linear, V1, V2, Cl1, Cl2, k10, k12, k21, clAt, k10At, elasticity,
    alpha: (sum + root) / 2, beta: (sum - root) / 2, ka: Math.LN2 / IM_PREMED.absHalfMin,
  };
}

const ugMinToMlH  = (ugMin, conc) => (ugMin * 60) / conc;
const roundToPump = mlh => Number((Math.round(mlh / PUMP_STEP_MLH) * PUMP_STEP_MLH).toFixed(2));
/** Mayor tasa programable que no supera el máximo de la bomba. */
const pumpCeiling = pump => Number((Math.floor(pump.max / PUMP_STEP_MLH + 1e-9) * PUMP_STEP_MLH).toFixed(2));
const HALF_BAND   = ADJUST_BAND / 2;

/**
 * Modelo no lineal: cantidades (µg) tras tMin minutos de infusión constante rUgMin
 * (µg/min), por Runge-Kutta 4 con pasos de 1 s como máximo.
 */
function integrate(pk, a1, a2, rUgMin, tMin) {
  const n = Math.max(1, Math.ceil(tMin * 60 - 1e-9));
  const h = tMin / n;
  const d1 = (x1, x2) => rUgMin - (pk.k10At(x1 / pk.V1) + pk.k12) * x1 + pk.k21 * x2;
  const d2 = (x1, x2) => pk.k12 * x1 - pk.k21 * x2;
  for (let i = 0; i < n; i++) {
    const p1 = d1(a1, a2), q1 = d2(a1, a2);
    const p2 = d1(a1 + (h / 2) * p1, a2 + (h / 2) * q1), q2 = d2(a1 + (h / 2) * p1, a2 + (h / 2) * q1);
    const p3 = d1(a1 + (h / 2) * p2, a2 + (h / 2) * q2), q3 = d2(a1 + (h / 2) * p2, a2 + (h / 2) * q2);
    const p4 = d1(a1 + h * p3, a2 + h * q3), q4 = d2(a1 + h * p3, a2 + h * q3);
    a1 += (h / 6) * (p1 + 2 * p2 + 2 * p3 + p4);
    a2 += (h / 6) * (q1 + 2 * q2 + 2 * q3 + q4);
  }
  return { a1: Math.max(0, a1), a2: Math.max(0, a2) };
}

/** Cantidades (µg) en cada compartimento tras tMin minutos sin infusión. */
function freeDecay(pk, a1, a2, tMin) {
  if (!pk.linear) return integrate(pk, a1, a2, 0, tMin);
  const { alpha, beta, k10, k12, k21 } = pk;
  const cA = (a1 * (k21 - alpha) + k21 * a2) / (beta - alpha);
  const cB = (a1 * (k21 - beta) + k21 * a2) / (alpha - beta);
  const eA = cA * Math.exp(-alpha * tMin);
  const eB = cB * Math.exp(-beta * tMin);
  const A1 = eA + eB;
  const dA1 = -alpha * eA - beta * eB;
  return { a1: A1, a2: (dA1 + (k10 + k12) * A1) / k21 };
}

/**
 * Tiempo (s) hasta que la Cp cae a `fraction` de su valor actual si se detiene la
 * infusión ahora (p. ej. 0.5 → tiempo de decremento del 50 %). null si > 24 h.
 */
function decrementTimeSec(pk, a1, a2, fraction) {
  const limit = a1 * fraction;
  if (!pk.linear) {
    let state = { a1, a2 };
    for (let s = 10; s <= 24 * 3600; s += 10) {
      state = integrate(pk, state.a1, state.a2, 0, 10 / 60);
      if (state.a1 <= limit) return s;
    }
    return null;
  }
  for (let s = 10; s <= 24 * 3600; s += 10) {
    if (freeDecay(pk, a1, a2, s / 60).a1 <= limit) return s;
  }
  return null;
}

/** Cantidades (µg) tras tMin minutos de infusión constante rUgMin (µg/min) al compartimento central. */
function forcedResponse(pk, a1, a2, rUgMin, tMin) {
  if (!pk.linear) return integrate(pk, a1, a2, rUgMin, tMin);
  const a1ss = rUgMin / pk.k10;
  const a2ss = (pk.k12 * a1ss) / pk.k21;
  const free = freeDecay(pk, a1 - a1ss, a2 - a2ss, tMin);
  return { a1: a1ss + free.a1, a2: a2ss + free.a2 };
}

/** Tasa constante (µg/min) que lleva A1 desde el estado actual hasta A1t en tMin minutos. */
function loadingRateUgMin(pk, a1, a2, A1t, tMin) {
  const base = forcedResponse(pk, a1, a2, 0, tMin).a1;
  const slope = forcedResponse(pk, a1, a2, 1, tMin).a1 - base;
  if (pk.linear) return (A1t - base) / slope;
  // No lineal: método de la secante desde la estimación lineal
  let r0 = (A1t - base) / slope, f0 = forcedResponse(pk, a1, a2, r0, tMin).a1 - A1t;
  let r1 = r0 * 1.05 + 1e-6, f1 = forcedResponse(pk, a1, a2, r1, tMin).a1 - A1t;
  for (let i = 0; i < 60 && Math.abs(f1) > A1t * 1e-10 && f1 !== f0; i++) {
    const r2 = r1 - (f1 * (r1 - r0)) / (f1 - f0);
    r0 = r1; f0 = f1;
    r1 = r2; f1 = forcedResponse(pk, a1, a2, r1, tMin).a1 - A1t;
  }
  return r1;
}

/**
 * Plan de un tramo con objetivo constante, desde el estado (a1, a2) en `fromSec`
 * hasta `toSec`. Devuelve los pasos de bomba del tramo.
 * isStart: primer tramo de la infusión (el resto son cambios de objetivo).
 * induction: "load" (TCI con carga en LOAD_SEC) o "none" (sin carga: infusión
 * continua a la tasa de equilibrio Cp·Cl1; la Cp se acerca al objetivo sin
 * superarlo, pero tarda horas por la eliminación lenta).
 * pump: { min, max } en mL/h. Como una bomba TCI, ninguna tasa supera pump.max:
 * si la carga lo necesitaría, se limita y se alarga hasta alcanzar el objetivo
 * (step.limited = true; step.unreached = true si no se alcanza en el tramo).
 * ad: µg de la premedicación IM aún sin absorber en `fromSec` (solo "none").
 */
function planSegment(pk, conc, targetCp, a1, a2, fromSec, toSec, isStart, induction, pump, ad = 0) {
  const ceiling = pumpCeiling(pump);
  const doseCeiling = pump.doseMaxMlH ?? Infinity;              // límite duro de dosis (µg/kg/h → mL/h)
  // requestedMlH: la tasa que haría falta; rateMlH: la que la bomba puede dar.
  // limited: por el máximo de la bomba; doseLimited: por el límite duro de dosis
  const cap = requestedMlH => ({
    rateMlH: Math.min(requestedMlH, ceiling, doseCeiling), requestedMlH,
    limited: requestedMlH > ceiling, doseLimited: requestedMlH > doseCeiling && requestedMlH <= ceiling,
  });

  if (induction === "none") {
    const kind = isStart ? "cri" : "target";
    const finalMlH = roundToPump(ugMinToMlH(targetCp * pk.clAt(targetCp), conc));
    if (ad <= 0) return [{ sec: fromSec, ...cap(finalMlH), kind, targetCp }];
    return planPremedSegment(pk, conc, targetCp, a1, a2, ad, fromSec, toSec, kind, pump, cap);
  }

  const steps = [];
  const A1t = targetCp * pk.V1;
  const cpNow = a1 / pk.V1;
  let t0 = fromSec;
  let firstKind = isStart ? "maintain" : "target";

  if (targetCp > cpNow * (1 + TARGET_TOLERANCE)) {
    // subir: carga en LOAD_SEC hasta el nuevo objetivo, o más larga si la bomba no da la tasa
    const { rateMlH, requestedMlH, limited, doseLimited } = cap(roundToPump(ugMinToMlH(loadingRateUgMin(pk, a1, a2, A1t, LOAD_SEC / 60), conc)));
    const rUgMin = (rateMlH * conc) / 60;
    let loadSec = Math.min(LOAD_SEC, toSec - fromSec);
    if ((limited || doseLimited) && pk.linear) {
      while (fromSec + loadSec < toSec && forcedResponse(pk, a1, a2, rUgMin, loadSec / 60).a1 < A1t) loadSec++;
    } else if (limited || doseLimited) {
      let state = forcedResponse(pk, a1, a2, rUgMin, loadSec / 60);
      while (fromSec + loadSec < toSec && state.a1 < A1t) {
        state = integrate(pk, state.a1, state.a2, rUgMin, 1 / 60);
        loadSec++;
      }
    }
    const unreached = (limited || doseLimited) && forcedResponse(pk, a1, a2, rUgMin, loadSec / 60).a1 < A1t;
    steps.push({ sec: fromSec, rateMlH, requestedMlH, loadSec, loadMl: (rateMlH * loadSec) / 3600, kind: "load", targetCp, limited, doseLimited, unreached });
    if (fromSec + loadSec >= toSec) return steps;
    t0 = fromSec + loadSec;
    a2 = forcedResponse(pk, a1, a2, rUgMin, loadSec / 60).a2;
    firstKind = "maintain";
  } else if (targetCp < cpNow * (1 - TARGET_TOLERANCE)) {
    // bajar: bomba detenida hasta que el descenso libre alcanza el objetivo
    steps.push({ sec: fromSec, rateMlH: 0, requestedMlH: 0, kind: "stop", targetCp, limited: false });
    let state = { a1, a2 };
    let s = fromSec;
    while (s < toSec && state.a1 > A1t) {
      s++;
      state = pk.linear ? freeDecay(pk, a1, a2, (s - fromSec) / 60) : integrate(pk, state.a1, state.a2, 0, 1 / 60);
    }
    if (s >= toSec) return steps;
    t0 = s;
    a2 = state.a2;
    firstKind = "resume";
  }

  // Mantenimiento con A1 = A1t constante desde t0 (aclaramiento constante: el del objetivo)
  const k10t = pk.k10At(targetCp);
  const a2ss = (pk.k12 * A1t) / pk.k21;
  const idealMlH = s => ugMinToMlH(
    Math.max(0, A1t * (k10t + pk.k12) - pk.k21 * (a2ss + (a2 - a2ss) * Math.exp((-pk.k21 * (s - t0)) / 60))),
    conc,
  );
  // A2 creciente → tasa ideal decreciente: la tasa se programa por debajo, y viceversa.
  // Modelo corregido: banda más estrecha, para que el error de la Cp siga dentro de ±HALF_BAND, y la
  // tasa nunca se programa al otro lado de la tasa de equilibrio final (la ideal no llegaría a ella)
  const half = pk.linear ? HALF_BAND : HALF_BAND * pk.elasticity(targetCp);
  const trend = Math.sign(a2ss - a2);
  const finalUgMin = A1t * k10t;
  const centered = ideal => {
    let rate = trend > 0 ? ideal / (1 + half) : trend < 0 ? ideal / (1 - half) : ideal;
    if (!pk.linear) {
      const finalMlH = ugMinToMlH(finalUgMin, conc);
      rate = trend > 0 ? Math.max(rate, finalMlH) : trend < 0 ? Math.min(rate, finalMlH) : rate;
    }
    return cap(roundToPump(rate));
  };

  steps.push({ sec: t0, ...centered(idealMlH(t0)), kind: firstKind, targetCp });
  for (let s = t0 + 1; s < toSec; s++) {
    const current = steps[steps.length - 1].rateMlH;
    const ideal = idealMlH(s);
    const inBand = current > 0
      ? ideal >= current * (1 - half) && ideal <= current * (1 + half)
      : ideal < PUMP_STEP_MLH / 2;
    if (inBand) continue;
    const next = centered(ideal);
    if (next.rateMlH !== current) steps.push({ sec: s, ...next, kind: "adjust", targetCp });
  }
  return steps;
}

const PREMED_ADJUST_SEC = 120;   // intervalo mínimo entre ajustes mientras se absorbe la dosis IM

/**
 * Tramo sin carga con premedicación IM en absorción (ad µg sin absorber en fromSec).
 * Si la Cp supera el objetivo, la bomba espera detenida a que baje; después la
 * mantiene en el objetivo descontando lo que aporta la absorción IM (Shafer-Gregg
 * con un aporte extra ka·Ad). Si la Cp está por debajo, sin carga, la bomba solo
 * complementa la absorción hasta la tasa de equilibrio Cp·Cl1.
 */
function planPremedSegment(pk, conc, targetCp, a1, a2, ad, fromSec, toSec, kind, pump, cap) {
  const A1t = targetCp * pk.V1;
  const steps = [];
  let t0 = fromSec;
  if (a1 > A1t * (1 + TARGET_TOLERANCE)) {
    steps.push({ sec: fromSec, ...cap(0), kind, targetCp });
    const dt = 1 / 60;
    while (t0 < toSec && a1 > A1t) {                  // misma integración que buildPlan
      const absorbed = pk.ka * ad;
      const dA1 = (absorbed - (pk.k10At(a1 / pk.V1) + pk.k12) * a1 + pk.k21 * a2) * dt;
      a2 += (pk.k12 * a1 - pk.k21 * a2) * dt;
      a1 += dA1;
      ad -= absorbed * dt;
      t0++;
    }
    if (t0 >= toSec) return steps;
  }

  const holding = a1 >= A1t * (1 - TARGET_TOLERANCE);   // Cp en el objetivo: mantenerla
  const half = pk.linear ? HALF_BAND : HALF_BAND * pk.elasticity(targetCp);
  const k10t = pk.k10At(targetCp);
  const clT = pk.clAt(targetCp);
  const a2ss = (pk.k12 * A1t) / pk.k21;
  const idealMlH = sec => {
    const tau = (Math.min(sec, toSec) - t0) / 60;
    const absorbed = pk.ka * ad * Math.exp(-pk.ka * tau);
    const need = holding
      ? A1t * (k10t + pk.k12) - pk.k21 * (a2ss + (a2 - a2ss) * Math.exp(-pk.k21 * tau))
      : targetCp * clT;
    return ugMinToMlH(Math.max(0, need - absorbed), conc);
  };
  const finalMlH = holding ? Infinity : roundToPump(ugMinToMlH(targetCp * clT, conc));
  // cada ajuste programa la tasa ideal a mitad del intervalo; bajo el mínimo de la bomba, detenida
  const program = sec => {
    const rate = Math.min(finalMlH, roundToPump(idealMlH(sec + PREMED_ADJUST_SEC / 2)));
    return cap(rate < pump.min ? 0 : rate);
  };

  const first = program(t0);
  if (!steps.length || first.rateMlH > 0) steps.push({ sec: t0, ...first, kind: steps.length ? "resume" : kind, targetCp });
  let last = steps[steps.length - 1];
  for (let sec = Math.max(t0, last.sec) + PREMED_ADJUST_SEC; sec < toSec; sec++) {
    if (sec - last.sec < PREMED_ADJUST_SEC) continue;
    const ideal = idealMlH(sec);
    const inBand = last.rateMlH > 0
      ? Math.abs(ideal - last.rateMlH) <= last.rateMlH * half
      : ideal < pump.min;
    if (inBand) continue;
    const next = program(sec);
    if (next.rateMlH === last.rateMlH) continue;
    last = { sec, ...next, kind: last.rateMlH > 0 ? "adjust" : "resume", targetCp };
    steps.push(last);
  }
  return steps;
}

/** Tasa distinta de 0 por debajo del mínimo programable de la bomba (el máximo nunca se supera). */
const isBelowPumpMin = (rateMlH, pump) => rateMlH > 0 && rateMlH < pump.min;

/**
 * Evalúa si una dilución es administrable con el objetivo inicial: la carga (si
 * la hay) cabe en LOAD_SEC sin superar el máximo de la bomba y el mantenimiento
 * queda dentro del rango de la bomba.
 */
function evaluateDilution(pk, targetCp, durationMin, conc, induction, pump) {
  const steps = planSegment(pk, conc, targetCp, 0, 0, 0, durationMin * 60, true, induction, pump);
  if (induction === "none") {
    const { requestedMlH, limited } = steps[0];
    const pumpOk = !limited && requestedMlH >= pump.min;
    return { conc, steps, loadMlH: NaN, loadMl: 0, startMlH: requestedMlH, endMlH: requestedMlH, pumpOk, loadOk: true, ok: pumpOk };
  }
  const [load, ...maintenance] = steps;
  const startMlH = maintenance.length ? maintenance[0].requestedMlH : NaN;
  const endMlH = maintenance.length ? maintenance[maintenance.length - 1].requestedMlH : NaN;
  const pumpOk = maintenance.length > 0 && !maintenance.some(st => st.limited) && endMlH >= pump.min;
  const loadOk = !load.limited && load.rateMlH >= pump.min;
  return {
    conc, steps, loadMlH: load.requestedMlH, loadMl: load.loadMl, startMlH, endMlH,
    pumpOk, loadOk, ok: pumpOk && loadOk,
  };
}

/** Diluciones disponibles (≤ presentación) que cumplen el rango de bomba en carga y mantenimiento. */
function validDilutions(weightKg, targetCp, durationMin, stock, induction, pump, model) {
  const pk = buildPK(weightKg, model);
  return DILUTION_OPTIONS
    .filter(conc => conc <= stock)
    .map(conc => evaluateDilution(pk, targetCp, durationMin, conc, induction, pump))
    .filter(option => option.ok);
}

/** Entre las diluciones válidas, la de tasa final más cercana a PREFERRED_END_MLH. */
function recommendConcentration(options) {
  let best = null;
  for (const option of options) {
    const distance = Math.abs(option.endMlH - PREFERRED_END_MLH);
    if (!best || distance < best.distance) best = { conc: option.conc, distance };
  }
  return best ? best.conc : null;
}

/** Índice del último paso del programa cuyo inicio es ≤ sec. */
function stepIndexAt(steps, sec) {
  let idx = 0;
  while (idx + 1 < steps.length && steps[idx + 1].sec <= sec) idx++;
  return idx;
}

/**
 * Plan completo de la infusión. `targetChanges` = [{ sec, targetCp, pause? }] ordenados,
 * con sec ≥ 1: cambios de objetivo hechos durante la infusión. Una entrada con
 * pause: true detiene la bomba (la Cp desciende libremente) hasta la entrada
 * siguiente, que replanifica el TCI desde el estado alcanzado.
 *
 * `timing` (modo manual) hace que la simulación siga a la bomba real y no al
 * programa ideal: { appliedAt: { [índice de paso]: segundo en que se confirmó },
 * ackIdx: último paso confirmado, nowSec: instante actual }. Un paso vencido y
 * sin confirmar no se aplica hasta nowSec + 1. Sin `timing`, todos los pasos se
 * aplican en su momento (bomba automática).
 */
function buildPlan({ model = DEFAULT_MODEL, weight, targetCp, durationMin, conc, induction, pumpMinMlH, pumpMaxMlH, syringeMl, premedUgKg = 0 }, targetChanges = [], timing = null) {
  const pump = { min: pumpMinMlH, max: pumpMaxMlH, doseMaxMlH: Math.floor(((SAFETY.rateUgKgH.hard * weight) / conc) / PUMP_STEP_MLH + 1e-9) * PUMP_STEP_MLH };
  const pk = buildPK(weight, model);
  const totalSec = durationMin * 60;
  const segments = [{ sec: 0, targetCp }, ...targetChanges.filter(c => c.sec > 0 && c.sec < totalSec)];
  const initial = evaluateDilution(pk, targetCp, durationMin, conc, induction, pump);

  // Simulación segundo a segundo; cada tramo se planifica desde el estado simulado
  const dt = 1 / 60;
  const cp          = new Float64Array(totalSec + 1);
  const c2          = new Float64Array(totalSec + 1);
  const target      = new Float64Array(totalSec + 1);
  const deliveredMl = new Float64Array(totalSec + 1);         // carga + mantenimiento
  const rateAt      = new Float64Array(totalSec + 1);         // tasa que infunde realmente la bomba
  const depot       = new Float64Array(totalSec + 1);         // µg aún en el depósito IM (para el descenso tras la infusión)
  const steps = [];
  let a1 = 0, a2 = 0, volume = 0, stepIdx = -1, segIdx = -1, maxDeviation = 0;
  let ad = induction === "none" ? premedUgKg * weight * IM_PREMED.F : 0;   // depósito IM (µg)

  const advance = inputUgMin => {
    const absorbed = pk.ka * ad;
    const dA1 = (inputUgMin + absorbed - (pk.k10At(a1 / pk.V1) + pk.k12) * a1 + pk.k21 * a2) * dt;
    const dA2 = (pk.k12 * a1 - pk.k21 * a2) * dt;
    ad = Math.max(0, ad - absorbed * dt);
    a1 = Math.max(0, a1 + dA1);
    a2 = Math.max(0, a2 + dA2);
  };
  // La premedicación IM se inyectó IM_PREMED.delayMin antes de iniciar la bomba
  if (ad > 0) for (let s = 0; s < IM_PREMED.delayMin * 60; s++) advance(0);

  // Segundo en que cada paso empieza a infundir de verdad
  const effectiveSec = i => {
    if (!timing || steps[i].kind === "pause") return steps[i].sec;   // la pausa la hace el usuario en la bomba
    if (timing.appliedAt[i] !== undefined) return Math.max(steps[i].sec, timing.appliedAt[i]);
    if (i > timing.ackIdx && timing.nowSec !== null && steps[i].sec <= timing.nowSec) return timing.nowSec + 1;
    return steps[i].sec;
  };

  for (let s = 0; s <= totalSec; s++) {
    if (segIdx + 1 < segments.length && segments[segIdx + 1].sec === s) {
      segIdx++;
      const end = segIdx + 1 < segments.length ? segments[segIdx + 1].sec : totalSec;
      const seg = segments[segIdx];
      if (seg.pause) steps.push({ sec: s, rateMlH: 0, requestedMlH: 0, kind: "pause", targetCp: seg.targetCp, limited: false });
      else steps.push(...planSegment(pk, conc, seg.targetCp, a1, a2, s, end, segIdx === 0, induction, pump, ad));
    }
    while (stepIdx + 1 < steps.length && effectiveSec(stepIdx + 1) <= s) stepIdx++;

    const tgt = segments[segIdx].targetCp;
    const rateMlH = steps[stepIdx].rateMlH;
    cp[s] = a1 / pk.V1;
    c2[s] = a2 / pk.V2;
    target[s] = tgt;
    deliveredMl[s] = volume;
    rateAt[s] = rateMlH;
    depot[s] = ad;
    if (!["stop", "load", "pause"].includes(steps[stepIdx].kind)) {   // subida y bajada no son error de dosificación
      maxDeviation = Math.max(maxDeviation, Math.abs(cp[s] - tgt) / tgt);
    }

    advance((rateMlH * conc) / 60);
    volume += rateMlH * (dt / 60);                           // mL/h × h
  }

  for (const step of steps) step.outOfRange = isBelowPumpMin(step.rateMlH, pump);

  // Muestras para gráficas: rejilla regular + instante exacto de cada paso
  const sampleAt = s => ({ t: s / 60, cp: cp[s], c2: c2[s], target: target[s], rate: rateAt[s] });
  const chart = [];
  for (let s = 0; s <= totalSec; s += CHART_SAMPLE_SEC) chart.push(sampleAt(s));
  for (const step of steps) if (step.sec % CHART_SAMPLE_SEC !== 0) chart.push(sampleAt(step.sec));
  chart.sort((a, b) => a.t - b.t);

  // Sin carga la Cp sube lentamente hacia el objetivo: se informa el tiempo en
  // alcanzar el 90 % en lugar de la desviación (que no es error de dosificación)
  let time90Sec = null;
  const firstEnd = segments.length > 1 ? segments[1].sec : totalSec;
  for (let s = 0; s <= firstEnd; s++) {
    if (cp[s] >= 0.9 * targetCp) { time90Sec = s; break; }
  }
  if (induction === "none") maxDeviation = NaN;

  // Resumen y advertencias
  const { loadMlH, loadMl, startMlH, endMlH, pumpOk, loadOk } = initial;
  const totalMl = deliveredMl[totalSec];
  const warnings = [];
  if (startMlH === 0) {
    warnings.push(`La tasa de infusión redondeada a la resolución de la bomba (${PUMP_STEP_MLH} mL/h) es 0 mL/h. Seleccione una concentración menor.`);
  }
  if (induction === "none" && time90Sec === null) {
    const when = segments.length > 1 ? "antes del primer cambio de objetivo" : "en la duración programada";
    warnings.push(`Sin carga, la Cp no alcanza el 90 % del objetivo ${when} (Cp ${cp[firstEnd].toFixed(2)} ng/mL).`);
  }
  if (!loadOk) {
    warnings.push(`La carga necesitaría ${loadMlH.toFixed(1)} mL/h o no cabe en ${LOAD_SEC / 60} min con el rango de la bomba (${pump.min}–${pump.max} mL/h).`);
  }
  if (premedUgKg > 0 && cp[0] > targetCp * (1 + TARGET_TOLERANCE)) {
    warnings.push(`La premedicación IM ya supera el objetivo al iniciar (Cp estimada ${cp[0].toFixed(2)} ng/mL): la bomba espera a que la absorción baje.`);
  }
  if (weight < MODEL_WEIGHT_KG.min || weight > MODEL_WEIGHT_KG.max) {
    warnings.push(`Peso fuera del rango habitual de la población del estudio (Beagles adultos, ~${MODEL_WEIGHT_KG.min}–${MODEL_WEIGHT_KG.max} kg): la predicción es una extrapolación.`);
  }
  if (endMlH < pump.min) {
    warnings.push(`La tasa final (${endMlH.toFixed(1)} mL/h) es inferior al mínimo operable de ${pump.min} mL/h. Seleccione una concentración menor.`);
  }
  const firstChangeSec = segments.length > 1 ? segments[1].sec : Infinity;
  const titration = steps.filter(st => st.sec >= firstChangeSec);
  const belowMin = titration.filter(st => st.outOfRange).length;
  if (belowMin > 0) {
    warnings.push(`${belowMin} paso(s) tras cambiar el objetivo quedan por debajo de la tasa mínima de la bomba (${pump.min} mL/h).`);
  }
  const limitedSteps = titration.filter(st => st.limited);
  if (limitedSteps.length > 0) {
    const unreached = limitedSteps.some(st => st.unreached);
    warnings.push(`${limitedSteps.length} paso(s) tras cambiar el objetivo se limitan al máximo de la bomba (${pump.max} mL/h): `
      + (unreached ? "el objetivo no se alcanza en el tiempo disponible." : "la carga se alarga más de 10 min."));
  }
  if (totalMl > syringeMl) {
    warnings.push(`El volumen total estimado (${totalMl.toFixed(1)} mL) excede una jeringa de ${syringeMl} mL. Prevea el recambio.`);
  }

  return {
    pk, totalSec, loadMlH, loadMl, loadUg: loadMl * conc, steps, cp, c2, target, deliveredMl, rateAt, depot, chart,
    totalMl, startMlH, endMlH, maxDeviation, warnings, pumpOk, loadOk, time90Sec, induction, pump, premedUgKg,
    initialSteps: initial.steps.length,
  };
}

/**
 * Descenso de la Cp tras detener la infusión en `endSec` (s): mismo paso de Euler de 1 s
 * que buildPlan, sin infusión y con la absorción IM que quede en el depósito.
 * Devuelve { endSec, cp, c2 } con un valor por segundo desde endSec.
 */
function simulateWashout(plan, endSec, seconds = WASHOUT_MAX_MIN * 60) {
  const { pk } = plan;
  const dt = 1 / 60;
  let a1 = plan.cp[endSec] * pk.V1, a2 = plan.c2[endSec] * pk.V2, ad = plan.depot[endSec];
  const cp = new Float64Array(seconds + 1);
  const c2 = new Float64Array(seconds + 1);
  for (let s = 0; s <= seconds; s++) {
    cp[s] = a1 / pk.V1;
    c2[s] = a2 / pk.V2;
    const absorbed = pk.ka * ad;
    const dA1 = (absorbed - (pk.k10At(a1 / pk.V1) + pk.k12) * a1 + pk.k21 * a2) * dt;
    const dA2 = (pk.k12 * a1 - pk.k21 * a2) * dt;
    ad = Math.max(0, ad - absorbed * dt);
    a1 = Math.max(0, a1 + dA1);
    a2 = Math.max(0, a2 + dA2);
  }
  return { endSec, cp, c2 };
}

/**
 * Tasas que infundió la bomba: [{ sec, rateMlH }] con cada cambio hasta `untilSec`
 * (incluido) y, si la infusión terminó, 0 mL/h en `endSec`. Con este registro, el peso
 * y la concentración se puede recalcular la Cp de cualquier muestra.
 */
function rateHistory(plan, endSec, untilSec) {
  const last = endSec !== null ? endSec - 1 : untilSec;
  const out = [];
  for (let s = 0; s <= Math.min(last, plan.totalSec); s++) {
    if (s === 0 || plan.rateAt[s] !== plan.rateAt[s - 1]) out.push({ sec: s, rateMlH: plan.rateAt[s] });
  }
  if (endSec !== null) out.push({ sec: endSec, rateMlH: 0, end: true });
  return out;
}

/**
 * Revisión de límites de seguridad de un plan: { hard: [...], soft: [...] }.
 * hard bloquea la programación; soft exige confirmación explícita.
 */
function safetyReview(plan, config) {
  const { weight, conc } = config;
  const hard = [], soft = [];
  const ugKg = ml => (ml * conc) / weight;
  const maxTarget = Math.max(...plan.target);
  if (maxTarget > SAFETY.targetCp.soft) {
    soft.push(`Cp objetivo ${fmt(maxTarget, 2)} ng/mL > ${SAFETY.targetCp.soft} ng/mL (equilibrio ≈ ${fmt(maxTarget * clearanceKgH(plan.pk.model, maxTarget), 1)} µg/kg/h, por encima de las CRI habituales).`);
  }
  for (const st of plan.steps.filter(x => x.kind === "load")) {
    if (ugKg(st.loadMl) > SAFETY.loadUgKg.soft) {
      soft.push(`Carga de ${fmt(ugKg(st.loadMl), 2)} µg/kg a las ${fmtClock(st.sec)} > ${SAFETY.loadUgKg.soft} µg/kg.`);
    }
  }
  const maxRate = Math.max(...plan.steps.map(x => (x.rateMlH * conc) / weight));
  if (maxRate > SAFETY.rateUgKgH.soft) {
    soft.push(`Tasa máxima ${fmt(maxRate, 1)} µg/kg/h > ${SAFETY.rateUgKgH.soft} µg/kg/h.`);
  }
  if (plan.steps.some(x => x.doseLimited)) {
    soft.push(`La carga se limita a ${SAFETY.rateUgKgH.hard} µg/kg/h (límite duro) y se alarga más de ${LOAD_SEC / 60} min.`);
  }
  let hourMl = 0;
  const win = Math.min(3600, plan.totalSec);
  for (let s = win; s <= plan.totalSec; s++) hourMl = Math.max(hourMl, plan.deliveredMl[s] - plan.deliveredMl[s - win]);
  const hourUg = ugKg(hourMl);
  if (hourUg > SAFETY.hourUgKg.hard) {
    hard.push(`Dosis en 60 min ${fmt(hourUg, 1)} µg/kg > ${SAFETY.hourUgKg.hard} µg/kg (límite duro).`);
  } else if (hourUg > SAFETY.hourUgKg.soft) {
    soft.push(`Dosis en 60 min ${fmt(hourUg, 1)} µg/kg > ${SAFETY.hourUgKg.soft} µg/kg.`);
  }
  if (config.durationMin > SAFETY.durationMin.soft) {
    soft.push(`Duración ${config.durationMin} min > ${SAFETY.durationMin.soft} min: fuera del periodo de muestreo del estudio.`);
  }
  if (config.premedUgKg > SAFETY.premedUgKg.soft) {
    soft.push(`Premedicación IM ${fmt(config.premedUgKg, 1)} µg/kg > ${SAFETY.premedUgKg.soft} µg/kg: absorción IM no validada en perros.`);
  }
  if (config.concMode === "custom") {
    soft.push(`Concentración personalizada (${config.conc} µg/mL): verifique la preparación con doble control.`);
  }
  if (weight < MODEL_WEIGHT_KG.min || weight > MODEL_WEIGHT_KG.max) {
    soft.push(`Peso ${weight} kg fuera de ${MODEL_WEIGHT_KG.min}–${MODEL_WEIGHT_KG.max} kg: extrapolación; en obesos use el peso magro.`);
  }
  return { hard, soft };
}

/** Texto de la acción que exige un paso del programa. */
function describeStep(step) {
  const rate = `${fmt(step.rateMlH, 1)} mL/h`;
  switch (step.kind) {
    case "load":     return `Carga ${rate} durante ${fmtDuration(step.loadSec)} (${fmt(step.loadMl, 2)} mL)${step.limited ? " · limitada por la bomba" : step.doseLimited ? ` · limitada a ${SAFETY.rateUgKgH.hard} µg/kg/h` : ""}`;
    case "stop":     return "Detener la bomba (0 mL/h)";
    case "pause":    return "Bomba en pausa (0 mL/h): la Cp desciende";
    case "maintain": return `Mantenimiento a ${rate}`;
    case "cri":      return step.rateMlH > 0 ? `Infusión continua a ${rate} (sin carga)` : "Bomba detenida: la premedicación IM cubre el objetivo";
    case "resume":   return `Reanudar a ${rate}`;
    case "target":   return `Nuevo objetivo: programar ${rate}`;
    default:         return `Programar ${rate}`;
  }
}

function syringeRecipe(conc, stock, syringeMl) {
  const drugMl = (syringeMl * conc) / stock;
  return { drugMl, salineMl: syringeMl - drugMl };
}

/** Motivo por el que una concentración queda fuera del rango de la bomba. */
function dilutionProblem(option, induction, pump) {
  const range = `rango de la bomba ${pump.min}–${pump.max} mL/h`;
  const tooHigh = Math.max(option.loadMlH || 0, option.startMlH) > pump.max;
  const hint = tooHigh
    ? `Aumente la tasa máxima de la bomba o use una concentración mayor.`
    : `Reduzca la tasa mínima de la bomba o use una concentración menor.`;
  if (induction === "none") {
    return `Con ${option.conc} µg/mL la infusión sería ${fmt(option.startMlH, 1)} mL/h (${range}). ${hint}`;
  }
  return `Con ${option.conc} µg/mL: carga ${fmt(option.loadMlH, 1)} mL/h, mantenimiento `
    + `${fmt(option.startMlH, 1)} → ${fmt(option.endMlH, 1)} mL/h (${range}). ${hint}`;
}

// ── Validación del formulario ────────────────────────────────────────────────
function parseField(key, raw) {
  const { min, max, unit, integer } = LIMITS[key];
  const text = String(raw).trim().replace(",", ".");
  const value = Number(text);
  if (text === "" || !Number.isFinite(value)) return { error: "Introduzca un valor numérico" };
  if (integer && !Number.isInteger(value))      return { error: "Debe ser un número entero" };
  if (value < min || value > max)               return { error: `Rango permitido: ${min}–${max} ${unit}` };
  return { value };
}

function validateDraft(draft) {
  const fields = {
    weight:   parseField("weight", draft.weight),
    targetCp: parseField("targetCp", draft.targetCp),
    duration: parseField("duration", draft.duration),
    pumpMin:  parseField("pumpMin", draft.pumpMin),
    pumpMax:  parseField("pumpMax", draft.pumpMax),
    ...(draft.induction === "none" ? { premed: parseField("premed", draft.premed) } : {}),
  };
  if (!fields.pumpMin.error && !fields.pumpMax.error && fields.pumpMax.value <= fields.pumpMin.value) {
    fields.pumpMax = { error: "Debe ser mayor que la tasa mínima" };
  }
  const fieldsValid = Object.values(fields).every(f => !f.error);
  const pump = { min: fields.pumpMin.value, max: fields.pumpMax.value };
  const concOptions = fieldsValid
    ? validDilutions(fields.weight.value, fields.targetCp.value, fields.duration.value, draft.stock, draft.induction, pump, draft.model)
    : [];

  // Concentración personalizada: entre CUSTOM_CONC_MIN y la presentación, y con la bomba en rango
  let custom = null;
  let customError = null;
  if (draft.conc === "custom") {
    const text = String(draft.concCustom).trim().replace(",", ".");
    const value = Number(text);
    if (text === "" || !Number.isFinite(value)) {
      customError = "Introduzca la concentración en µg/mL";
    } else if (value < CUSTOM_CONC_MIN || value > draft.stock) {
      customError = `Rango permitido: ${CUSTOM_CONC_MIN}–${draft.stock} µg/mL (no puede superar la presentación)`;
    } else if (fieldsValid) {
      custom = evaluateDilution(buildPK(fields.weight.value, draft.model), fields.targetCp.value, fields.duration.value, value, draft.induction, pump);
      if (!custom.ok) customError = dilutionProblem(custom, draft.induction, pump);
    }
  }

  const concError = draft.conc === "custom"
    ? customError
    : fieldsValid && concOptions.length === 0
      ? "Ninguna concentración predefinida deja la bomba dentro de rango. Pruebe una concentración personalizada o ajuste las tasas mínima y máxima de la bomba."
      : null;
  return {
    fields,
    fieldsValid,
    concOptions,
    concError,
    custom,
    recommendedConc: recommendConcentration(concOptions),
    valid: fieldsValid && (draft.conc === "custom" ? Boolean(custom?.ok) : concOptions.length > 0),
  };
}

function draftToConfig(draft, validation) {
  if (!validation.valid) return null;
  const isCustom = draft.conc === "custom";
  const manualConc = Number(draft.conc);
  // Una dilución manual que deja de ser válida (p. ej. al cambiar el peso) vuelve a la automática
  const useAuto = !isCustom && (draft.conc === "auto" || !validation.concOptions.some(o => o.conc === manualConc));
  return {
    model:       draft.model,
    weight:      validation.fields.weight.value,
    targetCp:    validation.fields.targetCp.value,
    durationMin: validation.fields.duration.value,
    stock:       draft.stock,
    conc:        isCustom ? validation.custom.conc : useAuto ? validation.recommendedConc : manualConc,
    concMode:    isCustom ? "custom" : useAuto ? "auto" : "preset",
    induction:   draft.induction,
    syringeMl:   draft.syringeMl,
    pumpMinMlH:  validation.fields.pumpMin.value,
    pumpMaxMlH:  validation.fields.pumpMax.value,
    premedUgKg:  validation.fields.premed?.value ?? 0,
  };
}

const sameConfig = (a, b) => !!a && !!b && Object.keys(a).every(k => a[k] === b[k]);

// ── Formato ──────────────────────────────────────────────────────────────────
const fmt = (v, digits) => (Number.isFinite(v) ? v.toFixed(digits) : "—");

/** Duración legible: "10 min", "32 min 24 s". */
function fmtDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return s ? `${m} min ${s} s` : `${m} min`;
}

function fmtClock(totalSec) {
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return [h, m, s].map(n => String(n).padStart(2, "0")).join(":");
}

const readClock = c => (c.startedAt === null ? c.baseMs : c.baseMs + (performance.now() - c.startedAt) * c.speed);

// ── Sonido de pre-aviso y alarma (Web Audio, sin archivos externos) ─────────
function createAudio() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    return Ctx ? new Ctx() : null;
  } catch {
    return null;
  }
}

function playTone(ctx, pattern) {
  if (!ctx) return;
  if (ctx.state === "suspended") ctx.resume();
  const isAlarm = pattern === "alarm";
  const offsets = isAlarm ? [0, 0.25, 0.5] : [0];
  for (const offset of offsets) {
    const start = ctx.currentTime + offset;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = isAlarm ? 880 : 620;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.2, start + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.18);
    osc.connect(gain).connect(ctx.destination);
    osc.start(start);
    osc.stop(start + 0.2);
  }
}

// ── Exportación del caso (CSV compatible con Excel en español) ──────────────
const EVENT_KIND_LABEL = {
  info: "Sistema", alarm: "Ajuste requerido", ok: "Ajuste confirmado", auto: "Ajuste automático",
  target: "Cambio de objetivo", milestone: "Hito",
};
const csvNumber = (v, digits) => (Number.isFinite(v) ? v.toFixed(digits).replace(".", ",") : "");
const csvExact  = v => (Number.isFinite(v) ? String(v).replace(".", ",") : "");   // sin redondeo (recálculo de la Cp)
const csvText   = t => {
  const text = String(t);
  const safe = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text;   // Excel ejecutaría =, +, -, @ como fórmula
  return `"${safe.replace(/"/g, '""')}"`;
};

/**
 * CSV del caso. `extra`: { endSec, untilSec, startMode }. El REGISTRO DE TASAS (tasa real de la bomba,
 * segundo a segundo) con el peso y la concentración sin redondeo permite recalcular la Cp en cualquier instante.
 */
function buildCaseCsv(config, plan, events, extra = {}) {
  const { endSec = null, untilSec = plan.totalSec, startMode = "" } = extra;
  const rates = rateHistory(plan, endSec, untilSec);
  const rows = [
    [csvText("Simulador TCI · Dexmedetomidina · Canino")],
    [csvText("Autor"), csvText(AUTHOR)],
    [csvText("Versión del simulador"), csvText(APP_VERSION)],
    [csvText("Exportado"), csvText(new Date().toLocaleString("es-ES"))],
    [csvText("Modelo"), csvText(`${PK_MODELS[plan.pk.model].label} · ${PK_MODELS[plan.pk.model].reference} · Shafer & Gregg 1992 · Cp-TCI`)],
    [csvText("Código del modelo"), csvText(plan.pk.model)],
    [csvText("Parámetros del modelo (V1 L/kg; V2 L/kg; Cl2 L/h/kg; Cl∞ L/h/kg; Cl0 L/h/kg; C50 ng/mL)"),
      ...["V1", "V2", "Cl2", "clInf", "cl0", "c50"].map(k => csvExact(PK_MODELS[plan.pk.model][k] ?? NaN))],
    [csvText("Modo de bomba al inicio"), csvText(startMode)],
    [csvText("Peso (kg)"), csvExact(config.weight)],
    [csvText("Cp objetivo inicial (ng/mL)"), csvNumber(config.targetCp, 2)],
    [csvText("Presentación (µg/mL)"), csvNumber(config.stock, 0)],
    [csvText("Concentración en jeringa (µg/mL)"), csvExact(config.conc)],
    [csvText("Jeringa (mL)"), csvNumber(config.syringeMl, 0)],
    [csvText("Rango de la bomba (mL/h)"), csvText(`${config.pumpMinMlH}–${config.pumpMaxMlH}`)],
    [csvText("Duración (min)"), csvNumber(config.durationMin, 0)],
    [csvText("Inicio de la infusión"), csvText(INDUCTION_LABEL[config.induction])],
    [csvText(`Premedicación IM ${IM_PREMED.delayMin} min antes (µg/kg)`), csvNumber(config.premedUgKg, 1)],
    [csvText("Volumen total estimado (mL)"), csvNumber(plan.totalMl, 2)],
    [csvText("Fin de la infusión (s)"), endSec === null ? csvText("en curso") : String(endSec)],
    [csvText("Fin de la infusión (tiempo)"), csvText(endSec === null ? "en curso" : fmtClock(endSec))],
    [csvText("Volumen infundido (mL)"), csvNumber(plan.deliveredMl[endSec ?? Math.min(untilSec, plan.totalSec)], 2)],
    [],
    [csvText("PROGRAMA DE INFUSIÓN")],
    ["N.º", "Tiempo", "Acción", "Tasa (mL/h)", "Dosis (µg/kg/h)", "Volumen de carga (mL)", "Objetivo (ng/mL)"].map(csvText),
    ...plan.steps.filter(step => endSec === null || step.sec < endSec).map((step, i) => [
      String(i), csvText(fmtClock(step.sec)), csvText(describeStep(step)), csvNumber(step.rateMlH, 1),
      csvNumber((step.rateMlH * config.conc) / config.weight, 2), csvNumber(step.loadMl, 2), csvNumber(step.targetCp, 2),
    ]),
    [],
    [csvText("REGISTRO DE TASAS")],
    ["Segundo", "Tiempo", "Tasa (mL/h)", "Dosis (µg/kg/h)", "Cp calculada (ng/mL)", "Nota"].map(csvText),
    ...rates.map(r => [
      String(r.sec), csvText(fmtClock(r.sec)), csvNumber(r.rateMlH, 1), csvNumber((r.rateMlH * config.conc) / config.weight, 3),
      csvNumber(plan.cp[Math.min(r.sec, plan.totalSec)], 4), csvText(r.end ? "Fin de la infusión" : ""),
    ]),
    [],
    [csvText("REGISTRO DE EVENTOS")],
    ["Tiempo", "Tipo", "Evento"].map(csvText),
    ...[...events].reverse().map(ev => [csvText(fmtClock(ev.sec)), csvText(EVENT_KIND_LABEL[ev.kind] ?? ev.kind), csvText(ev.text)]),
  ];
  return "﻿" + rows.map(r => r.join(";")).join("\r\n");
}

function downloadText(filename, text, mime) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════════
export default function TCISimulator() {
  const [draft, setDraft]   = useState(DEFAULT_DRAFT);
  const [config, setConfig] = useState(() => draftToConfig(DEFAULT_DRAFT, validateDraft(DEFAULT_DRAFT)));
  const [status, setStatus] = useState("idle");
  const [speed, setSpeed]   = useState(1);
  const [soundOn, setSoundOn] = useState(true);
  const [autoPump, setAutoPump] = useState(true);   // la bomba aplica los ajustes sola, como una bomba TCI
  const [elapsedMs, setElapsedMs] = useState(0);
  const [ackIdx, setAckIdx] = useState(0);        // último paso del programa aplicado en la bomba
  const [appliedAt, setAppliedAt] = useState({});  // modo manual: { índice de paso: segundo de confirmación }
  const [targetChanges, setTargetChanges] = useState([]);
  const [targetDraft, setTargetDraft] = useState("");
  const [targetError, setTargetError] = useState(null);
  const [events, setEvents] = useState([]);
  const [softAck, setSoftAck] = useState(false);            // avisos (límites blandos) confirmados antes de iniciar
  const [targetConfirm, setTargetConfirm] = useState(null); // cambio de objetivo pendiente de confirmar
  const [startMode, setStartMode] = useState("");
  const [endSec, setEndSec] = useState(null);               // segundo en que terminó la infusión (null: en curso)
  const [endConfirm, setEndConfirm] = useState(false);      // «Finalizar infusión» pendiente de confirmar
  const [unsaved, setUnsaved] = useState(false);            // hay datos del caso sin exportar

  const clock          = useRef({ baseMs: 0, startedAt: null, speed: 1 });
  const eventSeq       = useRef(0);
  const lastAlarmIdx   = useRef(0);
  const prealerted     = useRef(new Set());
  const audio          = useRef(null);

  const started    = status !== "idle";
  const infusing   = status === "running" || status === "paused";
  const locked     = infusing || status === "washout";          // formulario bloqueado mientras dura el caso
  const totalSecCfg = config.durationMin * 60;
  const clockSec   = Math.floor(elapsedMs / 1000);              // tiempo del caso (sigue tras la infusión)
  // Segundo del plan: el actual mientras se infunde; el del fin de la infusión después
  const elapsedSec = endSec !== null ? endSec : Math.min(totalSecCfg, clockSec);

  // En modo manual la simulación sigue a la bomba real: los ajustes sin confirmar
  // no se aplican. En automático solo cuentan los retrasos ya registrados.
  // (en automático no dependen del reloj, así el plan no se recalcula cada segundo)
  const timingAck = autoPump ? Infinity : ackIdx;
  const timingNow = autoPump ? null : elapsedSec;
  const timing = useMemo(
    () => (started ? { appliedAt, ackIdx: timingAck, nowSec: timingNow } : null),
    [started, appliedAt, timingAck, timingNow],
  );

  const validation = useMemo(() => validateDraft(draft), [draft]);
  const plan       = useMemo(() => buildPlan(config, targetChanges, timing), [config, targetChanges, timing]);

  const totalMs    = plan.totalSec * 1000;
  const activeIdx  = started ? stepIndexAt(plan.steps, elapsedSec) : 0;
  const pendingAdjust = infusing && !autoPump && activeIdx > ackIdx;
  const draftConfig   = draftToConfig(draft, validation);
  const dirty         = !sameConfig(draftConfig, config);
  const review        = useMemo(() => safetyReview(plan, config), [plan, config]);
  const draftKey      = JSON.stringify(draftConfig);
  const draftHard     = useMemo(() => {
    const c = JSON.parse(draftKey);
    return c ? safetyReview(buildPlan(c), c).hard : [];
  }, [draftKey]);
  const needsAck      = review.soft.length > 0 && !softAck;
  const wash          = useMemo(() => (endSec === null ? null : simulateWashout(plan, endSec)), [plan, endSec]);
  const washoutEndMs  = endSec === null ? Infinity : (endSec + WASHOUT_MAX_MIN * 60) * 1000;
  /** Cp, objetivo y tasa de la bomba en el segundo `sec` del caso (también tras la infusión). */
  const valuesAt = useCallback(sec => {
    if (wash && sec >= wash.endSec) {
      const i = Math.min(sec - wash.endSec, wash.cp.length - 1);
      return { cp: wash.cp[i], c2: wash.c2[i], target: NaN, rateMlH: 0, post: true };
    }
    const s = Math.min(sec, plan.totalSec);
    return { cp: plan.cp[s], c2: plan.c2[s], target: plan.target[s], rateMlH: plan.rateAt[s], post: false };
  }, [wash, plan]);
  const now           = started ? valuesAt(clockSec) : null;
  const currentTarget = started ? now.target : config.targetCp;
  const nextStep      = started ? plan.steps[activeIdx + 1] : null;
  const secToNext     = nextStep ? nextStep.sec - elapsedSec : null;
  const prealertStep  = infusing && !pendingAdjust && nextStep && secToNext <= PREALERT_SEC ? nextStep : null;

  const logEvent = useCallback((sec, text, kind = "info") => {
    const id = ++eventSeq.current;
    setEvents(prev => [{ id, sec, text, kind }, ...prev]);
  }, []);

  // Datos del caso sin exportar: aviso al recargar o cerrar la página
  useEffect(() => { if (events.length > 1) setUnsaved(true); }, [events]);
  useEffect(() => {
    if (!unsaved) return undefined;
    const warn = e => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved]);

  // Reloj: el tiempo simulado se deriva del reloj del sistema, no de contar ticks
  // En pausa y tras la infusión el tiempo sigue: la bomba está parada y la Cp desciende
  const capMs = endSec === null ? totalMs : washoutEndMs;
  useEffect(() => {
    if (!locked) return undefined;
    const id = setInterval(() => setElapsedMs(Math.min(readClock(clock.current), capMs)), TICK_MS);
    return () => clearInterval(id);
  }, [locked, capMs]);

  /** Detiene la infusión en `sec`: la bomba pasa a 0 mL/h y empieza el seguimiento posterior. */
  const endInfusion = useCallback((sec, text) => {
    setEndSec(sec);
    setEndConfirm(false);
    setStatus("washout");
    logEvent(sec, text);
  }, [logEvent]);

  /** Cierra el caso: el reloj se detiene y ya no se registran datos. */
  const closeCase = useCallback((sec, text) => {
    clock.current = { ...clock.current, baseMs: sec * 1000, startedAt: null };
    setElapsedMs(sec * 1000);
    setStatus("finished");
    logEvent(sec, text);
  }, [logEvent]);

  // Fin de la infusión programada y fin del seguimiento posterior
  useEffect(() => {
    if (infusing && elapsedMs >= totalMs) {
      endInfusion(plan.totalSec, "Fin de la infusión programada: detenga la bomba (0 mL/h). La Cp se sigue calculando tras la infusión");
    } else if (status === "washout" && elapsedMs >= washoutEndMs) {
      closeCase(Math.floor(washoutEndMs / 1000), `Fin del seguimiento: ${WASHOUT_MAX_MIN} min tras la infusión`);
    }
  }, [infusing, status, elapsedMs, totalMs, washoutEndMs, plan.totalSec, endInfusion, closeCase]);

  // Registro y alarma sonora de cada ajuste solicitado por el programa
  useEffect(() => {
    if (!infusing) return;
    let fired = false;
    for (let i = lastAlarmIdx.current + 1; i <= activeIdx; i++) {
      const step = plan.steps[i];
      if (step.kind === "pause") continue;                     // ya registrada al pulsar Pausar
      const text = `${describeStep(step)}${step.outOfRange ? " · fuera de rango" : ""}`;
      logEvent(step.sec, text, autoPump ? "auto" : "alarm");
      fired = true;
    }
    lastAlarmIdx.current = Math.max(lastAlarmIdx.current, activeIdx);
    if ((autoPump || plan.steps[activeIdx].kind === "pause") && activeIdx > ackIdx) setAckIdx(activeIdx);
    if (fired && soundOn) playTone(audio.current, autoPump ? "prealert" : "alarm");
  }, [infusing, activeIdx, ackIdx, autoPump, plan.steps, logEvent, soundOn]);

  // Pre-aviso sonoro, una vez por paso
  const prealertKey = prealertStep ? `${prealertStep.sec}|${prealertStep.rateMlH}|${prealertStep.kind}` : null;
  useEffect(() => {
    if (!prealertKey || prealerted.current.has(prealertKey)) return;
    prealerted.current.add(prealertKey);
    if (soundOn) playTone(audio.current, "prealert");
  }, [prealertKey, soundOn]);

  // Tiempo de decremento del 50 % si se detuviera la infusión ahora
  const nowCp = now?.cp, nowC2 = now?.c2;
  const decrement50 = useMemo(() => {
    if (!started) return null;
    const a1 = nowCp * plan.pk.V1;
    const a2 = nowC2 * plan.pk.V2;
    return a1 > 0 ? decrementTimeSec(plan.pk, a1, a2, 0.5) : null;
  }, [started, nowCp, nowC2, plan.pk]);

  // ── Acciones ────────────────────────────────────────────────────────────────
  const resetRun = () => {
    clock.current = { baseMs: 0, startedAt: null, speed };
    lastAlarmIdx.current = 0;
    prealerted.current = new Set();
    setElapsedMs(0);
    setAckIdx(0);
    setAppliedAt({});
    setTargetChanges([]);
    setTargetDraft("");
    setTargetError(null);
    setTargetConfirm(null);
    setEndSec(null);
    setEndConfirm(false);
  };

  const clearCase = () => {
    setEvents([]);
    setUnsaved(false);
  };

  const programInfusion = () => {
    if (!draftConfig || locked) return;
    resetRun();
    clearCase();
    setSoftAck(false);
    setConfig(draftConfig);
    setStatus("idle");
  };

  const startRun = () => {
    audio.current = audio.current ?? createAudio();            // requiere un gesto del usuario
    if (audio.current?.state === "suspended") audio.current.resume();
    resetRun();
    clock.current.startedAt = performance.now();
    clearCase();
    const mode = autoPump ? "automático" : "manual (cada ajuste se confirma)";
    setStartMode(`${mode} · velocidad ${speed}×`);
    logEvent(0, `Inicio · ${describeStep(plan.steps[0])}`);   // el paso 0 no depende de cambios de objetivo
    logEvent(0, `Bomba en modo ${mode} · velocidad ${speed}×`);
    logEvent(0, `Modelo farmacocinético: ${PK_MODELS[config.model].label}`);
    if (review.soft.length) logEvent(0, `Avisos confirmados por el usuario: ${review.soft.join(" · ")}`, "ok");
    setStatus("running");
  };

  // Pausa de la bomba: el tiempo sigue y la Cp desciende; al reanudar, el TCI
  // replanifica desde la Cp alcanzada (con carga, recarga hasta el objetivo)
  const pauseRun = () => {
    const sec = elapsedSec + 1;
    if (sec >= plan.totalSec) return;
    const targetCp = plan.target[elapsedSec];
    setTargetChanges(prev => [...prev.filter(c => c.sec < sec), { sec, targetCp, pause: true }]);
    setStatus("paused");
    logEvent(elapsedSec, `Infusión en pausa: bomba a 0 mL/h (Cp ${fmt(plan.cp[elapsedSec], 2)} ng/mL)`);
  };

  const resumeRun = () => {
    const sec = elapsedSec + 1;
    setStatus("running");
    if (sec >= plan.totalSec) return;
    const targetCp = plan.target[elapsedSec];
    setTargetChanges(prev => [...prev.filter(c => c.sec < sec), { sec, targetCp }]);
    logEvent(elapsedSec, `Infusión reanudada tras ${fmtDuration(elapsedSec + 1 - pauseStartSec)} (Cp ${fmt(plan.cp[elapsedSec], 2)} ng/mL): el TCI recalcula hasta ${fmt(targetCp, 2)} ng/mL`, "target");
  };

  // Finalizar la infusión (fin de la cirugía): pide confirmación con un segundo clic
  const requestEnd = () => {
    if (!endConfirm) { setEndConfirm(true); return; }
    endInfusion(elapsedSec, `Infusión finalizada por el usuario: detenga la bomba (0 mL/h) · Cp ${fmt(plan.cp[elapsedSec], 2)} ng/mL`);
  };

  const changeSpeed = value => {
    if (started && value !== speed) logEvent(clockSec, `Velocidad de simulación ${value}×${value === 1 ? " (tiempo real)" : " · no válida en un caso clínico"}`);
    const c = clock.current;
    clock.current = {
      baseMs: readClock(c),
      startedAt: c.startedAt === null ? null : performance.now(),
      speed: value,
    };
    setSpeed(value);
  };

  const pauseStartSec  = [...targetChanges].reverse().find(c => c.pause)?.sec ?? elapsedSec;
  const pendingSteps   = pendingAdjust ? plan.steps.slice(ackIdx + 1, activeIdx + 1) : [];
  const pendingOut     = pendingSteps.some(step => step.outOfRange);
  const latestStep     = plan.steps[activeIdx];
  const pendingAction  = describeStep(latestStep);

  /** Registra que los pasos pendientes empiezan a infundir en `sec` (simulación fiel a la bomba real). */
  const markApplied = sec => setAppliedAt(prev => {
    const next = { ...prev };
    for (let i = ackIdx + 1; i <= activeIdx; i++) next[i] = sec;
    return next;
  });

  const acknowledgeAdjust = () => {
    markApplied(elapsedSec);
    setAckIdx(activeIdx);
    logEvent(
      elapsedSec,
      `Confirmado: ${pendingAction.charAt(0).toLowerCase()}${pendingAction.slice(1)} (retraso ${elapsedSec - pendingSteps[0].sec} s)`,
      "ok",
    );
  };

  const applyTargetChange = () => {
    if (status === "paused") { setTargetError("Reanude la infusión para cambiar el objetivo"); return; }
    const parsed = parseField("targetCp", targetDraft);
    if (parsed.error) { setTargetError(parsed.error); return; }
    const sec = elapsedSec + 1;                                // el nuevo tramo empieza en el segundo siguiente
    if (sec >= plan.totalSec) { setTargetError("La infusión está terminando"); return; }
    const previous = plan.target[elapsedSec];
    if (parsed.value === previous) { setTargetError("Es el objetivo actual"); return; }

    // Límite duro: no se sube el objetivo mientras dura una carga (evita acumular cargas)
    const current = plan.steps[activeIdx];
    if (parsed.value > previous && current.kind === "load" && elapsedSec < current.sec + current.loadSec) {
      setTargetError(`Límite duro: espere a que termine la carga en curso (${fmtClock(current.sec + current.loadSec - elapsedSec)}) antes de subir el objetivo.`);
      return;
    }
    const changes = [...targetChanges.filter(c => c.sec < sec), { sec, targetCp: parsed.value }];
    const candidate = safetyReview(buildPlan(config, changes, timing), config);
    if (candidate.hard.length) { setTargetError(`Límite duro: ${candidate.hard.join(" ")}`); return; }
    const newSoft = candidate.soft.filter(w => !review.soft.includes(w));
    if (parsed.value - previous > SAFETY.targetStep.soft) {
      newSoft.unshift(`Subida de ${fmt(parsed.value - previous, 2)} ng/mL > ${SAFETY.targetStep.soft} ng/mL por cambio.`);
    }
    if (newSoft.length && targetConfirm !== parsed.value) {
      setTargetConfirm(parsed.value);
      setTargetError(`Aviso: ${newSoft.join(" ")} Pulse «Aplicar» de nuevo para confirmar.`);
      return;
    }
    setTargetChanges(changes);
    logEvent(elapsedSec, `Cambio de objetivo: ${fmt(previous, 2)} → ${fmt(parsed.value, 2)} ng/mL`, "target");
    if (newSoft.length) logEvent(elapsedSec, `Aviso confirmado: ${newSoft.join(" · ")}`, "ok");
    setTargetDraft("");
    setTargetError(null);
    setTargetConfirm(null);
  };

  const addMilestone = text => logEvent(clockSec, text, "milestone");

  const toggleAutoPump = enabled => {
    if (started && enabled !== autoPump) logEvent(clockSec, enabled ? "Ajuste automático activado" : "Modo manual activado: cada ajuste se confirma");
    // Al pasar a automático, los ajustes pendientes se aplican ahora, no en su hora teórica
    if (enabled && started && activeIdx > ackIdx) {
      markApplied(elapsedSec);
      setAckIdx(activeIdx);
    }
    setAutoPump(enabled);
  };

  const exportCase = () => {
    const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "");
    const csv = buildCaseCsv(config, plan, events, { endSec, untilSec: elapsedSec, startMode });
    downloadText(`caso_tci_dexmedetomidina_${stamp}.csv`, csv, "text/csv;charset=utf-8");
    setUnsaved(false);
  };

  // ── Valores del monitor ─────────────────────────────────────────────────────
  // La tasa mostrada es la que la bomba infunde realmente: el último ajuste confirmado.
  const pumpRateMlH = !started ? NaN : endSec !== null ? 0 : plan.steps[ackIdx].rateMlH;
  const volumeMl    = started ? plan.deliveredMl[elapsedSec] : NaN;
  const monitor = {
    cp:         started ? now.cp : NaN,
    rateMlH:    pumpRateMlH,
    doseUgKgH:  (pumpRateMlH * config.conc) / config.weight,
    volumeMl,
    totalUgKg:  (volumeMl * config.conc) / config.weight,
  };
  const live = useMemo(() => (started ? {
    t: clockSec / 60,
    cp: valuesAt(clockSec).cp,
    c2: valuesAt(clockSec).c2,
    target: endSec !== null && clockSec >= endSec ? null : plan.target[elapsedSec],
    rate: endSec !== null && clockSec >= endSec ? 0 : plan.rateAt[elapsedSec],
  } : null), [started, clockSec, elapsedSec, endSec, plan, valuesAt]);
  // Tras la infusión, las gráficas añaden el descenso previsto durante el seguimiento
  const chartData = useMemo(() => {
    if (!wash) return plan.chart;
    const tail = [];
    for (let s = 0; s < wash.cp.length; s += CHART_SAMPLE_SEC) {
      tail.push({ t: (wash.endSec + s) / 60, cp: wash.cp[s], c2: wash.c2[s], target: null, rate: 0 });
    }
    return [...plan.chart.filter(d => d.t < wash.endSec / 60), ...tail];
  }, [plan.chart, wash]);
  const chartMin = wash ? Math.ceil((wash.endSec / 60 + WASHOUT_MAX_MIN) / 10) * 10 : config.durationMin;

  return (
    <div className="tci">
      <style>{CSS}</style>

      <header className="tci-header">
        <div>
          <h1>Simulador TCI · Dexmedetomidina · Canino</h1>
          <p>Modelo {PK_MODELS[config.model].label} · Algoritmo Shafer &amp; Gregg 1992 · Modo Cp (plasma)</p>
          <p className="tci-author">Autor: {AUTHOR} · Versión {APP_VERSION}</p>
        </div>
        <span className={`tci-status tci-status--${status}`}>{STATUS_LABEL[status]}</span>
      </header>

      <div className="tci-layout">
        <aside className="tci-column">
          <SetupPanel
            draft={draft}
            setDraft={setDraft}
            validation={validation}
            locked={locked}
            dirty={dirty}
            onProgram={programInfusion}
            draftHard={draftHard}
          />
          <PreparationPanel config={config} plan={plan} />
        </aside>

        <main className="tci-column">
          <section className="tci-panel tci-monitor">
            {pendingAdjust && (
              <div className="tci-alarm" role="alert">
                <div>
                  <strong>AJUSTE DE BOMBA REQUERIDO · {fmtClock(pendingSteps[0].sec)}</strong>
                  <span>
                    {pendingAction} (bomba actual {fmt(plan.steps[ackIdx].rateMlH, 1)} mL/h)
                    {pendingSteps.length > 1 && ` · ${pendingSteps.length} ajustes acumulados`}
                  </span>
                  {pendingOut && <span className="tci-alarm__warn">⚠ Fuera del rango operable de la bomba</span>}
                </div>
                <button type="button" className="tci-btn tci-btn--alarm" onClick={acknowledgeAdjust}>
                  Confirmar ajuste
                </button>
              </div>
            )}
            {prealertStep && (
              <div className="tci-prealert" role="status">
                <strong>PRÓXIMO AJUSTE EN {fmtClock(secToNext)}</strong>
                <span>{describeStep(prealertStep)}</span>
              </div>
            )}

            <div className="tci-displays">
              <Display label="Cp objetivo"       value={fmt(currentTarget, 2)}      unit="ng/mL" />
              <Display label="Cp calculada"      value={fmt(monitor.cp, 2)}         unit="ng/mL" primary />
              <Display label="Tasa bomba"        value={fmt(monitor.rateMlH, 1)}    unit="mL/h" primary />
              <Display label="Dosis"             value={fmt(monitor.doseUgKgH, 2)}  unit="µg/kg/h" />
              <Display label="Volumen infundido" value={fmt(monitor.volumeMl, 2)}   unit="mL (incl. carga)" />
              <Display label="Dosis total"       value={fmt(monitor.totalUgKg, 2)}  unit="µg/kg" />
              <Display label="Decremento 50 %"   value={decrement50 === null ? "—" : fmtClock(decrement50)} unit={endSec === null ? "si se detiene ahora" : "desde ahora"} />
              <Display label="Tiempo"            value={fmtClock(clockSec)}
                unit={endSec === null ? `de ${fmtClock(plan.totalSec)}` : `fin de infusión ${fmtClock(endSec)} · +${fmtClock(Math.max(0, clockSec - endSec))}`} />
            </div>

            <div className="tci-progress" aria-hidden="true">
              <div style={{ width: `${(endSec === null ? elapsedSec / plan.totalSec : (clockSec - endSec) / (WASHOUT_MAX_MIN * 60)) * 100}%` }} />
            </div>

            <div className="tci-controls">
              <div className="tci-controls__group">
                {status === "idle"     && <button type="button" className="tci-btn tci-btn--primary" onClick={startRun} disabled={dirty || needsAck}>Iniciar</button>}
                {status === "running"  && <button type="button" className="tci-btn" onClick={pauseRun}>Pausar</button>}
                {status === "paused"   && <button type="button" className="tci-btn tci-btn--primary" onClick={resumeRun}>Reanudar</button>}
                {status === "finished" && <button type="button" className="tci-btn tci-btn--primary" onClick={startRun} disabled={dirty || needsAck}>Reiniciar</button>}
                {infusing && (
                  <button type="button" className={`tci-btn${endConfirm ? " tci-btn--danger" : ""}`} onClick={requestEnd}>
                    {endConfirm ? "Confirmar fin" : "Finalizar infusión"}
                  </button>
                )}
                {status === "washout" && (
                  <button type="button" className="tci-btn" onClick={() => closeCase(clockSec, "Caso cerrado por el usuario")}>Cerrar caso</button>
                )}
              </div>
              <div className="tci-controls__meta">
                <span>
                  Próximo ajuste:{" "}
                  <b>
                    {!started ? "—"
                      : endSec !== null ? "infusión finalizada"
                      : nextStep ? `${fmtClock(secToNext)} → ${describeStep(nextStep)}`
                      : "sin ajustes pendientes"}
                  </b>
                </span>
              </div>
            </div>

            <div className="tci-controls tci-controls--secondary">
              <form
                className="tci-inline"
                onSubmit={e => { e.preventDefault(); applyTargetChange(); }}
              >
                <label htmlFor="newTarget">Nuevo objetivo (ng/mL)</label>
                <input
                  id="newTarget"
                  inputMode="decimal"
                  value={targetDraft}
                  onChange={e => setTargetDraft(e.target.value)}
                  placeholder={fmt(currentTarget, 2)}
                  disabled={!infusing}
                />
                <button type="submit" className="tci-btn tci-btn--small" disabled={!infusing || !targetDraft.trim()}>Aplicar</button>
              </form>
              <div className="tci-controls__meta">
                <label className="tci-inline" title="Desactívelo para simular una bomba convencional en la que cada ajuste se confirma a mano">
                  <input type="checkbox" checked={autoPump} onChange={e => toggleAutoPump(e.target.checked)} />
                  Ajuste automático
                </label>
                <label className="tci-inline">
                  <input type="checkbox" checked={soundOn} onChange={e => setSoundOn(e.target.checked)} />
                  Sonido
                </label>
                <label className="tci-inline">
                  Velocidad
                  <select value={speed} onChange={e => changeSpeed(Number(e.target.value))}>
                    {SPEED_OPTIONS.map(v => <option key={v} value={v}>{v}×</option>)}
                  </select>
                </label>
              </div>
            </div>
            {endConfirm && infusing && (
              <div className="tci-ack tci-ack--end">
                <strong>¿Finalizar la infusión?</strong> Detenga la bomba (0 mL/h). El simulador seguirá calculando el descenso de la Cp
                durante {WASHOUT_MAX_MIN} min. Pulse «Confirmar fin» o{" "}
                <button type="button" className="tci-btn tci-btn--small" onClick={() => setEndConfirm(false)}>Cancelar</button>
              </div>
            )}
            {!locked && !dirty && review.soft.length > 0 && (
              <div className="tci-ack">
                <strong>Límites blandos superados · confirme para iniciar</strong>
                <ul>{review.soft.map(w => <li key={w}>{w}</li>)}</ul>
                <label className="tci-inline">
                  <input type="checkbox" checked={softAck} onChange={e => setSoftAck(e.target.checked)} />
                  He revisado estos avisos y asumo la programación
                </label>
              </div>
            )}
            {targetError && <p className="tci-note tci-note--warn">{targetError}</p>}
            {status === "finished" && unsaved && (
              <p className="tci-note tci-note--warn">Caso cerrado sin exportar: pulse «Exportar CSV» antes de programar otro caso o cerrar el programa.</p>
            )}
            {dirty && !locked && (
              <p className="tci-note tci-note--warn">Hay parámetros sin programar. Pulse «Programar infusión» antes de iniciar o reiniciar.</p>
            )}
          </section>

          <TrendCharts data={chartData} durationMin={chartMin} live={live} pump={plan.pump} />

          <div className="tci-grid-2">
            <ScheduleTable steps={plan.steps} conc={config.conc} weight={config.weight} activeIdx={started ? activeIdx : -1} induction={config.induction} premed={config.premedUgKg > 0} endSec={endSec} />
            <EventPanel events={events} canLog={started} onMilestone={addMilestone} onExport={exportCase} />
          </div>

          <SafetyPanel plan={plan} review={review} />
        </main>
      </div>

      <footer className="tci-footer">
        Levionnois et al. J Vet Pharmacol Ther. 2022;45:366-372 · Corrección para anestesia: Pascoe et al. 2006, Lin et al. 2008 ·
        Shafer &amp; Gregg, J Pharmacokinet Biopharm 1992 ·
        Modelo sin k<sub>e0</sub>: no se estima concentración en sitio efecto · Uso exclusivamente educativo
        <br />
        © {COPYRIGHT_YEAR} {AUTHOR}. Todos los derechos reservados.
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SUBCOMPONENTES
// ═══════════════════════════════════════════════════════════════════════════════
function Display({ label, value, unit, primary = false }) {
  return (
    <div className={`tci-display${primary ? " tci-display--primary" : ""}`}>
      <span className="tci-display__label">{label}</span>
      <span className="tci-display__value">{value}</span>
      <span className="tci-display__unit">{unit}</span>
    </div>
  );
}

function Field({ id, label, unit, error, children }) {
  return (
    <div className="tci-field">
      <label htmlFor={id}>{label}{unit && <span> ({unit})</span>}</label>
      {children}
      {error && <span className="tci-field__error">{error}</span>}
    </div>
  );
}

function SetupPanel({ draft, setDraft, validation, locked, dirty, onProgram, draftHard }) {
  const { fields, fieldsValid, concOptions, concError, recommendedConc, valid } = validation;
  const setSyringe = e => setDraft(d => ({ ...d, syringeMl: Number(e.target.value) }));
  const concValue = draft.conc === "custom" || concOptions.some(o => String(o.conc) === draft.conc) ? draft.conc : "auto";
  const set      = key => e => setDraft(d => ({ ...d, [key]: e.target.value }));
  const setStock = e => setDraft(d => ({ ...d, stock: Number(e.target.value) }));

  const cpValue = fields.targetCp.value;

  return (
    <section className="tci-panel">
      <h2>Datos del paciente y del fármaco</h2>
      <fieldset disabled={locked}>
        <Field id="model" label="Modelo farmacocinético">
          <select id="model" value={draft.model} onChange={set("model")}>
            {Object.entries(PK_MODELS).map(([value, m]) => (
              <option key={value} value={value}>{m.label}{value === DEFAULT_MODEL ? " · por defecto" : ""}</option>
            ))}
          </select>
        </Field>
        <p className="tci-note tci-note--field">
          {draft.model === "publicado"
            ? "Modelo original (perros despiertos, bolo de 10 µg/kg). En perros anestesiados predice el doble de la Cp medida: úselo solo para comparar."
            : `Aclaramiento corregido con perros anestesiados (Pascoe 2006, Lin 2008): Cl = ${PK_MODELS.anestesiado.clInf}–${PK_MODELS.anestesiado.cl0} L/h/kg según la Cp.`}
        </p>
        <Field id="weight" label="Peso" unit="kg" error={fields.weight.error}>
          <input id="weight" inputMode="decimal" value={draft.weight} onChange={set("weight")} />
        </Field>
        <Field id="targetCp" label="Cp objetivo" unit="ng/mL" error={fields.targetCp.error}>
          <input id="targetCp" inputMode="decimal" value={draft.targetCp} onChange={set("targetCp")} />
        </Field>
        {cpValue !== undefined && (
          <p className={`tci-note tci-note--field${cpValue > SAFETY.targetCp.soft ? " tci-note--warn" : ""}`}>
            En equilibrio equivale a {fmt(cpValue * clearanceKgH(draft.model, cpValue), 2)} µg/kg/h
            {cpValue > SAFETY.targetCp.soft ? ` · supera el límite blando (${SAFETY.targetCp.soft} ng/mL)` : ""} · máx. {SAFETY.targetCp.hard} ng/mL
          </p>
        )}
        {cpValue !== undefined && draft.model === "publicado" && cpValue <= EXTERNAL_BIAS_NOTE_MAX_CP && (
          <p className="tci-note tci-note--field tci-note--warn">
            Con objetivos ≤ {EXTERNAL_BIAS_NOTE_MAX_CP} ng/mL la Cp real puede ser menor que la mostrada (≈ 20 % en perros despiertos, ≈ 50 % en anestesiados).
          </p>
        )}
        <Field id="duration" label="Duración" unit="min" error={fields.duration.error}>
          <input id="duration" inputMode="numeric" value={draft.duration} onChange={set("duration")} />
        </Field>
        <Field id="induction" label="Inicio de la infusión">
          <select id="induction" value={draft.induction} onChange={set("induction")}>
            {Object.entries(INDUCTION_LABEL).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </Field>
        {draft.induction === "none" && (
          <>
            <Field id="premed" label="Premedicación IM (dexmedetomidina)" unit={`µg/kg, ${IM_PREMED.delayMin} min antes`} error={fields.premed?.error}>
              <input id="premed" inputMode="decimal" value={draft.premed} onChange={set("premed")} />
            </Field>
            <p className="tci-note tci-note--field">
              Se asume que la bomba se inicia {IM_PREMED.delayMin} min después de la inyección IM: la Cp parte de la estimada
              para la premedicación y la bomba solo complementa lo que aún se absorbe. Sin premedicación, la Cp sube lentamente.
            </p>
          </>
        )}
        <Field id="stock" label="Presentación comercial" unit="µg/mL">
          <select id="stock" value={draft.stock} onChange={setStock}>
            {STOCK_OPTIONS.map(s => <option key={s} value={s}>{s} µg/mL</option>)}
          </select>
        </Field>
        <Field id="conc" label="Concentración en jeringa" error={draft.conc === "custom" ? null : concError}>
          {fieldsValid ? (
            <select id="conc" value={concValue} onChange={set("conc")}>
              <option value="auto" disabled={!recommendedConc}>
                {recommendedConc ? `Automática (${recommendedConc} µg/mL)` : "Automática (ninguna predefinida válida)"}
              </option>
              {concOptions.map(o => (
                <option key={o.conc} value={o.conc}>
                  {draft.induction === "none"
                    ? `${o.conc} µg/mL — ${o.startMlH.toFixed(1)} mL/h continua`
                    : `${o.conc} µg/mL — carga ${o.loadMlH.toFixed(1)} mL/h · ${o.startMlH.toFixed(1)} → ${o.endMlH.toFixed(1)} mL/h`}
                </option>
              ))}
              <option value="custom">Personalizada…</option>
            </select>
          ) : (
            <select id="conc" disabled value="">
              <option value="">Complete los datos del paciente</option>
            </select>
          )}
        </Field>
        {draft.conc === "custom" && fieldsValid && (
          <Field id="concCustom" label="Concentración personalizada" unit={`µg/mL, máx. ${draft.stock}`} error={concError}>
            <input id="concCustom" inputMode="decimal" value={draft.concCustom} onChange={set("concCustom")} placeholder="p. ej. 100" />
          </Field>
        )}
        {draft.conc === "custom" && validation.custom?.ok && (
          <p className="tci-note tci-note--field">
            {draft.induction === "none"
              ? `Infusión continua ${fmt(validation.custom.startMlH, 1)} mL/h`
              : `Carga ${fmt(validation.custom.loadMlH, 1)} mL/h (${fmt(validation.custom.loadMl, 2)} mL) · mantenimiento ${fmt(validation.custom.startMlH, 1)} → ${fmt(validation.custom.endMlH, 1)} mL/h`}
          </p>
        )}
        <Field id="syringeMl" label="Jeringa" unit="mL">
          <select id="syringeMl" value={draft.syringeMl} onChange={setSyringe}>
            {SYRINGE_OPTIONS.map(v => <option key={v} value={v}>{v} mL</option>)}
          </select>
        </Field>
        <div className="tci-field-row">
          <Field id="pumpMin" label="Bomba mín." unit="mL/h" error={fields.pumpMin.error}>
            <input id="pumpMin" inputMode="decimal" value={draft.pumpMin} onChange={set("pumpMin")} />
          </Field>
          <Field id="pumpMax" label="Bomba máx." unit="mL/h" error={fields.pumpMax.error}>
            <input id="pumpMax" inputMode="decimal" value={draft.pumpMax} onChange={set("pumpMax")} />
          </Field>
        </div>
        {draftHard.length > 0 && (
          <p className="tci-note tci-note--error">Límite duro: {draftHard.join(" ")}</p>
        )}
        <button type="button" className="tci-btn tci-btn--primary tci-btn--block" onClick={onProgram} disabled={!valid || !dirty || draftHard.length > 0}>
          Programar infusión
        </button>
      </fieldset>
      {locked && <p className="tci-note">Parámetros bloqueados durante la infusión. Detenga la simulación para modificarlos.</p>}
    </section>
  );
}

const PreparationPanel = memo(function PreparationPanel({ config, plan }) {
  const { drugMl, salineMl } = syringeRecipe(config.conc, config.stock, config.syringeMl);
  const concModeLabel = { auto: " · automática", preset: "", custom: " · personalizada" }[config.concMode];
  const rows = [
    ["Modelo",           PK_MODELS[plan.pk.model].label],
    ["Paciente",         `Canino, ${config.weight} kg`],
    ["Cp objetivo inicial", `${fmt(config.targetCp, 2)} ng/mL`],
    ["Dilución",         salineMl > 0
      ? `${fmt(drugMl, 2)} mL de ${config.stock} µg/mL + ${fmt(salineMl, 2)} mL NaCl 0,9 %`
      : `${fmt(drugMl, 2)} mL de ${config.stock} µg/mL sin diluir`],
    ["Concentración",    `${config.conc} µg/mL (jeringa de ${config.syringeMl} mL)${concModeLabel}`],
    ["Inicio",           INDUCTION_LABEL[config.induction]],
    ...(config.induction === "none" ? [
      ...(config.premedUgKg > 0 ? [
        ["Premedicación IM", `${fmt(config.premedUgKg, 1)} µg/kg hace ${IM_PREMED.delayMin} min · Cp estimada al iniciar ${fmt(plan.cp[0], 2)} ng/mL`],
        ["Infusión complementaria", `${fmt(plan.steps[0].rateMlH, 1)} → ${fmt(plan.startMlH, 1)} mL/h`],
      ] : []),
      ["Infusión continua", `${fmt(plan.startMlH, 1)} mL/h · ${fmt((plan.startMlH * config.conc) / config.weight, 2)} µg/kg/h`],
    ] : [
      ["Carga (10 min)",   `${fmt(plan.loadMlH, 1)} mL/h · ${fmt(plan.loadMl, 2)} mL · ${fmt(plan.loadUg / config.weight, 3)} µg/kg`],
      ["Mantenimiento",    `${fmt(plan.startMlH, 1)} → ${fmt(plan.endMlH, 1)} mL/h`],
      ["Ajustes previstos", `${plan.initialSteps - 1} (sin cambios de objetivo)`],
    ]),
    ["90 % del objetivo", plan.time90Sec === null ? "no se alcanza en la duración programada" : fmtClock(plan.time90Sec)],
    ["Volumen total",    `${fmt(plan.totalMl, 1)} mL`],
  ];
  const m = PK_MODELS[plan.pk.model];
  const pkRows = [
    ["V1", fmt(plan.pk.V1, 3), "L"], ["V2", fmt(plan.pk.V2, 3), "L"],
    ...(plan.pk.linear
      ? [["Cl1", fmt(plan.pk.Cl1, 4), "L/min"]]
      : [[`Cl con ${fmt(config.targetCp, 2)} ng/mL`, fmt(plan.pk.clAt(config.targetCp), 4), "L/min"],
         ["Cl∞ · Cl0", `${m.clInf} · ${m.cl0}`, "L/h/kg"], ["C50", fmt(m.c50, 2), "ng/mL"]]),
    ["Cl2", fmt(plan.pk.Cl2, 4), "L/min"],
    [plan.pk.linear ? "k10" : `k10 con ${fmt(config.targetCp, 2)} ng/mL`, fmt(plan.pk.k10At(config.targetCp), 5), "min⁻¹"],
    ["k12", fmt(plan.pk.k12, 5), "min⁻¹"], ["k21", fmt(plan.pk.k21, 5), "min⁻¹"],
  ];

  return (
    <section className="tci-panel">
      <h2>Protocolo programado</h2>
      <dl className="tci-dl">
        {rows.map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{v}</dd></div>))}
      </dl>
      {drugMl < MIN_MEASURABLE_ML && (
        <p className="tci-note tci-note--warn">
          El volumen de fármaco ({fmt(drugMl, 3)} mL) es difícil de medir con precisión: use una jeringa mayor o una concentración más alta.
        </p>
      )}
      <p className="tci-note">
        {config.induction === "none"
          ? (config.premedUgKg > 0
            ? `Premedicado: la Cp inicial se estima a partir de la dosis IM (supuestos: absorción completa, pico a los ~${IM_PREMED.delayMin} min; no validados en perros). Si la Cp supera el objetivo, la bomba espera detenida; después ajusta la tasa por pasos descontando lo que aún se absorbe de la dosis IM.`
            : "Sin dosis de carga: la bomba infunde desde el inicio la tasa de equilibrio del objetivo. Evita el pico inicial, pero la Cp sube despacio.")
          : `La dosis de carga se infunde con la bomba en ${LOAD_SEC / 60} min, no como bolo rápido, para atenuar la hipertensión transitoria y la bradicardia refleja. La Cp alcanza el objetivo al final de la carga.`}
      </p>
      <details className="tci-details">
        <summary>Parámetros farmacocinéticos</summary>
        <table className="tci-table tci-table--compact">
          <tbody>
            {pkRows.map(([k, v, u]) => (<tr key={k}><th scope="row">{k}</th><td>{v}</td><td>{u}</td></tr>))}
          </tbody>
        </table>
      </details>
    </section>
  );
});

/**
 * Gráficas de tendencia: la curva prevista completa en tono claro y, encima, lo
 * ya transcurrido en trazo fuerte hasta el instante actual (`live`).
 */
const TrendCharts = memo(function TrendCharts({ data, durationMin, live, pump }) {
  const rows = useMemo(() => {
    const nowT = live ? live.t : -1;
    const planned = d => ({ t: d.t, target: d.target, cpPlan: d.cp, ratePlan: d.rate });
    const past = data.filter(d => d.t < nowT).map(d => ({ ...planned(d), cp: d.cp, c2: d.c2, rate: d.rate }));
    const future = data.filter(d => d.t > nowT).map(planned);
    const now = live ? [{ ...live, cpPlan: live.cp, ratePlan: live.rate }] : [];
    return [...past, ...now, ...future];
  }, [data, live]);

  const xAxis = (
    <XAxis dataKey="t" type="number" domain={[0, durationMin]} tickCount={9} stroke="#5b6b7c" tick={{ fontSize: 11 }}
      tickFormatter={v => String(Math.round(v))}
      label={{ value: "Tiempo (min)", position: "insideBottom", offset: -4, fontSize: 11, fill: "#5b6b7c" }} />
  );
  const cursor = live && <ReferenceLine x={live.t} stroke="#1d2733" strokeWidth={1} />;
  const tooltip = (
    <Tooltip
      formatter={(v, name, item) => [Number(v).toFixed(item.dataKey.startsWith("rate") ? 1 : 3), name]}
      labelFormatter={t => `t = ${Number(t).toFixed(1)} min`}
      contentStyle={{ fontSize: 12, borderRadius: 4, borderColor: "#c9d1da" }}
    />
  );
  const line = { dot: false, isAnimationActive: false, connectNulls: false };

  return (
    <section className="tci-panel">
      <h2>Tendencias</h2>
      <p className="tci-caption">Concentraciones calculadas (ng/mL) · trazo claro: previsto · trazo fuerte: transcurrido</p>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
          <CartesianGrid stroke="#e3e8ee" />
          {xAxis}
          <YAxis stroke="#5b6b7c" tick={{ fontSize: 11 }} />
          {tooltip}
          <Legend verticalAlign="top" height={24} wrapperStyle={{ fontSize: 11 }} />
          {cursor}
          <Line dataKey="target" name="Objetivo" type="stepAfter" stroke="#a0522d" strokeWidth={1.5} strokeDasharray="6 4" {...line} />
          <Line dataKey="cpPlan" name="Cp prevista" stroke="#b7c6d6" strokeWidth={2} {...line} />
          <Line dataKey="cp" name="Cp plasma" stroke="#1f3a5f" strokeWidth={2.5} {...line} />
          <Line dataKey="c2" name="C periférica" stroke="#7a8896" strokeWidth={1.5} strokeDasharray="4 3" {...line} />
        </LineChart>
      </ResponsiveContainer>

      <p className="tci-caption">Programa de bomba (mL/h)</p>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
          <CartesianGrid stroke="#e3e8ee" />
          {xAxis}
          <YAxis stroke="#5b6b7c" tick={{ fontSize: 11 }} />
          {tooltip}
          <ReferenceLine y={pump.max} stroke="#b3261e" strokeDasharray="2 3" ifOverflow="hidden" />
          <ReferenceLine y={pump.min} stroke="#b3261e" strokeDasharray="2 3" />
          {cursor}
          <Line dataKey="ratePlan" name="Tasa prevista" type="stepAfter" stroke="#b9d3c5" strokeWidth={2} {...line} />
          <Line dataKey="rate" name="Tasa mL/h" type="stepAfter" stroke="#2e6b4f" strokeWidth={2.5} {...line} />
        </LineChart>
      </ResponsiveContainer>
      <p className="tci-note">
        La Cp calculada sigue la tasa que infunde la bomba: en modo manual, cada ajuste cuenta desde que se confirma.
      </p>
    </section>
  );
});

const STEP_KIND_LABEL = {
  load: "Carga", maintain: "Mantenimiento", cri: "Infusión continua", adjust: "Ajuste",
  target: "Nuevo objetivo", stop: "Detener", resume: "Reanudar", pause: "Pausa",
};

const ScheduleTable = memo(function ScheduleTable({ steps, conc, weight, activeIdx, induction, premed, endSec }) {
  return (
    <section className="tci-panel">
      <h2>Programa de infusión</h2>
      <p className="tci-caption">
        {induction === "none" && premed
          ? `La bomba descuenta la absorción de la premedicación IM; ajustes cada ${PREMED_ADJUST_SEC / 60} min como mínimo`
          : induction === "none"
          ? "Infusión continua a la tasa de equilibrio del objetivo; solo cambia si se modifica el objetivo"
          : `Cada tasa se centra en la banda ±${HALF_BAND * 100} % de la tasa ideal; se reprograma al salir de ella`}
      </p>
      <div className="tci-scroll">
        <table className="tci-table">
          <thead>
            <tr><th>N.º</th><th>Tiempo</th><th>Acción</th><th>mL/h</th><th>µg/kg/h</th><th>Obj.</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {steps.map((step, i) => {
              const state = endSec !== null && step.sec >= endSec ? "No aplicado"
                : activeIdx < 0 || i > activeIdx ? "Pendiente"
                : i === activeIdx && endSec === null ? "En curso" : "Completado";
              return (
                <tr key={step.sec} className={[i === activeIdx && endSec === null && "is-active", step.outOfRange && "is-out", state === "No aplicado" && "is-void"].filter(Boolean).join(" ") || undefined}>
                  <td>{i === 0 ? "Inicio" : i}</td>
                  <td>{fmtClock(step.sec)}</td>
                  <td>{STEP_KIND_LABEL[step.kind]}</td>
                  <td><b>{fmt(step.rateMlH, 1)}</b></td>
                  <td>{fmt((step.rateMlH * conc) / weight, 2)}</td>
                  <td>{fmt(step.targetCp, 2)}</td>
                  <td>{state}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
});

function EventPanel({ events, canLog, onMilestone, onExport }) {
  const [milestone, setMilestone] = useState("");
  const submit = e => {
    e.preventDefault();
    const text = milestone.trim();
    if (!text) return;
    onMilestone(text);
    setMilestone("");
  };

  return (
    <section className="tci-panel">
      <div className="tci-panel__head">
        <h2>Registro del caso</h2>
        <button type="button" className="tci-btn tci-btn--small" onClick={onExport} disabled={events.length === 0}>
          Exportar CSV
        </button>
      </div>
      <form className="tci-inline tci-milestone" onSubmit={submit}>
        <input
          list="milestone-presets"
          value={milestone}
          onChange={e => setMilestone(e.target.value)}
          placeholder="Hito (p. ej. Incisión)"
          disabled={!canLog}
          aria-label="Hito"
        />
        <datalist id="milestone-presets">
          {MILESTONE_PRESETS.map(m => <option key={m} value={m} />)}
        </datalist>
        <button type="submit" className="tci-btn tci-btn--small" disabled={!canLog || !milestone.trim()}>Registrar</button>
      </form>
      <EventTable events={events} />
    </section>
  );
}

const EventTable = memo(function EventTable({ events }) {
  if (events.length === 0) {
    return <p className="tci-note">Sin eventos. Los ajustes, cambios de objetivo e hitos se registrarán aquí.</p>;
  }
  return (
    <div className="tci-scroll">
      <table className="tci-table">
        <thead><tr><th>Tiempo</th><th>Tipo</th><th>Evento</th></tr></thead>
        <tbody>
          {events.map(ev => (
            <tr key={ev.id} className={`is-${ev.kind}`}>
              <td>{fmtClock(ev.sec)}</td>
              <td>{EVENT_KIND_LABEL[ev.kind]}</td>
              <td>{ev.text}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});

const SafetyPanel = memo(function SafetyPanel({ plan, review }) {
  return (
    <section className="tci-panel">
      <h2>Verificación y precauciones</h2>
      <ul className="tci-list">
        <li className={plan.pumpOk ? "is-ok" : "is-error"}>
          Mantenimiento ({plan.pump.min}–{plan.pump.max} mL/h): {plan.pumpOk ? "conforme" : "NO conforme"}
          {" "}· inicial {fmt(plan.startMlH, 1)} mL/h, final {fmt(plan.endMlH, 1)} mL/h
        </li>
        {plan.induction === "load" && (
          <li className={plan.loadOk ? "is-ok" : "is-error"}>
            Carga en {LOAD_SEC / 60} min ({plan.pump.min}–{plan.pump.max} mL/h): {plan.loadOk ? "conforme" : "NO conforme"} · {fmt(plan.loadMlH, 1)} mL/h
          </li>
        )}
        {plan.induction === "load"
          ? <li>Desviación máxima de Cp por ajustes discretos: {fmt(plan.maxDeviation * 100, 1)} %</li>
          : <li>Sin carga: 90 % del objetivo {plan.time90Sec === null ? "no se alcanza en la duración programada" : `a las ${fmtClock(plan.time90Sec)}`}</li>}
        {plan.warnings.map(w => <li key={w} className="is-error">{w}</li>)}
        {review.hard.map(w => <li key={w} className="is-error">Límite duro · {w}</li>)}
        {review.soft.map(w => <li key={w} className="is-warn">Límite blando · {w}</li>)}
        {!review.hard.length && !review.soft.length && <li className="is-ok">Límites de seguridad: dentro de rango</li>}
      </ul>
      <details className="tci-details">
        <summary>Límites de seguridad programados</summary>
        <table className="tci-table tci-table--compact">
          <thead><tr><th>Parámetro</th><th>Blando (confirmar)</th><th>Duro (bloqueo)</th></tr></thead>
          <tbody>
            <tr><td>Cp objetivo</td><td>&gt; {SAFETY.targetCp.soft} ng/mL</td><td>&gt; {SAFETY.targetCp.hard} ng/mL</td></tr>
            <tr><td>Dosis por carga</td><td>&gt; {SAFETY.loadUgKg.soft} µg/kg</td><td>vía tasa máxima</td></tr>
            <tr><td>Tasa instantánea</td><td>&gt; {SAFETY.rateUgKgH.soft} µg/kg/h</td><td>{SAFETY.rateUgKgH.hard} µg/kg/h (la carga se alarga)</td></tr>
            <tr><td>Dosis en 60 min</td><td>&gt; {SAFETY.hourUgKg.soft} µg/kg</td><td>&gt; {SAFETY.hourUgKg.hard} µg/kg</td></tr>
            <tr><td>Subida de objetivo</td><td>&gt; +{SAFETY.targetStep.soft} ng/mL</td><td>no durante una carga</td></tr>
            <tr><td>Duración</td><td>&gt; {SAFETY.durationMin.soft} min</td><td>&gt; {LIMITS.duration.max} min</td></tr>
            <tr><td>Premedicación IM</td><td>&gt; {SAFETY.premedUgKg.soft} µg/kg</td><td>&gt; {LIMITS.premed.max} µg/kg</td></tr>
            <tr><td>Peso</td><td>fuera de {MODEL_WEIGHT_KG.min}–{MODEL_WEIGHT_KG.max} kg</td><td>fuera de {LIMITS.weight.min}–{LIMITS.weight.max} kg</td></tr>
          </tbody>
        </table>
        <p className="tci-note">Propuesta anclada al equilibrio del modelo publicado (Cp = dosis horaria / 1,16 L/h/kg), igual con los dos modelos: pendiente de validación clínica.</p>
      </details>
      <ul className="tci-list tci-list--muted">
        {plan.pk.linear ? (
          <li>
            Validación externa del modelo publicado: con objetivos ≤ {EXTERNAL_BIAS_NOTE_MAX_CP} ng/mL la concentración medida en otros
            estudios fue menor que la predicha, ≈ 20 % en perros despiertos y ≈ 50 % en perros anestesiados (Pascoe 2006, Lin 2008).
            En anestesia use el modelo corregido.
          </li>
        ) : (
          <li>
            Modelo corregido para perros anestesiados: calibrado con 2 estudios (Pascoe 2006, Lin 2008; error mediano 23 %) y comprobado
            en 5 estudios con perros despiertos (error mediano 18 %). En esos estudios, durante la anestesia la Cp real quedó por debajo de
            la predicha la primera hora y algo por encima después. En un perro concreto puede ser un 30–50 % mayor o menor: ajuste el
            objetivo según la respuesta clínica y vigile FC y PA, sobre todo con objetivos altos.
          </li>
        )}
        <li>Bradicardia y bloqueo AV: monitorización ECG obligatoria.</li>
        {plan.induction === "load" && (
          <li>La carga en {LOAD_SEC / 60} min atenúa, pero no elimina, la hipertensión transitoria y la bradicardia refleja: vigile FC y PA durante la carga.</li>
        )}
        <li>Modelo derivado en 8 Beagles adultos sanos tras un bolo único de 10 µg/kg (muestreo hasta 120 min): las infusiones prolongadas, otros pesos, razas, edades o patologías son extrapolaciones.</li>
        <li>Monitorización mínima: FC, PAM, SpO₂ y ECG cada 5 min.</li>
        <li>Simulador educativo: no sustituye el juicio clínico del especialista.</li>
      </ul>
    </section>
  );
});

// ═══════════════════════════════════════════════════════════════════════════════
// ESTILOS
// ═══════════════════════════════════════════════════════════════════════════════
const CSS = `
.tci {
  --bg: #eef1f4; --panel: #ffffff; --border: #c9d1da; --text: #1d2733; --muted: #5b6b7c;
  --accent: #1f3a5f; --ok: #2e6b4f; --warn: #9a6700; --error: #b3261e;
  --lcd: #0f1c2b; --lcd-text: #e8eef5; --lcd-muted: #8fa3b8;
  min-height: 100vh; background: var(--bg); color: var(--text);
  font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 13px;
  padding: 16px; box-sizing: border-box;
}
.tci *, .tci *::before, .tci *::after { box-sizing: border-box; }
.tci-header {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
  background: var(--accent); color: #fff; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;
}
.tci-header h1 { margin: 0; font-size: 17px; font-weight: 600; letter-spacing: .2px; }
.tci-header p { margin: 2px 0 0; font-size: 11px; opacity: .8; }
.tci-header .tci-author { font-size: 12px; font-weight: 600; opacity: 1; }
.tci-status { font-size: 11px; font-weight: 700; letter-spacing: 1px; padding: 5px 10px; border-radius: 3px; background: #fff; }
.tci-status--idle { color: var(--muted); }
.tci-status--running { color: #fff; background: var(--ok); }
.tci-status--paused { color: #fff; background: var(--warn); }
.tci-status--finished { color: var(--accent); }
.tci-status--washout { color: #fff; background: #6b4fa0; }
.tci-btn--danger { background: var(--error); border-color: var(--error); color: #fff; }
.tci-ack--end { margin-top: 10px; }
.tci-table tr.is-void td { color: var(--muted); text-decoration: line-through; }
.tci-layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 16px; }
.tci-column { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.tci-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.tci-panel { background: var(--panel); border: 1px solid var(--border); border-radius: 4px; padding: 14px 16px; }
.tci-panel h2 {
  margin: 0 0 12px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .8px;
  color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 8px;
}
.tci fieldset { border: 0; margin: 0; padding: 0; }
.tci-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.tci-field label { font-size: 12px; font-weight: 600; }
.tci-field label span { font-weight: 400; color: var(--muted); }
.tci input, .tci select {
  font: inherit; color: var(--text); background: #fff; border: 1px solid var(--border); border-radius: 3px;
  padding: 6px 8px; width: 100%;
}
.tci input:focus, .tci select:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
.tci input:disabled, .tci select:disabled { background: #f3f5f7; color: var(--muted); }
.tci-field__error { color: var(--error); font-size: 11px; }
.tci-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.tci-note { margin: 8px 0 0; font-size: 11px; color: var(--muted); line-height: 1.5; }
.tci-note--warn { color: var(--warn); }
.tci-note--error { color: var(--error); font-weight: 600; }
.tci-list .is-warn { color: var(--warn); }
.tci-ack { margin-top: 10px; padding: 10px 12px; border: 1px solid var(--warn); background: #fff8e6; color: #5c3d00; border-radius: 4px; font-size: 12px; }
.tci-ack ul { margin: 6px 0; padding-left: 18px; }
.tci-note--field { margin: -4px 0 12px; }
.tci-caption { margin: 4px 0 6px; font-size: 11px; color: var(--muted); }
.tci-btn {
  font: inherit; font-weight: 600; font-size: 12px; letter-spacing: .4px; text-transform: uppercase;
  padding: 8px 16px; border-radius: 3px; border: 1px solid var(--border); background: #fff; color: var(--text); cursor: pointer;
}
.tci-btn:hover:not(:disabled) { background: #f3f5f7; }
.tci-btn:disabled { opacity: .45; cursor: not-allowed; }
.tci-btn--primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.tci-btn--primary:hover:not(:disabled) { background: #2a4d7a; }
.tci-btn--alarm { background: #fff; border-color: #fff; color: var(--error); }
.tci-btn--block { width: 100%; margin-top: 4px; }
.tci-monitor { background: var(--lcd); border-color: var(--lcd); color: var(--lcd-text); }
.tci-alarm {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
  background: var(--error); color: #fff; padding: 10px 12px; border-radius: 3px; margin-bottom: 12px;
}
.tci-alarm div { display: flex; flex-direction: column; gap: 2px; }
.tci-alarm strong { font-size: 12px; letter-spacing: .6px; }
.tci-alarm__warn { font-weight: 700; }
.tci-prealert {
  display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap;
  background: #f2c46d; color: #1d2733; padding: 8px 12px; border-radius: 3px; margin-bottom: 12px; font-size: 12px;
}
.tci-prealert strong { letter-spacing: .6px; }
.tci-displays { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: #243447; border: 1px solid #243447; }
.tci-display { background: var(--lcd); padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.tci-display__label { font-size: 10px; text-transform: uppercase; letter-spacing: .8px; color: var(--lcd-muted); }
.tci-display__value {
  font-family: "Roboto Mono", Consolas, "Courier New", monospace; font-variant-numeric: tabular-nums;
  font-size: 22px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.tci-display--primary .tci-display__value { font-size: 28px; color: #9fd3ff; }
.tci-display__unit { font-size: 10px; color: var(--lcd-muted); }
.tci-progress { height: 4px; background: #243447; margin: 12px 0; }
.tci-progress div { height: 100%; background: #9fd3ff; }
.tci-controls { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.tci-controls__group { display: flex; gap: 8px; }
.tci-controls__meta { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--lcd-muted); }
.tci-controls__meta b { color: var(--lcd-text); font-family: "Roboto Mono", Consolas, monospace; }
.tci-inline { display: flex; align-items: center; gap: 6px; }
.tci-inline select { width: auto; padding: 3px 6px; }
.tci-inline input:not([type="checkbox"]) { width: 90px; padding: 4px 6px; }
.tci-inline input[type="checkbox"] { width: auto; }
.tci-controls--secondary { margin-top: 10px; padding-top: 10px; border-top: 1px solid #243447; font-size: 12px; color: var(--lcd-muted); }
.tci-btn--small { padding: 5px 10px; font-size: 11px; }
.tci-monitor .tci-btn--small:disabled { opacity: .35; }
.tci-panel__head { display: flex; justify-content: space-between; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); margin-bottom: 10px; padding-bottom: 6px; }
.tci-panel__head h2 { border: 0; margin: 0; padding: 0; }
.tci-milestone { margin-bottom: 10px; }
.tci-milestone input { flex: 1; width: auto !important; }
.tci-monitor .tci-note { color: #f2c46d; }
.tci-dl { margin: 0; }
.tci-dl div { display: grid; grid-template-columns: 120px 1fr; gap: 8px; padding: 5px 0; border-bottom: 1px solid #edf0f3; }
.tci-dl dt { color: var(--muted); }
.tci-dl dd { margin: 0; font-weight: 600; }
.tci-details { margin-top: 10px; }
.tci-details summary { cursor: pointer; font-size: 12px; color: var(--accent); font-weight: 600; }
.tci-scroll { max-height: 320px; overflow: auto; }
.tci-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.tci-table th {
  position: sticky; top: 0; background: #f3f5f7; text-align: left; font-size: 11px; font-weight: 600;
  color: var(--muted); padding: 6px 8px; border-bottom: 1px solid var(--border);
}
.tci-table td { padding: 6px 8px; border-bottom: 1px solid #edf0f3; }
.tci-table--compact th { position: static; background: none; border-bottom: 1px solid #edf0f3; }
.tci-table tr.is-active td { background: #e3edf8; font-weight: 600; }
.tci-table tr.is-alarm td:last-child { color: var(--error); }
.tci-table tr.is-ok td:last-child, .tci-table tr.is-auto td:last-child { color: var(--ok); }
.tci-table tr.is-target td:last-child { color: var(--accent); font-weight: 600; }
.tci-table tr.is-milestone td:last-child { color: #6b4fa0; font-weight: 600; }
.tci-table tr.is-out td { color: var(--error); }
.tci-list { margin: 0 0 10px; padding-left: 18px; line-height: 1.7; }
.tci-list .is-ok { color: var(--ok); }
.tci-list .is-error { color: var(--error); font-weight: 600; }
.tci-list--muted { color: var(--muted); margin-bottom: 0; }
.tci-footer { margin-top: 16px; text-align: center; font-size: 11px; color: var(--muted); line-height: 1.7; }
@media (max-width: 960px) {
  .tci-layout, .tci-grid-2 { grid-template-columns: minmax(0, 1fr); }   /* sin minmax, una tabla ancha desborda la pantalla */
}
@media (max-width: 600px) {
  .tci { padding: 12px; }
  .tci-displays { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tci-display--primary .tci-display__value { font-size: 24px; }
}
`;
