#!/bin/sh
# Verificación completa de la v1.4.0. Uso: sh verificacion/v140/ejecutar_verificacion_v140.sh [carpeta de salida]
# Requisitos: Node.js 22 (npm ci en compilar/), Python 3 con numpy y scipy, y Playwright con Chromium.
#   1. REG-03 y TCI-C (verificar_v140.mjs): regresión de los modelos anteriores frente a la v1.3.0 (tomada de git)
#      y precisión de la carga y el mantenimiento con el modelo corregido
#   2. Reconstrucción independiente de la Cp desde el CSV de cada caso (reconstruir_cp.py --verificar)
#   3. Peritaje: pruebas de hallazgos H-01 a H-09 con cada modelo y prueba de estrés (4991 casos)
#   4. Interfaz en Chromium (prueba_interfaz_v140.cjs)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/verificacion/v140/salida}"   # los resúmenes de referencia están en resultados/
JSX="$ROOT/simulador/tci_dexmedetomidina_perros.jsx"
HTML="$ROOT/simulador/simulador_tci_dexmedetomidina.html"
mkdir -p "$OUT"
[ -d "$ROOT/compilar/node_modules" ] || (cd "$ROOT/compilar" && npm ci --no-audit --no-fund)
git -C "$ROOT" show 3ed65b6:simulador/tci_dexmedetomidina_perros.jsx > "$OUT/v130.jsx"   # commit de la v1.3.0 recuperada
grep -q 'APP_VERSION = "1.3.0"' "$OUT/v130.jsx"

echo "── 1. Regresión y precisión del TCI"
node "$ROOT/verificacion/v140/verificar_v140.mjs" "$JSX" "$OUT/v130.jsx" "$OUT/motor" 100
echo "── 2. Reconstrucción independiente de la Cp"
python3 "$ROOT/verificacion/motor/reconstruir_cp.py" --verificar "$OUT/motor/csv" --json "$OUT/reconstruccion.json" | tail -1
echo "── 3. Peritaje"
for m in corregido anestesiado publicado; do
  printf "H-01–H-09 con «%s»: " "$m"
  node "$ROOT/verificacion/peritaje/pruebas_hallazgos.mjs" "$JSX" "$OUT/hallazgos_$m" "$m" | tail -1
done
node "$ROOT/verificacion/peritaje/estres_motor.mjs" "$JSX" "$OUT/estres" 4991 | grep -E '"casos"|"fallos"'
echo "── 4. Interfaz"
node "$ROOT/verificacion/v140/prueba_interfaz_v140.cjs" "$HTML" "$OUT/interfaz" | tail -1
sha256sum "$JSX" "$HTML"
