"""Genera el informe de la Fase 1 (PDF), versión 4 (curvas completas de Lin 2008 y Pascoe 2006 digitalizadas): siete estudios, incluidos perros anestesiados, y el modelo corregido
para perros anestesiados que usa por defecto el simulador desde la v1.2.0 (modelo_corregido.py)."""
import json
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
RES = ROOT / "resultados"
R = json.loads((RES / "resultados_fase1.json").read_text())
FIG = json.loads((RES / "figuras_fase1.json").read_text())
MX = json.loads((RES / "modelo_experimental.json").read_text())
MC = json.loads((RES / "modelo_corregido.json").read_text())
MV = json.loads((RES / "modelo_volumen.json").read_text())
OUT = ROOT / "informe" / "Informe_Fase1_validacion_externa_v4.pdf"

# ── Figuras (paleta validada: azul = modelo, naranja = medido) ────────────────
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})
COMMA = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))
SHORT = {"Kuusela 2000 · DEX10": "Kuusela 2000 · 10 µg/kg (despiertos)",
         "Kuusela 2000 · DEX20": "Kuusela 2000 · 20 µg/kg (despiertos)",
         "Honkavaara 2012 · D (sin MK-467)": "Honkavaara 2012 · 10 µg/kg (despiertos)",
         "de Sant'Ana Alves 2024 · 2 ug/kg en 2 min": "de Sant'Ana Alves 2024 · 2 µg/kg (despiertos)",
         "van Oostrom 2011 · 1 µg/kg + 1 µg/kg/h": "van Oostrom 2011 · 1 µg/kg/h (despiertos)",
         "van Oostrom 2011 · 3 µg/kg + 3 µg/kg/h": "van Oostrom 2011 · 3 µg/kg/h (despiertos)",
         "van Oostrom 2011 · 5 µg/kg + 5 µg/kg/h": "van Oostrom 2011 · 5 µg/kg/h (despiertos)",
         "Lin 2008 · ISO: isoflurano 2 h + 24 h": "Lin 2008 · ≈1 µg/kg/h · isoflurano 2 h",
         "Lin 2008 · PRO: propofol 2 h + 24 h": "Lin 2008 · ≈1 µg/kg/h · propofol 2 h",
         "Pascoe 2006 · 0.5 µg/kg en 6 min + 0.5 µg/kg/h": "Pascoe 2006 · 0,5 µg/kg/h · isoflurano",
         "Pascoe 2006 · 3 µg/kg en 6 min + 3 µg/kg/h": "Pascoe 2006 · 3 µg/kg/h · isoflurano",
         "Dent 2019 · 5 µg/kg IV": "Dent 2019 · 5 µg/kg (despiertos)"}


def fig_estudios():
    keys = list(FIG.keys())
    fig, axes = plt.subplots(6, 2, figsize=(6.6, 10.6))
    for ax, k in zip(axes.flat, keys):
        d = FIG[k]
        t = np.array(d["t"])
        ax.fill_between(t, d["lo"], d["hi"], color=BLUE, alpha=0.15, lw=0, label="Incertidumbre del modelo (IC 95 %)")
        ax.plot(t, d["pred"], color=BLUE, lw=2, label="Predicción del modelo")
        to, ob, ok = np.array(d["t_obs"]), np.array(d["obs"]), np.array(d["ok"])
        ax.plot(to[ok], ob[ok], ls="none", marker="o", ms=5, mfc=ORANGE, mec="white", mew=0.8, label="Medido (media publicada)")
        if (~ok).any():
            ax.plot(to[~ok], ob[~ok], ls="none", marker="o", ms=5, mfc="white", mec=ORANGE, mew=1.2, label="Medido, no fiable")
        ax.set_yscale("log")
        lo_y = min(min(d["lo"]), ob.min()) * 0.75; hi_y = max(max(d["hi"]), ob.max()) * 1.3
        ax.set_ylim(lo_y, hi_y)
        ax.yaxis.set_major_locator(FixedLocator([v for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50) if lo_y <= v <= hi_y]))
        ax.yaxis.set_major_formatter(COMMA)
        ax.yaxis.set_minor_locator(NullLocator()); ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_title(SHORT.get(k, k), fontsize=7.6, color=INK, loc="left")
        ax.set_xlim(0, t[-1])
        ax.xaxis.set_major_formatter(COMMA)
    for ax in axes[-1, :]:
        ax.set_xlabel("Tiempo (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Cp (ng/mL, log)")
    h, l = [], []
    for ax in list(axes.flat)[:len(keys)]:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l:
                h.append(hh); l.append(ll)
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=7.4, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = RES / "fig_estudios.png"; fig.savefig(p, dpi=220); plt.close(fig)
    return p


def fig_meseta():
    """Aclaramiento aparente (tasa / Cp en meseta) frente a la Cp medida."""
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    c = np.array(MC["cl_vs_c"]["c"]); keep = c > 0
    ax.plot(c[keep], np.array(MC["cl_vs_c"]["cl"])[keep], color=BLUE, lw=2, label="Modelo corregido (simulador v1.2.0)")
    ax.axhline(1.16, color=BLUE, lw=1.2, ls=(0, (4, 3)), label="Modelo publicado (Levionnois): 1,16 constante")
    cx = np.array(MX["cl_vs_c"]["c"]); kx = cx > 0
    ax.plot(cx[kx], np.array(MX["cl_vs_c"]["cl"])[kx], color=MUTED, lw=1, ls=(0, (1, 1.5)), label="Modelo experimental (apartado 6, no adoptado)")
    awake = [m for m in R["meseta"] if m["cp"] and "despiertos" in m["estudio"]]
    anest = [m for m in R["meseta"] if m["cp"] and "despiertos" not in m["estudio"]]
    ax.plot([m["cp"] for m in awake], [m["Cl_aparente_Lhkg"] for m in awake], "o", ms=7, mfc="white", mec=ORANGE, mew=1.8,
            ls="none", label="Medido · despiertos (van Oostrom)")
    ax.plot([m["cp"] for m in anest], [m["Cl_aparente_Lhkg"] for m in anest], "o", ms=7, mfc=ORANGE, mec="white", mew=0.8,
            ls="none", label="Medido · anestesiados (Pascoe 2006, Lin 2008)")
    for m in R["meseta"]:
        if not m["cp"]:
            continue
        txt = {"Lin 2008 ISO (24 h)": "Lin 24 h", "Lin 2008 PRO (24 h)": "Lin 24 h"}.get(m["estudio"])
        if txt:
            ax.annotate(txt, (m["cp"], m["Cl_aparente_Lhkg"]), textcoords="offset points", xytext=(7, -2), fontsize=7, color=MUTED)
    ax.set_xscale("log")
    ax.set_xlim(0.15, 6); ax.set_ylim(0, 5.2)
    ax.xaxis.set_major_locator(FixedLocator([0.2, 0.5, 1, 2, 5])); ax.xaxis.set_major_formatter(COMMA)
    ax.xaxis.set_minor_locator(NullLocator()); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_xlabel("Cp medida durante la infusión (ng/mL, escala log)")
    ax.set_ylabel("Aclaramiento aparente (L/h/kg)")
    ax.legend(loc="upper right", fontsize=7.2)
    fig.tight_layout()
    p = RES / "fig_cl_meseta.png"; fig.savefig(p, dpi=220); plt.close(fig)
    return p


def fig_obs_pred():
    """Medido frente a predicho, con el modelo publicado y con el corregido."""
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.3), sharex=True, sharey=True)
    for ax, key, title in ((axes[0], "pred_publicado", "Modelo publicado"), (axes[1], "pred_corregido", "Modelo corregido")):
        lim = (0.12, 20)
        x = np.geomspace(*lim, 50)
        ax.fill_between(x, x * 0.7, x * 1.3, color=BLUE, alpha=0.10, lw=0, label="±30 %")
        ax.plot(x, x, color=BLUE, lw=1.2, label="Medido = predicho")
        for state, mfc, lab in (("despiertos", "white", "Despiertos (no usados para calibrar)"),
                                ("anestesiados", ORANGE, "Anestesiados (calibración)")):
            pts = [(p, c) for g in MC["por_grupo"] if g["estado"] == state and not g["estudio"].startswith("Dent")
                   for p, c in zip(g[key], g["c"])]
            ax.plot([a for a, _ in pts], [b for _, b in pts], "o", ms=5, mfc=mfc, mec=ORANGE, mew=1.2, ls="none", label=lab)
        dent = [g for g in MC["por_grupo"] if g["estudio"].startswith("Dent")]
        for g in dent:
            ax.plot(g[key], g["c"], "x", ms=6, color=MUTED, ls="none", label="Dent 2019 (fuera de patrón)")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*lim); ax.set_ylim(*lim)
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(FixedLocator([0.2, 0.5, 1, 2, 5, 10])); axis.set_major_formatter(COMMA)
            axis.set_minor_locator(NullLocator()); axis.set_minor_formatter(NullFormatter())
        ax.set_title(title, fontsize=8.5, color=INK, loc="left")
        ax.set_xlabel("Cp predicha (ng/mL)")
    axes[0].set_ylabel("Cp medida (ng/mL)")
    h, l = axes[1].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7.2, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    p = RES / "fig_obs_pred.png"; fig.savefig(p, dpi=220); plt.close(fig)
    return p


def fig_volumen():
    """Curso temporal en anestesia: medido frente al modelo corregido (solo Cl) y al exploratorio (Cl + V1)."""
    keys = list(MV["curvas"].keys())
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.6))
    for ax, k in zip(axes.flat, keys):
        d = MV["curvas"][k]
        t = np.array(d["t"]) / 60
        ax.plot(t, d["Cl0+C50"], color=BLUE, lw=2, label="Modelo corregido (Cl dependiente de la Cp; simulador)")
        ax.plot(t, d["Cl0+C50+V1"], color=MUTED, lw=1.4, ls=(0, (4, 2)), label="Exploratorio: además V1 × 2,8")
        ax.plot(np.array(d["t_obs"]) / 60, d["obs"], "o", ms=5, mfc=ORANGE, mec="white", mew=0.8, ls="none",
                label="Medido (media publicada)")
        ax.set_title(SHORT.get(k, k), fontsize=7.6, color=INK, loc="left")
        ax.set_xlim(0, t[-1])
        ax.set_ylim(0, max(max(d["obs"]), max(d["Cl0+C50"])) * 1.25)
        ax.xaxis.set_major_formatter(COMMA)
        ax.yaxis.set_major_formatter(COMMA)
    for ax in axes[-1, :]:
        ax.set_xlabel("Tiempo (h)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Cp (ng/mL)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=7.2, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    p = RES / "fig_volumen.png"
    fig.savefig(p, dpi=220)
    plt.close(fig)
    return p


F1, F2, F3, F4 = fig_estudios(), fig_meseta(), fig_obs_pred(), fig_volumen()

# ── PDF ───────────────────────────────────────────────────────────────────────
D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", D + "DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DVB", D + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")
NAVY = colors.HexColor("#1f3a5f"); GRIDC = colors.HexColor("#9aa7b4"); SHADE = colors.HexColor("#eef2f6"); MUT = colors.HexColor("#5b6b7c")
st = lambda n, **k: ParagraphStyle(n, fontName=k.pop("f", "DV"), **k)
T = st("t", f="DVB", fontSize=16.5, leading=21, textColor=NAVY)
ST = st("st", fontSize=9.5, leading=13, textColor=MUT, spaceAfter=8)
H1 = st("h1", f="DVB", fontSize=12, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=5)
H2 = st("h2", f="DVB", fontSize=9.5, leading=13, textColor=NAVY, spaceBefore=6, spaceAfter=3)
N = st("n", fontSize=8.8, leading=12.2, spaceAfter=4)
B = st("b", fontSize=8.8, leading=12.2, leftIndent=10, spaceAfter=2)
C = st("c", fontSize=7.6, leading=9.8); CB = st("cb", f="DVB", fontSize=7.6, leading=9.8, textColor=colors.white)
CAP = st("cap", fontSize=7.6, leading=10, textColor=MUT, spaceBefore=2, spaceAfter=8)
P = Paragraph
bul = lambda items: [P(x, B, bulletText="•") for x in items]
pc = lambda x, d=0: f"{x:.{d}f} %".replace(".", ",")
spc = lambda x, d=0: ("0 %" if round(x, d) == 0 else f"{x:+.{d}f} %".replace(".", ","))
num = lambda x, d=2: f"{x:.{d}f}".replace(".", ",")


def table(data, widths, head=True, style=None):
    body = [[P(str(c), CB if (head and i == 0) else (style or C)) for c in r] for i, r in enumerate(data)]
    t = Table(body, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    sty = [("GRID", (0, 0), (-1, -1), 0.4, GRIDC), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
           ("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, SHADE])]
    if head:
        sty.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    t.setStyle(TableStyle(sty))
    return t


def footer(cv, doc):
    cv.saveState(); cv.setFont("DV", 7); cv.setFillColor(MUT)
    cv.drawString(18 * mm, 10 * mm, "Simulador TCI · Dexmedetomidina canina · Fase 1: validación externa (v4) · © 2026 Francisco Carvajal Sánchez")
    cv.drawRightString(192 * mm, 10 * mm, str(doc.page)); cv.restoreState()


S = R["sensibilidad"]
G = R["global"]
an, aw = S["anestesiados"], S["despiertos"]
lg = MX["loso_global"]
exp_better = lg["experimental"]["MDAPE"] < lg["publicado"]["MDAPE"] - 2
tci = {r["objetivo"]: r for r in MX["tci"]}
mes = {m["estudio"] + str(m["tasa"]): m for m in R["meseta"]}
rz = MC["tasa_1ngml_reajuste_vs_simulador"]
NOVEDAD = ('<br/><br/><font size="10.5" color="#1f3a5f"><b>Novedad (v4): curvas completas de Lin 2008 y Pascoe 2006</b></font><br/>'
           f'Con las figuras digitalizadas (20 puntos en anestesia en lugar de 6), el reajuste da Cl<sub>0</sub> '
           f'{num(MC["ajuste_redondeado"]["Cl_0_Lhkg"])} y C50 {num(MC["ajuste_redondeado"]["C50_ngml"])}: la dosis de mantenimiento cambia un '
           f'{num(abs(rz[0] / rz[1] - 1) * 100, 1)} %, así que el simulador conserva 3,15 y 0,92. Pero el error en anestesiados es mayor de lo '
           f'que parecía (MDAPE {pc(MC["resumen"]["anestesiados"]["corregido"]["MDAPE"])}): la Cp <b>sube</b> durante las primeras 2–3 h pese a la '
           'carga, y ningún modelo con los volúmenes de Levionnois lo reproduce. Un volumen central ≈ 2,8 veces mayor en anestesia lo '
           'explicaría (apartado 8), pero no se adopta: los datos no lo fijan con seguridad y supondría cargas casi 3 veces mayores. Es la '
           'pregunta principal para el revisor y para la Fase 3.')
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm, bottomMargin=17 * mm,
                        title="Fase 1 · Validación externa del modelo de dexmedetomidina canina (v4)", author="Francisco Carvajal Sánchez")
mcs = MC["resumen"]
mpar = MC["simulador"]
loso_c = {r["estudio_excluido"]: r for r in MC["loso"]}
risk = {r["objetivo"]: r for r in MC["riesgo"]}
E = []
E += [P("Fase 1 · Validación externa con datos publicados", T),
      P(f"Modelo de Levionnois et al. (2022) usado por el Simulador TCI de dexmedetomidina canina · Versión 2: siete estudios, "
        f"incluidos perros anestesiados · Versión 3: modelo corregido (simulador v1.2.0) · Versión 4: curvas completas de Lin 2008 y Pascoe 2006 · "
        f"{date.today().strftime('%d/%m/%Y')}", ST)]
RB = st("rb", fontSize=8.6, leading=12.5)
E += [table([[
    '<font size="10.5" color="#1f3a5f"><b>Resultado</b></font><br/>'
    f'Con {G["n"]} medias publicadas de 7 estudios, el modelo publicado tiene un sesgo global de {spc(G["MDPE"])} y una imprecisión de '
    f'{pc(G["MDAPE"])}, fuera de lo aceptado para un TCI (±20 % y ≤ 30 %). La cifra global pesa mucho Lin 2008, con 38 puntos; en '
    f'perros despiertos fue {spc(aw["MDPE"])} y {pc(aw["MDAPE"])}. El resultado depende de las condiciones. '
    f'<b>En perros anestesiados con las infusiones de uso clínico (0,5–1 µg/kg/h), la Cp medida fue aproximadamente la mitad de la '
    f'predicha</b> (MDPE {spc(an["MDPE"])}; Lin 2008 y Pascoe 2006), con 3 µg/kg/h un 25 % menor, y en 24 h de infusión la diferencia '
    f'llegó al −65/−70 %. El aclaramiento aparente pasa de 1,2–1,6 L/h/kg con Cp de 2–4 ng/mL a 2,4–4,6 L/h/kg con Cp de 0,2–0,5 ng/mL: '
    f'la dexmedetomidina se elimina más deprisa cuanto menor es su concentración. Única excepción: Dent 2019 (perros jóvenes '
    f'despiertos, bolo de 5 µg/kg), con Cp mayor que la predicha. <b>Consecuencia para el simulador:</b> con objetivos de '
    f'0,5–1 ng/mL en un perro anestesiado, la Cp real sería aproximadamente la mitad de la mostrada (riesgo de efecto insuficiente, '
    f'no de sobredosis). '
    + (f'El modelo con aclaramiento dependiente de la concentración predice ahora mejor en validación cruzada (MDAPE '
       f'{pc(lg["experimental"]["MDAPE"])} frente a {pc(lg["publicado"]["MDAPE"])}).'
       if exp_better else
       f'El modelo con aclaramiento dependiente de la concentración no mejora claramente en validación cruzada (MDAPE '
       f'{pc(lg["experimental"]["MDAPE"])} frente a {pc(lg["publicado"]["MDAPE"])}).')
    + f'<br/><br/><font size="10.5" color="#1f3a5f"><b>Decisión (v3): modelo corregido para perros anestesiados</b></font><br/>'
    f'Se recalibró solo el aclaramiento con los dos estudios en perros anestesiados (Cl<sub>0</sub> {num(mpar["Cl_0_Lhkg"])} L/h/kg, '
    f'C50 {num(mpar["C50_ngml"])} ng/mL; a concentración alta, igual al publicado). En anestesiados el error pasa de '
    f'{spc(mcs["anestesiados"]["publicado"]["MDPE"])} a {spc(mcs["anestesiados"]["corregido"]["MDPE"])} (MDAPE {pc(mcs["anestesiados"]["corregido"]["MDAPE"])}), '
    f'y en los estudios con perros despiertos, que no se usaron para calibrarlo, también mejora: MDAPE '
    f'{pc(mcs["despiertos"]["corregido"]["MDAPE"])} frente a {pc(mcs["despiertos"]["publicado"]["MDAPE"])}. Es el modelo por defecto del '
    f'simulador desde la v1.2.0; el publicado queda como alternativa. Con solo 2 estudios calibrados, la Fase 3 debe confirmarlo (apartado 7).'
    + NOVEDAD
    ]], [174], head=False, style=RB)]

E += [P("1. Objetivo", H1),
      P("Comprobar si el modelo farmacocinético del simulador, obtenido en 8 Beagles despiertos tras un bolo de 10 µg/kg, predice "
        "las concentraciones medidas por otros grupos. Es una validación del <b>modelo</b>, no de la TCI: ningún perro de estos estudios "
        "recibió dexmedetomidina con el simulador. La v2 añadió tres estudios a la v1 (Lin 2008, Pascoe 2006 y Dent 2019); los dos "
        "primeros son los únicos con perros anestesiados, que es el uso real del simulador. La v3 añade el modelo corregido para perros "
        "anestesiados (apartado 7) que el simulador usa por defecto desde la v1.2.0. La v4 sustituye las cifras del texto de Lin 2008 y "
        "Pascoe 2006 por sus figuras digitalizadas y explora si en anestesia cambia también el volumen (apartado 8).", N)]

E += [P("2. Datos utilizados", H1),
      table([["Estudio", "Diseño", "Perros", "Análisis", "Datos extraídos"],
             ["Kuusela 2000 (J Vet Pharmacol Ther 23:15)", "Bolo de 10 y 20 µg/kg", "6 Beagles, despiertos", "GC-MS, arterial", "7 tiempos por dosis (Fig. 3 y texto)"],
             ["Honkavaara 2012 (Drug Metab Dispos 40:445)", "Bolo de 10 µg/kg", "8 Beagles, despiertos", "LC-MS, venosa central", "9 tiempos (Fig. 1)"],
             ["de Sant'Ana Alves 2024 (Res Vet Sci 171:105229)", "2 µg/kg en 2 min", "6 mestizos, despiertos", "UHPLC-MS/MS, venosa", "10 tiempos (Fig. 1); 60 y 90 min no fiables"],
             ["van Oostrom 2011 (Vet J 190:338)", "Bolo + infusión de 1, 3 o 5 µg/kg/h", "8 Beagles, despiertos", "LC-MS/MS, venosa", "5 muestras por dosis a 37–77 min (Fig. 3)"],
             ["<b>Lin 2008</b> (Vet Anaesth Analg 35:141)", "≈1 µg/kg + ≈1 µg/kg/h (25 µg/m²) 24 h; 2 h de isoflurano o propofol",
              "10 Beagles, <b>anestesiados</b> 2 h", "LC-MS/MS, venosa", "Fig. 2 digitalizada: 21 tiempos por grupo (5 min–26 h, con 2 h tras detener la infusión); AUC 0–26 h"],
             ["<b>Pascoe 2006</b> (Vet Anaesth Analg 33:97)", "Carga + infusión de 0,1, 0,5 o 3 µg/kg/h, ≈5–7 h", "6 Beagles, <b>anestesiados</b> (isoflurano)",
              "GC-MS, suero arterial", "Fig. 1 digitalizada: 4 tomas por dosis (1–7 h)"],
             ["<b>Dent 2019</b> (Am J Vet Res 80:969)", "Bolo de 5 µg/kg", "6 mestizos de 9 meses, despiertos", "UPLC-MS/MS, venosa",
              "Parámetros no compartimentales y última Cp a ≈110 min"]],
            [37, 34, 30, 24, 49]),
      P("Akashi 2020 y Pascoe 2015 no midieron concentraciones (se usan solo en el apartado de efecto clínico). Hector 2017/2021 y Pavlica 2022 están pendientes. Los puntos de Lin 2008 parcialmente ocultos por los del otro grupo se marcan como aproximados (±0,02 ng/mL). "
        "Lin 2008 dosificó por superficie corporal: 25 µg/m² ≈ 1,055 µg/kg en un Beagle de 13,7 kg.", CAP)]

E += [P("3. Método", H1)] + bul([
    "Cada protocolo se reprodujo con el modelo publicado (V1 1,03 · V2 0,41 L/kg · Cl1 1,16 · Cl2 1,87 L/h/kg) con la solución exacta, "
    "la misma dosis, velocidad de administración y tiempos de muestreo.",
    "Error de predicción de Varvel: PE = (medida − predicha) / predicha; MDPE (sesgo) y MDAPE (imprecisión) sobre las medias publicadas. "
    "Criterio orientativo de los TCI humanos: MDPE dentro de ±20 % y MDAPE ≤ 30 %.",
    "Además, comparación de los resúmenes publicados (AUC) y del aclaramiento aparente en meseta (tasa de infusión / Cp media).",
    "Banda de incertidumbre del modelo: 1000 conjuntos de parámetros dentro de los IC 95 % de Levionnois.",
    "Modelo experimental con aclaramiento dependiente de la concentración, ajustado de nuevo con todos los datos y evaluado en "
    "validación cruzada (cada estudio se predice con el modelo ajustado sin él).",
    "v4: figuras de Lin 2008 y Pascoe 2006 digitalizadas a partir de la imagen, con los ejes calibrados en sus marcas. Los valores "
    "coinciden con las cifras del texto (Lin: 0,64 a 5 min y 0,23/0,28 a 24 h; Pascoe: medias 0,205 y 1,92 frente a 0,198 y 1,903).",
    "v3: modelo corregido, ajustado solo con perros anestesiados y evaluado en los estudios con perros despiertos (que no usa) y en "
    "validación cruzada entre los dos estudios en anestesiados (apartado 7)."])

rows = [["Estudio · grupo", "n", "MDPE", "MDAPE", "PE (rango)", "Cl que ajusta (L/h/kg)"]]
for r in R["estudios"]:
    rows.append([SHORT.get(f"{r['estudio']} · {r['grupo']}", r["estudio"]), r["n_puntos"], spc(r["MDPE"]), pc(r["MDAPE"]),
                 f"{r['PE_min']:+.0f} a {r['PE_max']:+.0f} %", num(r["Cl_ajustado_Lhkg"])])
E += [P("4. Resultados", H1), table(rows, [70, 10, 20, 20, 28, 26]),
      P("Modelo de Levionnois: Cl = 1,16 L/h/kg. «Cl que ajusta» = aclaramiento que mejor reproduce cada curva con los volúmenes fijos.", CAP)]

sens_rows = [["Conjunto de puntos", "n", "MDPE", "MDAPE"]]
names = [("todos", "Todos los puntos fiables"), ("despiertos", "Perros despiertos"), ("anestesiados", "Perros anestesiados (Lin, Pascoe)"),
         ("infusiones_t>=10min", "Todas las infusiones continuas, desde el minuto 10"), ("solo_t>=10min", "Desde el minuto 10"),
         ("sin_2024_y_t>=10min", "Sin el estudio de 2024 y desde el minuto 10"), ("sin_puntos_aproximados", "Sin puntos de tiempo aproximado"),
         ("sin_Dent", "Sin Dent 2019")]
for k, lab in names:
    v = S[k]
    sens_rows.append([lab, v["n"], spc(v["MDPE"], 1), pc(v["MDAPE"], 1)])
E += [KeepTogether([P("Análisis de sensibilidad", H2), table(sens_rows, [90, 18, 33, 33]),
                    P("El sesgo es negativo (el modelo sobrestima la concentración) en todos los conjuntos, y mucho mayor en perros anestesiados.", CAP)])]

res_rows = [["Resumen publicado", "Medido", "Predicho", "Diferencia", "Cl aparente (L/h/kg)"]]
for r in R["resumenes"]:
    res_rows.append([f"{r['estudio']} · {r['medida']}", num(r["medido"]), num(r["predicho"]), spc(r["PE"]), num(r["Cl_aparente_Lhkg"])])
E += [KeepTogether([P("Exposición total (AUC)", H2), table(res_rows, [86, 18, 18, 22, 30]),
                    P("Cl aparente = dosis total / AUC. En Lin 2008 la exposición en 26 h fue un 62 % menor que la predicha.", CAP)])]

E += [PageBreak(), KeepTogether([P("Figura 1 · Concentraciones medidas frente a las predichas por el modelo", H2), Image(str(F1), width=150 * mm, height=241 * mm),
                    P("Kuusela, Honkavaara y van Oostrom a 3–5 µg/kg/h quedan cerca del modelo. Con dosis bajas (bolo de 2 µg/kg; "
                      "infusión de 0,5–1 µg/kg/h) la Cp medida queda por debajo, sobre todo en los perros anestesiados de Lin y Pascoe. "
                      "Dent 2019 es la excepción en sentido contrario.", CAP)])]

mrows = [["Estudio", "Tasa (µg/kg/h)", "Cp medida", "Cp del modelo en equilibrio", "Cl aparente (L/h/kg)"]]
for m in R["meseta"]:
    mrows.append([m["estudio"], num(m["tasa"], 2), num(m["cp"], 3) if m["cp"] else "< 0,05", num(m["cp_modelo_equilibrio"], 2),
                  num(m["Cl_aparente_Lhkg"]) if m["Cl_aparente_Lhkg"] else "> 2,0"])
E += [KeepTogether([P("Aclaramiento aparente durante las infusiones", H2), table(mrows, [52, 24, 24, 38, 36]),
                    Spacer(1, 4), Image(str(F2), width=168 * mm, height=86 * mm),
                    P("Figura 2 · Cuanto menor es la concentración, mayor es el aclaramiento: los puntos dibujan la curva que el modelo "
                      "publicado no tiene (línea discontinua constante en 1,16). En Lin 2008 el aclaramiento siguió aumentando a lo largo "
                      "de las 24 h, a la vez que la frecuencia cardiaca se recuperaba.", CAP)])]

E += [P("5. Interpretación", H1)] + bul([
    "<b>El modelo funciona en las condiciones en que se construyó</b>: bolos de 10–20 µg/kg e infusiones de 3–5 µg/kg/h en Beagles "
    "despiertos, con concentraciones de 2–15 ng/mL (Honkavaara, Kuusela 20 µg/kg y van Oostrom 3–5 µg/kg/h con MDAPE de 15–21 %).",
    "<b>A las concentraciones clínicas (0,2–1 ng/mL) sobrestima la Cp</b>, y más en perros anestesiados y en infusiones largas. "
    "El mecanismo es conocido: la dexmedetomidina reduce el gasto cardiaco y el flujo hepático, y con ello su propio aclaramiento. "
    "A dosis altas (las del estudio original) ese efecto es máximo; a dosis bajas el aclaramiento es 2–4 veces mayor. Bloquear el "
    "efecto periférico con MK-467 duplica el aclaramiento (Honkavaara 2012), y Lin 2008 observó cómo la Cp bajaba a lo largo de 24 h "
    "mientras la frecuencia cardiaca se recuperaba.",
    "<b>Para el simulador</b>: el mantenimiento a 1 ng/mL equivale a ≈ 1,2 µg/kg/h, el mismo régimen de Lin 2008, donde la Cp medida "
    "fue 0,33–0,47 ng/mL durante la anestesia y 0,23–0,28 a las 24 h. Con objetivos de 0,5–1 ng/mL, la Cp real en un perro "
    "anestesiado sería ≈ 40–55 % de la mostrada; con 2–3 ng/mL, ≈ 70–80 %. El error va siempre en el sentido de dar menos fármaco: "
    "riesgo de sedación o analgesia insuficientes, no de sobredosis.",
    "<b>Precaución con la magnitud</b>: aclaramientos aparentes de 2,4–4,6 L/h/kg superan el flujo sanguíneo hepático del perro "
    "(≈ 2 L/h/kg). O hay eliminación fuera del hígado, o parte de la diferencia se debe al método (estabilidad de las muestras, "
    "calibración del ensayo, dosis real). Que tres laboratorios independientes (Lin, Pascoe, de Sant'Ana Alves) coincidan en la "
    "dirección hace improbable un artefacto de uno solo, pero la cifra exacta debe confirmarse con muestras propias.",
    "<b>Dent 2019</b> (perros de 9 meses, mestizos, despiertos) dio concentraciones mayores que las predichas y un aclaramiento de "
    "0,48 L/h/kg, el más bajo de todos. Es un único estudio con 6 perros y solo parámetros resumidos; muestra que la variabilidad "
    "entre poblaciones es grande y que la Fase 3 debe medirla en los pacientes reales."])

pm = MX["principal_sin_2024"]
E += [P("6. Modelo experimental: aclaramiento dependiente de la concentración", H1),
      P("Mantiene la estructura de Levionnois (V1, V2 y Cl2 iguales) con un aclaramiento que disminuye al aumentar la concentración: "
        "<b>Cl(C) = Cl<sub>∞</sub> + (Cl<sub>0</sub> − Cl<sub>∞</sub>) · C50 / (C50 + C)</b>. Se ajustó con todos los puntos desde el minuto 10 "
        "(salvo el estudio de 2024), obligándolo a reproducir el AUC publicado por Levionnois y con los parámetros acotados a "
        "valores fisiológicos (Cl entre 0,3 y 6 L/h/kg; C50 entre 0,05 y 10 ng/mL).", N),
      table([["Parámetro", "Valor"],
             ["Cl<sub>0</sub> (concentración muy baja)", f"{num(pm['Cl_0_Lhkg'])} L/h/kg"],
             ["Cl<sub>∞</sub> (concentración alta)", f"{num(pm['Cl_inf_Lhkg'])} L/h/kg"],
             ["C50", f"{num(pm['C50_ngml'])} ng/mL"],
             ["AUC tras 10 µg/kg (Levionnois publicado: 8,65)", f"{num(MX['auc_levionnois_pred'])} h·ng/mL"]], [100, 74])]
lo = [["Estudio excluido (se predice sin usarlo)", "Publicado MDPE", "Publicado MDAPE", "Experimental MDPE", "Experimental MDAPE"]]
for r in MX["loso"]:
    lo.append([r["estudio_excluido"], spc(r["publicado"]["MDPE"]), pc(r["publicado"]["MDAPE"]), spc(r["experimental"]["MDPE"]), pc(r["experimental"]["MDAPE"])])
lo.append(["<b>Global (sin 2024)</b>", f"<b>{spc(lg['publicado']['MDPE'])}</b>", f"<b>{pc(lg['publicado']['MDAPE'])}</b>",
           f"<b>{spc(lg['experimental']['MDPE'])}</b>", f"<b>{pc(lg['experimental']['MDAPE'])}</b>"])
E += [KeepTogether([P("Validación cruzada: cada estudio se predice con el modelo ajustado sin él", H2), table(lo, [58, 29, 29, 29, 29]),
                    P(("El modelo experimental predice mejor los estudios que no ha visto: corrige gran parte del sesgo en los perros "
                       "anestesiados y en las infusiones a dosis bajas." if exp_better else
                       "El modelo experimental mejora los estudios de infusión a concentración baja (Lin, Pascoe, van Oostrom, 2024) "
                       "pero empeora los bolos de dosis alta (Kuusela, Honkavaara), y en conjunto no supera al publicado. Ni siquiera "
                       "predice bien Lin 2008 cuando se ajusta sin él: sus concentraciones son más bajas de lo que anticipan los demás estudios.")
                      + " Dent 2019 no lo explica ninguno de los dos modelos.", CAP)])]
ti = [["Objetivo en pantalla", "Cp real a 10 min", "a 30 min", "a 60 min", "a 120 min"]]
for r in MX["tci"]:
    d = r["diferencia_pct"]
    ti.append([f"{num(r['objetivo'], 1)} ng/mL"] + [spc(d[k]) for k in ("10", "30", "60", "120")])
E += [KeepTogether([P("Si el modelo experimental es correcto: Cp real con el programa v1.1.1 (modelo publicado; perro de 25 kg, carga en 10 min)", H2), table(ti, [46, 32, 32, 32, 32]),
                    P("La carga llega cerca del objetivo, pero en el mantenimiento la Cp real se queda por debajo, más con objetivos bajos "
                      "y con el tiempo. Es una estimación prudente: los datos directos de perros anestesiados (Lin 2008, Pascoe 2006) "
                      "indican diferencias mayores, ≈ −50 % con 0,5–1 µg/kg/h.", CAP)])]


cal_desc = "; ".join(f"{g['estudio']} {g['grupo'].split(':')[0].split(' en ')[0]} ({len(g['t'])})" for g in MC["calibracion"])
E += [PageBreak(), P("7. Modelo corregido para perros anestesiados (simulador v1.2.0)", H1),
      P("El modelo experimental del apartado 6 intentaba explicar a la vez bolos de dosis alta en perros despiertos e infusiones bajas en "
        "anestesiados, y no mejoró en validación cruzada. El simulador se usa en perros anestesiados con infusiones de 0,5–3 µg/kg/h, "
        "así que se ajustó un modelo más sencillo y específico para ese uso:", N)] + bul([
    "Misma estructura y mismos V1, V2 y Cl2 que Levionnois. Solo cambia el aclaramiento: <b>Cl(C) = 1,16 + (Cl<sub>0</sub> − 1,16) · "
    "C50 / (C50 + C)</b>. A concentración alta es el publicado (1,16 L/h/kg); a concentración baja aumenta hasta Cl<sub>0</sub>.",
    f"Calibración con los puntos medidos en perros <b>anestesiados</b> desde el minuto 10: {cal_desc}. Lin 2008 de 3 a 26 h "
    "(perros ya despiertos, con la infusión y tras detenerla) se usa como comprobación.",
    "Se ajustan dos parámetros (Cl<sub>0</sub> y C50) por mínimos cuadrados en escala logarítmica. El simulador v1.2.0 usa 3,15 y 0,92, "
    "fijados con la calibración anterior (solo cifras del texto); todas las cifras de este apartado se calculan con esos valores.",
    "Comprobación con datos no usados: los 4 estudios con perros despiertos (Kuusela, Honkavaara, de Sant'Ana Alves, van Oostrom) y "
    "validación cruzada entre los dos estudios en anestesiados."])
E += [table([["Parámetro", "Ajuste", "Simulador v1.2.0"],
             ["Cl<sub>0</sub> (concentración muy baja)", f"{num(MC['ajuste']['Cl_0_Lhkg'], 3)} L/h/kg", f"<b>{num(mpar['Cl_0_Lhkg'])} L/h/kg</b>"],
             ["C50", f"{num(MC['ajuste']['C50_ngml'], 3)} ng/mL", f"<b>{num(mpar['C50_ngml'])} ng/mL</b>"],
             ["Cl<sub>∞</sub> (concentración alta), V1, V2, Cl2", "fijos", "1,16 L/h/kg · 1,03 · 0,41 L/kg · 1,87 L/h/kg"]], [70, 50, 54])]
E += [P(f"Con las curvas completas, el reajuste da Cl<sub>0</sub> {num(MC['ajuste']['Cl_0_Lhkg'], 3)} y C50 {num(MC['ajuste']['C50_ngml'], 3)} "
        f"(anestesiados: MDAPE {pc(mcs['anestesiados']['reajuste']['MDAPE'], 1)}, frente a {pc(mcs['anestesiados']['corregido']['MDAPE'], 1)} con los "
        f"del simulador). La velocidad de mantenimiento con 1 ng/mL pasaría de {num(rz[1])} a {num(rz[0])} µg/kg/h: "
        "no justifica cambiar el simulador.", N)]
sum_rows = [["Conjunto", "n", "Publicado MDPE", "Publicado MDAPE", "Corregido MDPE", "Corregido MDAPE"]]
for k, lab in (("anestesiados", "Anestesiados (calibración)"), ("despiertos", "Despiertos (no usados; incluye Lin 3–26 h)"), ("global", "Todos (desde el minuto 10)")):
    v = mcs[k]
    sum_rows.append([lab, v["corregido"]["n"], spc(v["publicado"]["MDPE"], 1), pc(v["publicado"]["MDAPE"], 1),
                     f"<b>{spc(v['corregido']['MDPE'], 1)}</b>", f"<b>{pc(v['corregido']['MDAPE'], 1)}</b>"])
E += [KeepTogether([P("Resultados", H2), table(sum_rows, [56, 12, 26, 27, 26, 27])])]
wo = MC["lin_descenso_24h"]
grp = [["Estudio · grupo", "Estado", "Publicado MDPE", "Corregido MDPE", "Corregido MDAPE"]]
for g in MC["por_grupo"]:
    grp.append([SHORT.get(f"{g['estudio']} · {g['grupo']}", g["estudio"]), "anestesiados" if g["estado"] == "anestesiados" else "despiertos",
                spc(g["publicado"]["MDPE"]), spc(g["corregido"]["MDPE"]), pc(g["corregido"]["MDAPE"])])
E += [Spacer(1, 4), table(grp, [70, 26, 26, 26, 26]),
      P("Lin 2008 se divide en la anestesia (15–120 min, calibración) y las 3–26 h siguientes (despiertos, comprobación). "
        f"Tras detener la infusión a las 24 h, la semivida aparente medida fue {num(wo['medido_t12_h'])} h; el modelo corregido "
        f"predice {num(wo['corregido_t12_h'])} h y el publicado {num(wo['publicado_t12_h'])} h. "
        "Dent 2019 no lo explica ninguno de los dos modelos y el corregido lo empeora (concentraciones de Dent ≈ 4 veces las de los demás "
        "estudios con dosis parecidas).", CAP),
      KeepTogether([Image(str(F3), width=168 * mm, height=84 * mm),
                    P("Figura 3 · Medido frente a predicho. Con el modelo publicado casi todos los puntos quedan por debajo de la diagonal "
                      "(el modelo sobrestima la Cp); con el corregido se reparten a ambos lados y la mayoría cae dentro de ±30 %, también "
                      "en los perros despiertos que no se usaron para calibrarlo.", CAP)])]
lc = [["Estudio en anestesiados excluido", "Ajuste sin él", "Publicado MDPE", "Corregido MDPE"]]
for s_, r in loso_c.items():
    lc.append([s_, f"Cl<sub>0</sub> {num(r['Cl_0'])} · C50 {num(r['C50'])}", spc(r["publicado"]["MDPE"]), spc(r["corregido"]["MDPE"])])
E += [KeepTogether([P("Validación cruzada entre los dos estudios en anestesiados", H2), table(lc, [56, 50, 34, 34]),
                    P("Calibrado solo con Pascoe 2006, el modelo predice Lin 2008 con un error de "
                      f"{spc(loso_c['Lin 2008']['corregido']['MDPE'])} (publicado {spc(loso_c['Lin 2008']['publicado']['MDPE'])}). "
                      "Al revés no es informativo: Lin 2008 solo tiene concentraciones de ≈ 0,4 ng/mL, con las que no se puede estimar la "
                      "forma de la curva (C50 llega al límite de 10 ng/mL), y el error en Pascoe es "
                      f"{spc(loso_c['Pascoe 2006']['corregido']['MDPE'])}. Conclusión: la corrección a concentraciones bajas está respaldada "
                      "por dos laboratorios independientes, pero la forma exacta de la curva depende de un único grupo con Cp alta "
                      "(Pascoe 3 µg/kg/h). La Fase 3 debe incluir objetivos bajos y altos para estimarla.", CAP)])]
rk = [["Objetivo", "Tasa de mantenimiento corregida", "Publicada", "Cp si el perro elimina como el modelo publicado", "Cp si elimina como Dent 2019"]]
for t in (0.5, 1.0, 1.5, 2.0, 3.0):
    r = risk[t]
    rk.append([f"{num(t, 1)} ng/mL", f"{num(r['tasa_corregida_ugkgh'])} µg/kg/h", f"{num(r['tasa_publicada_ugkgh'])} µg/kg/h",
               f"{num(r['Css_si_publicado'])} ng/mL ({spc((r['Css_si_publicado'] / t - 1) * 100)})", f"{num(r['Css_si_Dent'])} ng/mL"])
E += [KeepTogether([P("Consecuencias para la dosificación y riesgo de sobredosificación", H2), table(rk, [22, 38, 26, 50, 38]),
                    P("Con el modelo corregido el simulador infunde más que antes, dentro de las CRI clínicas habituales (1–5 µg/kg/h). Si "
                      "un perro concreto eliminara como el modelo publicado, la Cp real sería de 1,4 a 2,1 veces el objetivo (más con "
                      "objetivos bajos: con 0,5 ng/mL llegaría a ≈ 1 ng/mL); si eliminara como los perros de Dent 2019, mucho más. Los "
                      "límites de seguridad del simulador son de dosis y no cambian (≤ 30 µg/kg/h instantánea, ≤ 12 µg/kg en 60 min). "
                      "Monitorizar FC y PA es imprescindible.", CAP)])]
E += bul([
    f"<b>AUC del estudio original</b>: tras 10 µg/kg el modelo corregido predice {num(MC['auc_levionnois'])} h·ng/mL frente a 8,65 "
    "publicado por Levionnois (−31 %). Los perros de Levionnois tuvieron más exposición que los de Kuusela con la misma dosis "
    "(Kuusela: corregido −5 %, publicado −27 %): es variabilidad entre estudios. El modelo corregido no sirve para describir el "
    "estudio original; para eso queda el publicado en el selector.",
    "<b>Lo que no corrige</b>: la subida de la Cp en las primeras horas de anestesia (apartado 8), el descenso a lo largo de 24 h de "
    "infusión (Lin 2008) y la variabilidad entre perros. Un error mediano del 20–25 % en medias de grupo no significa lo mismo en un "
    "perro concreto: en los TCI humanos el error individual habitual es del 20–30 %, y aquí puede ser mayor hasta que la Fase 3 lo mida."])

va = MV["ajustes"]
cv = MV["validacion_cruzada"]
lind = MV["lin_despiertos"]
cv_lin_only = cv["Cl0+C50+V1 · sin Pascoe 2006"]["par"]
E += [PageBreak(), P("8. Curso temporal en anestesia: ¿cambia también el volumen?", H1),
      P("En los dos estudios en perros anestesiados la Cp sube durante las primeras 2–3 h pese a la dosis de carga (Lin: 0,40 → 0,47 y "
        "0,33 → 0,41 ng/mL; Pascoe: 1,52 → 2,0–2,2 ng/mL). Los autores de Pascoe ya lo atribuyeron a una carga insuficiente. Los modelos con "
        "los volúmenes de Levionnois predicen lo contrario: la Cp baja tras la carga. Se probaron 4 estructuras con los mismos datos:", N)]
st = [["Estructura (anestesiados)", "Cl<sub>0</sub>", "C50", "V1 ×", "V2 ×", "Error (obj.)", "MDAPE"]]
for k in ("Cl0+C50", "Cl0+C50+V1", "Cl0+C50+V2", "Cl0+C50+V1+V2"):
    r = va[k]
    st.append([k.replace("Cl0", "Cl<sub>0</sub>"), num(r["par"][0]), num(r["par"][1]), num(r["par"][2]), num(r["par"][3]),
               num(r["obj"], 3), pc(r["MDAPE"], 1)])
E += [table(st, [52, 18, 18, 18, 18, 24, 26]),
      KeepTogether([Image(str(F4), width=160 * mm, height=111 * mm),
                    P("Figura 4 · Con un volumen central ≈ 2,8 veces mayor (V1 ≈ 2,9 L/kg) el modelo reproduce la subida inicial y la meseta "
                      "de los dos estudios.", CAP)])]
cvr = [["Estructura", "Ajustada sin", "Predice", "MDPE", "MDAPE"]]
for k, r in cv.items():
    name, out = k.split(" · sin ")
    cvr.append([name.replace("Cl0", "Cl<sub>0</sub>"), out, "Pascoe 2006" if out.startswith("Lin") else "Lin 2008",
                spc(r["MDPE"]), pc(r["MDAPE"])])
E += [KeepTogether([P("Validación cruzada y comprobaciones", H2), table(cvr, [46, 34, 34, 30, 30])])] + bul([
    "El modelo con V1 mayor predice mejor el estudio que no ha visto, pero sus parámetros son inestables: ajustado solo con Lin 2008 da "
    f"Cl<sub>0</sub> {num(cv_lin_only[0])} y C50 {num(cv_lin_only[1])}.",
    f"Con Lin 2008 tras la anestesia (3–24 h, despiertos) empeora: MDPE {spc(lind['Cl0+C50+V1 · ISO 3-24 h'])} frente a "
    f"{spc(lind['Cl0+C50 · ISO 3-24 h'])} con el corregido, y predice un descenso tras la infusión mucho más lento que el medido. "
    "Es coherente con que el volumen solo sea mayor durante la anestesia, pero no lo demuestra.",
    "Consecuencia práctica si fuera cierto: con el simulador actual la Cp quedaría por debajo del objetivo la primera hora (como en "
    "Lin 2008) y, ya en meseta, entre un 30 y un 40 % por encima con objetivos de 0,5–2 ng/mL, porque este modelo da un aclaramiento menor "
    "con 1 ng/mL (1,59 frente a 2,11 L/h/kg). Entre 0,2 y 2 ng/mL no hay datos de meseta en anestesia que decidan entre los dos.",
    "Adoptarlo supondría cargas casi 3 veces mayores (≈ 2,9 µg/kg en el compartimento central con 1 ng/mL y ≈ 5,8 con 2 ng/mL), con "
    "más riesgo de hipertensión y bradicardia transitorias. <b>No se adopta</b>: se plantea al revisor farmacocinético, y la Fase 3 "
    "debe poder estimar V1 (muestras tempranas tras la carga) y el aclaramiento con 1 ng/mL en meseta."])

E += [P("9. Efecto clínico observado (para interpretar los objetivos)", H1)] + bul([
    "<b>Reducción de la CAM de isoflurano</b> (Pascoe 2006): −6 % con 0,1 µg/kg/h (Cp no detectable), −18 % con 0,5 µg/kg/h (Cp 0,20 ng/mL) "
    "y −59 % con 3 µg/kg/h (Cp 1,9 ng/mL). Con sevoflurano y carga en 10 min, como el simulador (Akashi 2020): −13 % con 0,1, −27 % con "
    "0,5, −34 % con 1 y −59 % con 5 µg/kg/h.",
    "<b>Efecto cardiovascular</b> (Pascoe 2015, isoflurano): con 0,5 µg/kg/h el índice cardiaco bajó 1–17 % y con 3 µg/kg/h un 27–56 %. "
    "Una caída de la frecuencia cardiaca menor del 20 % se acompañó de cambios mínimos del índice cardiaco. Lin 2008 (≈1 µg/kg/h) "
    "describe ≈ 30 % de descenso del gasto cardiaco.",
    "Con el modelo publicado (v1.1.1), lo que el simulador llamaba «1 ng/mL» correspondía a ≈ 0,4–0,5 ng/mL medidos y a una "
    "reducción de la CAM de ≈ 30–35 %. Con el modelo corregido (v1.2.0) «1 ng/mL» debería ser ≈ 1 ng/mL medido (reducción de la CAM "
    "esperable ≈ 40–50 %, entre los 0,5 y 3 µg/kg/h de Pascoe): útil para elegir objetivos en la Fase 2."])

E += [P("10. Recomendaciones", H1)] + bul([
    "<b>Modelo corregido por defecto (simulador v1.2.0)</b>, con el publicado como alternativa seleccionable y los mismos límites de "
    "seguridad. Avisos según el modelo: con el publicado, que en anestesiados la Cp real puede ser la mitad; con el corregido, que está "
    "calibrado con 2 estudios y que en un perro concreto la Cp puede ser un 30–50 % mayor o menor.",
    "<b>Fase 3</b>: la bomba se guía con el modelo corregido; con el registro de tasas del CSV se calcula la Cp de cada muestra con los dos "
    "modelos (reconstruir_cp.py --muestras) y se comparan con la medida. Objetivos bajos y altos (0,5, 1 y 2 ng/mL) para estimar la forma "
    "de la curva; muestras a 10, 30, 60 y 120 min y tras detener la infusión.",
    "Con los datos de la Fase 3, recalibrar Cl<sub>0</sub> y C50 (y comprobar V1) con un análisis poblacional antes de cualquier uso "
    "clínico o comercial del simulador.",
    "<b>Fase 3, muestras tempranas</b>: añadir una o dos muestras entre el final de la carga y los 30 min (p. ej., 15 y 20 min) para "
    "estimar el volumen central en anestesia, y vigilar en el análisis intermedio si la Cp de los primeros 30–60 min queda por debajo "
    "del objetivo y la de meseta por encima.",
    "Hector 2017/2021 y Pavlica 2022 (perros anestesiados) pueden ayudar a decidir entre las estructuras del apartado 8."])

E += [P("11. Limitaciones", H1)] + bul([
    "Datos agregados (medias de grupo), digitalizados de figuras o tomados del texto; en Lin 2008 y Dent 2019 algunos tiempos son aproximados "
    "(el análisis sin ellos da el mismo resultado). Los índices de Varvel se definen sobre perros individuales.",
    "Métodos analíticos, matrices (plasma o suero) y lugares de muestreo distintos.",
    "En Lin 2008 la dosis se convirtió desde µg/m² con el peso mediano; la duración de los bolos de Lin y Dent no consta.",
    "Siete estudios y ~50 perros en total: las diferencias entre poblaciones son tan grandes como algunos de los efectos analizados.",
    "El modelo corregido se calibró con medias de grupo de 2 estudios (20 puntos; 16 Beagles adultos sanos, ambos en diseño cruzado): sus parámetros son una estimación "
    "provisional, no un resultado definitivo."])

E += [P("12. Pendiente", H1),
      table([["Documento", "Para qué"],
             ["Hector et al. 2017 y 2021 (sevoflurano, infusiones)", "Más datos en perros anestesiados a 0,5–4,5 µg/kg/h, si midieron concentraciones"],
             ["Pavlica et al. 2022, Animals (libre)", "0,5 µg/kg IV en perros anestesiados: concentraciones muy bajas"],
             ["Estudios IM (AJVR 2023; Di Cesare 2019)", "Revisar el supuesto de la premedicación IM del simulador"]], [80, 94])]

doc.build(E, onFirstPage=footer, onLaterPages=footer)
print("Informe:", OUT)
