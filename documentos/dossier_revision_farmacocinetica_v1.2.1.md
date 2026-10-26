# Dossier para revisión farmacocinética independiente · Simulador TCI de dexmedetomidina en perros v1.2.1

Oct 9, 2026 · @francisco

## 1. Qué se pide al revisor

Pedimos una opinión independiente sobre si el modelo farmacocinético que guía la bomba del simulador es adecuado para iniciar un estudio clínico en perros anestesiados (Fases 2 y 3), y qué cambiaría antes. No se pide revisar el código línea a línea: la verificación del software (Fase 0) se resume en el apartado 6.

El simulador usaba el modelo de Levionnois et al. (2022). La validación externa mostró que, en perros anestesiados y a concentraciones clínicas (0,2–2 ng/mL), la concentración medida es aproximadamente la mitad de la predicha. Desde la versión 1.2.0 el simulador usa por defecto un aclaramiento dependiente de la concentración calibrado con las medias de grupo de solo 2 estudios en perros anestesiados. Esa decisión es lo que más necesita revisión.

**Preguntas concretas**

1. **Calibración escasa.** ¿Es defendible usar como modelo por defecto en la Fase 3 un modelo calibrado con las medias de grupo de 2 estudios (Pascoe 2006 y Lin 2008; 20 puntos tras digitalizar sus figuras)? ¿O sería preferible el modelo publicado con un factor de corrección constante del aclaramiento, o el ajuste solo con Pascoe 2006 (Cl0 3,00 L/h/kg; C50 0,55 ng/mL)?
2. **Plausibilidad fisiológica.** Cl0 = 3,15 L/h/kg supera el flujo sanguíneo hepático del perro (≈ 1,8–2,4 L/h/kg en sangre). ¿Lo considera compatible con la eliminación de la dexmedetomidina (relación sangre/plasma, eliminación extrahepática) o apunta a un problema de método en los estudios de origen?
3. **Estructura.** ¿Es razonable atribuir toda la diferencia al aclaramiento, o habría que modificar también V1 (la anestesia y la vasoconstricción α2 cambian la distribución inicial)? ¿Recomienda un modelo mecanicista en el que el aclaramiento dependa del gasto cardíaco, que la propia dexmedetomidina reduce? Es la pregunta principal. Con las curvas completas, la Cp en anestesia sube durante 2–3 h pese a la carga; un V1 ≈ 2,8 veces mayor lo reproduce mucho mejor (apartado 5), pero implicaría cargas casi 3 veces mayores.
4. **Elección del ajuste.** Cl∞ fijado en 1,16 L/h/kg (el publicado), mínimos cuadrados en escala logarítmica, mismo peso por grupo y puntos de 10 a 240 min. ¿Cambiaría alguna de estas decisiones?
5. **Escalado por peso.** El simulador escala todos los parámetros de forma lineal con el peso (2–80 kg; el estudio incluye perros de 5–40 kg). ¿Recomienda escalado alométrico del aclaramiento (exponente 0,75) antes de la Fase 3?
6. **Diseño de la Fase 3.** Con 18 perros, objetivos de 0,5, 1 y 2 ng/mL y 8 muestras por perro (10, 15, 20, 30 y 60 min; final o 120 min; +15 y +60 min tras detener la infusión), ¿se pueden estimar Cl0, C50 y V1 con efectos mixtos? ¿Qué muestras añadiría o movería? Las de 15 y 20 min se añadieron en la versión 1.2 del protocolo para estimar V1.
7. **Criterio de aceptación.** ¿Son adecuados MDPE dentro de ±20 % y MDAPE ≤ 30 % (criterio de los TCI humanos) para un TCI veterinario de dexmedetomidina?
8. **Discordancia de Dent 2019.** Concentraciones ≈ 4 veces mayores que las de los demás estudios con dosis parecidas (Cl 0,48 L/h/kg). ¿La excluiría como atípica o la tendría en cuenta como variabilidad real entre poblaciones?

Cualquier otra observación es bienvenida. Indique por favor, para cada punto, si lo considera **bloqueante** (debe resolverse antes del primer perro) o **mejora** (puede esperar a los datos de la Fase 3).

## 2. Resumen

El simulador calcula la velocidad de una bomba de jeringa convencional para alcanzar y mantener una concentración plasmática objetivo (Cp) de dexmedetomidina en el perro. El modelo publicado reproduce bien las concentraciones altas, pero en perros anestesiados a concentraciones clínicas sobrestima la Cp alrededor de un 50 %. La versión 1.2.0 corrige el aclaramiento a concentraciones bajas.

| Elemento | Situación (v1.2.1, 9/10/2026) |
| --- | --- |
| Modelo base | Levionnois et al. 2022: bicompartimental, 8 Beagles despiertos, bolo de 10 µg/kg |
| Algoritmo TCI | Shafer y Gregg (1992), modo plasma, carga en 10 min, pasos de bomba de 0,1 mL/h |
| Modelo por defecto | «Perro anestesiado (corregido)»: Cl(C) = 1,16 + 1,99 · 0,92 / (0,92 + C) L/h/kg; V1, V2 y Cl2 publicados |
| Alternativa | Modelo publicado, seleccionable |
| Fase 0, verificación | Conforme: 944 escenarios frente a una referencia independiente; error numérico máx. 0,06 %; mantenimiento dentro de ±4,4 % del objetivo |
| Fase 1, validación externa | 7 estudios, 93 medias de grupo (figuras de Lin 2008 y Pascoe 2006 digitalizadas). Modelo publicado: MDPE −41 % y MDAPE 46 % en total; −31 % y 42 % en despiertos; −50 % en anestesiados |
| Modelo corregido | Anestesiados (calibración, n = 20): MDPE −11 %, MDAPE 23 %. Despiertos (no usados, n = 63, incluye Lin 3–26 h): MDPE −3 %, MDAPE 18 % (publicado −37 % y 40 %). No reproduce la subida de la Cp en las primeras horas de anestesia |
| Fases 2 y 3 | Protocolo TCI-DEX-01 redactado: 30 perros anestesiados con isoflurano, 18 con muestras, objetivos de 0,5, 1 y 2 ng/mL. No iniciado |

El simulador es por ahora una herramienta educativa y de investigación. No controla bombas ni está validado clínicamente.

## 3. Modelo base y algoritmo TCI

El simulador implementa el modelo final de Levionnois et al. (2022, Tabla 2) sin cambios en volumen ni en aclaramiento intercompartimental. Todos los parámetros se escalan de forma lineal con el peso.

| Parámetro | Estimación | IC 95 % publicado | Unidad |
| --- | --- | --- | --- |
| V1 | 1,03 | 0,92–1,15 | L/kg |
| V2 | 0,41 | 0,13–0,70 | L/kg |
| Cl1 (sistémico) | 1,16 | 0,95–1,37 | L/h/kg |
| Cl2 (intercompartimental) | 1,87 | 1,35–2,38 | L/h/kg |

Con estos valores el programa reproduce los parámetros secundarios publicados: t½ 0,91 h (publicado 0,92), AUC tras 10 µg/kg 8,62 h·ng/mL (8,65) y MRT 1,24 h (1,25). Cantidades A1 y A2 en µg, Cp = A1/V1 en ng/mL, R = velocidad de infusión en µg/min:

```latex
\frac{dA_1}{dt} = R(t) - (k_{10} + k_{12})\,A_1 + k_{21}\,A_2 \qquad \frac{dA_2}{dt} = k_{12}\,A_1 - k_{21}\,A_2 \qquad k_{10} = \frac{Cl}{V_1},\; k_{12} = \frac{Cl_2}{V_1},\; k_{21} = \frac{Cl_2}{V_2}
```

**Algoritmo TCI (Shafer y Gregg 1992, modo plasma).**

1. Subida de objetivo: carga a velocidad constante durante 10 min, calculada para que la Cp llegue exactamente al objetivo al final de la carga (no se usa bolo rápido, para atenuar la respuesta hipertensiva). Con el modelo publicado la solución es analítica; con el corregido, Runge-Kutta 4 con paso de 1 s y método de la secante.
2. Mantenimiento: con la Cp fija en el objetivo, la velocidad ideal es R(τ) = A1·(k10 + k12) − k21·A2(τ), exacta también con el modelo corregido porque el aclaramiento es constante cuando la Cp no cambia.
3. Bomba discreta: cada velocidad se redondea a 0,1 mL/h y se mantiene mientras la ideal quede dentro de una banda de ±5 %. Con el modelo corregido la banda se estrecha según la sensibilidad d ln(C·Cl)/d ln C (0,77–1) y la velocidad nunca se programa al otro lado de la de equilibrio final.
4. Bajada de objetivo o pausa: bomba a 0 hasta que la Cp, en descenso libre, alcanza el objetivo; después, mantenimiento.
5. La Cp mostrada se integra por Euler con paso de 1 s con la velocidad que lleva realmente la bomba. En modo manual se usa la hora a la que el operador confirma cada cambio.
6. Tras detener la infusión, la Cp se sigue calculando durante 120 min.

Hay un módulo de premedicación IM con supuestos no validados (F = 1; absorción de primer orden con t½ de 3 min). El protocolo de las Fases 2 y 3 no lo usa: la premedicación es metadona.

**Límites de seguridad** (iguales con los dos modelos):

- Cp objetivo: aviso por encima de 2,5 ng/mL y bloqueo por encima de 4.
- Velocidad instantánea: aviso por encima de 20 µg/kg/h; máximo duro de 30 µg/kg/h, y si se alcanza la carga se alarga.
- Dosis en 60 min: aviso por encima de 6 µg/kg y bloqueo por encima de 12.
- Carga: aviso por encima de 3 µg/kg.

## 4. Validación externa con datos publicados (Fase 1)

El modelo publicado predice bien las concentraciones de 2–15 ng/mL, pero sobrestima las de uso clínico, sobre todo en perros anestesiados (MDPE −50 %, n = 22). El aclaramiento que reproduce cada estudio aumenta cuando la concentración baja.

**Método.**

- Se reprodujo el protocolo de cada estudio (dosis, duración de la administración, infusión y tiempos de muestreo) con la solución exacta del modelo.
- Las concentraciones se tomaron del texto o se digitalizaron de las figuras; son medias de grupo, no perros individuales.
- Error de Varvel sobre esas medias: PE = (medida − predicha) / predicha, con MDPE como sesgo y MDAPE como imprecisión.
- «Cl que ajusta» es el aclaramiento que mejor reproduce cada curva con V1, V2 y Cl2 fijos (mínimos cuadrados en escala logarítmica).

| Estudio · grupo | Estado | Ensayo | n | MDPE | MDAPE | Cl que ajusta (L/h/kg) |
| --- | --- | --- | --- | --- | --- | --- |
| Kuusela 2000 · bolo 10 µg/kg | despiertos | GC-MS | 7 | −23 % | 31 % | 1,62 |
| Kuusela 2000 · bolo 20 µg/kg | despiertos | GC-MS | 7 | −12 % | 21 % | 1,36 |
| Honkavaara 2012 · bolo 10 µg/kg | despiertos | LC-MS | 9 | +20 % | 20 % | 1,20 |
| de Sant'Ana Alves 2024 · 2 µg/kg en 2 min | despiertos | UHPLC-MS/MS | 8 | −38 % | 44 % | 3,92 |
| van Oostrom 2011 · 1 µg/kg + 1 µg/kg/h | despiertos | LC-MS/MS | 5 | −37 % | 37 % | 2,01 |
| van Oostrom 2011 · 3 + 3 µg/kg/h | despiertos | LC-MS/MS | 5 | −18 % | 18 % | 1,62 |
| van Oostrom 2011 · 5 + 5 µg/kg/h | despiertos | LC-MS/MS | 5 | 0 % | 15 % | 1,09 |
| Lin 2008 · ≈1 µg/kg/h 24 h, isoflurano 2 h | anestesiados 2 h; después despiertos | LC-MS/MS | 20 | −60 % | 60 % | 3,05 |
| Lin 2008 · ≈1 µg/kg/h 24 h, propofol 2 h | anestesiados 2 h; después despiertos | LC-MS/MS | 18 | −59 % | 59 % | 3,09 |
| Pascoe 2006 · 0,5 µg/kg/h, isoflurano | anestesiados | GC-MS (suero) | 4 | −52 % | 52 % | 2,51 |
| Pascoe 2006 · 3 µg/kg/h, isoflurano | anestesiados | GC-MS (suero) | 4 | −23 % | 23 % | 1,56 |
| Dent 2019 · bolo 5 µg/kg | despiertos | UPLC-MS/MS | 1 | +83 % | 83 % | 0,68 |

Todos los puntos (n = 93): MDPE −41 %, MDAPE 46 %; la cifra pesa mucho Lin 2008, con 38 puntos. Despiertos (n = 71): −31 % y 42 %. Anestesiados (n = 22): −50 % y 50 %. Sin los puntos aproximados: −37 % y 44 %.

**Aclaramiento aparente en meseta** (velocidad / Cp media durante la infusión):

- Anestesiados: 2,5 L/h/kg con 0,20 ng/mL y 1,6 con 1,9 ng/mL (Pascoe); 2,5–2,9 con 0,36–0,43 ng/mL (Lin, 15–120 min).
- Despiertos: 1,9 con 0,53 ng/mL; 1,6 con 1,87; y 1,2 con 4,0 ng/mL (van Oostrom).
- Lin 2008 ya despiertos con la infusión: 2,8 L/h/kg con 0,37–0,38 ng/mL de 3 a 12 h, y 3,7–4,5 a las 24 h. Indica que el aclaramiento sigue aumentando con el tiempo.

**Extracción de los datos.**

- Lin 2008: figura 2 digitalizada, con 21 tiempos por grupo de 5 min a 26 h (la infusión se detiene a las 24 h). Ejes calibrados con sus marcas; los valores coinciden con las cifras del texto. Seis puntos de propofol tapados por los de isoflurano se marcan como aproximados (±0,02 ng/mL) y dos como no legibles.
- Pascoe 2006: figura 1 digitalizada, con 4 tomas por dosis entre 1 y 7 h. Medias 0,205 y 1,92 ng/mL, frente a 0,198 y 1,903 publicadas.
- Lin 2008 dosificó 25 µg/m², que equivale a 1,055 µg/kg con el peso mediano de 13,7 kg.
- Dent 2019: una sola concentración (Clast 1,4 ng/mL a ≈ 110 min) y parámetros no compartimentales (Cl 8,0 mL/min/kg = 0,48 L/h/kg; Vss 0,37 L/kg).

## 5. Modelo corregido para perros anestesiados

Con solo el aclaramiento corregido (Cl0 = 3,15 L/h/kg, C50 = 0,92 ng/mL), el sesgo en perros anestesiados pasa de −50 % a −11 % (MDAPE 23 %), y en perros despiertos que no se usaron para calibrar, de −37 % a −3 % (MDAPE 18 %). Pero las curvas completas muestran un curso temporal que este modelo no reproduce: en anestesia la Cp sube durante 2–3 h pese a la carga.

```latex
Cl(C) = Cl_{\infty} + \left(Cl_0 - Cl_{\infty}\right)\frac{C_{50}}{C_{50} + C} \qquad Cl_{\infty} = 1{,}16 \text{ L/h/kg (fijo)},\quad Cl_0 = 3{,}15 \text{ L/h/kg},\quad C_{50} = 0{,}92 \text{ ng/mL}
```

V1, V2 y Cl2 son los publicados; C es la Cp. A concentración alta el modelo es el publicado. Mecanismo propuesto: la dexmedetomidina reduce el gasto cardíaco y el flujo hepático de forma dependiente de la concentración. Honkavaara 2012 observó que bloquear el efecto periférico con MK-467 aumenta el aclaramiento.

**Calibración.**

- Datos: los puntos de perros anestesiados desde el minuto 10, de las figuras digitalizadas. Son 6 por grupo de Lin 2008 (15–120 min) y 4 por dosis de Pascoe 2006 (1–7 h). Lin de 3 a 26 h, con los perros ya despiertos, sirve de comprobación.
- Ajuste: Cl0 y C50 por mínimos cuadrados de log(medida) − log(predicha), con el mismo peso por grupo. Se usó Nelder-Mead desde 4 puntos de partida, con límites Cl0 1,16–6 L/h/kg y C50 0,05–10 ng/mL.
- Integración: LSODA con tolerancia relativa de 10⁻⁸.
- Resultado con las cifras del texto (v1.2.0): Cl0 = 3,147 y C50 = 0,917, redondeados a 3,15 y 0,92. Con las curvas completas el reajuste da 3,21 y 0,95: la velocidad de mantenimiento con 1 ng/mL pasa de 2,11 a 2,16 µg/kg/h (+2 %), así que el simulador conserva 3,15 y 0,92. Todas las cifras de este apartado son con 3,15 y 0,92.

| Grupo de calibración | Tiempos (min) | Medida (ng/mL) | Corregido (ng/mL) | MDPE corregido | MDPE publicado |
| --- | --- | --- | --- | --- | --- |
| Lin 2008 · isoflurano | 15, 30, 45, 60, 90, 120 | 0,44 · 0,41 · 0,40 · 0,42 · 0,43 · 0,47 | 0,66 · 0,55 · 0,51 · 0,48 · 0,45 · 0,44 | −17 % | −48 % |
| Lin 2008 · propofol | 15, 30, 45, 60, 90, 120 | 0,34 · 0,33 · 0,34 · 0,35 · 0,39 · 0,41 | 0,66 · 0,55 · 0,51 · 0,48 · 0,45 · 0,44 | −30 % | −57 % |
| Pascoe 2006 · 0,5 µg/kg/h | 68, 151, 236, 319 | 0,18 · 0,20 · 0,23 · 0,21 | 0,20 · 0,18 · 0,18 · 0,18 | +15 % | −52 % |
| Pascoe 2006 · 3 µg/kg/h | 70, 180, 290, 412 | 1,52 · 2,18 · 1,99 · 1,99 | 1,74 · 1,61 · 1,59 · 1,59 | +25 % | −23 % |

El modelo sobrestima la Cp al principio y la subestima en meseta. La Cp medida sube durante las primeras 2–3 h en los dos estudios, mientras que el modelo predice que baja tras la carga. Se analiza más abajo, en «Curso temporal y volumen».

| Conjunto | n | Publicado MDPE | Publicado MDAPE | Corregido MDPE | Corregido MDAPE |
| --- | --- | --- | --- | --- | --- |
| Anestesiados (calibración) | 20 | −49,9 % | 49,9 % | −10,7 % | 23,3 % |
| Anestesiados con el reajuste (3,21 / 0,95) | 20 | — | — | −8,6 % | 23,7 % |
| Despiertos (no usados; incluye Lin 3–26 h) | 63 | −37,3 % | 39,5 % | −2,7 % | 17,8 % |
| Todos, desde el minuto 10 | 83 | −45,3 % | 45,7 % | −5,2 % | 18,7 % |

Por estudio, en despiertos:

- Mejoran Kuusela (−5 % y +4 %, frente a −27 % y −15 % con el publicado), van Oostrom con 1 y 3 µg/kg/h (+11 % y +11 %, frente a −37 % y −18 %) y de Sant'Ana Alves (−32 % frente a −45 %); también Lin 2008 de 3 a 26 h (−22 % y −19 %, frente a −68 % y −63 %). Tras detener la infusión a las 24 h, la semivida aparente medida fue 0,43 h; el corregido predice 0,37 h y el publicado 0,85 h.
- Empeoran Honkavaara (+24 % frente a +1 %), van Oostrom con 5 µg/kg/h (+23 % frente a 0 %) y Dent 2019 (+474 % frente a +83 %).

&#91;image: Aclaramiento aparente frente a la Cp medida, con las curvas de los modelos publicado, corregido y experimental\]

Figura 1 · Aclaramiento aparente en meseta (velocidad / Cp media) frente a la Cp medida, con la curva del modelo corregido. La línea gris punteada es un modelo experimental ajustado con todos los estudios (Cl0 4,69; Cl∞ 0,92; C50 0,20). En validación cruzada no mejoró al publicado y no se adoptó.

&#91;image: Cp medida frente a predicha con el modelo publicado y con el corregido\]Asd

Figura 2 · Medido frente a predicho. La banda indica ±30 %.

**Validación cruzada entre los dos estudios en anestesiados.**

- Calibrado solo con Pascoe 2006 (Cl0 3,00; C50 0,55), predice Lin 2008 con un MDPE de −32 %, frente a −51 % con el publicado.
- Al revés no es informativo. Lin 2008 solo tiene Cp de ≈ 0,4 ng/mL, así que C50 no es identificable y llega al límite de 10 ng/mL; el error en Pascoe es entonces de +42 %.

**Curso temporal y volumen (exploración, no adoptada).** En los dos estudios la Cp de los perros anestesiados sube durante 2–3 h pese a la carga (Lin: 0,40 → 0,47 y 0,33 → 0,41 ng/mL; Pascoe 3 µg/kg/h: 1,52 → 2,0–2,2). Los autores de Pascoe ya lo atribuyeron a una carga insuficiente. Se probaron 4 estructuras con los mismos datos (`modelo_volumen.py`):

| Estructura (anestesiados) | Cl0 (L/h/kg) | C50 (ng/mL) | V1 × | V2 × | Error (obj.) | MDAPE |
| --- | --- | --- | --- | --- | --- | --- |
| Cl0 + C50 (como el simulador) | 3,21 | 0,95 | 1 | 1 | 0,302 | 23,7 % |
| Cl0 + C50 + V1 | 3,39 | 0,24 | 2,80 | 1 | 0,044 | 7,3 % |
| Cl0 + C50 + V2 | 2,86 | 0,59 | 1 | 4,52 | 0,156 | 8,6 % |
| Cl0 + C50 + V1 + V2 | 3,47 | 0,20 | 2,62 | 1,75 | 0,042 | 8,5 % |

&#91;image: Curso temporal en anestesia: medido, modelo corregido y modelo con volumen central mayor\]

Figura 3 · Con un volumen central ≈ 2,8 veces mayor (V1 ≈ 2,9 L/kg) el modelo reproduce la subida inicial y la meseta de los dos estudios.

- **Validación cruzada.** El modelo con V1 mayor predice mejor el estudio que no ha visto: Lin 2008 con un MDPE de −15 % (frente a −32 %) y Pascoe 2006 con +28 % (frente a +43 %). Pero es inestable: ajustado solo con Lin 2008 da Cl0 11,8 y C50 0,05.
- **Comprobación con Lin 2008 ya despiertos (3–24 h).** Empeora (−40 % frente a −15 %) y predice un descenso tras la infusión mucho más lento que el medido. Es coherente con un volumen mayor solo durante la anestesia, pero no lo demuestra.
- **Consecuencia si fuera cierto.** Con el simulador actual, la Cp quedaría por debajo del objetivo la primera hora y, en meseta, un 30–40 % por encima con objetivos de 0,5–2 ng/mL. La causa es que este modelo da menos aclaramiento con 1 ng/mL (1,59 frente a 2,11 L/h/kg). Entre 0,2 y 2 ng/mL no hay datos de meseta en anestesia que decidan entre los dos modelos.
- **Por qué no se adopta.** Supondría cargas casi 3 veces mayores: ≈ 2,9 µg/kg en el compartimento central con 1 ng/mL y ≈ 5,8 con 2 ng/mL, con más riesgo de hipertensión y bradicardia transitorias.

**Comprobación con el estudio original.** Tras 10 µg/kg IV, el modelo corregido predice un AUC de 6,00 h·ng/mL, frente a 8,65 publicado por Levionnois (−31 %). En cambio predice bien Kuusela 2000, con la misma dosis y raza. Lo interpretamos como variabilidad entre estudios, pero el revisor puede valorarlo de otra forma.

**Consecuencias para la dosificación y riesgo.** La tabla da la velocidad de mantenimiento en equilibrio y la Cp de equilibrio si el perro eliminara como el modelo publicado (Cl 1,16) o como los perros de Dent 2019 (Cl 0,46).

| Objetivo (ng/mL) | Cl corregido (L/h/kg) | Velocidad corregida (µg/kg/h) | Velocidad publicada (µg/kg/h) | Cp si Cl = 1,16 | Cp si Cl = 0,46 |
| --- | --- | --- | --- | --- | --- |
| 0,5 | 2,45 | 1,22 | 0,58 | 1,06 | 2,66 |
| 1 | 2,11 | 2,11 | 1,16 | 1,82 | 4,59 |
| 2 | 1,79 | 3,57 | 2,32 | 3,08 | 7,77 |
| 3 | 1,63 | 4,88 | 3,48 | 4,21 | 10,61 |

El riesgo relativo de sobredosificación es mayor con objetivos bajos (2,1 veces con 0,5 ng/mL); el absoluto, con objetivos altos. En el estudio, la protección son los límites de dosis, que no cambian, la monitorización continua y una regla de parada: se revisa el modelo si la Cp medida supera a la predicha en más de un 50 % en 2 de los 6 primeros perros con muestras.

## 6. Verificación del software (Fase 0)

La versión 1.2.1 calcula lo que predicen sus dos modelos: es conforme en todos los requisitos frente a una implementación de referencia escrita aparte. Con los dos modelos da los mismos resultados, bit a bit, que la 1.2.0 (solo cambian textos de aviso), y con el publicado, los mismos que la 1.1.1.

| Comprobación | Resultado |
| --- | --- |
| Referencia independiente: constantes del artículo y de la calibración; exponencial de matriz (publicado) y Dormand-Prince 8 con tolerancia relativa 10⁻¹⁰ (corregido) | 944 escenarios (472 por modelo): pesos de 2–80 kg, objetivos de 0,25–4 ng/mL, 30–240 min, cambios de objetivo, pausas, modo manual y límites de bomba |
| Error numérico del motor (Euler, 1 s) | máx. 0,06 % de la escala del caso |
| Cp al final de la carga | dentro de ±1 % (máx. 0,97 %); sin sobreimpulso > 1 % |
| Velocidad de carga frente a la exacta | diferencia máx. 0,05 mL/h (resolución de la bomba: 0,1) |
| Mantenimiento | dentro de ±5 % (máx. 4,4 %) |
| Descenso tras la infusión (120 min) | error máx. 0,03 % |
| Regresión: modelo publicado frente a la v1.1.1 | 922/922 comparaciones idénticas |
| Regresión: los dos modelos en la v1.2.1 frente a la v1.2.0 | 1844/1844 comparaciones idénticas (la v1.2.1 solo cambia textos de aviso) |
| Cp recalculada solo desde el CSV exportado | 221 valores en 20 archivos; diferencia máx. 0,26 %, debida al redondeo de la pantalla |
| Interfaz y aplicación de Windows | 22 pruebas en HTML y en .exe; 9 de instalación y ejecución |

Durante el desarrollo de la v1.2.0 apareció y se corrigió un defecto. Con el modelo corregido y objetivos de 0,25–1,5 ng/mL en 240 min, el mantenimiento se apartaba hasta un 6,7 % del objetivo. La causa era que un error del 5 % en la velocidad produce más del 5 % en la Cp cuando el aclaramiento depende de la concentración. La implementación de referencia y las pruebas son del mismo equipo que el programa, con ayuda de IA; una revisión por terceros también sería útil aquí.

## 7. Plan farmacocinético de la Fase 3

En 18 perros con muestras, la bomba se guiará con el modelo corregido y cada concentración medida se comparará con la que predicen ambos modelos con la infusión realmente administrada. Después se reestimarán Cl0 y C50. El protocolo completo es TCI-DEX-01, versión 1.2.

| Aspecto | Diseño previsto |
| --- | --- |
| Perros | 18 de propietario, ASA I–II, 10–40 kg (subcohorte farmacocinética), 6 por objetivo; 30 en total contando los que solo aportan datos clínicos |
| Anestesia | Metadona 0,2 mg/kg IM; propofol IV; isoflurano (FE'Iso inicial 1,3 %), ventilación mecánica. Sin agonistas α2 en las 24 h previas |
| Objetivos | 0,5, 1 o 2 ng/mL, asignación aleatoria; carga en 10 min; duración máxima de 180 min |
| Bomba | Modo manual: un operador confirma cada cambio y el CSV guarda la hora real de cada velocidad |
| Muestras | M0 (antes); M10, M15, M20, M30 y M60 (M15 y M20 añadidas en la versión 1.2 del protocolo para estimar V1); MF (fin de la infusión o 120 min); P15 y P60 tras detenerla. Hora exacta con el reloj del simulador |
| Lugar y matriz | Arterial (metatarsiana dorsal) preferente; si no, yugular o safena, nunca de la extremidad de la infusión. Plasma (heparina de litio o EDTA K2 según el laboratorio, sin gel separador), centrifugado en < 30 min a 4 °C y conservado a −80 °C |
| Análisis | LC-MS/MS validada, ciego al grupo y a la hora; LLOQ ≤ 0,05 ng/mL; exactitud y precisión ±15 %; reanalítica del 10 %. Valores < LLOQ imputados como LLOQ/2, con análisis de sensibilidad |
| Cp predicha | `reconstruir_cp.py --muestras`: Cp de los dos modelos en el segundo exacto de cada muestra, a partir del registro de tasas |

**Análisis previsto.**

- Variable principal: PE, MDPE y MDAPE por perro (Varvel), con mediana poblacional e IC 95 % por bootstrap de perros. Criterio de aceptación: MDPE ±20 % y MDAPE ≤ 30 %. Se describen también divergencia y wobble.
- Factores del sesgo: modelo de efectos mixtos sobre log(Cm/Cp), con el objetivo, el tiempo, la FE'Iso, la PAM y el lugar de muestreo como efectos fijos.
- Comparación de modelos: MDAPE individual del corregido frente al publicado, con la prueba de Wilcoxon pareada.
- Reestimación: NLME de Cl0, C50 y, si es posible, V1 con todas las concentraciones medidas; el resultado define el modelo de la versión siguiente.
- Análisis intermedio tras 6 perros con muestras: se revisa el modelo si la Cp medida supera a la predicha en más de un 50 % en 2 o más perros.

Semiamplitud esperada del IC 95 % del MDPE poblacional: ±9 puntos con 18 perros, suponiendo una DE entre perros del 20 %. Por objetivo es de ±16 puntos. Las preguntas 5 a 7 del apartado 1 se refieren a este diseño.

## 8. Limitaciones conocidas

La principal limitación es la cantidad de datos en perros anestesiados: medias de grupo de 2 estudios (20 puntos), sin datos individuales. Además, el modelo no reproduce el curso temporal en anestesia.

- **Datos agregados.** Todos los datos externos son medias de grupo. El error de Varvel se define sobre perros individuales, y las medias ocultan la variabilidad entre perros.
- **Curvas digitalizadas.** Las curvas de Lin 2008 y Pascoe 2006 se digitalizaron de capturas de sus figuras. El error de lectura es de ≈ ±0,01 ng/mL, y de ±0,02 en los puntos de propofol tapados por los de isoflurano.
- **Ensayos y matrices distintos.** Hay GC-MS, LC-MS y UHPLC-MS/MS, con plasma o suero y sangre arterial, venosa central o periférica.
- **Conversiones y tiempos aproximados.** La dosis de Lin 2008 se convirtió desde µg/m²; en Lin y Dent algunos tiempos son aproximados.
- **Validez del modelo base.** Levionnois 2022 se obtuvo en 8 Beagles con muestreo de 120 min. El simulador lo usa en infusiones de hasta 240 min y en perros de 2–80 kg con escalado lineal por peso.
- **Dependencia del tiempo.** El modelo corregido no incluye el aumento del aclaramiento con el tiempo que sugiere Lin 2008 a las 24 h. En el rango del simulador (≤ 4 h) parece poco relevante, pero no está comprobado.
- **Concentración en plasma, no en el sitio efecto.** Sin ke0 no hay concentración en el sitio efecto.
- **Premedicación IM.** Sus supuestos están sin validar; no se usa en el estudio.
- **Autoría.** El modelo corregido, el análisis y el software son del mismo autor, que tiene un interés comercial en el simulador. Por eso se pide esta revisión independiente.

## 9. Material adjunto y cómo reproducir los cálculos

Todos los cálculos se reproducen con Python 3 (numpy, scipy, matplotlib, reportlab) y Node.js 22. Los datos de entrada son un CSV con una fila por media publicada.

| Archivo | Contenido |
| --- | --- |
| `validacion_fase1/datos/concentraciones_publicadas.csv` | 99 medias publicadas (93 fiables): estudio, grupo, dosis, duración, infusión y fin de la infusión, estado, ensayo, tiempo, Cp y fuente (texto o figura digitalizada). Las capturas de las figuras de Lin y Pascoe están en `datos/figuras/` |
| `validacion_fase1/datos/notas_datos.md` | Decisiones de extracción de cada estudio |
| `validacion_fase1/analisis.py` | Validación del modelo publicado: Varvel, sensibilidad, AUC y aclaramiento en meseta |
| `validacion_fase1/modelo_corregido.py` | Calibración del modelo corregido, validación cruzada y tabla de riesgo |
| `validacion_fase1/modelo_experimental.py` | Modelo de 3 parámetros ajustado con todos los estudios (no adoptado). Junto a él, `modelo_volumen.py`: exploración con volumen central o periférico mayor en anestesia (apartado 5) |
| `Informe_Fase1_validacion_externa_v4.pdf` | Informe completo de la Fase 1, con figuras por estudio |
| `Informe_verificacion_Fase0_v1.2.1.pdf` | Informe de verificación del software |
| `verificacion/motor/referencia.py` | Implementación de referencia independiente de los dos modelos |
| `verificacion/motor/reconstruir_cp.py` | Cp de los dos modelos a partir del CSV de un caso, por ejemplo en la hora de cada muestra |
| `tci_dexmedetomidina_perros.jsx` | Código del simulador (motor y modelos al principio del archivo) |
| Protocolo TCI-DEX-01 v1.2 | Fases 2 y 3 completas, con CRF y procedimiento de muestras |

Para reproducir: `python3 validacion_fase1/modelo_corregido.py` (≈ 15 s) y `verificacion/ejecutar_verificacion.sh` (Fase 0 completa, ≈ 15 min).

Respuesta deseada: un breve informe con la valoración de cada pregunta del apartado 1, indicando si es bloqueante o mejora. Puede comentar directamente sobre este documento.
