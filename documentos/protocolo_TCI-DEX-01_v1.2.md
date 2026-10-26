# Protocolo de estudio · Evaluación clínica y farmacocinética del Simulador TCI de dexmedetomidina en perros (Fases 2 y 3)

Oct 8, 2026 · @francisco

## 1. Datos administrativos y sinopsis

| Campo | Contenido |
| --- | --- |
| Código del estudio | TCI-DEX-01 |
| Versión y fecha del protocolo | 1.2 · 9 de octubre de 2026 (simulador v1.2.1) |
| Título | Evaluación clínica y farmacocinética del Simulador TCI de dexmedetomidina en perros anestesiados (Fases 2 y 3) |
| Investigador principal | Francisco Carvajal Sánchez, MV |
| Centro | \[completar: hospital o clínica, dirección\] |
| Comité de ética | \[completar: comité de ética / bienestar animal y número de registro\] |
| Normativa aplicable | \[completar: legislación nacional sobre uso de animales en investigación clínica veterinaria\] |
| Financiación | \[completar\] |
| Software evaluado | Simulador TCI de dexmedetomidina para perros, versión 1.2.1: modelo bicompartimental de Levionnois et al. (2022) con el aclaramiento corregido para perros anestesiados (por defecto); el modelo publicado queda como alternativa |
| Laboratorio analítico | \[completar: laboratorio externo con LC-MS/MS validada para dexmedetomidina\] |
| Diseño | Prospectivo, abierto, unicéntrico, aleatorizado 1:1:1 a tres concentraciones objetivo |
| Animales | 30 perros de propietario (5 de fase piloto incluidos), ASA I–II, sometidos a anestesia general programada ≥ 60 min |
| Subcohorte farmacocinética | 18 perros (6 por objetivo) con consentimiento específico para extracción de muestras |
| Intervención | Infusión de dexmedetomidina guiada por el simulador con el modelo corregido (objetivo 0,5, 1 o 2 ng/mL) durante anestesia con isoflurano |
| Variable principal | Rendimiento predictivo: MDPE y MDAPE de la concentración plasmática medida frente a la predicha por el modelo corregido (y, en paralelo, por el publicado) |
| Variables secundarias | Divergencia y *wobble*; eventos cardiovasculares; reducción de FE'Iso; rescates analgésicos; usabilidad |
| Criterio de aceptación | MDPE dentro de ±20 % y MDAPE ≤ 30 % |
| Duración prevista | 12 meses (2 de preparación, 8 de reclutamiento, 2 de análisis) |

**Sinopsis.** El simulador calcula, segundo a segundo, la velocidad de bomba necesaria para alcanzar y mantener una concentración plasmática objetivo de dexmedetomidina en el perro, con el modelo farmacocinético de Levionnois et al. (2022) y, desde la versión 1.2.0, con su aclaramiento corregido para perros anestesiados. La verificación del software (Fase 0) demostró que el programa calcula exactamente lo que predicen sus dos modelos. La validación externa con datos publicados (Fase 1) mostró que el modelo publicado sobrestima la concentración con dosis bajas: alrededor de un 20 % en perros despiertos y un 50 % en perros anestesiados (Lin et al. 2008; Pascoe et al. 2006). El modelo corregido, calibrado con esos dos estudios, reduce el error mediano en los datos publicados a un 23 % en perros anestesiados y un 18 % en despiertos. Pero se basa en las medias de grupo de solo 2 estudios, y no reproduce que en anestesia la Cp suba durante las primeras 2–3 h. Falta comprobar en pacientes reales anestesiados si la concentración que alcanza el perro coincide con la que muestra la pantalla (Fase 3, farmacocinética) y si su uso es seguro y práctico en el quirófano (Fase 2, clínica). Este protocolo combina ambas fases en un único estudio.

## 2. Antecedentes y justificación

**La dexmedetomidina en anestesia canina.** La dexmedetomidina es un agonista α2-adrenérgico que, en infusión continua durante la anestesia inhalatoria, aporta sedación, analgesia y reducción del requerimiento de anestésico volátil. Sus efectos cardiovasculares (bradicardia, aumento inicial de la resistencia vascular sistémica, bloqueo auriculoventricular) dependen de la concentración plasmática. Dosificarla por concentración en lugar de por velocidad fija permitiría alcanzar el efecto deseado con menos efectos adversos.

**Infusión controlada por objetivo (TCI).** Un sistema TCI usa un modelo farmacocinético para calcular, en cada momento, la velocidad de infusión que alcanza y mantiene la concentración plasmática elegida por el clínico. En medicina humana es práctica habitual con propofol y remifentanilo. En veterinaria se han descrito y validado sistemas TCI de propofol (Beths et al. 2001; Cattai et al. 2019) y de otros fármacos en perros, pero no existe ningún sistema TCI de dexmedetomidina para perros validado en pacientes clínicos.

**Modelo farmacocinético.** Levionnois et al. (2022) publicaron un modelo bicompartimental poblacional de dexmedetomidina intravenosa en perros: V1 1,03 L/kg; V2 0,41 L/kg; Cl1 1,16 L/h/kg; Cl2 1,87 L/h/kg. El simulador TCI-DEX implementa este modelo con el algoritmo de Shafer y Gregg (1992), una fase de carga de 10 minutos y pasos de bomba de 0,1 mL/h. Desde la versión 1.2.0 usa por defecto un modelo corregido para perros anestesiados, con los mismos volúmenes y Cl2 y un aclaramiento que aumenta cuando la concentración baja: Cl = 1,16 + 1,99 · 0,92 / (0,92 + C) L/h/kg, con C en ng/mL (Cl0 = 3,15 L/h/kg a concentración muy baja; C50 = 0,92 ng/mL). Con 0,5 ng/mL el aclaramiento es 2,45 L/h/kg; con 1 ng/mL, 2,11; con 2 ng/mL, 1,79; a concentraciones altas tiende al publicado (1,16). El modelo publicado sigue disponible en el selector del programa.

**Trabajo previo con el simulador.**

- *Fase 0 — verificación del software (v1.2.1).* 944 escenarios (472 con cada modelo) y 14 casos de fin de infusión comparados con una solución de referencia independiente (exacta con el modelo publicado; integrador de alta precisión con el corregido): error numérico máximo 0,06 %; Cp de mantenimiento dentro de ±4,4 % del objetivo; con el modelo publicado, resultados idénticos bit a bit a los de la v1.1.1 (922 comparaciones) y, con los dos modelos, a los de la v1.2.0 (1844 comparaciones; la v1.2.1 solo cambia textos de aviso); 22 pruebas de interfaz y 9 pruebas de la aplicación de escritorio superadas; la Cp de los dos modelos se puede recalcular de forma independiente desde el CSV exportado. El programa calcula correctamente lo que predicen sus dos modelos.
- *Fase 1 — validación externa con datos publicados (v4).* Se reprodujeron los protocolos de siete estudios: Kuusela et al. (2000), Honkavaara et al. (2012), van Oostrom et al. (2011), de Sant'Ana Alves et al. (2024) y Dent et al. (2019) en perros despiertos, y Lin et al. (2008) y Pascoe et al. (2006) en perros anestesiados. El modelo predice bien a concentraciones altas (2–15 ng/mL), pero sobrestima la concentración a las de uso clínico: con infusiones de 0,5–1 µg/kg/h en perros anestesiados la concentración medida fue aproximadamente la mitad de la predicha (MDPE −50 %), y hasta un 65–70 % menor tras 24 h. El aclaramiento aparente aumenta cuando la concentración baja (de 1,2–1,6 L/h/kg con 2–4 ng/mL a 2,4–4,6 L/h/kg con 0,2–0,5 ng/mL). El error va en la dirección de la infradosificación. Un modelo experimental con aclaramiento dependiente de la concentración mejoró los estudios de infusión a dosis baja pero no el conjunto en validación cruzada (MDAPE 23 % frente a 21 %), y no se adoptó. En cambio, un modelo corregido ajustado solo con los perros anestesiados (Cl0 3,15 L/h/kg; C50 0,92 ng/mL) reduce el error en anestesiados de −50 % a −11 % (MDAPE 23 %, con las curvas completas de Lin 2008 y Pascoe 2006 digitalizadas). En perros despiertos que no se usaron para calibrarlo, lo reduce de −37 % a −3 % (MDAPE 18 % frente a 40 %). Es el modelo por defecto del simulador desde la v1.2.0. El reajuste con las curvas completas (Cl0 3,21; C50 0,95) cambia la dosis un 2 % y no se ha aplicado. Sus límites: solo dos estudios calibrados, y la Cp en anestesia sube durante 2–3 h pese a la carga, algo que este modelo no reproduce. Un volumen central ≈ 2,8 veces mayor lo explicaría, pero no se ha adoptado porque supondría cargas casi 3 veces mayores.

**Por qué hace falta este estudio.** Los datos externos proceden de bolos o infusiones de velocidad fija, y solo dos estudios midieron la concentración en perros anestesiados (son los que se usaron para calibrar el modelo corregido). Nadie ha medido la concentración de dexmedetomidina en perros anestesiados con isoflurano que reciben un programa TCI, con sus cambios de velocidad. La anestesia inhalatoria modifica el gasto cardíaco y el flujo hepático, y por tanto puede modificar el aclaramiento. Solo una medición directa en este contexto puede decir si la concentración que muestra la pantalla es la real y si el sistema es apto para uso clínico.

## 3. Objetivos e hipótesis

**Objetivo principal (Fase 3, farmacocinética).** Determinar el rendimiento predictivo del simulador TCI-DEX v1.2.1, con su modelo corregido para perros anestesiados, en perros anestesiados con isoflurano, comparando la concentración plasmática de dexmedetomidina medida por LC-MS/MS con la concentración predicha por el simulador en el mismo instante.

**Objetivos secundarios.**

1. Describir la evolución del error de predicción en el tiempo (divergencia) y su variabilidad dentro de cada perro (*wobble*).
2. Comparar el rendimiento predictivo entre las tres concentraciones objetivo (0,5, 1 y 2 ng/mL).
3. Comparar, sin modificar el tratamiento, el modelo corregido (el que guía la bomba) con el modelo publicado de Levionnois, recalculando ambos con el programa de bomba real registrado en cada perro, y reestimar el aclaramiento (Cl0 y C50) con las concentraciones medidas.
4. Describir la incidencia de bradicardia, bloqueo auriculoventricular, hipotensión e hipertensión en función de la concentración objetivo y de la concentración medida (Fase 2, seguridad).
5. Describir la reducción de la fracción espirada de isoflurano (FE'Iso) y la necesidad de analgesia de rescate en cada grupo (Fase 2, efecto clínico).
6. Evaluar la usabilidad del simulador en el quirófano: tiempo de programación, errores de uso, ajustes de bomba no realizados a tiempo y valoración del operador.

**Hipótesis.**

- *H1 (principal).* En perros anestesiados con isoflurano, el simulador alcanza un MDPE dentro de ±20 % y un MDAPE ≤ 30 %, valores aceptados para sistemas TCI clínicos (Varvel et al. 1992).
- *H2.* Con el modelo corregido se espera un sesgo dentro de ±20 % en los tres objetivos. Con el modelo publicado, recalculado con la misma infusión, se espera un sesgo de alrededor de −50 % con 0,5 y 1 ng/mL (Fase 1). Si la corrección fuera excesiva, el sesgo del modelo corregido sería positivo (concentración medida mayor que la predicha), sobre todo con objetivos bajos. Por el curso temporal de la Fase 1, es posible además que la Cp medida quede por debajo de la predicha en los primeros 30–60 min y por encima en meseta.
- *H3.* La incidencia de efectos cardiovasculares que requieren intervención aumenta con la concentración objetivo, y es baja (< 10 %) con objetivos ≤ 1 ng/mL.

El estudio es exploratorio para los objetivos secundarios: sus resultados se presentarán con intervalos de confianza y sin corrección por multiplicidad.

## 4. Diseño del estudio

**Tipo.** Estudio clínico prospectivo, abierto, unicéntrico, con asignación aleatoria 1:1:1 a tres concentraciones plasmáticas objetivo de dexmedetomidina: 0,5, 1 y 2 ng/mL.

**Por qué tres objetivos.** El error del modelo en la Fase 1 dependía de la dosis. Estudiar un rango de objetivos permite saber si el sesgo cambia con la concentración y, de ser así, corregirlo. El límite superior de 2 ng/mL queda por debajo del límite blando de Cp objetivo del simulador (2,5 ng/mL) y dentro del rango usado clínicamente. Con el modelo corregido, la forma de la curva de aclaramiento depende de un único grupo con concentración alta (Pascoe 2006): los tres objetivos permiten estimarla. Con 2 ng/mL el simulador pide confirmar un aviso blando por la dosis de la primera hora (≈ 6,2 µg/kg frente al límite blando de 6 µg/kg); es esperado y queda registrado.

**Aleatorización.** Lista generada por ordenador en bloques de 3 y 6, estratificada por peso (< 15 kg y ≥ 15 kg), preparada por una persona ajena a la anestesia. La asignación se guarda en sobres opacos, cerrados y numerados que se abren después de la inducción.

**Enmascaramiento.** El anestesista y el operador de la bomba conocen el objetivo (es imprescindible para programar el simulador y vigilar al paciente). El laboratorio analítico desconoce el grupo, la concentración predicha y la hora de cada muestra: recibe solo un código de muestra. El análisis farmacocinético se hace con el plan de análisis cerrado antes de recibir los resultados.

**Fase piloto.** Los 5 primeros perros, aleatorizados igual que el resto, sirven para comprobar la logística de muestras, los tiempos de procesado y la usabilidad. Si no requieren cambios del protocolo, se incluyen en el análisis. Cualquier cambio se presentará al comité como enmienda antes de continuar.

**Subcohorte farmacocinética.** De los 30 perros, 18 (6 por objetivo) tendrán muestras de sangre seriadas, siempre que el propietario dé su consentimiento específico. Los 12 restantes aportan solo datos clínicos y de seguridad.

**Fin del estudio para cada perro.** 60 minutos después de detener la infusión (última muestra) o al alta de la recuperación anestésica, lo que ocurra después. Se registra cualquier evento adverso hasta 24 horas después.

**Diagrama de flujo del estudio.**

&#91;embedded content: Flujo del estudio TCI-DEX-01 · 6 pasos, 3 grupos, 2 resultados\]

Los 30 perros aportan datos clínicos y de seguridad (Fase 2); los 18 con muestras de sangre aportan además la comparación entre la concentración medida y la predicha (Fase 3).

## 5. Población de estudio

Perros de propietario remitidos al centro para un procedimiento quirúrgico o diagnóstico programado bajo anestesia general.

**Criterios de inclusión.**

1. Estado físico ASA I o II.
2. Edad ≥ 1 año.
3. Peso entre 5 y 40 kg (dentro del rango de los perros del modelo y de los límites del simulador).
4. Duración prevista de la anestesia ≥ 60 minutos.
5. Consentimiento informado firmado por el propietario (y consentimiento específico para muestras en la subcohorte farmacocinética).

**Criterios de exclusión.**

1. Cardiopatía conocida, soplo de grado ≥ 3/6, arritmia o bloqueo auriculoventricular en el ECG basal.
2. Hipovolemia, deshidratación > 5 %, anemia (hematocrito < 30 %) o hipoproteinemia (proteínas totales < 5 g/dL).
3. Enfermedad hepática o renal (ALT > 2 veces el límite superior, creatinina > 1,6 mg/dL o signos clínicos).
4. Gestación o lactancia.
5. Condición corporal ≥ 7/9 (el peso real sobrestima el volumen de distribución).
6. Administración de cualquier agonista α2 (dexmedetomidina, medetomidina, xilacina) o antagonista (atipamezol) en las 24 horas previas.
7. Tratamiento con fármacos que alteren el metabolismo hepático (por ejemplo, ketoconazol, fenobarbital) en el último mes.
8. Procedimiento con pérdida de sangre prevista > 10 % del volumen sanguíneo o cirugía cardíaca, torácica o intracraneal.
9. Peso < 10 kg en la subcohorte farmacocinética (para no superar el volumen máximo de extracción; ver sección 8).

**Criterios de retirada.** El perro se retira del estudio, y recibe el tratamiento que el anestesista considere oportuno, si: el propietario retira el consentimiento; aparece un evento adverso grave atribuible a la dexmedetomidina (sección 10); la anestesia dura < 45 minutos; o hay un error de dosificación (dilución o bomba) confirmado. Los datos recogidos hasta la retirada se analizan si el propietario lo permite, y el motivo se registra. Los perros retirados de la subcohorte farmacocinética antes de la muestra de 60 minutos se reemplazan.

## 6. Tamaño muestral

No hay un contraste de hipótesis formal para validar un sistema TCI: lo que se busca es estimar el sesgo (MDPE) y la imprecisión (MDAPE) con suficiente precisión. Los estudios de validación de TCI en personas y en perros suelen incluir entre 10 y 20 sujetos con 5 a 10 muestras cada uno. El tamaño se justifica por precisión y por seguridad.

**Subcohorte farmacocinética: 18 perros (6 por objetivo).**

- Cada perro aporta 8 muestras tras el inicio de la infusión (10, 15, 20, 30 y 60 min; final o 120 min; +15 y +60 min tras detenerla): unas 144 parejas medida–predicha.
- La unidad de análisis para la inferencia es el perro (MDPE y MDAPE individuales). Suponiendo una desviación estándar entre perros del MDPE individual del 20 % (dispersión observada entre estudios en la Fase 1), con 18 perros el intervalo de confianza del 95 % del MDPE poblacional tiene una semiamplitud de ±9 puntos porcentuales (1,96 · 20 / √18). Esto basta para distinguir un sesgo aceptable (|MDPE| ≤ 20 %) de uno inaceptable cuando el valor real está lejos del límite.
- Por objetivo (6 perros), la semiamplitud es de ±16 puntos: suficiente para detectar en un grupo un sesgo de ±20 % o mayor (con el modelo publicado, recalculado, se espera ≈ −50 %), no para comparaciones finas entre grupos (análisis exploratorio).

**Cohorte clínica y de seguridad: 30 perros (10 por objetivo).**

- Con 30 perros, la probabilidad de observar al menos un caso de un evento adverso con una incidencia real del 10 % es del 96 % (1 − 0,9³⁰).
- Si no se observa ningún evento grave en 30 perros, el límite superior del intervalo de confianza del 95 % de su incidencia es del 10 % (regla del tres: 3/30).

**Pérdidas.** Los perros de la subcohorte retirados antes de la muestra de 60 minutos, o con menos de 4 muestras válidas, se reemplazan hasta completar 6 por objetivo. Se estima reclutar hasta 34 perros en total.

## 7. Procedimientos

### 7.1 Preparación y anestesia

1. **Valoración previa.** Exploración física, condición corporal, peso en báscula calibrada el mismo día, hematocrito, proteínas totales, ALT, creatinina y ECG de 1 minuto. Ayuno de sólidos 6–8 h; agua hasta la premedicación.
2. **Premedicación.** Metadona 0,2 mg/kg IM. **No se administra ningún agonista α2** antes de la infusión: la dexmedetomidina IM añadiría una concentración de partida desconocida y el módulo de premedicación IM del simulador aún no está validado.
3. **Catéteres.** Uno en la vena cefálica para la inducción, los fluidos y la dexmedetomidina. En la subcohorte farmacocinética, un segundo acceso exclusivo para muestras: preferentemente arterial (arteria metatarsiana dorsal, que además permite la presión invasiva); si no es posible, venoso en la yugular o en la safena de otra extremidad. Nunca se toman muestras de la extremidad de la infusión. El sitio se registra y se mantiene en todo el perro.
4. **Inducción.** Propofol IV a efecto (1–4 mg/kg en 60–90 s); se registra la dosis total. Intubación orotraqueal.
5. **Mantenimiento.** Isoflurano en oxígeno con FE'Iso inicial de 1,3 %. La profundidad se evalúa cada 5 minutos (reflejo palpebral, posición del globo ocular, tono mandibular, respuesta de FC y PAM a la estimulación) y la FE'Iso se ajusta en pasos de 0,1–0,2 % con criterios fijos: se reduce si el plano es profundo y se aumenta si es superficial. Ventilación mecánica para EtCO₂ 35–45 mmHg. Ringer lactato 5 mL/kg/h. Soporte térmico activo para temperatura ≥ 37 °C.
6. **Analgesia de rescate.** Si la FC o la PAM suben > 20 % sobre el valor previo ante el estímulo quirúrgico con un plano anestésico adecuado: fentanilo 2 µg/kg IV. Se registran la hora y la dosis.
7. **Analgesia locorregional.** Permitida si forma parte del protocolo habitual del procedimiento; se registra el bloqueo, el fármaco y la hora (es una covariable del consumo de isoflurano).

### 7.2 Preparación de la dexmedetomidina

- Dexmedetomidina 0,5 mg/mL diluida en NaCl 0,9 % a la concentración que propone el simulador para el peso del perro, en una jeringa de 50 mL (o la indicada en el simulador).
- **Doble comprobación:** una persona prepara la dilución y otra comprueba el cálculo, el volumen extraído del vial y la etiqueta (fármaco, concentración en µg/mL, hora, iniciales). Ambas firman en el CRF.
- Línea exclusiva de bajo volumen muerto conectada lo más cerca posible del catéter, purgada antes de empezar. Bomba de jeringa con resolución de 0,1 mL/h; modelo y número de serie en el CRF.

### 7.3 Programación y uso del simulador (v1.2.1)

1. Se abre el sobre de aleatorización tras la inducción.
2. En el simulador se comprueba que el modelo farmacocinético es «Perro anestesiado (corregido)», el que aparece por defecto, y se introducen: peso, concentración objetivo asignada, **duración programada = duración prevista del procedimiento + 30 min** (máximo 180), inducción con carga de 10 minutos, concentración de la dilución, volumen de la jeringa y límites de la bomba. Premedicación con dexmedetomidina: 0 µg/kg. Velocidad de simulación 1× (tiempo real): cualquier cambio queda registrado. El **código de caso** (TCI-DEX-01-NNN) se anota en el CRF y se usa como nombre del CSV exportado.
3. Si aparecen avisos blandos, el anestesista los revisa y los confirma; quedan registrados en el caso.
4. **Modo manual obligatorio** (“Ajuste automático” desactivado). Un operador dedicado programa la bomba física cada vez que el simulador pide un cambio y lo confirma en la pantalla. Así el simulador calcula la Cp con la velocidad que realmente lleva la bomba, y el registro de tasas refleja cada cambio con su hora exacta.
5. **Inicio de la infusión (t = 0)**: 5 minutos después de la inducción, inmediatamente después de la muestra basal M0. El reloj del simulador es la referencia horaria de todo el estudio.
6. **El objetivo no se cambia** durante el estudio salvo por seguridad (sección 10). Cualquier cambio o pausa se hace desde el simulador para que la Cp predicha siga siendo correcta, y queda registrado.
7. **Registro clínico en el CRF** (hoja B6) cada 5 minutos y en cada muestra: hora del reloj del simulador, FC, PAS/PAD/PAM, SpO₂, EtCO₂, temperatura, FE'Iso, ritmo/bloqueo AV, Cp que muestra la pantalla, tasa de la bomba y observaciones.
8. **Muestras de sangre**: a mitad de cada extracción se anota en el CRF (hoja B7) la hora exacta del reloj del simulador (hh:mm:ss) y el código de muestra (sección 8). La Cp predicha de cada muestra se calcula después a partir del CSV (sección 11.4).
9. **Fin de la infusión** al terminar el procedimiento (cierre de piel): se detiene la bomba física y, en el mismo momento, se pulsa “Finalizar infusión” y se confirma. El simulador pasa a POST-INFUSIÓN: la bomba queda a 0 y la Cp predicha se sigue calculando durante 120 minutos para las muestras MF, P15 y P60. Si el procedimiento dura más de lo previsto, la infusión puede continuar a criterio clínico hasta un máximo de 180 minutos.
10. Tras la muestra P60 se pulsa “Cerrar caso” y “Exportar CSV”; el archivo se renombra con el código de caso (p. ej. TCI-DEX-01-001.csv) y se guarda según la sección 12. El registro del caso solo está en memoria hasta exportarlo: no se cierra ni recarga el programa antes de exportar.

### 7.4 Recuperación

Extubación cuando haya reflejo deglutorio. Monitorización de FC, FR, temperatura y sedación cada 15 minutos hasta la última muestra y después según el protocolo del centro. Hasta la muestra de +60 minutos no se administra ningún agonista α2. El atipamezol solo se usa como rescate (sección 10); si se administra, las muestras posteriores se excluyen del análisis farmacocinético.

### 7.5 Cronograma del perro

| Momento | Acción |
| --- | --- |
| Día de la anestesia, antes de la premedicación | Valoración, peso, analítica, ECG, consentimiento |
| −30 min | Metadona 0,2 mg/kg IM |
| −10 min | Catéteres; inducción con propofol; isoflurano |
| −5 a 0 min | Apertura del sobre; preparación y doble comprobación de la dilución; programación del simulador |
| 0 min | Muestra M0; inicio de la infusión TCI (carga de 10 min) |
| Cada 5 min | Registro clínico en el CRF (hoja B6) |
| 10, 15, 20, 30 y 60 min | Muestras M10, M15, M20, M30 y M60 |
| Fin de infusión o 120 min | Muestra MF (si la infusión sigue a los 120 min, se toma a los 120 y otra al detenerla) |
| +15 y +60 min tras detener | Muestras P15 y P60 |
| +24 h | Llamada o revisión: eventos adversos tardíos |

## 8. Muestras de sangre y análisis de laboratorio

### 8.1 Calendario y volumen

| Código | Momento (reloj del simulador) | Finalidad |
| --- | --- | --- |
| M0 | Justo antes de iniciar la infusión | Blanco: confirma ausencia de dexmedetomidina |
| M10 | 10 min (fin de la carga) | Pico tras la carga |
| M15 | 15 min (5 min tras la carga) | Distribución tras la carga: volumen central en anestesia |
| M20 | 20 min (10 min tras la carga) | Distribución tras la carga: volumen central en anestesia |
| M30 | 30 min | Transición carga–mantenimiento |
| M60 | 60 min | Mantenimiento |
| MF | Fin de la infusión, o 120 min si sigue (con otra muestra al detenerla) | Mantenimiento prolongado |
| P15 | 15 min tras detener la infusión | Caída rápida |
| P60 | 60 min tras detener la infusión | Eliminación |

Se admite una ventana de ±2 minutos alrededor de cada momento; lo que importa es la hora exacta, que se anota en el CRF con el reloj del simulador (hh:mm:ss).

**Volumen.** 2 mL de sangre por muestra más el descarte del espacio muerto (unos 1 mL): máximo 10 muestras × 3 mL = 30 mL por perro. En un perro de 10 kg (volumen sanguíneo aproximado 850 mL) supone menos del 4 %, muy por debajo del 10 % máximo recomendado en 24 horas.

### 8.2 Extracción

1. Del acceso exclusivo para muestras (sección 7.1), nunca de la línea de la infusión ni de la extremidad donde se infunde.
2. Descartar 3 veces el volumen muerto del catéter y la llave (≈ 1 mL) con una jeringa aparte.
3. Extraer 2 mL con una jeringa nueva y **anotar en el CRF la hora del reloj del simulador a mitad de la extracción** (hh:mm:ss), con el código de muestra (M0, M10…).
4. Pasar la sangre al tubo indicado por el laboratorio (habitualmente heparina de litio o EDTA K2), el mismo en todo el estudio. **No usar tubos con gel separador**: los fármacos lipofílicos pueden adsorberse al gel. Invertir el tubo 8–10 veces.
5. Lavar el acceso con 1–2 mL de suero salino heparinizado.
6. Si no se pudo anotar la hora exacta, registrar la mejor estimación y marcarla como desviación.

### 8.3 Procesado y almacenamiento

- Centrifugar en los 30 minutos siguientes a la extracción: 1500 g, 10 minutos, 4 °C. Hasta entonces, el tubo en hielo o a 4 °C.
- Separar el plasma con una pipeta de polipropileno en **dos criotubos de polipropileno** (alícuota A para análisis, alícuota B de reserva), ≥ 0,4 mL cada uno.
- Etiquetar con un **código de muestra aleatorio de 6 dígitos** (lista preimpresa). Solo el investigador principal guarda la tabla que relaciona el código con el perro y el momento.
- Congelar a −80 °C en menos de 60 minutos desde la extracción. Registro diario de la temperatura del congelador. Si solo hay −20 °C, el tiempo máximo hasta el traslado a −80 °C será el que indique la validación de estabilidad del laboratorio.
- Envío de las alícuotas A en hielo seco, con registrador de temperatura y hoja de cadena de custodia. Las alícuotas B se quedan en el centro hasta recibir los resultados.

### 8.4 Requisitos del laboratorio

- Cromatografía líquida con espectrometría de masas en tándem (LC-MS/MS), validada según la guía ICH M10 de validación bioanalítica en plasma canino.
- Límite inferior de cuantificación (LLOQ) ≤ 0,05 ng/mL; intervalo de calibración al menos 0,05–10 ng/mL.
- Exactitud y precisión ±15 % (±20 % en el LLOQ); controles de calidad a tres niveles en cada serie; reanalítica del 10 % de las muestras (*incurred sample reanalysis*).
- Estabilidad demostrada: tres ciclos de congelación–descongelación y almacenamiento a −80 °C durante el tiempo del estudio.
- El laboratorio desconoce el grupo, la Cp predicha y la hora de cada muestra. Entrega los resultados en ng/mL con el informe de cada serie analítica.

El procedimiento operativo detallado está en el Anexo C.

## 9. Variables

### 9.1 Variable principal

**Error de predicción (PE)** de cada muestra: diferencia entre la concentración plasmática medida por LC-MS/MS y la predicha por el simulador en el mismo segundo, expresada como porcentaje de la predicha. A partir de los PE se calculan el MDPE (sesgo) y el MDAPE (imprecisión) de cada perro y de la población (fórmulas en la sección 11).

### 9.2 Variables secundarias

| Variable | Definición | Momento |
| --- | --- | --- |
| Divergencia | Pendiente del APE frente al tiempo, en % por hora | Todas las muestras durante la infusión |
| *Wobble* | Mediana de la desviación absoluta del PE respecto al MDPE de cada perro | Todas las muestras |
| PE tras detener la infusión | PE de P15 y P60 | Tras la infusión |
| Comparación de modelos | MDAPE individual del modelo corregido (el que guía la bomba) frente al publicado, ambos recalculados con el registro de tasas real; reestimación de Cl0 y C50 | Análisis posterior |
| Bradicardia | FC < 50 lpm (aviso) y < 40 lpm (alarma) | Continua; registro cada 5 min |
| Bloqueo AV | De 2.º grado (Mobitz I/II, avanzado) o de 3.º grado en el ECG | Continua |
| Hipotensión | PAM < 60 mmHg (aviso); < 50 mmHg mantenida > 5 min (alarma) | Continua |
| Hipertensión | PAM > 160 mmHg mantenida > 5 min | Continua |
| Hipoxemia | SpO₂ < 90 % | Continua |
| Intervenciones | Atropina, glicopirrolato, efedrina, dopamina, bolos de fluido, atipamezol, pausa o cambio de objetivo: tipo, dosis y hora | Cuando ocurran |
| FE'Iso | Valor cada 5 minutos; media de 30–60 min y de 60 min al final | Cada 5 min |
| Analgesia de rescate | Número de bolos de fentanilo y dosis total (µg/kg) | Durante la anestesia |
| Recuperación | Tiempo hasta extubación y hasta decúbito esternal; puntuación de sedación a los 15, 30 y 60 min | Recuperación |
| Usabilidad | Tiempo de programación del simulador; ajustes de bomba confirmados con > 60 s de retraso; errores de uso; cuestionario SUS (System Usability Scale) del operador | Cada caso |
| Eventos adversos | Cualquier evento hasta 24 h, con gravedad y relación con la dexmedetomidina | Hasta 24 h |

### 9.3 Covariables

Edad, sexo y estado reproductivo, raza, peso, condición corporal, ASA, procedimiento, dosis de propofol, bloqueos locorregionales, duración de la infusión, dosis total de dexmedetomidina (µg/kg), FC y PAM basales, temperatura, sitio de muestreo (arterial o venoso), hematocrito y proteínas totales.

## 10. Seguridad del paciente

La seguridad del perro tiene prioridad sobre el estudio en todo momento. El anestesista responsable puede pausar o detener la infusión, cambiar el objetivo o administrar cualquier tratamiento cuando lo considere necesario. Las pausas y los cambios de objetivo se hacen desde el simulador, que sigue calculando la Cp predicha con la infusión real: las muestras posteriores siguen siendo válidas para el análisis farmacocinético. Solo el atipamezol invalida las muestras siguientes.

### 10.1 Umbrales y actuación

| Situación | Umbral | Actuación |
| --- | --- | --- |
| Bradicardia (aviso) | FC < 50 lpm con PAM ≥ 60 mmHg | Comprobar plano anestésico y reducir FE'Iso si es profundo. Vigilar: es la respuesta esperada a la vasoconstricción α2. No se recomienda anticolinérgico de rutina (riesgo de hipertensión y arritmias). |
| Bradicardia (alarma) | FC < 40 lpm, o < 50 lpm con PAM < 60 mmHg | Pausar la infusión en el simulador. Anticolinérgico a criterio del anestesista. Si no responde o hay inestabilidad: atipamezol. |
| Bloqueo AV | 2.º grado avanzado o 3.º grado | Pausar la infusión. Tratamiento a criterio del anestesista. Reanudar solo si el ritmo se normaliza, con un objetivo menor. |
| Hipotensión (aviso) | PAM < 60 mmHg | Reducir FE'Iso si el plano lo permite; bolo de cristaloide 5 mL/kg en 10 min. |
| Hipotensión (alarma) | PAM < 50 mmHg mantenida > 5 min | Pausar la infusión. Vasopresor o inotrópico (efedrina, dopamina, noradrenalina) a criterio del anestesista. |
| Hipertensión | PAM > 160 mmHg mantenida > 5 min | Descartar plano superficial o dolor (profundizar, rescate con fentanilo). Si persiste sin causa: pausar la infusión. |
| Hipoxemia | SpO₂ < 90 % | Revisar vía aérea, ventilación y circuito; FiO₂ 1,0. |
| Fallo del simulador o del equipo | Bloqueo, cierre o pérdida de alimentación | La bomba mantiene la última velocidad. Anotar la hora. Reiniciar en el equipo de reserva o pasar a velocidad fija a criterio clínico. Registrar como incidente del software. |
| Discrepancia bomba–simulador | Velocidad de la bomba distinta de la indicada en > 5 % | Corregir la bomba de inmediato y anotar hora y valores. |

Antes de cada caso: portátil con batería cargada y conectado a la red, un segundo equipo con el simulador abierto, y el programa de infusión del caso visible en pantalla.

### 10.2 Eventos adversos

- **Evento adverso (EA):** cualquier hecho clínico desfavorable durante el estudio o en las 24 h siguientes, esté o no relacionado con la dexmedetomidina o el simulador.
- **Gravedad:** leve (no requiere tratamiento), moderado (requiere tratamiento y se resuelve), grave (muerte, riesgo vital, reanimación cardiopulmonar, hospitalización prolongada o secuela).
- **Relación:** improbable, posible, probable o segura, según la cronología, la concentración predicha y la respuesta a la pausa.
- **Comunicación:** EA graves al comité de ética en 72 h y al propietario de inmediato. Todos los EA, en el CRF y en el informe final.

### 10.3 Reglas de parada del estudio

1. **Cualquier muerte o EA grave posible o probablemente relacionado** con la dexmedetomidina o el simulador: se suspende el reclutamiento hasta que un revisor independiente y el comité valoren el caso.
2. **Un objetivo concreto:** si 3 de los primeros 10 perros de un grupo necesitan pausar la infusión por causas cardiovasculares, se cierra ese grupo y se comunica al comité.
3. **Software:** cualquier error de cálculo del simulador confirmado (Cp o velocidad distintas de las del motor verificado) suspende el estudio hasta corregirlo, verificarlo y notificar una enmienda.
4. **Farmacocinética (análisis intermedio tras 6 perros con muestras):** si la Cp medida supera a la predicha por el modelo corregido en más de un 50 % en 2 o más perros, se revisa el modelo antes de continuar.

## 11. Análisis estadístico

El plan de análisis se cierra y se fecha antes de recibir el primer resultado del laboratorio. Los scripts de análisis (Python) se preparan y prueban con datos simulados durante la fase piloto.

### 11.1 Rendimiento predictivo (Varvel et al. 1992)

Para la muestra *j* del perro *i*, con concentración medida Cm y predicha Cp:

```latex
\mathrm{PE}_{ij} = \frac{C_{m,ij} - C_{p,ij}}{C_{p,ij}} \times 100 \qquad \mathrm{APE}_{ij} = \left|\mathrm{PE}_{ij}\right|
```

```latex
\mathrm{MDPE}_i = \operatorname{mediana}_j\left(\mathrm{PE}_{ij}\right) \qquad \mathrm{MDAPE}_i = \operatorname{mediana}_j\left(\mathrm{APE}_{ij}\right)
```

```latex
\mathrm{wobble}_i = \operatorname{mediana}_j\left|\mathrm{PE}_{ij} - \mathrm{MDPE}_i\right| \qquad \mathrm{divergencia}_i = \text{pendiente de } \mathrm{APE}_{ij} \text{ frente al tiempo (\% / h)}
```

- **Valores poblacionales:** mediana de los valores individuales, con intervalo de confianza del 95 % por *bootstrap* de perros (2000 remuestreos). Como análisis de sensibilidad, el enfoque de dos etapas de Varvel y un modelo de efectos mixtos sobre log(Cm/Cp).
- **Análisis principal:** muestras durante la infusión (M10, M15, M20, M30, M60, MF). Las muestras P15 y P60 se analizan aparte.
- **Criterio de aceptación:** MDPE poblacional entre −20 % y +20 % y MDAPE poblacional ≤ 30 %. Divergencia y *wobble* se describen sin umbral formal.
- **Concentraciones por debajo del LLOQ** en muestras tras M0: se imputan como LLOQ/2 en el análisis principal y se excluyen en un análisis de sensibilidad. M0 debe estar por debajo del LLOQ; si no lo está, el perro se excluye del análisis farmacocinético.

### 11.2 Análisis secundarios

- **Por objetivo:** MDPE y MDAPE de cada grupo con su IC 95 %; comparación con Kruskal-Wallis (exploratoria).
- **Factores del sesgo:** modelo lineal de efectos mixtos con log(Cm/Cp) como respuesta, el perro como efecto aleatorio y como efectos fijos el objetivo, el tiempo desde el inicio, la FE'Iso, la PAM y el sitio de muestreo.
- **Modelo corregido frente a publicado:** con el registro de tasas real de cada perro se recalcula la Cp con ambos modelos (reconstruir\_cp.py da las dos en cada muestra). Se compara el MDAPE individual con la prueba de rangos con signo de Wilcoxon para datos pareados. Además, Cl0 y C50 (y V1, si los datos lo permiten: la Fase 1 sugiere un volumen central mayor en anestesia) se reestiman con un modelo de efectos mixtos sobre las concentraciones medidas. El resultado define el modelo de la versión siguiente del simulador, que deberá pasar de nuevo la verificación de la Fase 0.
- **Seguridad:** incidencia de cada evento por grupo, con IC 95 % exacto de Clopper-Pearson. Relación entre la Cp predicha (y medida, en la subcohorte) en el momento del evento y su aparición, con regresión logística de efectos mixtos si hay eventos suficientes.
- **FE'Iso y analgesia:** FE'Iso media por grupo (ANOVA o Kruskal-Wallis según la distribución); número de rescates (Poisson o binomial negativa).
- **Usabilidad:** estadística descriptiva de los tiempos, errores y puntuación SUS.

### 11.3 Datos que faltan y desviaciones

No se imputan datos que faltan salvo lo indicado para el LLOQ. Las muestras extraídas fuera de la ventana de ±2 minutos se analizan con su hora real (la Cp predicha se recalcula a ese segundo). Toda desviación del protocolo se registra y se describe en el informe final.

### 11.4 Software

Python 3 (numpy, scipy, statsmodels). La Cp predicha de cada muestra se calcula con el registro de tasas del CSV exportado por el simulador y la hora de la muestra anotada en el CRF, con la herramienta `reconstruir_cp.py` de la verificación (opción `--muestras`). La herramienta da la Cp de los dos modelos: el corregido, por integración numérica de alta precisión, y el publicado, de forma exacta (matriz exponencial). Para M0 (antes del inicio) la Cp predicha es 0.

## 12. Gestión de datos y calidad

**Fuentes de datos.**

1. **CSV del simulador** (uno por perro), exportado al terminar el caso. Contiene la configuración, el programa de infusión, el registro de tasas realmente aplicadas con su hora (incluido el fin de la infusión) y los eventos (avisos confirmados, cambios de objetivo, pausas). Lleva la versión del simulador. Con él y la hora de cada muestra se recalcula la Cp predicha.
2. **CRF en papel** (Anexo B): datos del paciente, preparación de la dilución con doble firma, fármacos, eventos adversos, desviaciones, recuperación, registro clínico cada 5 minutos y hora exacta de cada muestra (reloj del simulador).
3. **Resultados del laboratorio**, por código de muestra aleatorio.

**Anonimización.** Cada perro recibe un código TCI-DEX-01-NNN, que se usa en el CRF y como nombre del CSV. El simulador no guarda ningún dato del paciente ni del propietario. La tabla que relaciona el código con la historia clínica y la que relaciona los códigos de muestra con el perro y el momento las custodia el investigador principal, en un archivo cifrado aparte.

**Archivo y copias.** Los CSV se copian el mismo día a una carpeta cifrada con copia de seguridad semanal en un segundo soporte. Se calcula y anota la huella SHA-256 de cada CSV al guardarlo, para demostrar que no se ha modificado.

**Control de calidad.**

- Revisión del CRF frente al CSV en las 48 horas siguientes a cada caso (horas de muestras, peso, objetivo, dilución).
- Comprobación automática: un script recalcula la Cp predicha anotada en cada cambio de tasa del CSV con el modelo que guiaba la bomba (indicado en el CSV); una diferencia > 1 % se investiga como posible fallo del software.
- La base de datos de análisis se cierra (sin más cambios) antes de unir los resultados del laboratorio.

**Versión del software.** Todo el estudio usa el simulador v1.2.1 con el modelo «Perro anestesiado (corregido)» (huella SHA-256 del instalador y del HTML registrada en el archivo del estudio). Cualquier cambio de versión durante el estudio requiere repetir la verificación de la Fase 0 y comunicarlo al comité.

**Conservación.** Datos y alícuotas de reserva durante 5 años tras la publicación (o lo que exija la normativa local). Los datos anonimizados se pondrán a disposición de otros investigadores con la publicación.

## 13. Consideraciones éticas y conflicto de intereses

### 13.1 Bienestar animal

- **Pacientes clínicos, no animales de experimentación.** Los perros se anestesian por su propio procedimiento, que se haría igual sin el estudio. La dexmedetomidina en infusión es una técnica de uso clínico habitual en anestesia equilibrada; en algunos países su uso en infusión continua es fuera de ficha técnica, lo que se explica al propietario.
- **Carga añadida por el estudio:** un catéter adicional (subcohorte farmacocinética), un máximo de 30 mL de sangre y 60 minutos más de monitorización en la recuperación. Todo se hace bajo anestesia o en la recuperación inmediata, sin molestias apreciables añadidas.
- **Las 3R.** *Reemplazo:* las Fases 0 y 1 ya agotaron lo que se puede comprobar sin animales (verificación del software y datos publicados). *Reducción:* tamaño justificado por precisión (sección 6) y muestras solo en la subcohorte necesaria. *Refinamiento:* objetivos por debajo del límite blando de Cp del simulador (2,5 ng/mL), monitorización continua, umbrales de actuación y reglas de parada definidos (sección 10).
- **Posible beneficio para el paciente:** analgesia y sedación complementarias, menor necesidad de isoflurano y monitorización más estrecha que la habitual.

### 13.2 Consentimiento del propietario

Consentimiento informado por escrito antes de la premedicación (Anexo A), con una casilla aparte para la extracción de muestras. El propietario puede retirarse en cualquier momento sin que cambie la atención de su perro. Costes a cargo del estudio: \[completar: analítica de laboratorio, catéter adicional, etc.\]. Seguro o cobertura de complicaciones: \[completar\].

### 13.3 Conflicto de intereses

El investigador principal es el autor del simulador y tiene un interés comercial en él (posible cesión a una empresa). Para que este interés no influya en los resultados:

1. **Laboratorio ciego:** el laboratorio externo no conoce el grupo, la hora ni la Cp predicha de ninguna muestra.
2. **Plan de análisis previo:** protocolo y plan de análisis registrados antes del primer caso \[completar: registro, p. ej. AVMA Animal Health Studies Database\] y fechados antes de recibir resultados.
3. **Revisor independiente:** un anestesiólogo veterinario sin relación con el software \[completar nombre\] revisa los eventos adversos graves, las desviaciones y el análisis final, y tiene acceso a los datos brutos.
4. **Publicación sin condiciones:** los resultados se publicarán sea cual sea el resultado, con la declaración del conflicto de intereses, y los datos anonimizados se pondrán a disposición pública.
5. **Ninguna empresa** interviene en el diseño, la recogida de datos, el análisis ni la publicación. Si en el futuro hay financiación comercial, se comunicará al comité como enmienda.

## 14. Calendario y recursos

### 14.1 Calendario

| Meses | Actividad |
| --- | --- |
| 1–2 | Aprobación del comité; registro del protocolo; contrato con el laboratorio y confirmación de su método validado; verificación de la Fase 0 sobre v1.2.1 (completada el 9/10/2026; repetirla si cambia la versión); formación del equipo; lista de aleatorización y etiquetas de muestras |
| 3 | Fase piloto (5 perros); revisión de logística y, si hace falta, enmienda |
| 3–10 | Reclutamiento (unos 4 perros al mes); envíos de muestras al laboratorio cada 2–3 meses |
| 5 | Análisis intermedio de seguridad y farmacocinético tras los 6 primeros perros con muestras (regla de parada 4) |
| 11 | Últimas muestras analizadas; cierre de la base de datos |
| 11–12 | Análisis estadístico, informe final al comité y manuscrito |

### 14.2 Personal por caso

- **Anestesista responsable** (investigador principal): anestesia, decisiones clínicas y de seguridad.
- **Operador de bomba y registro:** programa la bomba, confirma los ajustes en el simulador y hace el registro clínico cada 5 minutos.
- **Responsable de muestras** (subcohorte farmacocinética): extracción, anotación de la hora exacta, centrifugación y congelación. Puede ser la misma persona que el operador si el procedimiento lo permite, pero nunca el anestesista.
- **Persona ajena a la anestesia:** prepara la lista de aleatorización y los sobres.
- **Revisor independiente** (sección 13.3).

### 14.3 Equipos y material

| Elemento | Cantidad o requisito |
| --- | --- |
| Portátil con el simulador v1.2.1 + equipo de reserva | 2 |
| Bomba de jeringa con resolución 0,1 mL/h | 1 (+ 1 de reserva) |
| Monitor multiparamétrico: ECG, presión invasiva y oscilométrica, SpO₂, capnografía, analizador de gases, temperatura | 1 |
| Centrífuga refrigerada (1500 g, 4 °C) | 1, en el centro |
| Congelador de −80 °C con registro de temperatura | Acceso continuo |
| Tubos de extracción (sin gel), criotubos de polipropileno, pipetas de polipropileno | ≈ 190 tubos y 380 criotubos |
| Dexmedetomidina 0,5 mg/mL | Según casos |
| Envío en hielo seco con registrador de temperatura | 3–4 envíos |

### 14.4 Presupuesto (a completar)

| Partida | Unidades | Precio unitario | Total |
| --- | --- | --- | --- |
| Análisis LC-MS/MS (18 perros × 9–10 muestras + 10 % de reanalítica) | ≈ 190 | \[completar\] | \[completar\] |
| Puesta a punto del método en plasma canino (si el laboratorio no lo tiene) | 1 | \[completar\] | \[completar\] |
| Material de extracción y procesado | — | \[completar\] | \[completar\] |
| Envíos en hielo seco | 3–4 | \[completar\] | \[completar\] |
| Analítica preanestésica y catéter adicional no cubiertos por el propietario | 30 | \[completar\] | \[completar\] |
| Tasas del comité y del registro | — | \[completar\] | \[completar\] |
| **Total** |  |  | **\[completar\]** |

## 15. Referencias

1. Levionnois OL, Barbarossa A, Bardhi A, Siegenthaler J, Forss Pleyers T, Guidi M, Spadavecchia C, Raillard M. Enantiospecific pharmacokinetics of intravenous dexmedetomidine in beagles. *J Vet Pharmacol Ther.* 2022;45(4):366–372. doi:10.1111/jvp.13063
2. Shafer SL, Gregg KM. Algorithms to rapidly achieve and maintain stable drug concentrations at the site of drug effect with a computer-controlled infusion pump. *J Pharmacokinet Biopharm.* 1992;20(2):147–169.
3. Varvel JR, Donoho DL, Shafer SL. Measuring the predictive performance of computer-controlled infusion pumps. *J Pharmacokinet Biopharm.* 1992;20(1):63–94. doi:10.1007/BF01143186
4. Kuusela E, Raekallio M, Anttila M, Falck I, Mölsä S, Vainio O. Clinical effects and pharmacokinetics of medetomidine and its enantiomers in dogs. *J Vet Pharmacol Ther.* 2000;23(1):15–20.
5. Honkavaara J, Restitutti F, Raekallio M, Salla K, Kuusela E, Ranta-Panula V, Rinne V, Vainio O, Scheinin M. Influence of MK-467, a peripherally acting α2-adrenoceptor antagonist on the disposition of intravenous dexmedetomidine in dogs. *Drug Metab Dispos.* 2012;40(3):445–449. doi:10.1124/dmd.111.042671
6. van Oostrom H, Doornenbal A, Schot A, Stienen PJ, Hellebrekers LJ. Neurophysiological assessment of the sedative and analgesic effects of a constant rate infusion of dexmedetomidine in the dog. *Vet J.* 2011;190(3):338–344. doi:10.1016/j.tvjl.2010.11.025
7. de Sant'Ana Alves L, Arcoverde KN, de Oliveira CVA, Cavalcante JM, Araújo-Silva G, de Paula VV. Pharmacokinetics and pharmacodynamics of intravenous dexmedetomidine (2 µg/kg) in dogs. *Res Vet Sci.* 2024;171:105229. doi:10.1016/j.rvsc.2024.105229
8. Cattai A, Bizzotto R, Cagnardi P, Di Cesare F, Franci P. A pharmacokinetic model optimized by covariates for propofol target-controlled infusion in dogs. *Vet Anaesth Analg.* 2019;46(5):568–578. doi:10.1016/j.vaa.2019.04.009
9. Beths T, Glen JB, Reid J, Monteiro AM, Nolan AM. Evaluation and optimisation of a target-controlled infusion system for administering propofol to dogs as part of a total intravenous anaesthetic technique during dental surgery. *Vet Rec.* 2001;148(7):198–203. doi:10.1136/vr.148.7.198
10. Grint NJ, Burford J, Dugdale AHA. Does pethidine affect the cardiovascular and sedative effects of dexmedetomidine in dogs? *J Small Anim Pract.* 2009;50(2):62–66.
11. Wagner MC, Hecker KG, Pang DSJ. Sedation levels in dogs: a validation study. *BMC Vet Res.* 2017;13:110.
12. International Council for Harmonisation. ICH M10: Bioanalytical method validation and study sample analysis. 2022.
13. Carvajal Sánchez F. Simulador TCI de dexmedetomidina en perros — Informe de verificación del software, Fase 0, v1.2.1. Documento interno, 2026.
14. Carvajal Sánchez F. Simulador TCI de dexmedetomidina en perros — Validación externa preliminar con datos publicados, Fase 1. Documento interno, 2026.
15. Lin GY, Robben JH, Murrell JC, et al. Dexmedetomidine constant rate infusion for 24 hours during and after propofol or isoflurane anaesthesia in dogs. *Vet Anaesth Analg.* 2008;35(2):141–153.
16. Pascoe PJ, Raekallio M, Kuusela E, McKusick B, Granholm M. Changes in the minimum alveolar concentration of isoflurane and some cardiopulmonary measurements during three continuous infusion rates of dexmedetomidine in dogs. *Vet Anaesth Analg.* 2006;33(2):97–103. doi:10.1111/j.1467-2995.2005.00236.x
17. Dent BT, Aarnes TK, Wavreille VA, et al. Pharmacokinetics and pharmacodynamic effects of oral transmucosal and intravenous administration of dexmedetomidine in dogs. *Am J Vet Res.* 2019;80(10):969–975.
18. Pascoe PJ. The cardiopulmonary effects of dexmedetomidine infusions in dogs during isoflurane anesthesia. *Vet Anaesth Analg.* 2015;42(4):360–368. doi:10.1111/vaa.12220
19. Akashi N, Murahata Y, Kishida H, Hikasa Y, Azuma K, Imagawa T. Effects of constant rate infusions of dexmedetomidine, remifentanil and their combination on minimum alveolar concentration of sevoflurane in dogs. *Vet Anaesth Analg.* 2020;47(4):490–498. doi:10.1016/j.vaa.2020.04.002
20. Carvajal Sánchez F. Simulador TCI de dexmedetomidina en perros — Validación externa con datos publicados, Fase 1, versión 4 (modelo corregido para perros anestesiados; curvas completas de Lin 2008 y Pascoe 2006). Documento interno, 2026.

*Comprobar la paginación de las referencias 2, 5, 10 y 11 con el artículo original antes de enviar el protocolo.*

## Anexo A. Hoja de información y consentimiento del propietario

**Estudio TCI-DEX-01 · Evaluación de un programa que ayuda a dosificar la dexmedetomidina durante la anestesia de perros**

Investigador principal: Francisco Carvajal Sánchez, MV · Centro: \[completar\] · Teléfono de contacto: \[completar\] · Aprobado por: \[completar comité y número\]

### ¿Por qué le proponemos participar?

Su perro va a ser anestesiado para \[procedimiento\]. Durante muchas anestesias se usa un medicamento llamado dexmedetomidina, que ayuda a que el perro esté tranquilo, con menos dolor y necesite menos gas anestésico. Hemos desarrollado un programa de ordenador que calcula, minuto a minuto, cuánta dexmedetomidina debe recibir cada perro para mantener una cantidad estable en la sangre. Queremos comprobar si ese cálculo es exacto y si su uso es seguro.

### ¿Qué cambia para mi perro si participa?

- La anestesia y el procedimiento son los mismos que tendría sin el estudio. La única diferencia es que la dexmedetomidina se administra según el programa, a una de tres dosis elegida al azar (todas dentro del rango que se usa habitualmente).
- Su perro estará vigilado de forma continua (electrocardiograma, presión arterial, oxigenación y temperatura) por un veterinario dedicado solo a la anestesia.
- **Si acepta también las muestras de sangre** (opcional): con su perro ya anestesiado se le colocará un segundo catéter y se le sacarán de 9 a 10 muestras pequeñas (en total, unos 30 mL; menos del 4 % de su sangre en un perro de 10 kg). La última se toma una hora después de terminar la anestesia, por lo que el alta podría retrasarse alrededor de una hora.
- Le llamaremos al día siguiente para preguntarle cómo está.

### ¿Qué riesgos tiene?

La dexmedetomidina puede bajar la frecuencia del corazón y cambiar la presión arterial. Son efectos conocidos, que se vigilan de forma continua y que tienen tratamiento; el veterinario puede detener el medicamento en cualquier momento. La dosis se calcula con un modelo ajustado a perros anestesiados; si su perro elimina el medicamento más despacio de lo previsto, la concentración podría ser mayor que la calculada, y por eso la vigilancia es continua. El catéter adicional puede dejar un pequeño hematoma. En algunos países el uso de la dexmedetomidina en infusión continua no figura en su ficha técnica, aunque es una práctica habitual en anestesia veterinaria.

### ¿Qué beneficios tiene?

Su perro recibirá una monitorización más estrecha que la habitual. Es posible que necesite menos gas anestésico. Su participación ayudará a que la anestesia de otros perros sea más precisa.

### Costes

&#91;completar: qué cubre el estudio — por ejemplo, análisis de sangre, catéter adicional — y qué no\]. Usted no recibe pago por participar.

### Sus datos

Su perro se identificará solo con un código. Su nombre y sus datos de contacto no aparecerán en ningún registro del estudio ni en ninguna publicación. Los resultados se publicarán sin datos que permitan identificarles.

### Participación voluntaria

Participar es voluntario. Puede negarse o retirarse en cualquier momento, sin dar explicaciones, y su perro recibirá la misma atención. El veterinario también puede retirar a su perro del estudio si lo considera mejor para su salud.

### Conflicto de intereses

El investigador principal es el autor del programa que se evalúa y podría obtener un beneficio económico de él en el futuro. Por eso, las muestras se analizan en un laboratorio externo que no sabe a qué perro pertenecen, y un veterinario independiente revisa los resultados.

### Consentimiento

Nombre del perro: \_\_\_\_\_\_\_\_\_\_\_\_\_\_ · Código de estudio: TCI-DEX-01-\_\_\_\_

Nombre del propietario o responsable: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

- [ ] He leído esta hoja, he podido hacer preguntas y acepto que mi perro participe en el estudio.
- [ ] Acepto también la extracción de muestras de sangre (opcional).
- [ ] No acepto la extracción de muestras de sangre.

Firma del propietario: …………………… · Fecha (dd/mm/aaaa): ………………

Veterinario que informa: …………………… · Firma: ……………… · Fecha (dd/mm/aaaa): ………………

*Se entrega una copia firmada al propietario.*

## Anexo B. Cuaderno de recogida de datos (CRF)

Un CRF por perro. Todas las horas se anotan con el reloj del simulador (hh:mm:ss desde el inicio de la infusión). El CSV exportado guarda la configuración, el registro de tasas y los eventos; todo lo demás se registra aquí.

### B1. Identificación y selección

| Campo | Valor |
| --- | --- |
| Código de caso | TCI-DEX-01- |
| Fecha |  |
| Raza / sexo y estado reproductivo / edad (años) |  |
| Peso (kg, báscula del día) / condición corporal (/9) |  |
| ASA |  |
| Procedimiento y duración prevista |  |
| ¿Cumple todos los criterios de inclusión y ninguno de exclusión? (sí / no) |  |
| Consentimiento firmado: estudio / muestras (sí / no) |  |
| Subcohorte farmacocinética (sí / no) |  |

### B2. Valoración preanestésica

| Hto (%) | PT (g/dL) | ALT (U/L) | Creatinina (mg/dL) | ECG basal (ritmo) | FC basal | PAM basal | T (°C) |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

### B3. Fármacos no del estudio

| Fármaco | Dosis (mg/kg o µg/kg) | Vía | Hora (reloj de pared) |
| --- | --- | --- | --- |
| Metadona |  | IM |  |
| Propofol (dosis total de inducción) |  | IV |  |
| Bloqueo locorregional (tipo y fármaco) |  |  |  |
| Otros |  |  |  |

### B4. Preparación de la dexmedetomidina

| Campo | Valor |
| --- | --- |
| Concentración final propuesta por el simulador (µg/mL) |  |
| Volumen de dexmedetomidina 0,5 mg/mL extraído (mL) |  |
| Volumen final de la jeringa (mL) |  |
| Lote y caducidad del vial |  |
| Preparado por (iniciales y firma) |  |
| Comprobado por (iniciales y firma) |  |
| Bomba: modelo y n.º de serie |  |
| Versión del simulador y equipo usado |  |

### B5. Aleatorización y programación

| Campo | Valor |
| --- | --- |
| N.º de sobre / objetivo asignado (ng/mL) |  |
| Hora de apertura del sobre |  |
| Hora de inducción (reloj de pared) |  |
| Hora de inicio de la infusión, t = 0 (reloj de pared) |  |
| Modo manual activado (sí / no) |  |
| Modelo del simulador: «Perro anestesiado (corregido)» (sí / no) |  |
| Avisos blandos mostrados y confirmados |  |
| Tiempo de programación del simulador (min) |  |
| Sitio de muestreo (arterial / venoso, vaso) |  |
| Hora de fin de la infusión (reloj del simulador) |  |

### B6. Registro clínico (cada 5 min y en cada muestra)

| Hora (simulador) | FC | PAS | PAD | PAM | SpO₂ | EtCO₂ | T | FE'Iso | Ritmo / bloqueo AV | Cp en pantalla | Tasa bomba (mL/h) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |

### B7. Muestras de sangre

| Muestra | Código aleatorio | Hora (simulador) | Cp predicha (ng/mL) | Hora centrifugación | Hora congelación | Iniciales | Incidencias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 |  |  |  |  |  |  |  |
| M10 |  |  |  |  |  |  |  |
| M15 |  |  |  |  |  |  |  |
| M20 |  |  |  |  |  |  |  |
| M30 |  |  |  |  |  |  |  |
| M60 |  |  |  |  |  |  |  |
| MF / 120 |  |  |  |  |  |  |  |
| MF (al detener, si procede) |  |  |  |  |  |  |  |
| P15 |  |  |  |  |  |  |  |
| P60 |  |  |  |  |  |  |  |

### B8. Intervenciones y rescates

| Hora (simulador) | Motivo | Intervención (fármaco, dosis, pausa, cambio de objetivo) | Respuesta |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### B9. Eventos adversos (hasta 24 h)

| Hora | Descripción | Gravedad (leve / moderado / grave) | Relación con la dexmedetomidina o el simulador | Tratamiento y desenlace |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |

### B10. Recuperación

| Extubación (min tras fin de isoflurano) | Decúbito esternal (min) | Sedación +15 min | Sedación +30 min | Sedación +60 min | Llamada 24 h (sin incidencias / incidencias) |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

### B11. Usabilidad (operador)

| Ajustes de bomba confirmados con > 60 s de retraso (n.º) | Errores de uso (descripción) | Puntuación SUS (0–100) | Comentarios |
| --- | --- | --- | --- |
|  |  |  |  |

### B12. Desviaciones y cierre

| Campo | Valor |
| --- | --- |
| Desviaciones del protocolo (descripción) |  |
| Retirada del estudio (sí / no; motivo) |  |
| CSV exportado (nombre del archivo) |  |
| Huella SHA-256 del CSV |  |
| CRF revisado frente al CSV (fecha, iniciales) |  |
| Firma del investigador principal y fecha |  |

## Anexo C. Procedimiento operativo: extracción, procesado y envío de muestras

**PNT-TCI-DEX-01-M · versión 1.0** · Responsable: persona encargada de las muestras (nunca el anestesista).

### C1. Antes del caso

1. Comprobar que la centrífuga refrigerada está a 4 °C y el congelador a −80 °C (anotar la temperatura en su registro).
2. Preparar una gradilla en hielo con 8 tubos de extracción (sin gel) y 16 criotubos de polipropileno.
3. Pegar en los criotubos las etiquetas preimpresas con el **código aleatorio de 6 dígitos** (A y B por muestra). Anotar en la hoja B7 qué código corresponde a cada momento. Las etiquetas no llevan el código de caso, el grupo ni la hora.
4. Preparar jeringas de 2–3 mL (extracción), de 5 mL (descarte) y suero salino heparinizado para lavados.
5. Abrir el simulador y comprobar que el reloj (“Tiempo”) está visible para quien anota las muestras.

### C2. En cada extracción

1. Comprobar en el reloj del simulador que se está en la ventana (±2 min del momento previsto).
2. Cerrar la llave hacia el lavado. Extraer y apartar unos 1 mL (3 veces el espacio muerto) con la jeringa de descarte.
3. Con una jeringa nueva, extraer 2 mL de forma lenta y continua. **A mitad de la extracción, anotar en B7 la hora del reloj del simulador (hh:mm:ss)** y el código de muestra (M0, M10…).
4. Llenar el tubo sin forzar la sangre por la aguja (evitar hemólisis). Invertir 8–10 veces y ponerlo en hielo.
5. Desechar la sangre de descarte (no se reinyecta). Lavar el acceso con 1–2 mL de salino heparinizado.
6. Anotar también en B7 la Cp que muestra la pantalla en ese momento (control). Si la hora exacta no se pudo anotar, registrar la mejor estimación y marcar la incidencia.

### C3. Procesado (en menos de 30 minutos)

1. Centrifugar 10 minutos a 1500 g y 4 °C, con el contrapeso adecuado.
2. Con pipeta de polipropileno, pasar el plasma sin tocar la capa leucocitaria: al menos 0,4 mL al criotubo A y el resto al B.
3. Si el plasma está hemolizado o lipémico, anotarlo en B7 (no se descarta).
4. Congelar a −80 °C antes de 60 minutos desde la extracción, en la caja del estudio. Anotar las horas de centrifugación y congelación.
5. **Nunca** usar tubos de vidrio ni de poliestireno para el plasma, ni descongelar las muestras antes del envío.

### C4. Almacenamiento

- Caja del estudio identificada solo con “TCI-DEX-01” y el número de caja; mapa de posiciones en el archivo del estudio.
- Registro diario de la temperatura del congelador. Si la temperatura sube por encima de −60 °C, anotar duración y temperatura máxima, avisar al investigador principal y al laboratorio.

### C5. Envío al laboratorio

1. Enviar solo los criotubos A; los B se quedan en el centro hasta tener los resultados validados.
2. Caja aislante con hielo seco suficiente para 72 h y registrador de temperatura en marcha.
3. Hoja de cadena de custodia con la lista de códigos aleatorios (sin código de caso ni horas), número de tubos, fecha, firma de quien envía y espacio para la firma de quien recibe.
4. Enviar de lunes a miércoles para evitar la llegada en fin de semana. Avisar al laboratorio con el número de seguimiento.
5. El laboratorio confirma la recepción, el estado de las muestras (congeladas o no) y la lectura del registrador.

### C6. Resultados

El laboratorio entrega una tabla con código aleatorio, concentración (ng/mL), indicación de < LLOQ y la serie analítica, junto con el informe de calidad de cada serie. El investigador principal une los resultados con la tabla de códigos solo después de cerrar la base de datos clínica (sección 12).
