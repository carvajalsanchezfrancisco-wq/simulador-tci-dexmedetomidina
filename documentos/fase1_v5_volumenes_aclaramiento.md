# Fase 1 · v5: aclaramiento corregido con los volúmenes central y periférico

**Fecha:** 27/10/2026. Responde a las observaciones de la reunión con IRNASUS UCC-CONICET.

**Archivos:**
- Script: `validacion_fase1/modelo_volumenes_aclaramiento.py`
- Resultados: `validacion_fase1/resultados/modelo_volumenes_aclaramiento.json`
- Figura: `validacion_fase1/resultados/fig_volumenes_aclaramiento.png`

## Resultado principal

Ajustar los volúmenes junto con el aclaramiento reduce el error en perros anestesiados de un MDAPE de 23,7 % a 8,5 %. Los revisores tenían razón: al fijar los volúmenes de Levionnois, el error de volumen se cargaba sobre el aclaramiento.

- **Volumen central:** bien determinado. En anestesia es unas 2,6 veces el de Levionnois (IC 95 % aproximado: 2,2–3,0), es decir, V1 ≈ 2,7 L/kg.
- **Volumen periférico:** no se puede determinar con estos datos (IC 95 % aproximado: 0,5–3,5 veces).
- **Aclaramiento en el rango clínico:** baja de 2,5 / 2,2 / 1,8 a 1,8 / 1,6 / 1,4 L/h/kg (con 0,5 / 1 / 2 ng/mL). Ahora queda dentro del flujo hepático del perro.

## Comparación de estructuras (perros anestesiados, n = 20)

| Estructura | Parámetros | MDPE / MDAPE | AICc | Validación cruzada: predice Lin / Pascoe (MDPE) |
|---|---|---|---|---|
| A · Cl(C), volúmenes de Levionnois (actual) | Cl0 3,21 · C50 0,95 | −8,8 / 23,7 % | −47,0 | −32 % / +42 % |
| B · Cl constante + V1 + V2 | Cl 1,56 · f1 2,65 · f2 4,15 | −3,8 / 11,4 % | −62,5 | −18 % / +12 % |
| **C · Cl(C) + V1 + V2** | Cl0 3,47 · C50 0,21 · f1 2,62 · f2 1,75 | −0,3 / 8,5 % | −80,2 | −20 % / +17 % |
| D · Cl con retraso + V1 + V2 | Cl0 3,99 · C50 0,12 · kh 0,012 min⁻¹ · f1 2,16 · f2 1,03 | +0,1 / 9,1 % | −80,3 | −17 % / +4 % |
| E · Cl con retraso, volúmenes de Levionnois | Cl0 5,26 · C50 0,03 · kh en el límite | −5,2 / 9,2 % | −75,5 | −15 % / +12 % |

En las estructuras con retraso, el aclaramiento sigue a la Cp con un retraso de t½ ≈ 1 h.

**Lectura de la tabla**

- **La dependencia de la concentración se mantiene** con los volúmenes libres: C supera a B por 18 puntos de AICc.
- **C y D empatan.** En D el volumen periférico vuelve al de Levionnois y el retraso hace el papel del cambio fisiológico en el tiempo.
- **Solo el retraso no basta:** E queda peor y su parámetro de retraso termina en el límite.

## Comprobaciones externas

| Estructura | Despiertos no usados (MDPE / MDAPE) | Lin tras despertar, 3–24 h | t½ al detener a las 24 h (medida 0,43 h) | AUC del bolo de Levionnois (8,65) |
|---|---|---|---|---|
| A | +12,8 / 17,7 % | −15 % | 0,36 h | 5,92 |
| C | −11,6 / 16,2 % | −45 % | 0,47 h | 7,32 |
| D | +3,8 / 11,2 % | −48 % | 0,62 h | 6,72 |

**El modelo actual (A) sobrestima el aclaramiento tras detener la infusión.** Predice una t½ de 0,36 h, más rápida que la medida (0,43 h), como señalaron los revisores. C la reproduce mejor (0,47 h).

**Ningún modelo predice bien a los perros de Lin después de despertar.**
- Con la misma infusión, la Cp baja de 0,40–0,47 ng/mL en anestesia a unos 0,23 ng/mL despiertos. El aclaramiento casi se duplica al terminar la anestesia.
- Es una prueba, dentro de un mismo estudio, de que el estado fisiológico cambia el aclaramiento.
- Por eso el modelo C vale solo para perros anestesiados.

## Aclaramiento aparente fuera del estado estacionario

Con 1 µg/kg/h sin carga, el cociente tasa/Cp de cada modelo es (L/h/kg):

| Modelo | 30 min | 1 h | 2 h | 4 h | 8 h | Equilibrio |
|---|---|---|---|---|---|---|
| C | 7,6 | 4,7 | 3,0 | 2,2 | 1,9 | 1,78 |
| A | 4,4 | 3,3 | 2,8 | 2,6 | 2,6 | 2,62 |

**Calcular el aclaramiento con tasa/Cp antes del equilibrio lo sobrestima:** con el modelo C, un 70 % a las 2 h. Con los volúmenes corregidos el equilibrio tarda más de 8 h en alcanzarse. Esto afecta a los aclaramientos aparentes de van Oostrom (37–77 min) que se usaron como argumento.

## Consecuencias para la dosificación en anestesia

| Objetivo | Carga en 10 min (A → C) | Mantenimiento en equilibrio (A → C) |
|---|---|---|
| 0,5 ng/mL | 0,70 → 1,51 µg/kg | 1,25 → 0,92 µg/kg/h |
| 1 ng/mL | 1,38 → 2,99 µg/kg | 2,16 → 1,55 µg/kg/h |
| 2 ng/mL | 2,69 → 5,94 µg/kg | 3,64 → 2,75 µg/kg/h |

Con el modelo C, la carga se duplica y el mantenimiento baja entre un 25 % y un 30 %. Con 2 ng/mL, la carga supera el límite blando de 3 µg/kg. Esto concuerda con Pascoe 2006: una carga de 3 µg/kg seguida de 3 µg/kg/h dio unos 1,5 ng/mL a la hora y unos 2 ng/mL desde las 3 h.

## Limitaciones

- Siguen siendo medias de grupo de dos estudios (20 puntos).
- El volumen periférico no está determinado.
- C y D no se pueden distinguir con estos datos.

**Para el ensayo:** hacen falta muestras de 5 a 20 min (para V1), muestras tras detener la infusión con el perro aún anestesiado (para V2 y para el retraso), y gasto cardíaco o al menos FC y PA continuas.
