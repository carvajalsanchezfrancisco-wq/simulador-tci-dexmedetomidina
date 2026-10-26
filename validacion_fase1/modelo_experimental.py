"""Modelo experimental: aclaramiento dependiente de la concentración.

Estructura bicompartimental de Levionnois et al. 2022 (V1, V2 y Cl2 sin cambios) con un aclaramiento
que disminuye al aumentar la concentración plasmática:

    Cl(C) = Cl_inf + (Cl_0 − Cl_inf) · C50 / (C50 + C)

Cl_0 = aclaramiento a concentraciones muy bajas; Cl_inf = a concentraciones altas; C50 = concentración
a la que el aclaramiento está a mitad de camino. Mecanismo: la dexmedetomidina reduce el gasto cardiaco
y el flujo hepático, y con ello su propia eliminación (Honkavaara 2012; Kuusela 2000).

Ajuste a los datos externos (t ≥ 10 min, puntos fiables) más una restricción que obliga a reproducir el
AUC publicado por Levionnois (8,65 h·ng/mL tras 10 µg/kg IV). Validación cruzada dejando fuera un estudio
cada vez. NO se usa en el simulador: es una hipótesis para comprobar en la Fase 3.
Uso: python3 modelo_experimental.py
"""
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"
V1, V2, CL2 = 1.03, 0.41, 1.87 / 60          # L/kg y L/min/kg (Levionnois, sin cambios)
CL_PUB = 1.16 / 60
AUC_LEVIONNOIS = 8.65 * 60                   # ng·min/mL tras 10 µg/kg (estimación poblacional publicada)


# Límites fisiológicos de los parámetros (L/h/kg, L/h/kg, ng/mL): evitan soluciones degeneradas
# (p. ej. C50 → 0 con Cl0 → ∞) cuando se ajusta con pocos estudios
LOWER, UPPER = np.log([0.3, 0.3, 0.05]), np.log([6.0, 3.0, 10.0])


def cl_fun(theta):
    cl0, clinf, c50 = np.exp(np.clip(theta, LOWER, UPPER))
    return lambda c: (clinf + (cl0 - clinf) * c50 / (c50 + c)) / 60     # L/min/kg


def simulate(theta, t_obs, dose, dur, rate_h, rate_fn=None, t_end=None, inf_end=None):
    """Cp (ng/mL) en t_obs. Entrada: bolo `dose` µg/kg en `dur` min + `rate_h` µg/kg/h, o una función rate_fn(t) en µg/kg/min."""
    cl = cl_fun(theta) if theta is not None else (lambda c: CL_PUB)

    def rhs(t, a):
        c = max(a[0], 0) / V1
        r = rate_fn(t) if rate_fn else ((dose / dur if t < dur else 0) + (rate_h / 60 if inf_end is None or t < inf_end else 0))
        return [r - cl(c) * c - CL2 * c + CL2 * a[1] / V2, CL2 * c - CL2 * a[1] / V2]

    t_obs = np.asarray(t_obs, dtype=float)
    end = max(t_end or 0, float(t_obs.max()))
    if rate_fn:
        sol = solve_ivp(rhs, (0, end), [0, 0], t_eval=t_obs, method="LSODA", max_step=0.5, rtol=1e-7, atol=1e-9)
        return sol.y[0] / V1
    early, late = t_obs[t_obs <= dur], t_obs[t_obs > dur]
    s1 = solve_ivp(rhs, (0, dur), [0, 0], t_eval=early if len(early) else None, method="LSODA", max_step=dur / 20,
                   rtol=1e-7, atol=1e-9, dense_output=False)
    y_end = solve_ivp(rhs, (0, dur), [0, 0], method="LSODA", max_step=dur / 20, rtol=1e-7, atol=1e-9).y[:, -1]
    out = list(s1.y[0] / V1) if len(early) else []
    if len(late):
        if inf_end is not None and late.max() > inf_end:            # la infusión se detiene: dos tramos
            a_, b_ = late[late <= inf_end], late[late > inf_end]
            kw = dict(method="LSODA", max_step=5.0, rtol=1e-7, atol=1e-9)
            if len(a_):
                out += list(solve_ivp(rhs, (dur, inf_end), y_end, t_eval=a_, **kw).y[0] / V1)
            y_inf = solve_ivp(rhs, (dur, inf_end), y_end, **kw).y[:, -1]
            out += list(solve_ivp(rhs, (inf_end, end), y_inf, t_eval=b_, **dict(kw, max_step=2.0)).y[0] / V1)
        else:
            s2 = solve_ivp(rhs, (dur, end), y_end, t_eval=late, method="LSODA", max_step=5.0, rtol=1e-7, atol=1e-9)
            out += list(s2.y[0] / V1)
    return np.array(out)


rows = list(csv.DictReader(open(ROOT / "datos" / "concentraciones_publicadas.csv", encoding="utf-8")))
groups = {}
for r in rows:
    if r["fiable"] != "si" or float(r["t_min"]) < 10:
        continue
    groups.setdefault((r["estudio"], r["grupo"]), []).append(r)
GROUPS = []
for (study, group), rs in groups.items():
    GROUPS.append({"estudio": study, "grupo": group, "dose": float(rs[0]["dosis_ugkg"]), "dur": float(rs[0]["duracion_admin_min"]),
                   "rate": float(rs[0]["infusion_ugkgh"]), "t": np.array([float(x["t_min"]) for x in rs]),
                   "c": np.array([float(x["c_ngml"]) for x in rs]),
                   "inf_end": float(rs[0]["fin_infusion_min"]) if rs[0].get("fin_infusion_min") else None})
STUDY = lambda g: g["estudio"].split(" ")[0].replace("de", "de Sant'Ana") if g["estudio"].startswith("de") else g["estudio"].split(" ")[0]


def auc_levionnois(theta):
    t = np.linspace(0, 720, 1441)
    c = simulate(theta, t, 10.0, 1.0, 0.0)
    return float(np.trapezoid(c, t))


def objective(theta, use):
    err = 0.0
    for g in use:
        p = simulate(theta, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])
        err += float(np.mean((np.log(g["c"]) - np.log(np.maximum(p, 1e-6))) ** 2))
    err += math.log(auc_levionnois(theta) / AUC_LEVIONNOIS) ** 2           # mantener el estudio original
    err += 10 * float(np.sum((theta - np.clip(theta, LOWER, UPPER)) ** 2))  # dentro de los límites
    return err


def fit(use):
    best = None
    for start in ([1.0, 0.1, 0.0], [0.7, -0.2, 1.0], [1.4, 0.0, -1.0]):
        r = minimize(objective, np.array(start), args=(use,), method="Nelder-Mead",
                     options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 1500})
        if best is None or r.fun < best.fun:
            best = r
    return best.x


def metrics(theta, gs):
    pe = []
    for g in gs:
        p = simulate(theta, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])
        pe += list((g["c"] - p) / p * 100)
    pe = np.array(pe)
    return {"n": len(pe), "MDPE": float(np.median(pe)), "MDAPE": float(np.median(np.abs(pe)))}


no_rvs = [g for g in GROUPS if not g["estudio"].startswith("de Sant")]
print("Ajustando modelo principal (sin el estudio de 2024)…")
theta_main = fit(no_rvs)
print("Ajustando variante con todos los estudios…")
theta_all = fit(GROUPS)
par = lambda th: dict(zip(["Cl_0_Lhkg", "Cl_inf_Lhkg", "C50_ngml"], [float(x) for x in np.exp(np.clip(th, LOWER, UPPER))]))

# Validación cruzada: dejar fuera un estudio, ajustar con el resto, predecir el excluido
studies = sorted({g["estudio"] for g in GROUPS})
loso = []
for s in studies:
    train = [g for g in no_rvs if g["estudio"] != s]
    test = [g for g in GROUPS if g["estudio"] == s]
    th = theta_main if s.startswith("de Sant") else fit(train)
    loso.append({"estudio_excluido": s, "parametros": par(th), "experimental": metrics(th, test), "publicado": metrics(None, test)})
    print(f"  fuera {s:24s} experimental MDPE {loso[-1]['experimental']['MDPE']:+6.1f} MDAPE {loso[-1]['experimental']['MDAPE']:5.1f}"
          f" | publicado MDPE {loso[-1]['publicado']['MDPE']:+6.1f} MDAPE {loso[-1]['publicado']['MDAPE']:5.1f}")

all_test = [g for g in GROUPS if not g["estudio"].startswith("de Sant")]
pe_exp, pe_pub = [], []
for row in loso:
    if row["estudio_excluido"].startswith("de Sant"):
        continue
    test = [g for g in GROUPS if g["estudio"] == row["estudio_excluido"]]
    th = np.log([row["parametros"]["Cl_0_Lhkg"], row["parametros"]["Cl_inf_Lhkg"], row["parametros"]["C50_ngml"]])
    for g in test:
        pe_exp += list((g["c"] - simulate(th, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])) / simulate(th, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"]) * 100)
        pp = simulate(None, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])
        pe_pub += list((g["c"] - pp) / pp * 100)
loso_pool = {"experimental": {"MDPE": float(np.median(pe_exp)), "MDAPE": float(np.median(np.abs(pe_exp))), "n": len(pe_exp)},
             "publicado": {"MDPE": float(np.median(pe_pub)), "MDAPE": float(np.median(np.abs(pe_pub))), "n": len(pe_pub)}}

# Por grupo, con el modelo principal
per_group = []
for g in GROUPS:
    pm = simulate(theta_main, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])
    pp = simulate(None, g["t"], g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"])
    per_group.append({"estudio": g["estudio"], "grupo": g["grupo"],
                      "experimental": {"MDPE": float(np.median((g["c"] - pm) / pm * 100)), "MDAPE": float(np.median(np.abs((g["c"] - pm) / pm * 100)))},
                      "publicado": {"MDPE": float(np.median((g["c"] - pp) / pp * 100)), "MDAPE": float(np.median(np.abs((g["c"] - pp) / pp * 100)))}})

# Implicaciones para la TCI: programa de bomba real del simulador (modelo publicado) y Cp que daría el experimental
tci = json.loads((RES / "programas_tci.json").read_text())
impl = []
for case in tci:
    changes = case["rateChanges"]                       # [[seg, µg/kg/min], …]
    ts = np.array([c[0] for c in changes]) / 60
    rs = np.array([c[1] for c in changes])
    fn = lambda t, ts=ts, rs=rs: float(rs[np.searchsorted(ts, t, side="right") - 1])
    tt = np.array([10, 30, 60, 120], dtype=float)
    c_exp = simulate(theta_main, tt, 0, 1, 0, rate_fn=fn, t_end=120)
    impl.append({"objetivo": case["target"], "Cp_real_estimada": {str(int(a)): float(b) for a, b in zip(tt, c_exp)},
                 "diferencia_pct": {str(int(a)): float((b - case["target"]) / case["target"] * 100) for a, b in zip(tt, c_exp)}})
    print(f"  TCI objetivo {case['target']}: Cp real estimada " + " · ".join(f"{int(a)}' {b:.2f} ({(b - case['target']) / case['target'] * 100:+.0f}%)" for a, b in zip(tt, c_exp)))

# Curvas para figuras
curves = {}
for g in GROUPS:
    t = np.linspace(10, max(g["t"]) * 1.05, 120)
    curves[f"{g['estudio']} · {g['grupo']}"] = {"t": t.tolist(), "exp": simulate(theta_main, t, g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"]).tolist(),
                                                "pub": simulate(None, t, g["dose"], g["dur"], g["rate"], inf_end=g["inf_end"]).tolist(),
                                                "t_obs": g["t"].tolist(), "obs": g["c"].tolist()}
cgrid = np.linspace(0, 6, 61)
out = {"principal_sin_2024": par(theta_main), "variante_con_2024": par(theta_all),
       "auc_levionnois_pred": auc_levionnois(theta_main) / 60, "auc_levionnois_pub": 8.65,
       "loso": loso, "loso_global": loso_pool, "por_grupo": per_group, "tci": impl,
       "cl_vs_c": {"c": cgrid.tolist(), "cl": [float(cl_fun(theta_main)(c) * 60) for c in cgrid],
                   "cl_con_2024": [float(cl_fun(theta_all)(c) * 60) for c in cgrid]}}
(RES / "modelo_experimental.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
(RES / "curvas_modelo_experimental.json").write_text(json.dumps(curves))
print("Parámetros (sin 2024):", par(theta_main), "\nParámetros (con 2024):", par(theta_all))
print("AUC Levionnois predicho:", round(out["auc_levionnois_pred"], 2), "h·ng/mL (publicado 8,65)")
print("Validación cruzada global (sin 2024):", loso_pool)
