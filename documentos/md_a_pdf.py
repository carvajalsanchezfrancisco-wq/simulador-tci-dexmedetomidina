"""Convierte un documento Markdown de esta carpeta en PDF (A4) con Chromium.

Uso: python3 md_a_pdf.py <documento.md> <salida.pdf> [pie de página]
Requisitos: python3 -m pip install markdown; Node.js con Playwright y Chromium.
Las imágenes se resuelven respecto a la carpeta del documento.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CSS = """
body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 9.6pt; line-height: 1.42; color: #1b1f24; }
h1 { font-size: 16pt; margin: 0 0 3pt; color: #12324f; }
.byline { color: #5b6672; margin: 0 0 12pt; font-size: 9pt; }
h2 { font-size: 12.5pt; color: #12324f; border-bottom: 1.2pt solid #c9d3dd; padding-bottom: 3pt; margin: 16pt 0 7pt; page-break-after: avoid; }
p { margin: 0 0 6pt; }
ul, ol { margin: 0 0 7pt; padding-left: 18pt; } li { margin-bottom: 2.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 8.4pt; margin: 4pt 0 9pt; page-break-inside: avoid; }
th, td { border: 0.6pt solid #c9d3dd; padding: 3.5pt 5pt; text-align: left; vertical-align: top; }
th { background: #e8eef4; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.2pt; background: #f1f5f9; padding: 0 2pt; word-break: break-all; }
pre { background: #f1f5f9; padding: 7pt 9pt; border-left: 3pt solid #3a6ea5; page-break-inside: avoid; }
pre code { background: none; padding: 0; word-break: normal; }
img { max-width: 100%; display: block; margin: 6pt auto 2pt; }
em { color: #4a5560; }
a { color: #1f5fa0; text-decoration: none; }
"""

src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
footer = sys.argv[3] if len(sys.argv) > 3 else src.stem
body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
title = src.stem.replace("_", " ")
html = f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"
with tempfile.NamedTemporaryFile("w", suffix=".html", dir=src.parent, delete=False, encoding="utf-8") as f:
    f.write(html)
    tmp = Path(f.name)
js = """
const { chromium } = require('playwright');
(async () => { const [src, out, footer] = JSON.parse(process.argv[1]);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + src); await p.waitForLoadState('networkidle');
  await p.pdf({ path: out, format: 'A4', printBackground: true, margin: { top: '17mm', bottom: '17mm', left: '16mm', right: '16mm' },
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: `<div style="font-size:7.5px;color:#888;width:100%;text-align:right;padding-right:16mm">${footer} · <span class="pageNumber"></span>/<span class="totalPages"></span></div>` });
  await b.close(); })();
"""
try:
    subprocess.run(["node", "-e", js, json.dumps([str(tmp), str(out), footer])], check=True)
finally:
    tmp.unlink(missing_ok=True)
print("PDF:", out)
