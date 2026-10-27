"""Recalcula la Cp a partir del CSV exportado por el simulador (v1.1.1 o posterior).

Implementación independiente del simulador: lee del CSV el peso, la concentración de la jeringa, la
premedicación IM y el REGISTRO DE TASAS (tasa que infundió la bomba, segundo a segundo), y resuelve:
  · el modelo publicado (Levionnois et al. 2022) de forma exacta (exponencial de matriz por tramos), y
  · los modelos con aclaramiento dependiente de la Cp con un integrador de alta precisión (Dormand-Prince 8,
    tolerancia relativa 1e-10): «anestesiado» (v1.2.0; volúmenes de Levionnois) y «corregido» (v1.4.0; V1, V2
    y aclaramiento reajustados en perros anestesiados).
El CSV indica qué modelo guiaba la bomba («Código del modelo»; sin ese dato, v1.1.1: el publicado). Las
constantes son las de este archivo; se comprueba que coinciden con las que anotó el simulador en el CSV.

  · Verificación (Fase 0): compara la Cp exacta con la que el programa anotó en cada fila del registro de tasas.
  · Si junto al CSV hay un archivo «<nombre>_lecturas.csv» (codigo;tiempo;cp_pantalla), compara también la Cp
    leída en pantalla en esos instantes, incluidos los posteriores al fin de la infusión.
  · Fase 3: con --muestras, calcula la Cp predicha POR CADA MODELO en la hora de cada muestra de sangre
    (anotada en el cuaderno con el reloj del simulador), con la misma infusión real. Así se comparan los
    modelos con la concentración medida, sea cual sea el que guiaba la bomba. Archivo con columnas «codigo;tiempo», tiempo en hh:mm:ss.

Usos:
  python3 reconstruir_cp.py caso.csv                          tabla por fila del registro de tasas
  python3 reconstruir_cp.py caso.csv --muestras horas.csv     Cp predicha en cada muestra
  python3 reconstruir_cp.py --verificar carpeta/ [--json r.json]
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

# Levionnois et al. 2022, Tabla 2 (por kg): L/kg y L/h/kg
V1_KG, V2_KG, CL1_KG, CL2_KG = 1.03, 0.41, 1.16, 1.87
# Aclaramiento dependiente de la Cp: Cl(C) = Cl∞ + (Cl0 − Cl∞)·C50/(C50 + C), Cl∞ = CL1_KG
#   «anestesiado» (v1.2.0, validacion_fase1/modelo_corregido.py): volúmenes de Levionnois
#   «corregido» (v1.4.0, validacion_fase1/modelo_volumenes_aclaramiento.py): V1 y V2 reajustados en anestesia
CL0_KG, C50 = 3.15, 0.92
V1C_KG, V2C_KG, CL0C_KG, C50C = 2.70, 0.72, 3.47, 0.21
MODELS = {"corregido": (V1C_KG, V2C_KG, CL2_KG, CL1_KG, CL0C_KG, C50C),      # V1, V2, Cl2, Cl∞, Cl0, C50
          "anestesiado": (V1_KG, V2_KG, CL2_KG, CL1_KG, CL0_KG, C50),
          "publicado": (V1_KG, V2_KG, CL2_KG, CL1_KG, CL1_KG, None)}
# Premedicación IM tal como la modela el simulador (supuestos, no publicados): inyección 10 min antes,
# biodisponibilidad 1, semivida de absorción 3 min
IM_DELAY_MIN, IM_F, IM_HALF_MIN = 10.0, 1.0, 3.0
TOL_REL, TOL_ABS = 0.005, 0.0005        # Fase 0: ≤ 0,5 % (o 0,0005 ng/mL con Cp casi nula)


def num(text):
    text = text.strip()
    return float(text.replace(",", ".")) if text else math.nan


def parse_case_csv(path):
    """Devuelve {"cabecera": {...}, "secciones": {nombre: [filas como dict]}}."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    header, sections, current, columns = {}, {}, None, None
    full = {}
    for row in rows:
        if not row or all(not c.strip() for c in row):
            current, columns = None, None
            continue
        if len(row) == 1 and row[0].isupper():
            current, columns = row[0], None
            sections[current] = []
            continue
        if current is None:
            if len(row) >= 2:
                header[row[0]] = row[1]
                full[row[0]] = row[1:]
            continue
        if columns is None:
            columns = row
            continue
        sections[current].append(dict(zip(columns, row)))
    return {"cabecera": header, "secciones": sections, "cabecera_completa": full}


def pump_model(case):
    """Modelo que guiaba la bomba y si los parámetros anotados en el CSV coinciden con los de este archivo."""
    code = case["cabecera"].get("Código del modelo", "publicado").strip() or "publicado"
    key = next((k for k in case["cabecera_completa"] if k.startswith("Parámetros del modelo")), None)
    if key is None:
        return code, code == "publicado"
    vals = [num(v) for v in case["cabecera_completa"][key][:6]]
    ref = MODELS.get(code)
    same = ref is not None and all((math.isnan(a) and b is None) or (b is not None and abs(a - b) < 1e-12) for a, b in zip(vals, ref))
    return code, same


def model(weight):
    V1, V2 = V1_KG * weight, V2_KG * weight
    k10, k12, k21 = CL1_KG * weight / 60 / V1, CL2_KG * weight / 60 / V1, CL2_KG * weight / 60 / V2
    ka = math.log(2) / IM_HALF_MIN
    A = np.array([[-(k10 + k12), k21, ka], [k12, -k21, 0.0], [0.0, 0.0, -ka]])
    return V1, A


def propagate(A, x, rate_ug_min, minutes):
    """Estado exacto tras `minutes` con infusión constante al compartimento central."""
    big = np.zeros((4, 4))
    big[:3, :3] = A
    big[0, 3] = 1.0
    E = expm(big * minutes)
    return E[:3, :3] @ x + E[:3, 3] * rate_ug_min


def nonlinear_cp(weight, conc, premed, no_load, changes, seconds, model_id):
    """Modelo corregido: Cp en cada segundo de `seconds`, integrando entre cambios de tasa."""
    v1, v2, cl2, clinf, cl0, c50 = MODELS[model_id]
    V1, V2, Cl2 = v1 * weight, v2 * weight, cl2 * weight / 60
    ka = math.log(2) / IM_HALF_MIN

    def rhs(t, x, R):
        c = x[0] / V1
        cl = (clinf + (cl0 - clinf) * c50 / (c50 + max(c, 0.0))) * weight / 60
        return [R + ka * x[2] - cl * c - Cl2 * c + Cl2 * x[1] / V2, Cl2 * c - Cl2 * x[1] / V2, -ka * x[2]]

    kw = dict(method="DOP853", rtol=1e-10, atol=1e-12)
    x = np.zeros(3)
    if no_load and premed > 0:
        x[2] = premed * weight * IM_F
        x = solve_ivp(rhs, (0, IM_DELAY_MIN), x, args=(0.0,), **kw).y[:, -1]
    out, t, idx, rate = {}, 0, 0, 0.0
    for target in sorted(set(seconds)):
        while t < target:
            while idx < len(changes) and changes[idx][0] <= t:
                rate = changes[idx][1]
                idx += 1
            nxt = changes[idx][0] if idx < len(changes) else math.inf
            step_to = min(target, nxt)
            x = solve_ivp(rhs, (t / 60, step_to / 60), x, args=(rate * conc / 60,), **kw).y[:, -1]
            t = step_to
        out[target] = x[0] / V1
    return out


def exact_cp(case, seconds, model_id=None):
    """Cp (ng/mL) en cada segundo de `seconds` según el registro de tasas del CSV, con el modelo indicado
    (por defecto, el que guiaba la bomba)."""
    model_id = model_id or pump_model(case)[0]
    h = case["cabecera"]
    weight = num(h["Peso (kg)"])
    conc = num(h["Concentración en jeringa (µg/mL)"])
    premed_key = next((k for k in h if k.startswith("Premedicación IM")), None)
    premed = num(h[premed_key]) if premed_key else 0.0
    no_load = h.get("Inicio de la infusión", "").startswith("Sin carga")
    if model_id != "publicado":
        changes = sorted((int(num(r["Segundo"])), num(r["Tasa (mL/h)"])) for r in case["secciones"]["REGISTRO DE TASAS"])
        return nonlinear_cp(weight, conc, premed, no_load, changes, seconds, model_id)
    V1, A = model(weight)
    x = np.zeros(3)
    if no_load and premed > 0:
        x[2] = premed * weight * IM_F
        x = expm(A * IM_DELAY_MIN) @ x
    changes = [(int(num(r["Segundo"])), num(r["Tasa (mL/h)"])) for r in case["secciones"]["REGISTRO DE TASAS"]]
    changes.sort()
    out, t, idx, rate = {}, 0, 0, 0.0
    for target in sorted(set(seconds)):
        while t < target:
            while idx < len(changes) and changes[idx][0] <= t:
                rate = changes[idx][1]
                idx += 1
            nxt = changes[idx][0] if idx < len(changes) else math.inf
            step_to = min(target, nxt)
            x = propagate(A, x, rate * conc / 60, (step_to - t) / 60)
            t = step_to
        out[target] = x[0] / V1
    return out


def clock(text):
    h, m, s = (int(x) for x in text.strip().split(":"))
    return 3600 * h + 60 * m + s


def predict_samples(path, times_path):
    """Fase 3: Cp predicha por cada modelo en la hora de cada muestra anotada en el cuaderno."""
    case = parse_case_csv(path)
    with open(times_path, encoding="utf-8-sig", newline="") as f:
        items = [(r["codigo"].strip(), clock(r["tiempo"])) for r in csv.DictReader(f, delimiter=";")]
    secs = [s for _, s in items]
    pred = {m: exact_cp(case, secs, m) for m in MODELS}
    end = case["cabecera"].get("Fin de la infusión (s)", "")
    end = int(num(end)) if end and end[0].isdigit() else None
    return [{"codigo": c, "segundo": s, "tiempo": f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}",
             "min_desde_fin": round((s - end) / 60, 2) if end is not None and s >= end else None,
             **{f"cp_{m}": float(pred[m][s]) for m in MODELS}} for c, s in items]


def analyse(path):
    case = parse_case_csv(path)
    sec = case["secciones"]
    rates = sec.get("REGISTRO DE TASAS", [])
    secs = [int(num(r["Segundo"])) for r in rates]
    exact = exact_cp(case, secs) if secs else {}
    rows = []
    for r in rates:
        s = int(num(r["Segundo"]))
        shown = num(r["Cp calculada (ng/mL)"])
        ref = float(exact[s])
        diff = shown - ref
        rel = diff / ref if ref > 1e-9 else 0.0
        rows.append({"tipo": "fin" if r.get("Nota") else "tasa", "segundo": s, "tasa_ml_h": num(r["Tasa (mL/h)"]),
                     "cp_simulador": shown, "cp_exacta": ref, "dif_ng_ml": diff, "dif_pct": 100 * rel,
                     "pass": bool(abs(diff) <= max(TOL_REL * ref, TOL_ABS))})
    readings = Path(path).with_name(Path(path).stem + "_lecturas.csv")
    if readings.exists():
        with open(readings, encoding="utf-8-sig", newline="") as f:
            items = list(csv.DictReader(f, delimiter=";"))
        ex = exact_cp(case, [clock(r["tiempo"]) for r in items])
        for r in items:
            s = clock(r["tiempo"])
            text = r["cp_pantalla"].strip().replace(",", ".")
            shown = float(text)
            rounding = 0.5 * 10 ** -(len(text.split(".")[1]) if "." in text else 0)   # redondeo de la pantalla
            ref = float(ex[s])
            diff = shown - ref
            rows.append({"tipo": f"pantalla {r['codigo']}", "segundo": s, "tasa_ml_h": math.nan, "cp_simulador": shown,
                         "cp_exacta": ref, "dif_ng_ml": diff, "dif_pct": 100 * diff / ref if ref > 1e-9 else 0.0,
                         "pass": bool(abs(diff) <= max(TOL_REL * ref, TOL_ABS) + rounding)})
    h = case["cabecera"]
    code, params_ok = pump_model(case)
    return {"archivo": Path(path).name, "version": h.get("Versión del simulador", ""), "lecturas": readings.exists(),
            "modelo": code, "parametros_coinciden": params_ok,
            "peso_kg": num(h["Peso (kg)"]), "conc_ug_ml": num(h["Concentración en jeringa (µg/mL)"]),
            "n_tasas": len(sec.get("REGISTRO DE TASAS", [])), "filas": rows,
            "max_dif_pct": max((abs(r["dif_pct"]) for r in rows), default=0.0),
            "pass": all(r["pass"] for r in rows) and len(rows) > 0 and params_ok}


def main(argv):
    out_json, verify, paths, times = None, False, [], None
    it = iter(argv)
    for a in it:
        if a == "--json":
            out_json = next(it)
        elif a == "--muestras":
            times = next(it)
        elif a == "--verificar":
            verify = True
        else:
            p = Path(a)
            paths += sorted(q for q in p.glob("*.csv") if not q.stem.endswith("_lecturas")) if p.is_dir() else [p]
    if times:
        rows = predict_samples(paths[0], times)
        code = pump_model(parse_case_csv(paths[0]))[0]
        print(f"{paths[0].name} · bomba guiada por el modelo «{code}» · Cp predicha por cada modelo (ng/mL)")
        print(f"    {'código':6s} {'tiempo':8s}  " + "  ".join(f"{m:>11s}" for m in MODELS))
        for r in rows:
            post = f" · {r['min_desde_fin']} min tras el fin" if r["min_desde_fin"] is not None else ""
            print(f"    {r['codigo']:6s} {r['tiempo']}  " + "  ".join(f"{r['cp_' + m]:11.4f}" for m in MODELS) + post)
        if out_json:
            Path(out_json).write_text(json.dumps({"archivo": paths[0].name, "modelo_bomba": code, "muestras": rows},
                                                 ensure_ascii=False, indent=1))
        return 0
    results = [analyse(p) for p in paths]
    for r in results:
        print(f"{'✔' if r['pass'] else '✘'} {r['archivo']} · v{r['version']} · modelo {r['modelo']}"
              f"{'' if r['parametros_coinciden'] else ' (PARÁMETROS DISTINTOS)'} · "
              f"{len(r['filas'])} valores · dif. máx. {r['max_dif_pct']:.3f} %")
        if not verify:
            for f in r["filas"]:
                print(f"    {f['tipo']:13s} {f['segundo']:6d} s  {f['tasa_ml_h']:6.1f} mL/h  simulador {f['cp_simulador']:.4f}  "
                      f"exacta {f['cp_exacta']:.4f}  ({f['dif_pct']:+.3f} %)")
    if out_json:
        Path(out_json).write_text(json.dumps({"tolerancia_rel": TOL_REL, "tolerancia_abs": TOL_ABS, "archivos": results},
                                             ensure_ascii=False, indent=1))
    ok = all(r["pass"] for r in results) and len(results) > 0
    if verify:
        print("RECONSTRUCCIÓN DESDE EL CSV:", "CONFORME" if ok else "NO CONFORME")
    return 0 if ok or not verify else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
