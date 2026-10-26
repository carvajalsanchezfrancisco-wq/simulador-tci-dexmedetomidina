"""Exploración: ¿se puede integrar el estudio de Levionnois 2022 con la corrección para anestesia en un solo modelo?

El modelo corregido del simulador (v1.2.x) toma de Levionnois la estructura, V1, V2, Cl2 y el aclaramiento a
concentración alta (Cl_inf = 1,16 L/h/kg), pero se calibró solo con perros anestesiados (Pascoe 2006, Lin 2008).
Tras el bolo de 10 µg/kg del propio estudio de Levionnois predice un AUC un 31 % menor que el publicado, es decir,
no reproduce el estudio en el que se basa. Aquí se ajusta con los dos tipos de datos a la vez:

  · Levionnois 2022: la curva del modelo publicado (población típica) en sus tiempos de muestreo (2–120 min) tras
    10 µg/kg IV en 60 s, como resumen de sus datos (no hay datos individuales publicados).
  · Pascoe 2006 y Lin 2008: los mismos 20 puntos en anestesia que la calibración del simulador.

Estructuras probadas (V1, V2 y Cl2 de Levionnois en todas):
  A. Cl dependiente de la Cp (la del simulador), reajustada incluyendo a Levionnois.
  B. Cl dependiente de un compartimento hemodinámico Ch con retardo:
        dCh/dt = kh·(Cp − Ch),   Cl = Cl_inf + (Cl_0 − Cl_inf)·C50/(C50 + Ch)
     Hipótesis: el aclaramiento depende del flujo hepático, que la dexmedetomidina reduce, y la recuperación
     hemodinámica tras un bolo alto va retrasada respecto a la Cp. En infusión estable Ch = Cp y B equivale a A.
En las dos se prueba Cl_inf fijo en 1,16 (el de Levionnois) y libre.

Uso: python3 modelo_integrado.py   (desde validacion_fase1/; ~2–4 min)
"""
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

from modelo_corregido import V1, V2, CL2, CL_INF, anesthetized_window, load_groups, varvel

RES = Path(__file__).resolve().parent / "resultados"
LEV_T = np.array([2, 4, 8, 16, 30, 60, 80, 90, 120], dtype=float)     # muestreo de Levionnois (min)
LEV_AUC = {"popPK": 8.65, "IC95": (6.52, 9.70), "NCA_mediana": 8.09, "NCA_RIC": (6.29, 9.50)}   # h·ng/mL, Tabla 2


def simulate(p, t_obs, dose, dur, rate_h, inf_end=None):
    """Cp (ng/mL) en t_obs. p: dict con cl_inf, cl0, c50 (Cl en L/h/kg) y kh (min⁻¹; None = Cl según la Cp)."""
    cl_inf, cl0, c50, kh = p["cl_inf"] / 60, p["cl0"] / 60, p["c50"], p.get("kh")

    def rhs(t, y, r):
        c = max(y[0], 0.0) / V1
        drive = c if kh is None else max(y[2], 0.0)
        cl = cl_inf + (cl0 - cl_inf) * c50 / (c50 + drive) if c50 else cl_inf
        dch = 0.0 if kh is None else kh * (c - y[2])
        return [r - cl * c - CL2 * c + CL2 * y[1] / V2, CL2 * c - CL2 * y[1] / V2, dch]

    t_obs = np.asarray(t_obs, dtype=float)
    end = max(float(t_obs.max()), dur)
    stop = end if inf_end is None else min(inf_end, end)
    pieces = [(0.0, dur, dose / dur + rate_h / 60, dur / 20), (dur, stop, rate_h / 60, 2.0)]
    if stop < end:
        pieces.append((stop, end, 0.0, 2.0))
    sols, y = [], [0.0, 0.0, 0.0]
    for a, b, r, ms in pieces:
        if b <= a:
            continue
        sol = solve_ivp(rhs, (a, b), y, args=(r,), method="LSODA", rtol=1e-7, atol=1e-10, max_step=ms, dense_output=True)
        sols.append((a, b, sol))
        y = sol.y[:, -1]

    def at(t):
        for a, b, sol in sols:
            if t <= b + 1e-9:
                return sol.sol(max(t, a))[0]
        return sols[-1][2].sol(sols[-1][1])[0]
    return np.array([at(t) / V1 for t in t_obs])


PUB = {"cl_inf": CL_INF, "cl0": CL_INF, "c50": None, "kh": None}
SIM = {"cl_inf": CL_INF, "cl0": 3.15, "c50": 0.92, "kh": None}


def levionnois_group():
    return {"estudio": "Levionnois 2022", "grupo": "10 µg/kg IV (curva del modelo publicado)", "estado": "despiertos",
            "dose": 10.0, "dur": 1.0, "rate": 0.0, "inf_end": None, "t": LEV_T, "c": simulate(PUB, LEV_T, 10.0, 1.0, 0.0)}


def pred(p, g):
    return simulate(p, g["t"], g["dose"], g["dur"], g["rate"], g["inf_end"])


def auc_bolus(p):
    t = np.linspace(0, 720, 1441)
    return float(np.trapezoid(simulate(p, t, 10.0, 1.0, 0.0), t)) / 60


def unpack(x, free_inf, hyst):
    v = np.exp(x)
    p = {"cl0": v[0], "c50": v[1], "cl_inf": v[2] if free_inf else CL_INF, "kh": None}
    if hyst:
        p["kh"] = v[-1]
    return p


BOUNDS = {"cl0": (1.0, 8.0), "c50": (0.02, 10.0), "cl_inf": (0.5, 2.0), "kh": (0.002, 2.0)}


def objective(x, use, free_inf, hyst):
    p = unpack(x, free_inf, hyst)
    err = sum(float(np.mean((np.log(g["c"]) - np.log(np.maximum(pred(p, g), 1e-9))) ** 2)) for g in use)
    names = ["cl0", "c50"] + (["cl_inf"] if free_inf else []) + (["kh"] if hyst else [])
    lo = np.log([BOUNDS[n][0] for n in names]); hi = np.log([BOUNDS[n][1] for n in names])
    return err + 10 * float(np.sum((x - np.clip(x, lo, hi)) ** 2))


def fit(use, free_inf=False, hyst=False):
    starts = [[3.0, 0.5], [2.5, 0.2], [4.0, 1.0], [3.5, 2.0]]
    if free_inf:
        starts = [s + [1.16] for s in starts] + [[3.0, 0.5, 0.9]]
    if hyst:
        starts = [s + [kh] for s in starts for kh in (0.02, 0.1)]
    best = None
    for s in starts:
        r = minimize(objective, np.log(s), args=(use, free_inf, hyst), method="Nelder-Mead",
                     options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 3000})
        if best is None or r.fun < best.fun:
            best = r
    return unpack(best.x, free_inf, hyst), float(best.fun)


def evaluate(p, groups, lev):
    """Error de predicción (Varvel, % ) por conjuntos, como en modelo_corregido.py (t ≥ 10 min)."""
    sets = {"anestesiados_calibracion": [], "despiertos_externos": [], "bolos_despiertos": [], "levionnois": []}
    for g in groups:
        w = anesthetized_window(g)
        if w is not None:
            sets["anestesiados_calibracion"].append(w)
        if w is None or "0-2 h" in g["estado"]:
            keep = g["t"] >= 10
            if "0-2 h" in g["estado"]:
                keep &= g["t"] > 120
            gg = dict(g, t=g["t"][keep], c=g["c"][keep])
            if len(gg["t"]):
                sets["despiertos_externos"].append(gg)
                if gg["rate"] == 0 and not g["estudio"].startswith("Dent"):
                    sets["bolos_despiertos"].append(gg)
    sets["levionnois"] = [lev]
    out = {}
    for k, gs in sets.items():
        pe = np.concatenate([(g["c"] - pred(p, g)) / pred(p, g) * 100 for g in gs])
        out[k] = varvel(pe)
    out["auc_10ugkg"] = auc_bolus(p)
    out["Cl_en_0.5_1_2_ngml"] = [float(p["cl_inf"] + (p["cl0"] - p["cl_inf"]) * p["c50"] / (p["c50"] + c)) if p["c50"] else p["cl_inf"]
                                 for c in (0.5, 1.0, 2.0)]
    return out


def main():
    groups = load_groups()
    lev = levionnois_group()
    calib = [w for w in (anesthetized_window(g) for g in groups) if w is not None]
    joint = calib + [lev]
    print("Levionnois (curva publicada):", " · ".join(f"{t:g} min {c:.2f}" for t, c in zip(LEV_T, lev["c"])))

    models = {"publicado (Levionnois 2022)": PUB, "corregido del simulador (3,15/0,92)": SIM}
    fits = {}
    for name, kw in (("A · Cl(Cp), Cl_inf 1,16, con Levionnois", dict()),
                     ("A · Cl(Cp), Cl_inf libre, con Levionnois", dict(free_inf=True)),
                     ("B · Cl(Ch) con retardo, Cl_inf 1,16, con Levionnois", dict(hyst=True)),
                     ("B · Cl(Ch) con retardo, Cl_inf libre, con Levionnois", dict(free_inf=True, hyst=True))):
        p, f = fit(joint, **kw)
        models[name] = p
        fits[name] = f
        print(f"{name}: " + ", ".join(f"{k} {v:.3f}" for k, v in p.items() if v is not None) + f"  (objetivo {f:.4f})")

    # Solo anestesiados con retardo: ¿mejora B a A sin Levionnois? (control)
    p, f = fit(calib, hyst=True)
    models["B · Cl(Ch) con retardo, solo anestesiados"] = p
    print("B solo anestesiados: " + ", ".join(f"{k} {v:.3f}" for k, v in p.items() if v is not None))

    results = {}
    for name, p in models.items():
        e = evaluate(p, groups, lev)
        results[name] = {"parametros": {k: (float(v) if v is not None else None) for k, v in p.items()}, **e}
        print(f"\n{name}")
        for k in ("levionnois", "anestesiados_calibracion", "despiertos_externos", "bolos_despiertos"):
            v = e[k]
            print(f"   {k:26s} n={v['n']:3d}  MDPE {v['MDPE']:+6.1f}  MDAPE {v['MDAPE']:5.1f}")
        print(f"   AUC tras 10 µg/kg {e['auc_10ugkg']:.2f} h·ng/mL (Levionnois 8,65; IC95 6,52–9,70) · "
              f"Cl con 0,5/1/2 ng/mL: " + " / ".join(f"{c:.2f}" for c in e["Cl_en_0.5_1_2_ngml"]))
    (RES / "modelo_integrado.json").write_text(json.dumps({"levionnois_auc": LEV_AUC, "modelos": results}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
