"""Fase 1 · v5: aclaramiento corregido junto con los volúmenes central (V1) y periférico (V2) en perros anestesiados.

Motivo (reunión con IRNASUS UCC-CONICET, 27/10/2026):
  - El error de los volúmenes perjudica la estimación del aclaramiento. Al fijar V1 y V2 de Levionnois, el ajuste carga
    sobre el aclaramiento lo que es un error de volumen.
  - Las ecuaciones del aclaramiento solo valen cerca del estado estacionario; fuera de él sobrestiman el aclaramiento.
  - La fisiología no es constante. El aclaramiento depende del flujo hepático y del gasto cardíaco, que la propia
    dexmedetomidina reduce con cierto retraso.

Estructuras comparadas (anestesia: V1·f1 y V2·f2; Cl2 de Levionnois):
  A  Cl(C), volúmenes de Levionnois                       (modelo actual del simulador, reajustado)
  B  Cl constante + V1 + V2                               (¿hace falta la no linealidad si los volúmenes son libres?)
  C  Cl(C) + V1 + V2                                      (aclaramiento corregido con influencia central y periférica)
  D  Cl(Ch) con retraso + V1 + V2                         (C, con el aclaramiento siguiendo a la Cp con un retraso kh)
  E  Cl(Ch) con retraso, volúmenes de Levionnois          (alternativa: solo la fisiología que cambia en el tiempo)
  Cl(x) = Cl_inf + (Cl_0 − Cl_inf)·C50/(C50 + x), Cl_inf = 1,16 L/h/kg. Ch: compartimento hemodinámico, dCh/dt = kh·(C − Ch).

Calibración: los mismos puntos que modelo_corregido.py (perros anestesiados desde el minuto 10: Pascoe 2006 y Lin 2008
0–120 min), mínimos cuadrados en escala logarítmica con el mismo peso por grupo.
Comprobaciones:
  - validación cruzada entre estudios;
  - perfil de verosimilitud de f1 y f2 (¿son identificables con medias de grupo?);
  - estudios en perros despiertos (f1 = f2 = 1; mismo aclaramiento);
  - Lin 2008 tras despertar, con los volúmenes volviendo a los de Levionnois (τ = 30 min);
  - descenso tras detener la infusión a las 24 h;
  - AUC del bolo de Levionnois;
  - dosis de carga y de mantenimiento en anestesia;
  - aclaramiento aparente (tasa/Cp) fuera del estado estacionario.

Uso: python3 modelo_volumenes_aclaramiento.py      (≈ 10 min)
"""
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize

from modelo_corregido import CL2, CL_INF, V1, V2, anesthetized_window, load_groups

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"
WAKE_TAU = 30.0                                   # min: vuelta de los volúmenes a los de Levionnois al despertar
BOUNDS = {"cl0": (CL_INF, 8.0), "c50": (0.02, 10.0), "f1": (0.3, 6.0), "f2": (0.3, 8.0), "kh": (0.002, 1.0), "cl": (0.3, 6.0)}
DEFAULTS = {"cl0": 3.15, "c50": 0.92, "f1": 1.0, "f2": 1.0, "kh": None, "cl": None}
MODELS = {
    "A": {"nombre": "A · Cl(C), volúmenes de Levionnois", "libres": ["cl0", "c50"], "inicio": [[3.2, 0.9], [2.5, 0.3], [4.0, 2.0]]},
    "B": {"nombre": "B · Cl constante + V1 + V2", "libres": ["cl", "f1", "f2"], "inicio": [[1.8, 1.5, 2.0], [2.2, 2.5, 1.0], [1.5, 1.0, 4.0]]},
    "C": {"nombre": "C · Cl(C) + V1 + V2", "libres": ["cl0", "c50", "f1", "f2"],
          "inicio": [[3.4, 0.2, 2.6, 1.8], [2.9, 0.6, 1.0, 4.5], [3.2, 0.9, 1.5, 1.5], [4.0, 0.1, 3.0, 3.0]]},
    "D": {"nombre": "D · Cl(Ch) con retraso + V1 + V2", "libres": ["cl0", "c50", "kh", "f1", "f2"],
          "inicio": [[3.4, 0.3, 0.02, 2.0, 1.5], [4.0, 0.2, 0.05, 1.5, 2.5], [3.0, 0.6, 0.01, 1.2, 1.2], [5.0, 0.1, 0.1, 2.5, 1.0]]},
    "E": {"nombre": "E · Cl(Ch) con retraso, volúmenes de Levionnois", "libres": ["cl0", "c50", "kh"],
          "inicio": [[4.0, 0.3, 0.02], [6.0, 0.1, 0.01], [3.2, 0.9, 0.05]]},
}


def params(model, x):
    p = dict(DEFAULTS)
    for k, v in zip(MODELS[model]["libres"], x):
        p[k] = float(v)
    return p


def cl_fun(p, drive):
    """Aclaramiento (L/h/kg) en función de la concentración que lo gobierna (C, o Ch con retraso)."""
    if p["cl"] is not None:
        return p["cl"]
    return CL_INF + (p["cl0"] - CL_INF) * p["c50"] / (p["c50"] + max(drive, 0.0))


def simulate(p, g, t, anest=True, wake=None):
    """Cp (ng/mL) en t (min). `anest`: aplica f1 y f2; `wake`: minuto en que el perro despierta (los volúmenes vuelven
    a los de Levionnois con constante WAKE_TAU, conservando la cantidad de fármaco en cada compartimento)."""
    f1, f2, kh = (p["f1"], p["f2"], p["kh"]) if anest else (1.0, 1.0, p["kh"])

    def fac(tt, f):
        if wake is None or tt <= wake:
            return f
        return 1.0 + (f - 1.0) * np.exp(-(tt - wake) / WAKE_TAU)

    def rhs(tt, y, r):
        v1, v2 = V1 * fac(tt, f1), V2 * fac(tt, f2)
        c = max(y[0], 0.0) / v1
        cl = cl_fun(p, y[2] if kh else c) / 60
        return [r - cl * c - CL2 * c + CL2 * y[1] / v2, CL2 * c - CL2 * y[1] / v2, kh * (c - y[2]) if kh else 0.0]

    t = np.asarray(t, dtype=float)
    end = max(float(t.max()), g["dur"])
    stop = end if g["inf_end"] is None else min(g["inf_end"], end)
    cuts = sorted({0.0, g["dur"], stop, end} | ({wake} if wake is not None and wake < end else set()))
    sols, y = [], [0.0, 0.0, 0.0]
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b <= a:
            continue
        r = (g["dose"] / g["dur"] if a < g["dur"] else 0.0) + (g["rate"] / 60 if a < stop else 0.0)
        s = solve_ivp(rhs, (a, b), y, args=(r,), method="LSODA", rtol=1e-7, atol=1e-10,
                      max_step=min(2.0, (b - a) / 4), dense_output=True)
        sols.append((a, b, s))
        y = s.y[:, -1]
    out = []
    for tt in t:
        for a, b, s in sols:
            if tt <= b + 1e-9:
                out.append(s.sol(max(tt, a))[0] / (V1 * fac(tt, f1)))
                break
    return np.array(out)


def fit(model, use, fixed=None):
    """Ajuste por Nelder-Mead desde varios inicios. `fixed` = {parámetro: valor} para los perfiles de verosimilitud."""
    free = [k for k in MODELS[model]["libres"] if not fixed or k not in fixed]
    best = None
    for start in MODELS[model]["inicio"]:
        full = dict(zip(MODELS[model]["libres"], start))
        x0 = np.log([full[k] for k in free])

        def f(x):
            lo = np.log([BOUNDS[k][0] for k in free]); hi = np.log([BOUNDS[k][1] for k in free])
            p = dict(DEFAULTS); p.update(fixed or {}); p.update(zip(free, np.exp(np.clip(x, lo, hi))))
            err = sum(float(np.mean((np.log(g["c"]) - np.log(np.maximum(simulate(p, g, g["t"]), 1e-9))) ** 2)) for g in use)
            return err + 10 * float(np.sum((x - np.clip(x, lo, hi)) ** 2))

        r = minimize(f, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-8, "maxiter": 4000, "maxfev": 6000})
        if best is None or r.fun < best.fun:
            best = r
    lo = [BOUNDS[k][0] for k in free]; hi = [BOUNDS[k][1] for k in free]
    p = dict(DEFAULTS); p.update(fixed or {}); p.update(zip(free, np.clip(np.exp(best.x), lo, hi)))
    return {k: (float(v) if v is not None else None) for k, v in p.items()}, float(best.fun)


def pe(p, gs, **kw):
    out = []
    for g in gs:
        pr = simulate(p, g, g["t"], **kw)
        out += list((g["c"] - pr) / pr * 100)
    return np.array(out)


def varvel(x):
    return {"n": int(len(x)), "MDPE": float(np.median(x)), "MDAPE": float(np.median(np.abs(x)))} if len(x) else None


def aicc(obj, use, k):
    """AICc aproximado con la suma de cuadrados ponderada (mismo peso por grupo) que minimiza el ajuste."""
    n = sum(len(g["t"]) for g in use)
    wss = obj * n / len(use)
    return float(n * np.log(wss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1))


def load_10min(p, target):
    """µg/kg de una carga en 10 min (sin infusión) que deja la Cp en el objetivo al minuto 10, en anestesia."""
    def miss(dose):
        g = {"dose": dose, "dur": 10.0, "rate": 0.0, "inf_end": None}
        return simulate(p, g, [10.0])[0] - target
    return float(brentq(miss, 1e-4, 100.0, xtol=1e-5))


def main():
    groups = load_groups()
    calib = [w for w in (anesthetized_window(g) for g in groups) if w is not None]
    n_cal = sum(len(g["t"]) for g in calib)
    print("Calibración:", ", ".join(f"{g['estudio']} {g['grupo'].split(':')[0][:14]} ({len(g['t'])})" for g in calib), f"· n = {n_cal}")

    # ── 1. Ajustes ──
    fits = {}
    for m, spec in MODELS.items():
        p, obj = fit(m, calib)
        v = varvel(pe(p, calib))
        fits[m] = {"nombre": spec["nombre"], "parametros": p, "objetivo": obj, "k": len(spec["libres"]),
                   "AICc": aicc(obj, calib, len(spec["libres"])), "calibracion": v,
                   "obs_pred": {f"{g['estudio']} · {g['grupo']}": np.round(g["c"] / simulate(p, g, g["t"]), 3).tolist() for g in calib}}
        ptxt = " ".join(f"{k} {p[k]:.3g}" for k in spec["libres"])
        print(f"{spec['nombre']:48s} obj {obj:.4f} AICc {fits[m]['AICc']:7.1f} · MDPE {v['MDPE']:+5.1f} MDAPE {v['MDAPE']:4.1f} · {ptxt}")

    # ── 2. Validación cruzada entre estudios ──
    print("\nValidación cruzada (ajuste con un estudio, predicción del otro):")
    cv = {}
    for m in MODELS:
        for out in ("Lin 2008", "Pascoe 2006"):
            train = [g for g in calib if g["estudio"] != out]; test = [g for g in calib if g["estudio"] == out]
            p, _ = fit(m, train)
            v = varvel(pe(p, test))
            cv[f"{m} · sin {out}"] = {"parametros": p, **v}
            print(f"  {m} sin {out:12s} → predice {out}: MDPE {v['MDPE']:+5.0f} % MDAPE {v['MDAPE']:4.0f} %")

    # ── 3. Perfil de verosimilitud de f1 y f2 en C (¿identificables?) ──
    print("\nPerfil de verosimilitud en C (IC 95 %: aumento del AICc sin penalización < 3,84):")
    prof = {}
    base = fits["C"]["objetivo"]
    n = n_cal
    for par, grid in (("f1", [0.8, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.6, 4.5]), ("f2", [0.5, 0.8, 1.0, 1.4, 1.75, 2.5, 3.5, 5.0, 7.0])):
        rows = []
        for v in grid:
            p, obj = fit("C", calib, fixed={par: v})
            d = n * np.log(obj / base)
            rows.append({"valor": v, "objetivo": obj, "delta": float(d), "parametros": p})
        inside = [r["valor"] for r in rows if r["delta"] < 3.84]
        prof[par] = {"filas": rows, "ic95_aprox": [min(inside), max(inside)] if inside else None}
        print(f"  {par}: " + " · ".join(f"{r['valor']:.2g}→{r['delta']:.1f}" for r in rows) + f"  ⇒ IC 95 % ≈ {prof[par]['ic95_aprox']}")

    # ── 4. Comprobaciones externas ──
    print("\nPerros despiertos no usados en la calibración (f1 = f2 = 1, mismo aclaramiento) y Lin 2008 tras despertar:")
    ext = {}
    awake = [dict(g, t=g["t"][g["t"] >= 10], c=g["c"][g["t"] >= 10]) for g in groups if anesthetized_window(g) is None]
    awake = [g for g in awake if len(g["t"])]
    lin = [g for g in groups if g["estudio"] == "Lin 2008"]
    for m, f in fits.items():
        p = f["parametros"]
        a = pe(p, awake, anest=False)
        lin_pe = []
        for g in lin:
            pr = simulate(p, g, g["t"], wake=120.0)
            mk = (g["t"] > 120) & (g["t"] <= 1440)
            lin_pe += list(((g["c"] - pr) / pr * 100)[mk])
        iso = next(g for g in lin if g["grupo"].startswith("ISO"))
        tw = np.array([1440, 1455, 1470, 1485, 1500])
        pw = simulate(p, iso, tw, wake=120.0)
        meas = np.array([iso["c"][list(iso["t"]).index(x)] for x in tw])
        t12 = lambda c: float(np.log(2) / -np.polyfit(tw / 60, np.log(c), 1)[0])
        tt = np.linspace(0, 720, 2881)
        auc = float(np.trapezoid(simulate(p, {"dose": 10.0, "dur": 1.0, "rate": 0.0, "inf_end": None}, tt, anest=False), tt)) / 60
        ext[m] = {"despiertos": varvel(a), "lin_3_24h": varvel(np.array(lin_pe)), "descenso_relativo": (pw / pw[0]).tolist(),
                  "t12_descenso_h": t12(pw), "auc_levionnois": auc}
        print(f"  {m}: despiertos MDPE {ext[m]['despiertos']['MDPE']:+5.1f} MDAPE {ext[m]['despiertos']['MDAPE']:4.1f} · "
              f"Lin 3–24 h MDPE {ext[m]['lin_3_24h']['MDPE']:+5.1f} · t½ al detener {ext[m]['t12_descenso_h']:.2f} h (medida {t12(meas):.2f}) · "
              f"AUC bolo {auc:.2f} (Levionnois 8,65)")
    ext["medido"] = {"descenso_relativo": (meas / meas[0]).tolist(), "t12_descenso_h": t12(meas)}

    # ── 5. Dosis en anestesia y aclaramiento aparente fuera del estado estacionario ──
    print("\nDosis en anestesia: carga en 10 min / mantenimiento en equilibrio (µg/kg y µg/kg/h) para 0,5 · 1 · 2 ng/mL:")
    dosing = {}
    for m, f in fits.items():
        p = f["parametros"]
        loads = [load_10min(p, c) for c in (0.5, 1.0, 2.0)]
        maint = [c * (cl_fun(p, c)) for c in (0.5, 1.0, 2.0)]
        dosing[m] = {"carga_10min": loads, "mantenimiento": maint}
        print(f"  {m}: carga {np.round(loads, 2).tolist()} · mantenimiento {np.round(maint, 2).tolist()}")

    print("\nAclaramiento aparente (tasa/Cp) con 1 µg/kg/h sin carga, frente al aclaramiento en equilibrio (L/h/kg):")
    apparent = {}
    times = np.array([30, 60, 120, 240, 480, 960])
    for m, f in fits.items():
        p = f["parametros"]
        c = simulate(p, {"dose": 0.0001, "dur": 1.0, "rate": 1.0, "inf_end": None}, times)
        css = brentq(lambda x: x * cl_fun(p, x) - 1.0, 1e-4, 10)
        apparent[m] = {"t_min": times.tolist(), "aparente": (1.0 / c).tolist(), "equilibrio": float(cl_fun(p, css))}
        print(f"  {m}: " + " · ".join(f"{t:.0f} min {1 / x:.2f}" for t, x in zip(times, c)) + f" · equilibrio {cl_fun(p, css):.2f}")

    # ── 6. Curvas para la figura ──
    curves = {}
    for g in calib:
        tt = np.linspace(10, float(g["t"].max()) * 1.05, 90)
        curves[f"{g['estudio']} · {g['grupo']}"] = {"t": tt.tolist(), "t_obs": g["t"].tolist(), "obs": g["c"].tolist(),
                                                     **{m: simulate(fits[m]["parametros"], g, tt).tolist() for m in fits}}
    (RES / "modelo_volumenes_aclaramiento.json").write_text(json.dumps(
        {"modelos": fits, "validacion_cruzada": cv, "perfil_C": prof, "externa": ext, "dosis": dosing,
         "aclaramiento_aparente": apparent, "curvas": curves, "wake_tau_min": WAKE_TAU}, ensure_ascii=False, indent=1))
    print("Guardado: resultados/modelo_volumenes_aclaramiento.json")


if __name__ == "__main__":
    main()
