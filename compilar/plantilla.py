"""Envuelve el bundle de esbuild en una sola página HTML (sin conexión).

Uso: python3 plantilla.py <bundle.js> <salida.html>
"""
import sys
from pathlib import Path

CABECERA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Francisco Carvajal Sánchez">
<meta name="copyright" content="© 2026 Francisco Carvajal Sánchez. Todos los derechos reservados.">
<title>Simulador TCI · Dexmedetomidina canina — Francisco Carvajal Sánchez</title>
<style>html,body{margin:0;background:#eef1f4}</style>
</head>
<body>
<!-- Simulador TCI de dexmedetomidina en perros. Autor: Francisco Carvajal Sánchez. © 2026. Todos los derechos reservados. -->
<div id="root"></div>
<script>"""
PIE = """</script>
</body>
</html>
"""

bundle = Path(sys.argv[1]).read_text(encoding="utf-8")
assert "</script" not in bundle.lower(), "el bundle contiene </script"
Path(sys.argv[2]).write_text(CABECERA + bundle + PIE, encoding="utf-8")
