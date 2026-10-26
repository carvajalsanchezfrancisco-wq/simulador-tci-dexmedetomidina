"""Fase 0 · Implementación de referencia independiente.

No reutiliza código del simulador: toma las constantes directamente de
Levionnois et al. 2022 (Tabla 2) y resuelve el modelo bicompartimental de forma
exacta (exponencial de matriz, entrada constante por tramos de 1 s). Con esa
solución comprueba, escenario a escenario, los requisitos del motor TCI.

Modelo «anestesiado» (v1.2.0): mismo modelo con aclaramiento dependiente de la Cp,
Cl(C) = Cl∞ + (Cl0 − Cl∞)·C50/(C50 + C), con Cl0 y C50 de la calibración de la Fase 1
(validacion_fase1/modelo_corregido.py). No tiene solución analítica: se resuelve con
un integrador de alta precisión (Dormand-Prince de orden 8, tolerancia relativa 1e-10)
entre cada cambio de tasa de la bomba.

Uso: python3 motor/referencia.py
"""
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "resultados"
data = json.loads((RES / "motor_casos.json").read_text())

# ── Constantes publicadas (Tabla 2, análisis poblacional final) ─────────────────
PUB = {"V1": 1.03, "V2": 0.41, "Cl1": 1.16, "Cl2": 1.87,          # L/kg y L/h/kg
       "t12_h": 0.92, "Vss": 1.45, "AUC10": 8.65, "MRT_h": 1.25}  # parámetros secundarios publicados
NCA_CMAX = {"mediana": 9.7, "q1": 7.2, "q3": 10.4}                  # ng/mL tras 10 µg/kg IV (NCA)
# Modelo corregido: parámetros de la calibración de la Fase 1 (Pascoe 2006 + Lin 2008, redondeados a 2 decimales)
CORR = {"Cl0": 3.15, "C50": 0.92}                                  # L/h/kg y ng/mL; Cl∞ = PUB["Cl1"]
CAL_JSON = ROOT.parent / "validacion_fase1" / "resultados" / "modelo_corregido.json"
# Supuestos de la vía IM (no publicados): se verifica que el programa los implemente bien
IM = data["imPremed"]
SAFETY = data["safety"]

# Tolerancias de aceptación
TOL_NUM = 0.005      # error numérico máx. relativo al objetivo
TOL_LOAD = 0.01      # Cp al final de la carga
TOL_OVER = 0.01      # sobreimpulso permitido durante la carga
TOL_MAINT = 0.05     # mantenimiento
TOL_PUB = 0.02       # parámetros secundarios frente a lo publicado


def system(weight, ka):
    V1, V2 = PUB["V1"] * weight, PUB["V2"] * weight
    Cl1, Cl2 = PUB["Cl1"] * weight / 60, PUB["Cl2"] * weight / 60      # L/min
    k10, k12, k21 = Cl1 / V1, Cl2 / V1, Cl2 / V2
    A = np.array([[-(k10 + k12), k21, ka], [k12, -k21, 0.0], [0.0, 0.0, -ka]])
    return V1, V2, Cl1, A


def discretize(A, dt_min):
    """x(t+dt) = E x + g·R, con R en µg/min constante en el intervalo (exacto)."""
    n = A.shape[0]
    big = np.zeros((n + 1, n + 1))
    big[:n, :n] = A
    big[0, n] = 1.0                       # la infusión entra al compartimento central
    Eb = expm(big * dt_min)
    return Eb[:n, :n], Eb[:n, n]


def cl_kgh(model, c):
    """Aclaramiento (L/h/kg) con la Cp c (ng/mL)."""
    if model == "publicado":
        return PUB["Cl1"]
    return PUB["Cl1"] + (CORR["Cl0"] - PUB["Cl1"]) * CORR["C50"] / (CORR["C50"] + max(c, 0.0))


def model_of(cfg):
    return cfg.get("model") or "anestesiado"


def rate_series(rate_changes, total):
    r = np.zeros(total + 1)
    for (s, v), nxt in zip(rate_changes, rate_changes[1:] + [[total + 1, None]]):
        r[s:nxt[0]] = v
    return r


def simulate_nl(case):
    """Modelo no lineal: Cp (ng/mL), A1 y A2 en cada segundo, integrando entre cambios de tasa."""
    cfg, plan = case["config"], case["plan"]
    W, conc, total = cfg["weight"], cfg["conc"], plan["totalSec"]
    model = model_of(cfg)
    V1, V2 = PUB["V1"] * W, PUB["V2"] * W
    Cl2 = PUB["Cl2"] * W / 60
    ka = math.log(2) / IM["absHalfMin"]

    def rhs(t, x, R):
        a1, a2, ad = x
        c = a1 / V1
        cl = cl_kgh(model, c) * W / 60
        return [R + ka * ad - cl * c - Cl2 * c + Cl2 * a2 / V2, Cl2 * c - Cl2 * a2 / V2, -ka * ad]

    kw = dict(method="DOP853", rtol=1e-10, atol=1e-12)
    x = np.zeros(3)
    if cfg["induction"] == "none" and cfg.get("premedUgKg", 0) > 0:     # inyección IM 10 min antes de la bomba
        x[2] = cfg["premedUgKg"] * W * IM["F"]
        x = solve_ivp(rhs, (0, IM["delayMin"]), x, args=(0.0,), **kw).y[:, -1]
    rate = rate_series(plan["rateChanges"], total)
    bounds = [s for s, _ in plan["rateChanges"] if 0 < s <= total] + [total]
    a1 = np.empty(total + 1); a2 = np.empty(total + 1)
    s0 = 0
    for s1 in bounds:
        if s1 <= s0:
            continue
        R = rate[s0] * conc / 60
        sol = solve_ivp(rhs, (s0 / 60, s1 / 60), x, args=(R,), t_eval=np.arange(s0, s1 + 1) / 60, **kw)
        a1[s0:s1 + 1] = sol.y[0]; a2[s0:s1 + 1] = sol.y[1]
        x = sol.y[:, -1]
        s0 = s1
    if s0 == 0:
        a1[0], a2[0] = x[0], x[1]
    return a1 / V1, rate, V1, a1, a2


def simulate(case):
    """Cp exacta (ng/mL) en cada segundo para la tasa que infunde realmente la bomba."""
    if model_of(case["config"]) != "publicado":
        cp, rate, V1, a1, a2 = simulate_nl(case)
        case["_estado"] = (a1, a2)
        return cp, rate, V1, None
    cfg, plan = case["config"], case["plan"]
    W, conc, total = cfg["weight"], cfg["conc"], plan["totalSec"]
    ka = math.log(2) / IM["absHalfMin"]
    V1, V2, Cl1, A = system(W, ka)
    E, g = discretize(A, 1 / 60)
    E = E.tolist(); g = g.tolist()
    rate = rate_series(plan["rateChanges"], total)
    a1 = a2 = 0.0
    ad = cfg.get("premedUgKg", 0) * W * IM["F"] if cfg["induction"] == "none" else 0.0
    if ad > 0:                                          # inyección IM 10 min antes de la bomba
        Ep = expm(A * IM["delayMin"])
        a1, a2, ad = (Ep @ np.array([a1, a2, ad])).tolist()
    cp = np.empty(total + 1)
    ug = (rate * conc / 60).tolist()
    (e00, e01, e02), (e10, e11, e12), (e20, e21, e22) = E
    g0, g1, g2 = g
    for s in range(total + 1):
        cp[s] = a1 / V1
        R = ug[s]
        a1, a2, ad = (e00 * a1 + e01 * a2 + e02 * ad + g0 * R,
                      e10 * a1 + e11 * a2 + e12 * ad + g1 * R,
                      e20 * a1 + e21 * a2 + e22 * ad + g2 * R)
    return cp, rate, V1, Cl1


def exact_load_rate_mlh(cp_state, case, sec, target, load_min):
    """Tasa constante (mL/h) que lleva la Cp exacta al objetivo en load_min, desde el estado en `sec`."""
    cfg = case["config"]
    W, conc = cfg["weight"], cfg["conc"]
    if model_of(cfg) != "publicado":
        model = model_of(cfg)
        V1n, V2n, Cl2 = PUB["V1"] * W, PUB["V2"] * W, PUB["Cl2"] * W / 60

        def a1_end(R):
            def rhs(t, x):
                c = x[0] / V1n
                return [R - cl_kgh(model, c) * W / 60 * c - Cl2 * c + Cl2 * x[1] / V2n, Cl2 * c - Cl2 * x[1] / V2n]
            return solve_ivp(rhs, (0, load_min), list(cp_state), method="DOP853", rtol=1e-10, atol=1e-12).y[0, -1]
        hi = 10 * target * V1n / load_min
        while a1_end(hi) < target * V1n:
            hi *= 2
        R = brentq(lambda r: a1_end(r) - target * V1n, 0.0, hi, xtol=1e-10, rtol=1e-12)
        return R * 60 / conc
    V1, V2, Cl1, A = system(W, 1.0)
    A2 = A[:2, :2]
    E, g = discretize(A2, load_min)
    a1, a2 = cp_state
    free = (E @ np.array([a1, a2]))[0]
    per_unit = g[0]
    R = (target * V1 - free) / per_unit
    return R * 60 / conc


def state_at(case, sec):
    """Estado exacto (A1, A2) en `sec` integrando el programa real (sin depósito IM)."""
    if "_estado" in case:
        return np.array([case["_estado"][0][sec], case["_estado"][1][sec]])
    cfg, plan = case["config"], case["plan"]
    W, conc = cfg["weight"], cfg["conc"]
    V1, V2, Cl1, A = system(W, 1.0)
    A2 = A[:2, :2]
    E, g = discretize(A2, 1 / 60)
    rate = rate_series(plan["rateChanges"], plan["totalSec"])
    x = np.zeros(2)
    for s in range(sec):
        x = E @ x + g[:2] * rate[s] * conc / 60
    return x


# ── PK-01 / PK-02 / PK-03 ──────────────────────────────────────────────────────
req = {}
models = data["models"]
paper = {"V1": PUB["V1"], "V2": PUB["V2"], "Cl2": PUB["Cl2"], "clInf": PUB["Cl1"]}
pk01 = all(abs(models[m][k] - v) < 1e-12 for m in ("publicado", "anestesiado") for k, v in paper.items())
pk01 &= models["publicado"]["cl0"] == PUB["Cl1"]
req["PK-01"] = {"pass": pk01, "descripcion": "Constantes de Levionnois 2022 (V1, V2, Cl2 y Cl1/Cl∞) idénticas en los dos modelos",
                "detalle": {m: {k: models[m][k] for k in ("V1", "V2", "Cl2", "clInf", "cl0", "c50")} for m in models}}

# PK-04: modelo corregido = calibración de la Fase 1, y función de aclaramiento correcta
cal = json.loads(CAL_JSON.read_text())["simulador"] if CAL_JSON.exists() else None
par_ok = models["anestesiado"]["cl0"] == CORR["Cl0"] and models["anestesiado"]["c50"] == CORR["C50"]
cal_ok = cal is None or (cal["Cl_0_Lhkg"] == CORR["Cl0"] and cal["C50_ngml"] == CORR["C50"])
cl_err = max(abs(r["anestesiado"] - cl_kgh("anestesiado", r["c"])) / cl_kgh("anestesiado", r["c"]) for r in data["clTable"])
pub_err = max(abs(r["publicado"] - PUB["Cl1"]) for r in data["clTable"])
limits = abs(cl_kgh("anestesiado", 0) - CORR["Cl0"]) < 1e-12 and abs(cl_kgh("anestesiado", 1e9) - PUB["Cl1"]) < 1e-6
req["PK-04"] = {"pass": par_ok and cal_ok and cl_err < 1e-12 and pub_err == 0 and limits and data["defaultModel"] == "anestesiado",
                "descripcion": "Modelo corregido: Cl0 y C50 = calibración de la Fase 1; Cl(C) igual a la fórmula; por defecto",
                "detalle": {"Cl0": models["anestesiado"]["cl0"], "C50": models["anestesiado"]["c50"],
                            "calibracion_fase1": cal, "error_rel_max_Cl": cl_err, "modelo_por_defecto": data["defaultModel"],
                            "tabla": [{"c": r["c"], "Cl_simulador": r["anestesiado"], "Cl_referencia": cl_kgh("anestesiado", r["c"])}
                                      for r in data["clTable"]]}}

# REG-01: con el modelo publicado, la v1.2.0 calcula exactamente lo mismo que la versión anterior
reg = data["regression"]
req["REG-01"] = {"pass": reg["n"] > 0 and reg["identicos"] == reg["n"], "n": reg["n"],
                 "descripcion": f"Modelo publicado: programa, Cp, avisos y configuración idénticos a la v{reg['anterior']}",
                 "detalle": {"identicos": reg["identicos"], "diferencias": reg["diferencias"][:20]}}
reg2 = data.get("regression120")
if reg2:
    req["REG-02"] = {"pass": reg2["n"] > 0 and reg2["identicos"] == reg2["n"], "n": reg2["n"],
                     "descripcion": f"Los dos modelos: programa, Cp, avisos y configuración idénticos a la v{reg2['anterior']}",
                     "detalle": {"identicos": reg2["identicos"], "diferencias": reg2["diferencias"][:20]}}

pk1 = data["pk1kg"]
V1, V2, Cl1, A = system(1.0, 1.0)
eig = np.sort(-np.linalg.eigvals(A[:2, :2]).real)[::-1]
beta = pk1["beta"]
second = {
    "t12_h": math.log(2) / beta / 60,
    "Vss": pk1["V1"] + pk1["V2"],
    "AUC10": 10 / (pk1["Cl1"] * 60),
    "MRT_h": (pk1["V1"] + pk1["V2"]) / (pk1["Cl1"] * 60),
}
pk02_rows = [{"parametro": k, "programa": round(v, 4), "publicado": PUB[k],
              "diferencia_pct": round(100 * (v - PUB[k]) / PUB[k], 2)} for k, v in second.items()]
micro_ok = (abs(pk1["k10"] - Cl1 / V1) < 1e-12 and abs(pk1["alpha"] - eig[0]) < 1e-9 and abs(pk1["beta"] - eig[1]) < 1e-9)
req["PK-02"] = {"pass": micro_ok and all(abs(r["diferencia_pct"]) <= 100 * TOL_PUB for r in pk02_rows),
                "detalle": pk02_rows, "microconstantes_identicas": micro_ok}

# Experimento del artículo: 10 µg/kg en 60 s, Cp a los 2 min (primera muestra)
E1, g1 = discretize(A[:2, :2], 1.0)
x = E1 @ np.zeros(2) + g1[:2] * 10.0      # 10 µg (por kg) en 1 min
E2, _ = discretize(A[:2, :2], 1.0)
cmax2 = (E2 @ x)[0] / V1
req["PK-03"] = {"pass": NCA_CMAX["q1"] <= cmax2 <= NCA_CMAX["q3"], "informativo": True,
                "detalle": {"cp_predicha_2min": round(cmax2, 2), "cmax_NCA_mediana": NCA_CMAX["mediana"],
                            "IQR": [NCA_CMAX["q1"], NCA_CMAX["q3"]]}}

# ── Comprobación de escenarios ────────────────────────────────────────────────
rows, figs = [], {}
agg = {k: [] for k in ["NUM", "RATE", "VOL", "LOAD_END", "LOAD_RATE", "OVERSHOOT", "MAINT", "DOWN", "PAUSE", "MANUAL",
                        "NONE_CRI", "PREMED_HOLD", "PREMED_COMP", "PUMP_LIMIT", "WASH"]}


def record(key, case_id, ok, value=None, note=""):
    agg[key].append({"caso": case_id, "pass": bool(ok), "valor": value, "nota": note})


for case in data["cases"]:
    cid, cfg, plan = case["id"], case["config"], case["plan"]
    W, conc, total = cfg["weight"], cfg["conc"], plan["totalSec"]
    cp, rate, V1c, _ = simulate(case)
    Cl1c = cl_kgh(model_of(cfg), cfg["targetCp"]) * W / 60      # L/min con la Cp objetivo inicial
    tg = rate_series(plan["targetChanges"], total)
    maxT = float(tg.max())

    # Exactitud numérica del motor (Euler 1 s) frente a la solución exacta
    eng = np.array(plan["cp10"])
    ex = cp[::10][: len(eng)]
    scale = max(maxT, float(cp.max()))                 # escala de concentración del caso
    num_err = float(np.max(np.abs(eng - ex)) / scale)
    record("NUM", cid, num_err <= TOL_NUM, num_err)

    # Tasas: resolución 0,1 mL/h, máximo de la bomba y límite duro de dosis
    dose_max = SAFETY["rateUgKgH"]["hard"] * W / conc
    rates = [st["rateMlH"] for st in plan["steps"]]
    grid_ok = all(abs(r * 10 - round(r * 10)) < 1e-6 for r in rates)
    max_ok = all(r <= cfg["pumpMaxMlH"] + 1e-9 and r <= dose_max + 1e-9 for r in rates)
    record("RATE", cid, grid_ok and max_ok, max(rates), "" if grid_ok else "tasa fuera de la resolución de 0,1 mL/h")

    # Volumen administrado = integral de la tasa
    vol_ref = float(rate[:total].sum() / 3600)
    vol_err = abs(plan["deliveredEndMl"] - vol_ref)
    record("VOL", cid, vol_err <= max(1e-6, 1e-3 * vol_ref), vol_err)

    steps = plan["steps"]
    seg_bounds = sorted({0, total, *[c["sec"] for c in case["changes"]], *[s for s, _ in plan["targetChanges"]]})
    max_maint = 0.0
    for i, st in enumerate(steps):
        seg_end = next((b for b in seg_bounds if b > st["sec"]), total)
        if st["kind"] == "load":
            end = min(st["sec"] + st["loadSec"], total)
            over = float(cp[st["sec"]:end + 1].max() / st["targetCp"] - 1)
            record("OVERSHOOT", cid, over <= TOL_OVER, over)
            if end < seg_end and not st["unreached"]:
                e = float(abs(cp[end] / st["targetCp"] - 1))
                record("LOAD_END", cid, e <= TOL_LOAD, e, "carga limitada" if (st["limited"] or st["doseLimited"]) else "")
            if not (st["limited"] or st["doseLimited"]) and st["loadSec"] == data["loadSec"] and case["timing"] is None:
                x0 = state_at(case, st["sec"]) if st["sec"] > 0 else np.zeros(2)
                ref = exact_load_rate_mlh(x0, case, st["sec"], st["targetCp"], st["loadSec"] / 60)
                d = abs(st["rateMlH"] - ref)
                record("LOAD_RATE", cid, d <= 0.1 + 1e-9, d, f"programa {st['rateMlH']} · exacta {ref:.3f} mL/h")
        if st["kind"] in ("maintain", "resume") and cfg["induction"] == "load" and case["timing"] is None:
            # mantenimiento: desde el inicio de este paso hasta el final del tramo
            seg = cp[st["sec"]:seg_end + 1] / st["targetCp"] - 1
            dev = float(np.max(np.abs(seg)))
            max_maint = max(max_maint, dev)
            record("MAINT" if st["kind"] == "maintain" else "DOWN", cid, dev <= TOL_MAINT, dev)
        if st["kind"] == "stop":
            nxt = steps[i + 1]["sec"] if i + 1 < len(steps) else total
            zero = bool(np.all(rate[st["sec"]:nxt] == 0))
            above = bool(np.all(cp[st["sec"]:nxt] >= st["targetCp"] * (1 - TOL_LOAD)))
            record("DOWN", cid, zero and above, None, "bomba detenida mientras la Cp baja al objetivo")

    if case["group"] == "G4":
        p = case["pause"]
        zero = bool(np.all(rate[p["from"]:p["to"]] == 0))
        record("PAUSE", cid, zero, float(cp[p["to"]] / cp[p["from"]]), "tasa 0 durante la pausa; valor = Cp fin/inicio")

    if case["group"] == "G5":
        delay = case["delaySec"]
        ok = True
        base = case["baseSteps"]
        for (s, r), (_, rprev) in zip(base[1:], base[:-1]):
            if delay > 0 and s + delay - 1 <= total and rate[s + delay - 1] != rprev:
                ok = False
            if s + delay <= total and rate[s + delay] != r:
                ok = False
        dev = float(np.max(np.abs(cp[600:] / 2.0 - 1)))
        record("MANUAL", cid, ok, dev, "la Cp sigue la tasa realmente confirmada; valor = desviación máx. resultante")

    if cfg["induction"] == "none":
        tgt = cfg["targetCp"]
        if cfg.get("premedUgKg", 0) == 0:
            exp_rate = round(tgt * Cl1c * 60 / conc * 10) / 10
            ok = len(steps) == 1 and abs(steps[0]["rateMlH"] - exp_rate) < 1e-9 and cp.max() <= tgt * 1.01
            record("NONE_CRI", cid, ok, float(cp.max() / tgt), f"tasa {steps[0]['rateMlH']} · esperada {exp_rate} mL/h")
        else:
            first_on0 = next((s for s, r in plan["rateChanges"] if r > 0), None)
            infusing_above = first_on0 is not None and cp[first_on0] > tgt * (1 + TOL_LOAD)
            if cp[0] > tgt * 1.01 or abs(cp[0] / tgt - 1) <= 0.01:
                first_on = next((s for s, r in plan["rateChanges"] if r > 0), None)
                dev = float(np.max(np.abs(cp[first_on:] / tgt - 1))) if first_on is not None else 0.0
                record("PREMED_HOLD", cid, (not infusing_above) and dev <= TOL_MAINT, dev,
                       "la bomba no arranca con Cp > objetivo + 1 %; luego mantenimiento ±5 %")
            else:
                record("PREMED_COMP", cid, cp.max() <= tgt * 1.05, float(cp.max() / tgt), "sin sobreimpulso por la bomba")

    if case["group"] == "G6":
        lim = [st for st in steps if st["limited"] or st["doseLimited"]]
        extended = all(st["loadSec"] > data["loadSec"] for st in lim if st["kind"] == "load")
        warned = (not any(st["limited"] for st in lim)) or any(("máximo de la bomba" in w) or ("carga necesitaría" in w) for w in plan["warnings"])
        record("PUMP_LIMIT", cid, bool(lim) and extended and warned, max(rates),
               "carga limitada → se alarga; aviso si la limita la bomba")

    rows.append({"caso": cid, "modelo": model_of(cfg), "grupo": case["group"], "descripcion": case["desc"], "peso_kg": W, "objetivo": cfg["targetCp"],
                 "conc_ug_ml": conc, "duracion_min": cfg["durationMin"], "pasos": len(steps),
                 "error_numerico_pct": round(100 * num_err, 4), "desv_mant_max_pct": round(100 * max_maint, 2),
                 "tasa_max_mlh": max(rates), "volumen_ml": round(plan["deliveredEndMl"], 3)})
    if cid.split("-", 1)[1] in ("G1-25kg-2ng-60min", "G3-25kg-2ng", "G4-25kg-2ng", "G2-25kg-2ng-IM5-120min", "G5-25kg-retraso120s", "G6-bomba-max10"):
        figs[cid] = {"t": (np.arange(0, total + 1, 10) / 60).tolist(), "cp_exacta": cp[::10].tolist(),
                     "cp_programa": plan["cp10"], "objetivo": tg[::10].tolist(), "tasa": rate[::10].tolist(), "desc": case["desc"]}

# ── G8 · Fin de la infusión: descenso posterior frente a la solución exacta ───
wash_rows = []
for wc in data.get("washoutCases", []):
    end = wc["endSec"]
    total = end + data["washoutMaxMin"] * 60
    rc = wc["rateChanges"]
    zero_after = rc[-1] == [end, 0]                       # el registro de tasas termina con 0 mL/h en el fin
    cp, rate, _, _ = simulate({"config": wc["config"], "plan": {"rateChanges": rc, "totalSec": total}})
    eng = np.array(wc["wash10"])
    ex = cp[end::10][: len(eng)]
    scale = max(wc["config"]["targetCp"], float(cp.max()))
    err = float(np.max(np.abs(eng - ex)) / scale)
    falls = bool(np.all(np.diff(ex[ex > 0][-50:]) <= 1e-12))   # al final del seguimiento la Cp solo baja
    ok = zero_after and bool(np.all(rate[end:] == 0)) and err <= TOL_NUM and wc["washLen"] == data["washoutMaxMin"] * 60 + 1
    record("WASH", wc["id"], ok and falls, err, wc["desc"])
    wash_rows.append({"caso": wc["id"], "descripcion": wc["desc"], "fin_s": end, "cp_fin": round(float(cp[end]), 4),
                      "cp_mas15": round(float(cp[end + 900]), 4), "cp_mas60": round(float(cp[end + 3600]), 4),
                      "error_pct": round(100 * err, 4), "pass": ok and falls})

# ── Avisos de carga, tasa y dosis horaria frente a cálculo independiente ──────
thr = []
for tc in data["thresholdCases"]:
    W, conc, total = tc["weight"], tc["conc"], tc["totalSec"]
    rate = np.zeros(total + 1)
    for st, nxt in zip(tc["steps"], tc["steps"][1:] + [{"sec": total + 1}]):
        rate[st["sec"]:nxt["sec"]] = st["rateMlH"]
    ugkg = rate * conc / W / 3600                                   # µg/kg por segundo
    load = max((st["rateMlH"] * st["loadSec"] / 3600 * conc / W for st in tc["steps"] if st["kind"] == "load"), default=0)
    max_rate = max(st["rateMlH"] for st in tc["steps"]) * conc / W
    win = min(3600, total)
    csum = np.concatenate([[0], np.cumsum(ugkg[:total])])
    hour = float(np.max(csum[win:] - csum[:-win])) if total >= win else float(csum[-1])
    soft, hard = tc["soft"], tc["hard"]
    checks = {
        "carga": (load > SAFETY["loadUgKg"]["soft"]) == any("Carga de" in w for w in soft),
        "tasa": (max_rate > SAFETY["rateUgKgH"]["soft"]) == any("Tasa máxima" in w for w in soft),
        "hora_blando": (SAFETY["hourUgKg"]["soft"] < hour <= SAFETY["hourUgKg"]["hard"]) == any("Dosis en 60 min" in w for w in soft),
        "hora_duro": (hour > SAFETY["hourUgKg"]["hard"]) == any("Dosis en 60 min" in w for w in hard),
    }
    thr.append({"caso": tc["id"], "carga_ugkg": round(load, 3), "tasa_max_ugkgh": round(max_rate, 2), "dosis_60min_ugkg": round(hour, 3),
                **checks, "pass": all(checks.values())})

# ── Resumen por requisito ─────────────────────────────────────────────────────
def summary(key, metric=None):
    items = agg[key]
    vals = [it["valor"] for it in items if isinstance(it["valor"], (int, float))]
    out = {"n": len(items), "fallos": [it for it in items if not it["pass"]], "pass": all(it["pass"] for it in items) and len(items) > 0,
           "n_por_modelo": {m: sum(it["caso"].startswith(pre) for it in items) for m, pre in (("anestesiado", "COR-"), ("publicado", "PUB-"))}}
    if vals:
        out["max"] = max(vals)
        out["mediana"] = float(np.median(vals))
    return out

REQS = {
    "TCI-NUM": ("NUM", "Exactitud numérica del motor frente a la solución exacta (≤ 0,5 % del objetivo)"),
    "TCI-01": ("LOAD_END", "Cp al final de cada carga dentro de ±1 % del objetivo"),
    "TCI-01b": ("LOAD_RATE", "Tasa de carga = tasa exacta independiente (diferencia ≤ 0,1 mL/h, resolución de la bomba)"),
    "TCI-02": ("OVERSHOOT", "Sin sobreimpulso durante la carga (Cp ≤ objetivo + 1 %)"),
    "TCI-03": ("MAINT", "Mantenimiento dentro de ±5 % del objetivo hasta el final del tramo"),
    "TCI-04": ("DOWN", "Bajada de objetivo: bomba a 0 hasta alcanzarlo; después ±5 %"),
    "TCI-05": ("PAUSE", "Pausa: tasa 0 durante la pausa y recarga al reanudar"),
    "TCI-06": ("MANUAL", "Modo manual: la Cp sigue la tasa realmente confirmada"),
    "TCI-07": ("NONE_CRI", "Sin carga ni premedicación: tasa Cp·Cl(Cp) exacta y sin sobreimpulso"),
    "TCI-08": ("PREMED_HOLD", "Premedicación IM: la bomba no arranca con Cp > objetivo; después ±5 %"),
    "TCI-09": ("PREMED_COMP", "Premedicación IM baja: la bomba complementa sin sobreimpulso"),
    "TCI-10": ("WASH", "Fin de la infusión: bomba a 0 y Cp posterior (120 min) = solución exacta (≤ 0,5 %)"),
    "BOM-01": ("RATE", "Tasas múltiplo de 0,1 mL/h, ≤ máximo de la bomba y ≤ 30 µg/kg/h"),
    "BOM-02": ("VOL", "Volumen administrado = integral de la tasa (±0,1 %)"),
    "BOM-03": ("PUMP_LIMIT", "Carga limitada por bomba o dosis: se alarga y se avisa"),
}
for rid, (key, desc) in REQS.items():
    req[rid] = {"descripcion": desc, **summary(key)}
req["SEG-05"] = {"descripcion": "Avisos de carga, tasa y dosis en 60 min coinciden con el cálculo independiente",
                 "n": len(thr), "pass": all(t["pass"] for t in thr), "fallos": [t for t in thr if not t["pass"]]}
req["SEG-DIRECTAS"] = {"descripcion": "Umbrales de límites duros/blandos, validación de entradas y CSV",
                       "n": len(data["boundary"]), "pass": all(b["pass"] for b in data["boundary"]),
                       "fallos": [b for b in data["boundary"] if not b["pass"]]}

(RES / "referencia_resultados.json").write_text(json.dumps(
    {"version": data["version"], "sha256": data["sha256"], "requisitos": req, "umbrales": thr, "fin_infusion": wash_rows,
     "boundary": data["boundary"], "n_casos": len(data["cases"]),
     "n_casos_por_modelo": {m: sum(c.get("model") == m for c in data["cases"]) for m in ("anestesiado", "publicado")}}, ensure_ascii=False, indent=1, default=float))
(RES / "figuras_datos.json").write_text(json.dumps(figs))
with open(RES / "casos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

ok = all(r["pass"] for k, r in req.items() if not r.get("informativo"))
for rid, r in req.items():
    extra = f" · máx {r['max']:.4g}" if "max" in r else ""
    print(f"{'✔' if r['pass'] else '✘'} {rid:12s} n={r.get('n', '-')}{extra}  {r.get('descripcion', '')}")
    for fl in r.get("fallos", [])[:5]:
        print("     fallo:", fl)
print("RESULTADO GLOBAL:", "CONFORME" if ok else "NO CONFORME")
