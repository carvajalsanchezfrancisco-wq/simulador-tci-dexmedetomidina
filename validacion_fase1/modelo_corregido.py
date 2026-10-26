"""Modelo corregido para perros anestesiados (el que usa por defecto el simulador desde la v1.2.0).

Estructura bicompartimental de Levionnois et al. 2022 (V1, V2 y Cl2 sin cambios). Solo cambia el
aclaramiento, que aumenta cuando la concentración es baja:

    Cl(C) = Cl_inf + (Cl_0 − Cl_inf) · C50 / (C50 + C)        con Cl_inf = 1,16 L/h/kg (el publicado)

A concentraciones altas el modelo es el publicado; la corrección solo actúa en el rango clínico bajo
(0,2–2 ng/mL), donde los estudios en perros anestesiados midieron alrededor de la mitad de lo predicho.

Calibración: puntos fiables tomados con el perro ANESTESIADO, desde el minuto 10: Pascoe 2006 (isoflurano;
0,5 y 3 µg/kg/h; Fig. 1 digitalizada, 4 tomas por dosis hasta ≈ 7 h) y Lin 2008 (isoflurano y propofol;
1,055 µg/kg/h; Fig. 2 digitalizada, 15–120 min). Lin 2008 de 3 a 26 h (perros ya despiertos, con la infusión y
tras detenerla a las 24 h) sirve de comprobación externa.

Los parámetros del simulador v1.2.0 (Cl0 3,15; C50 0,92) se fijaron con la calibración anterior, que solo usaba las
cifras del texto de los dos estudios. Este script evalúa esos parámetros y compara con el reajuste actual.
Se ajustan Cl_0 y C50 (mínimos cuadrados en escala logarítmica, mismo peso por grupo). Validación
cruzada dejando fuera un estudio. Después se evalúa en todos los estudios (también en despiertos) y se
calcula el riesgo de sobredosificación si el perro se comporta como el modelo publicado o como Dent 2019.

Uso: python3 modelo_corregido.py
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
CL_INF = 1.16                                # L/h/kg (Levionnois)
BOUNDS = {"Cl_0": (1.16, 6.0), "C50": (0.05, 10.0)}   # límites fisiológicos para el ajuste
SIMULADOR = (3.15, 0.92)     # Cl0 (L/h/kg) y C50 (ng/mL) programados en el simulador v1.2.0


def cl_corr(cl0, c50):
    return lambda c: (CL_INF + (cl0 - CL_INF) * c50 / (c50 + c)) / 60       # L/min/kg


def cl_pub(_c):
    return CL_INF / 60


def simulate(cl, t_obs, dose, dur, rate_h, inf_end=None):
    """Cp (ng/mL) en t_obs: `dose` µg/kg en `dur` min y, a la vez, `rate_h` µg/kg/h hasta `inf_end` min (None: sin detenerla)."""
    def rhs(t, a, r):
        c = max(a[0], 0.0) / V1
        return [r - cl(c) * c - CL2 * c + CL2 * a[1] / V2, CL2 * c - CL2 * a[1] / V2]

    t_obs = np.asarray(t_obs, dtype=float)
    end = max(float(t_obs.max()), dur)
    kw = dict(method="LSODA", rtol=1e-8, atol=1e-10)
    stop = end if inf_end is None else min(inf_end, end)
    pieces = [(0.0, dur, dose / dur + rate_h / 60, dur / 20), (dur, stop, rate_h / 60, 2.0)]
    if stop < end:
        pieces.append((stop, end, 0.0, 2.0))
    sols, y = [], [0.0, 0.0]
    for a, b, r, ms in pieces:
        if b <= a:
            continue
        sol = solve_ivp(rhs, (a, b), y, args=(r,), max_step=ms, dense_output=True, **kw)
        sols.append((a, b, sol))
        y = sol.y[:, -1]
    def at(t):
        for a, b, sol in sols:
            if t <= b + 1e-9:
                return sol.sol(max(t, a))[0]
        return sols[-1][2].sol(sols[-1][1])[0]
    return np.array([at(t) / V1 for t in t_obs])


def load_groups():
    rows = list(csv.DictReader(open(ROOT / "datos" / "concentraciones_publicadas.csv", encoding="utf-8")))
    groups = {}
    for r in rows:
        if r["fiable"] != "si":
            continue
        groups.setdefault((r["estudio"], r["grupo"]), []).append(r)
    out = []
    for (study, group), rs in groups.items():
        t = np.array([float(x["t_min"]) for x in rs])
        out.append({"estudio": study, "grupo": group, "estado": rs[0]["estado"],
                    "dose": float(rs[0]["dosis_ugkg"]), "dur": float(rs[0]["duracion_admin_min"]),
                    "rate": float(rs[0]["infusion_ugkgh"]), "t": t, "c": np.array([float(x["c_ngml"]) for x in rs]),
                    "inf_end": float(rs[0]["fin_infusion_min"]) if rs[0].get("fin_infusion_min") else None})
    return out


def anesthetized_window(g):
    """Puntos tomados con el perro anestesiado, desde el minuto 10."""
    keep = g["t"] >= 10
    if not g["estado"].startswith("anestesiados"):
        return None
    if "0-2 h" in g["estado"]:                         # Lin 2008: anestesia solo las 2 primeras horas
        keep &= g["t"] <= 120
    return dict(g, t=g["t"][keep], c=g["c"][keep]) if keep.any() else None


def objective(x, use):
    cl0, c50 = np.exp(x)
    cl = cl_corr(cl0, c50)
    err = sum(float(np.mean((np.log(g["c"]) - np.log(np.maximum(simulate(cl, g["t"], g["dose"], g["dur"], g["rate"], g["inf_end"]), 1e-9))) ** 2))
              for g in use)
    lo = np.log([BOUNDS["Cl_0"][0], BOUNDS["C50"][0]])
    hi = np.log([BOUNDS["Cl_0"][1], BOUNDS["C50"][1]])
    return err + 10 * float(np.sum((x - np.clip(x, lo, hi)) ** 2))


def fit(use):
    best = None
    for start in ([3.0, 0.5], [2.0, 0.2], [4.0, 1.0], [2.5, 2.0]):
        r = minimize(objective, np.log(start), args=(use,), method="Nelder-Mead",
                     options={"xatol": 1e-5, "fatol": 1e-8, "maxiter": 2000})
        if best is None or r.fun < best.fun:
            best = r
    lo = [BOUNDS["Cl_0"][0], BOUNDS["C50"][0]]
    hi = [BOUNDS["Cl_0"][1], BOUNDS["C50"][1]]
    return [float(v) for v in np.clip(np.exp(best.x), lo, hi)]


def pe_list(cl, gs):
    out = []
    for g in gs:
        p = simulate(cl, g["t"], g["dose"], g["dur"], g["rate"], g["inf_end"])
        out += list((g["c"] - p) / p * 100)
    return np.array(out)


def varvel(pe):
    return {"n": int(len(pe)), "MDPE": float(np.median(pe)), "MDAPE": float(np.median(np.abs(pe)))} if len(pe) else None


def main():
    groups = load_groups()
    calib = [w for w in (anesthetized_window(g) for g in groups) if w is not None]
    print("Calibración:", ", ".join(f"{g['estudio']} {g['grupo'].split(':')[0]} ({len(g['t'])})" for g in calib))

    cl0, c50 = fit(calib)
    cl0_r, c50_r = round(cl0, 2), round(c50, 2)
    print(f"Reajuste con los datos actuales: Cl_0 = {cl0:.4f} L/h/kg · C50 = {c50:.4f} ng/mL (redondeado {cl0_r} · {c50_r})")
    print(f"Simulador v1.2.0: Cl_0 = {SIMULADOR[0]} · C50 = {SIMULADOR[1]} (se evalúan estos)")
    final = cl_corr(*SIMULADOR)
    refit = cl_corr(cl0_r, c50_r)

    # Validación cruzada dejando fuera un estudio (de los anestesiados)
    loso = []
    for s in sorted({g["estudio"] for g in calib}):
        train = [g for g in calib if g["estudio"] != s]
        test = [g for g in calib if g["estudio"] == s]
        p0, p50 = fit(train)
        loso.append({"estudio_excluido": s, "Cl_0": p0, "C50": p50,
                     "corregido": varvel(pe_list(cl_corr(p0, p50), test)), "publicado": varvel(pe_list(cl_pub, test))})
        r = loso[-1]
        print(f"  fuera {s:12s} (ajuste Cl_0 {p0:.2f}, C50 {p50:.2f}) corregido MDPE {r['corregido']['MDPE']:+6.1f} "
              f"MDAPE {r['corregido']['MDAPE']:5.1f} | publicado MDPE {r['publicado']['MDPE']:+6.1f} MDAPE {r['publicado']['MDAPE']:5.1f}")

    # Evaluación en todos los estudios (t ≥ 10 min), por grupo y por estado
    per_group, pe_c, pe_p = [], {"anestesiados": [], "despiertos": []}, {"anestesiados": [], "despiertos": []}
    parts = []
    for g in groups:
        w = anesthetized_window(g)
        if w is not None:
            parts.append(("anestesiados", g, w))
        if w is None or "0-2 h" in g["estado"]:          # Lin 2008 tras la anestesia (3–26 h): despiertos
            keep = g["t"] >= 10
            if "0-2 h" in g["estado"]:
                keep &= g["t"] > 120
            parts.append(("despiertos", g, dict(g, t=g["t"][keep], c=g["c"][keep])))
    for key, g, gg in parts:
        if not len(gg["t"]):
            continue
        a, b = pe_list(final, [gg]), pe_list(cl_pub, [gg])
        pe_c[key] += list(a); pe_p[key] += list(b)
        per_group.append({"estudio": g["estudio"], "grupo": g["grupo"] + (" · 3–26 h" if "0-2 h" in g["estado"] and key == "despiertos" else ""), "estado": key, "t": gg["t"].tolist(), "c": gg["c"].tolist(),
                          "pred_corregido": simulate(final, gg["t"], g["dose"], g["dur"], g["rate"], g["inf_end"]).tolist(),
                          "pred_publicado": simulate(cl_pub, gg["t"], g["dose"], g["dur"], g["rate"], g["inf_end"]).tolist(),
                          "corregido": varvel(a), "publicado": varvel(b)})
    summary = {k: {"corregido": varvel(np.array(pe_c[k])), "publicado": varvel(np.array(pe_p[k]))} for k in pe_c}
    summary["global"] = {"corregido": varvel(np.array(pe_c["anestesiados"] + pe_c["despiertos"])),
                         "publicado": varvel(np.array(pe_p["anestesiados"] + pe_p["despiertos"]))}
    summary["anestesiados"]["reajuste"] = varvel(pe_list(refit, calib))
    for k, v in summary.items():
        print(f"  {k:12s} n={v['corregido']['n']:2d} corregido MDPE {v['corregido']['MDPE']:+6.1f} MDAPE {v['corregido']['MDAPE']:5.1f}"
              f" | publicado MDPE {v['publicado']['MDPE']:+6.1f} MDAPE {v['publicado']['MDAPE']:5.1f}")

    # Lin 2008 por periodos (curva completa digitalizada) y descenso tras detener la infusión a las 24 h
    lin = {}
    for g in [g for g in groups if g["estudio"] == "Lin 2008"]:
        per = {"anestesia 15-120 min": (g["t"] >= 10) & (g["t"] <= 120), "despiertos 3-6 h": (g["t"] >= 180) & (g["t"] <= 360),
               "despiertos 8-24 h": (g["t"] >= 480) & (g["t"] <= 1440)}
        row = {}
        for name, cl in (("corregido", final), ("publicado", cl_pub)):
            pe = (g["c"] - simulate(cl, g["t"], g["dose"], g["dur"], g["rate"], g["inf_end"])) / simulate(cl, g["t"], g["dose"], g["dur"], g["rate"], g["inf_end"]) * 100
            row[name] = {k: float(np.median(pe[m])) for k, m in per.items()}
        lin[g["grupo"].split(":")[0]] = row
        print(f"  Lin {g['grupo'][:3]}: " + " · ".join(f"{k} corr {row['corregido'][k]:+.0f}% / pub {row['publicado'][k]:+.0f}%" for k in per))
    tw = np.array([1440, 1455, 1470, 1485, 1500])
    iso = next(g for g in groups if g["estudio"] == "Lin 2008" and g["grupo"].startswith("ISO"))
    measured = np.array([iso["c"][list(iso["t"]).index(x)] for x in tw])
    washout = {"t_min_desde_fin": (tw - 1440).tolist(), "medido_relativo": (measured / measured[0]).tolist()}
    for name, cl in (("corregido", final), ("publicado", cl_pub)):
        pw = simulate(cl, tw, iso["dose"], iso["dur"], iso["rate"], iso["inf_end"])
        washout[name + "_relativo"] = (pw / pw[0]).tolist()
        washout[name + "_t12_h"] = float(np.log(2) / -np.polyfit(tw / 60, np.log(pw), 1)[0])
    washout["medido_t12_h"] = float(np.log(2) / -np.polyfit(tw / 60, np.log(measured), 1)[0])
    print(f"  Descenso tras 24 h (ISO): t½ medida {washout['medido_t12_h']:.2f} h · corregido {washout['corregido_t12_h']:.2f} h · "
          f"publicado {washout['publicado_t12_h']:.2f} h")

    # Tasas de mantenimiento en equilibrio y riesgo si el perro elimina como el modelo publicado o como Dent 2019
    risk = []
    for target in (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
        cl_t = final(target) * 60
        rate = target * cl_t
        risk.append({"objetivo": target, "Cl_corregido_Lhkg": cl_t, "tasa_corregida_ugkgh": rate, "tasa_publicada_ugkgh": target * CL_INF,
                     "Css_si_publicado": rate / CL_INF, "Css_si_Dent": rate / 0.46})
    print("  Objetivo → tasa corregida (publicada) · Css si el perro fuera 'publicado' · si fuera 'Dent'")
    for r in risk:
        print(f"    {r['objetivo']:4.2f} → {r['tasa_corregida_ugkgh']:.2f} ({r['tasa_publicada_ugkgh']:.2f}) µg/kg/h · "
              f"{r['Css_si_publicado']:.2f} · {r['Css_si_Dent']:.2f} ng/mL")

    # AUC del estudio original (10 µg/kg IV en 1 min, despiertos) con el modelo corregido
    t = np.linspace(0, 720, 2881)
    auc = float(np.trapezoid(simulate(final, t, 10.0, 1.0, 0.0), t)) / 60
    print(f"  AUC 0-12 h tras 10 µg/kg: corregido {auc:.2f} h·ng/mL (publicado 8,65)")

    grid = np.linspace(0, 6, 121)
    out = {"modelo": "Cl(C) = Cl_inf + (Cl_0 - Cl_inf)·C50/(C50 + C)", "V1_Lkg": V1, "V2_Lkg": V2, "Cl2_Lhkg": CL2 * 60,
           "Cl_inf_Lhkg": CL_INF, "ajuste": {"Cl_0_Lhkg": cl0, "C50_ngml": c50},
           "ajuste_redondeado": {"Cl_0_Lhkg": cl0_r, "C50_ngml": c50_r},
           "simulador": {"Cl_0_Lhkg": SIMULADOR[0], "C50_ngml": SIMULADOR[1]},
           "lin_por_periodos": lin, "lin_descenso_24h": washout,
           "tasa_1ngml_reajuste_vs_simulador": [refit(1.0) * 60, final(1.0) * 60],
           "calibracion": [{"estudio": g["estudio"], "grupo": g["grupo"], "t": g["t"].tolist(), "c": g["c"].tolist()} for g in calib],
           "loso": loso, "resumen": summary, "por_grupo": per_group, "riesgo": risk, "auc_levionnois": auc,
           "cl_vs_c": {"c": grid.tolist(), "cl": [final(c) * 60 for c in grid]}}
    (RES / "modelo_corregido.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
