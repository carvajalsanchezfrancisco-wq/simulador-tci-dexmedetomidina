"""Fase 1 · Validación externa del modelo de Levionnois et al. (2022) con datos publicados.

Para cada estudio se reproduce su protocolo con el modelo (solución exacta) y se compara la
concentración predicha con la medida. Medidas de Varvel sobre datos agregados (medias de grupo):
PE = (medida − predicha) / predicha. Uso: python3 analisis.py
"""
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"
RES.mkdir(exist_ok=True)

# Modelo publicado (por kg): V1, V2 en L/kg; Cl1, Cl2 en L/h/kg; IC 95 % de la Tabla 2
PK = {"V1": 1.03, "V2": 0.41, "Cl1": 1.16, "Cl2": 1.87}
CI = {"V1": (0.92, 1.15), "V2": (0.13, 0.70), "Cl1": (0.95, 1.37), "Cl2": (1.35, 2.38)}


def simulate(p, t_obs, dose, dur_min, rate_h=0.0, inf_end=None):
    """Cp (ng/mL) en t_obs (min) tras `dose` µg/kg en `dur_min` min seguida de `rate_h` µg/kg/h hasta `inf_end` min
    (None: sin detenerla)."""
    V1, V2, Cl1, Cl2 = p["V1"], p["V2"], p["Cl1"] / 60, p["Cl2"] / 60
    k10, k12, k21 = Cl1 / V1, Cl2 / V1, Cl2 / V2
    A = np.array([[-(k10 + k12), k21], [k12, -k21]])

    def step(x, R, h):
        big = np.zeros((3, 3)); big[:2, :2] = A; big[0, 2] = 1.0
        E = expm(big * h)
        return E[:2, :2] @ x + E[:2, 2] * R

    out, x, t = [], np.zeros(2), 0.0
    for to in sorted(t_obs):
        # tramos: bolo [0, dur], después infusión
        while t < to - 1e-12:
            if t < dur_min:
                h = min(dur_min, to) - t
                R = dose / dur_min + rate_h / 60
            elif inf_end is None or t < inf_end - 1e-12:
                h = (to if inf_end is None else min(to, inf_end)) - t
                R = rate_h / 60
            else:
                h = to - t
                R = 0.0
            x = step(x, R, h); t += h
        out.append(x[0] / V1)
    return np.array(out)


rows = list(csv.DictReader(open(ROOT / "datos" / "concentraciones_publicadas.csv", encoding="utf-8")))
groups = {}
for r in rows:
    groups.setdefault((r["estudio"], r["grupo"]), []).append(r)

rng = np.random.default_rng(7)
sig = {k: (math.log(hi) - math.log(lo)) / 3.92 for k, (lo, hi) in CI.items()}
draws = [{k: PK[k] * math.exp(rng.normal(0, sig[k])) for k in PK} for _ in range(1000)]

results, all_pe, figs = [], [], {}
for (study, group), rs in groups.items():
    dose, dur, rate = float(rs[0]["dosis_ugkg"]), float(rs[0]["duracion_admin_min"]), float(rs[0]["infusion_ugkgh"])
    inf_end = float(rs[0]["fin_infusion_min"]) if rs[0].get("fin_infusion_min") else None
    t = np.array([float(r["t_min"]) for r in rs])
    obs = np.array([float(r["c_ngml"]) for r in rs])
    ok = np.array([r["fiable"] == "si" for r in rs])
    pred = simulate(PK, t, dose, dur, rate, inf_end)
    pe = (obs - pred) / pred * 100
    band = np.array([simulate(d, t, dose, dur, rate, inf_end) for d in draws])
    lo, hi = np.percentile(band, 5, axis=0), np.percentile(band, 95, axis=0)
    inside = (obs >= lo) & (obs <= hi)

    # Aclaramiento que mejor reproduce cada estudio (V1, V2 y Cl2 fijos)
    def loss(cl):
        q = dict(PK, Cl1=cl)
        return float(np.sum((np.log(obs[ok]) - np.log(simulate(q, t[ok], dose, dur, rate, inf_end))) ** 2))
    cl_fit = minimize_scalar(loss, bounds=(0.2, 8), method="bounded").x

    tt = np.linspace(0.05, max(t) * 1.08, 220)
    figs[f"{study} · {group}"] = {"t": tt.tolist(), "pred": simulate(PK, tt, dose, dur, rate, inf_end).tolist(),
                                   "lo": np.percentile([simulate(d, tt, dose, dur, rate, inf_end) for d in draws[:300]], 5, axis=0).tolist(),
                                   "hi": np.percentile([simulate(d, tt, dose, dur, rate, inf_end) for d in draws[:300]], 95, axis=0).tolist(),
                                   "t_obs": t.tolist(), "obs": obs.tolist(), "ok": ok.tolist(), "dosis": dose}
    def estado_de(r, ti):
        e = r["estado"]
        return "despiertos (tras la anestesia)" if "0-2 h" in e and ti > 120 else e
    all_pe += [(study, group, dose if rate == 0 else f"{rate:g}/h", ti, o, p_, e, estado_de(r, ti), r["fuente"])
               for ti, o, p_, e, k, r in zip(t, obs, pred, pe, ok, rs) if k]
    results.append({
        "estudio": study, "grupo": group, "dosis_ugkg": dose, "infusion_ugkgh": rate, "n_puntos": int(ok.sum()),
        "estado": rs[0]["estado"], "muestra": rs[0]["muestra"],
        "MDPE": float(np.median(pe[ok])), "MDAPE": float(np.median(np.abs(pe[ok]))),
        "PE_min": float(pe[ok].min()), "PE_max": float(pe[ok].max()),
        "dentro_banda_pct": float(100 * inside[ok].mean()),
        "Cl_ajustado_Lhkg": float(cl_fit),
        "puntos": [{"t": float(a), "medida": float(b), "predicha": round(float(c), 3), "PE": round(float(d), 1), "fiable": bool(k)}
                   for a, b, c, d, k in zip(t, obs, pred, pe, ok)],
    })

# van Oostrom 2011 (solo resumen): media durante la infusión; horas de muestreo desconocidas
vo = []
for d, meas in ((1, 0.533), (3, 1.869), (5, 4.017)):
    tt = np.linspace(10, 60, 51)
    p1 = float(simulate(PK, tt, d, 1.0, d).mean())
    tt2 = np.linspace(10, 120, 111)
    p2 = float(simulate(PK, tt2, d, 1.0, d).mean())
    vo.append({"infusion_ugkgh": d, "medida": meas, "pred_10_60": p1, "pred_10_120": p2,
               "PE_10_60": 100 * (meas - p1) / p1, "PE_10_120": 100 * (meas - p2) / p2,
               "Cl_aparente_Lhkg": d / meas})

PE = 6   # posición del error de predicción en cada tupla de all_pe
pe_all = np.array([x[PE] for x in all_pe])
pooled = {"n": len(pe_all), "MDPE": float(np.median(pe_all)), "MDAPE": float(np.median(np.abs(pe_all)))}
by_dose = {}
for d in sorted({str(x[2]) for x in all_pe}):
    e = np.array([x[PE] for x in all_pe if str(x[2]) == d])
    by_dose[d] = {"n": len(e), "MDPE": float(np.median(e)), "MDAPE": float(np.median(np.abs(e)))}

out = {"modelo": PK, "estudios": results, "van_oostrom_provisional": vo, "global": pooled, "por_dosis": by_dose}
(RES / "resultados_fase1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
(RES / "figuras_fase1.json").write_text(json.dumps(figs))

print(f"{'Estudio':38s} {'dosis':>5s} {'n':>3s} {'MDPE':>7s} {'MDAPE':>7s} {'PE rango':>16s} {'banda':>6s} {'Cl ajust.':>9s}")
for r in results:
    print(f"{r['estudio'] + ' · ' + r['grupo']:38s} {r['dosis_ugkg']:5g} {r['n_puntos']:3d} {r['MDPE']:+7.1f} {r['MDAPE']:7.1f} "
          f"{r['PE_min']:+7.0f} a {r['PE_max']:+5.0f} {r['dentro_banda_pct']:5.0f}% {r['Cl_ajustado_Lhkg']:9.2f}")
    for p in r["puntos"]:
        print(f"      t={p['t']:5g}  medida {p['medida']:6.2f}  predicha {p['predicha']:6.2f}  PE {p['PE']:+6.1f}%{'' if p['fiable'] else '  (no fiable)'}")
print("van Oostrom (provisional):")
for v in vo:
    print(f"   {v['infusion_ugkgh']} µg/kg/h: medida {v['medida']:.2f} · pred 10-60 {v['pred_10_60']:.2f} ({v['PE_10_60']:+.0f}%) · "
          f"pred 10-120 {v['pred_10_120']:.2f} ({v['PE_10_120']:+.0f}%) · Cl aparente {v['Cl_aparente_Lhkg']:.2f} L/h/kg")
print("Global:", pooled, "\nPor dosis:", by_dose)

# ── Sensibilidad ──────────────────────────────────────────────────────────────
def summ(sel):
    e = np.array([x[PE] for x in all_pe if sel(x)])
    return {"n": len(e), "MDPE": float(np.median(e)), "MDAPE": float(np.median(np.abs(e)))}
awake = lambda x: x[7].startswith("despiertos")
approx = lambda x: "aproximado" in x[8] or "asignado" in x[8]
sens = {
    "todos": summ(lambda x: True),
    "sin_de_SantAna_2024": summ(lambda x: not x[0].startswith("de Sant")),
    "solo_t>=10min": summ(lambda x: x[3] >= 10),
    "sin_2024_y_t>=10min": summ(lambda x: x[3] >= 10 and not x[0].startswith("de Sant")),
    "solo_infusiones": summ(lambda x: x[0].startswith("van Oostrom")),
    "solo_bolos_t>=10min_sin_2024": summ(lambda x: x[3] >= 10 and not x[0].startswith(("de Sant", "van Oostrom"))),
    "solo_t>=30min": summ(lambda x: x[3] >= 30),
    "despiertos": summ(awake),
    "anestesiados": summ(lambda x: not awake(x)),
    "infusiones_t>=10min": summ(lambda x: x[3] >= 10 and str(x[2]).endswith("/h")),
    "sin_puntos_aproximados": summ(lambda x: not approx(x)),
    "sin_Dent": summ(lambda x: not x[0].startswith("Dent")),
}

# ── Resúmenes publicados (AUC y concentración en meseta) y aclaramiento aparente ──
def pred_auc(dose, dur, rate_h, inf_min, t_end):
    tt = np.linspace(0, t_end, int(t_end * 2) + 1)
    c = []
    x_end = None
    c1 = simulate(PK, tt[tt <= inf_min], dose, dur, rate_h)
    if t_end > inf_min:                                       # tras detener la infusión: descenso libre
        tail_t = tt[tt > inf_min] - inf_min
        V1, V2, Cl1, Cl2 = PK["V1"], PK["V2"], PK["Cl1"] / 60, PK["Cl2"] / 60
        k10, k12, k21 = Cl1 / V1, Cl2 / V1, Cl2 / V2
        A = np.array([[-(k10 + k12), k21], [k12, -k21]])
        x0 = None
        # estado al final de la infusión
        big = np.zeros((3, 3)); big[:2, :2] = A; big[0, 2] = 1.0
        x = np.zeros(2); t0 = 0.0
        for seg_end, R in ((dur, dose / dur + rate_h / 60), (inf_min, rate_h / 60)):
            E = expm(big * (seg_end - t0)); x = E[:2, :2] @ x + E[:2, 2] * R; t0 = seg_end
        c2 = [(expm(A * h) @ x)[0] / V1 for h in tail_t]
        c = np.concatenate([c1, c2])
    else:
        c = c1
    return float(np.trapezoid(c, tt) / 60)                      # h·ng/mL

lin_dose = 1.055
resumenes = [
    {"estudio": "Levionnois 2022 (referencia)", "medida": "AUC0-∞ tras 10 µg/kg (h·ng/mL)", "medido": 8.65,
     "predicho": 10 / PK["Cl1"], "dosis_total": 10.0},
    {"estudio": "Dent 2019 · 5 µg/kg IV (despiertos)", "medida": "AUC0-∞ (h·ng/mL)", "medido": 655 / 60,
     "predicho": 5 / PK["Cl1"], "dosis_total": 5.0},
    {"estudio": "Lin 2008 · ISO (≈1 µg/kg + 1 µg/kg/h, 24 h)", "medida": "AUC 0-26 h (h·ng/mL)", "medido": 8.61,
     "predicho": pred_auc(lin_dose, 1, lin_dose, 1440, 1560), "dosis_total": lin_dose * 25},
    {"estudio": "Lin 2008 · PRO (≈1 µg/kg + 1 µg/kg/h, 24 h)", "medida": "AUC 0-26 h (h·ng/mL)", "medido": 8.53,
     "predicho": pred_auc(lin_dose, 1, lin_dose, 1440, 1560), "dosis_total": lin_dose * 25},
]
for r in resumenes:
    r["PE"] = 100 * (r["medido"] - r["predicho"]) / r["predicho"]
    r["Cl_aparente_Lhkg"] = r["dosis_total"] / r["medido"]

# Aclaramiento aparente en meseta = tasa / Cp media (infusiones con datos cerca del equilibrio)
meseta = [
    {"estudio": "Pascoe 2006 (isoflurano)", "tasa": 0.1, "cp": None, "nota": "Cp < 0,05 ng/mL (no cuantificable): Cl > 2,0"},
    {"estudio": "Pascoe 2006 (isoflurano)", "tasa": 0.5, "cp": 0.198},
    {"estudio": "Pascoe 2006 (isoflurano)", "tasa": 3.0, "cp": 1.903},
    # Lin 2008, Fig. 2 digitalizada: media de los puntos de cada periodo
    {"estudio": "Lin 2008 ISO (0,25-2 h)", "tasa": lin_dose, "cp": 0.427},
    {"estudio": "Lin 2008 PRO (0,25-2 h)", "tasa": lin_dose, "cp": 0.360},
    {"estudio": "Lin 2008 ISO (3-12 h, despiertos)", "tasa": lin_dose, "cp": 0.372},
    {"estudio": "Lin 2008 PRO (3-12 h, despiertos)", "tasa": lin_dose, "cp": 0.384},
    {"estudio": "Lin 2008 ISO (24 h)", "tasa": lin_dose, "cp": 0.234},
    {"estudio": "Lin 2008 PRO (24 h)", "tasa": lin_dose, "cp": 0.283},
    {"estudio": "van Oostrom 2011 (despiertos)", "tasa": 1.0, "cp": 0.533},
    {"estudio": "van Oostrom 2011 (despiertos)", "tasa": 3.0, "cp": 1.869},
    {"estudio": "van Oostrom 2011 (despiertos)", "tasa": 5.0, "cp": 4.017},
]
for m in meseta:
    m["Cl_aparente_Lhkg"] = m["tasa"] / m["cp"] if m["cp"] else None
    m["cp_modelo_equilibrio"] = m["tasa"] / PK["Cl1"]
out["resumenes"] = resumenes
out["meseta"] = meseta
out["sensibilidad"] = sens
(RES / "resultados_fase1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("Sensibilidad:")
for k, v in sens.items():
    print(f"   {k:24s} n={v['n']:2d}  MDPE {v['MDPE']:+6.1f}%  MDAPE {v['MDAPE']:5.1f}%")
(RES / "resultados_fase1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print("Resúmenes publicados:")
for r in resumenes:
    print(f"   {r['estudio']:45s} {r['medida']:32s} medido {r['medido']:6.2f}  predicho {r['predicho']:6.2f}  PE {r['PE']:+5.0f} %  Cl ap. {r['Cl_aparente_Lhkg']:.2f}")
print("Meseta (Cl aparente = tasa / Cp):")
for m in meseta:
    cl = f"{m['Cl_aparente_Lhkg']:.2f}" if m["Cl_aparente_Lhkg"] else m["nota"]
    print(f"   {m['estudio']:32s} {m['tasa']:5.2f} µg/kg/h  Cp {m['cp']}  (modelo {m['cp_modelo_equilibrio']:.2f})  Cl {cl}")
