"""Figura de modelo_volumenes_aclaramiento.py: Cp medida frente a la predicha por cada estructura en los cuatro grupos
de perros anestesiados (Pascoe 2006 y Lin 2008).

Uso: python3 figura_volumenes.py   (después de modelo_volumenes_aclaramiento.py)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
d = json.loads((ROOT / "resultados" / "modelo_volumenes_aclaramiento.json").read_text(encoding="utf-8"))
STYLE = {"A": ("#8a94a0", "--"), "C": ("#1f5fa0", "-"), "D": ("#c4622d", "-"), "E": ("#3f8f5a", ":")}

fig, axes = plt.subplots(2, 2, figsize=(10, 7.2))
for ax, (name, cv) in zip(axes.flat, d["curvas"].items()):
    t = [x / 60 for x in cv["t"]]
    for m, (col, ls) in STYLE.items():
        ax.plot(t, cv[m], color=col, ls=ls, lw=1.8, label=d["modelos"][m]["nombre"])
    ax.plot([x / 60 for x in cv["t_obs"]], cv["obs"], "o", color="#1b1f24", ms=5, label="Medido (media digitalizada)")
    ax.set_title(name.replace(": isoflurano 2 h + 24 h", " (isoflurano)").replace(": propofol 2 h + 24 h", " (propofol)"), fontsize=10)
    ax.set_xlabel("Tiempo (h)"); ax.set_ylabel("Cp (ng/mL)")
    ax.set_ylim(bottom=0); ax.grid(alpha=0.25)
h, lab = axes.flat[0].get_legend_handles_labels()
fig.legend(h, lab, loc="lower center", ncol=3, fontsize=8.5, frameon=False)
fig.suptitle("Perros anestesiados: Cp medida y predicha según la estructura del modelo", fontsize=12)
fig.tight_layout(rect=(0, 0.08, 1, 0.96))
out = ROOT / "resultados" / "fig_volumenes_aclaramiento.png"
fig.savefig(out, dpi=160)
print("Guardado:", out.relative_to(ROOT))
