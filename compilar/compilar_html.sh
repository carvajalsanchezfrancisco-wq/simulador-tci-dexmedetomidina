#!/bin/sh
# Compila simulador/tci_dexmedetomidina_perros.jsx en simulador/simulador_tci_dexmedetomidina.html
# (una sola página, sin conexión).
# Requisitos: Node.js 22 y las dependencias fijadas de esta carpeta (npm ci). Con estas versiones exactas
# la salida es idéntica byte a byte a la publicada (v1.2.1: 40195eca…; v1.3.0: 191c627f…).
set -e
cd "$(dirname "$0")"
[ -d node_modules ] || npm ci --no-audit --no-fund
NM=./node_modules
"$NM/.bin/esbuild" entrada.jsx --bundle --minify --format=iife --target=chrome90 --jsx=automatic \
  --define:process.env.NODE_ENV='"production"' --log-level=warning \
  --alias:react="$NM/react" --alias:react-dom="$NM/react-dom" --alias:recharts="$NM/recharts" --outfile=.bundle.js
python3 plantilla.py .bundle.js ../simulador/simulador_tci_dexmedetomidina.html
rm -f .bundle.js
sha256sum ../simulador/simulador_tci_dexmedetomidina.html
