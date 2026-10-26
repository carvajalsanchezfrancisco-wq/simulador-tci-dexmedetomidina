"""Exploración estructural (Fase 1, v4): ¿mejora el ajuste en perros anestesiados si, además del aclaramiento
dependiente de la concentración, cambia el volumen central (V1) o el periférico (V2)?

Motivo: con las curvas completas digitalizadas (Lin 2008 Fig. 2; Pascoe 2006 Fig. 1), la Cp de los perros anestesiados
SUBE durante las primeras 2–3 h pese a la dosis de carga, mientras que los modelos con los volúmenes de Levionnois
predicen que baja. Se comparan 4 estructuras, con validación cruzada entre estudios y comprobaciones con Lin 2008 tras
la anestesia. NO se usa en el simulador: es una pregunta para el revisor farmacocinético y para la Fase 3.
Uso: python3 modelo_volumen.py   (≈ 1 min)
"""
import sys, json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
from pathlib import Path
ROOT = Path(__file__).resolve().parent
import importlib.util
spec = importlib.util.spec_from_file_location("mc", ROOT / "modelo_corregido.py"); mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
V1, V2, CL2, CLI = 1.03, 0.41, 1.87 / 60, 1.16

def sim(par, g, t=None):
    cl0, c50, f1, f2 = par
    v1, v2 = V1 * f1, V2 * f2
    t = g["t"] if t is None else t
    def rhs(tt, a, r):
        c = max(a[0], 0) / v1
        cl = (CLI + (cl0 - CLI) * c50 / (c50 + c)) / 60
        return [r - cl * c - CL2 * c + CL2 * a[1] / v2, CL2 * c - CL2 * a[1] / v2]
    end = float(np.max(t)); stop = end if g["inf_end"] is None else min(g["inf_end"], end)
    pieces = [(0, g["dur"], g["dose"] / g["dur"] + g["rate"] / 60), (g["dur"], stop, g["rate"] / 60)] + ([(stop, end, 0.0)] if stop < end else [])
    y, sols = [0.0, 0.0], []
    for a, b, r in pieces:
        if b <= a: continue
        s = solve_ivp(rhs, (a, b), y, args=(r,), method="LSODA", rtol=1e-7, atol=1e-10, max_step=2.0, dense_output=True)
        sols.append((a, b, s)); y = s.y[:, -1]
    out = []
    for tt in t:
        for a, b, s in sols:
            if tt <= b + 1e-9: out.append(s.sol(max(tt, a))[0] / v1); break
    return np.array(out)

groups = mc.load_groups()
calib = [w for w in (mc.anesthetized_window(g) for g in groups) if w is not None]
def obj(x, free):
    par = [3.15, 0.92, 1.0, 1.0]
    for i, k in enumerate(free): par[k] = float(np.exp(x[i]))
    return sum(float(np.mean((np.log(g["c"]) - np.log(np.maximum(sim(par, g), 1e-9))) ** 2)) for g in calib), par
res = {}
for name, free, start in (("Cl0+C50", [0, 1], [3.2, 0.9]), ("Cl0+C50+V1", [0, 1, 2], [3.2, 0.9, 1.5]),
                          ("Cl0+C50+V2", [0, 1, 3], [3.2, 0.9, 2.0]), ("Cl0+C50+V1+V2", [0, 1, 2, 3], [3.2, 0.9, 1.5, 2.0])):
    best = None
    for jitter in (1.0, 0.7, 1.4):
        x0 = np.log(np.array(start) * np.array([1] * 2 + [jitter] * (len(start) - 2)))
        r = minimize(lambda x: obj(x, free)[0], x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 3000})
        if best is None or r.fun < best.fun: best = r
    sse, par = obj(best.x, free)
    pes = np.concatenate([(g["c"] - sim(par, g)) / sim(par, g) * 100 for g in calib])
    res[name] = {"par": par, "obj": sse, "MDPE": float(np.median(pes)), "MDAPE": float(np.median(np.abs(pes)))}
    print(f"{name:16s} obj {sse:.4f}  Cl0 {par[0]:.2f} C50 {par[1]:.2f} fV1 {par[2]:.2f} fV2 {par[3]:.2f}  MDPE {res[name]['MDPE']:+.1f} MDAPE {res[name]['MDAPE']:.1f}")
    for g in calib:
        print("     ", g["estudio"][:6], g["grupo"][:6], np.round(g["c"] / sim(par, g), 2).tolist())


# ── Validación cruzada entre estudios y comprobación con Lin despiertos y descenso tras la infusión ──
print("\nValidación cruzada (ajuste con un estudio, predicción del otro):")
def fit(free, start, use):
    best = None
    for jitter in (1.0, 0.7, 1.4):
        x0 = np.log(np.array(start) * np.array([1] * 2 + [jitter] * (len(start) - 2)))
        f = lambda x: sum(float(np.mean((np.log(g["c"]) - np.log(np.maximum(sim(_par(x, free), g), 1e-9))) ** 2)) for g in use) \
            + 10 * float(np.sum((x - np.clip(x, np.log(0.05), np.log(20))) ** 2))
        r = minimize(f, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 3000})
        if best is None or r.fun < best.fun: best = r
    return _par(best.x, free)
def _par(x, free):
    par = [3.15, 0.92, 1.0, 1.0]
    for i, k in enumerate(free): par[k] = float(np.exp(x[i]))
    return par
for name, free, start in (("Cl0+C50", [0, 1], [3.2, 0.9]), ("Cl0+C50+V1", [0, 1, 2], [3.2, 0.9, 1.5])):
    for out in ("Lin 2008", "Pascoe 2006"):
        train = [g for g in calib if g["estudio"] != out]; test = [g for g in calib if g["estudio"] == out]
        par = fit(free, start, train)
        pe = np.concatenate([(g["c"] - sim(par, g)) / sim(par, g) * 100 for g in test])
        print(f"  {name:12s} sin {out:12s} → Cl0 {par[0]:.2f} C50 {par[1]:.2f} fV1 {par[2]:.2f} · predice {out}: MDPE {np.median(pe):+.0f}% MDAPE {np.median(np.abs(pe)):.0f}%")
print("\nLin 2008 tras la anestesia (3–24 h) y descenso relativo tras detener la infusión (ISO):")
lin = [g for g in groups if g["estudio"] == "Lin 2008"]
for name in ("Cl0+C50", "Cl0+C50+V1"):
    par = res[name]["par"]
    for g in lin:
        m = (g["t"] >= 180) & (g["t"] <= 1440)
        p = sim(par, g)
        print(f"  {name:12s} {g['grupo'][:3]} 3–24 h: MDPE {np.median(((g['c'] - p) / p * 100)[m]):+.0f}%", end="")
        if g["grupo"].startswith("ISO"):
            tw = np.array([1440, 1455, 1470, 1485, 1500]); pw = sim(par, g, tw)
            print(f" · descenso pred {np.round(pw / pw[0], 2).tolist()} (medido [1.0, 0.76, 0.48, 0.32, 0.21])")
        else:
            print()
print("\nTasas de mantenimiento y carga (perro de 25 kg, objetivo 0,5 / 1 / 2 ng/mL):")
for name in ("Cl0+C50", "Cl0+C50+V1"):
    cl0, c50, f1, f2 = res[name]["par"]
    rates = [t * (CLI + (cl0 - CLI) * c50 / (c50 + t)) for t in (0.5, 1, 2)]
    print(f"  {name:12s} mantenimiento {np.round(rates, 2).tolist()} µg/kg/h · cantidad central en el objetivo {np.round([t * V1 * f1 for t in (0.5, 1, 2)], 2).tolist()} µg/kg")

cv = {}
for name, free, start in (("Cl0+C50", [0, 1], [3.2, 0.9]), ("Cl0+C50+V1", [0, 1, 2], [3.2, 0.9, 1.5])):
    for out in ("Lin 2008", "Pascoe 2006"):
        train = [g for g in calib if g["estudio"] != out]; test = [g for g in calib if g["estudio"] == out]
        par = fit(free, start, train)
        pe = np.concatenate([(g["c"] - sim(par, g)) / sim(par, g) * 100 for g in test])
        cv[f"{name} · sin {out}"] = {"par": par, "MDPE": float(np.median(pe)), "MDAPE": float(np.median(np.abs(pe)))}
lin_chk = {}
for name in ("Cl0+C50", "Cl0+C50+V1"):
    par = res[name]["par"]
    for g in lin:
        m = (g["t"] >= 180) & (g["t"] <= 1440)
        p = sim(par, g)
        lin_chk[f"{name} · {g['grupo'][:3]} 3-24 h"] = float(np.median(((g["c"] - p) / p * 100)[m]))
    iso = next(g for g in lin if g["grupo"].startswith("ISO"))
    tw = np.array([1440, 1455, 1470, 1485, 1500]); pw = sim(par, iso, tw)
    lin_chk[f"{name} · descenso relativo"] = (pw / pw[0]).tolist()
curves = {}
for g in calib:
    tt = np.linspace(10, float(g["t"].max()) * 1.05, 80)
    curves[f"{g['estudio']} · {g['grupo']}"] = {"t": tt.tolist(), "t_obs": g["t"].tolist(), "obs": g["c"].tolist(),
        **{name: sim(res[name]["par"], g, tt).tolist() for name in ("Cl0+C50", "Cl0+C50+V1")}}
(ROOT / "resultados" / "modelo_volumen.json").write_text(json.dumps(
    {"ajustes": res, "validacion_cruzada": cv, "lin_despiertos": lin_chk, "curvas": curves}, ensure_ascii=False, indent=1))
print("Guardado: resultados/modelo_volumen.json")
