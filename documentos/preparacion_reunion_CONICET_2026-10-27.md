# Preparación de la reunión con IRNASUS UCC-CONICET · 27 de octubre

Oct 24, 2026 · @francisco

## Qué esperar

La reunión es el **martes 27 de octubre a las 16:30 de Perú (18:30 en Córdoba)**, por Meet. El enlace aún no ha llegado.

El Dr. Lorenzutti anunció tres temas:

1. Su valoración del trabajo y de la metodología.
2. Propuestas para aprovechar mejor los datos del ensayo.
3. Con eso, un presupuesto ajustado a lo que usted necesita.

Dijo que no hace falta preparar puntos. Esta guía no es para presentar nada, sino para responder con calma a lo que surja.

**Actitud recomendada**

- Escuche primero y tome notas. Sus críticas son justamente el servicio que va a contratar.
- Reconozca los límites antes de que se los señalen (última sección).
- Si no sabe algo, dígalo: «No lo he evaluado. ¿Cómo lo abordarían ustedes?».
- Al empezar, pregunte si puede grabar la reunión o tomar notas.
- Tenga abiertos el informe técnico, el protocolo y el simulador v1.3.0.

**Si le piden que resuma el proyecto (un minuto)**

> Desarrollé un simulador TCI de dexmedetomidina para perros basado en el modelo de Levionnois et al. (2022). Al compararlo con siete estudios publicados vi que, a dosis clínicas y sobre todo en anestesia, el modelo predice el doble de la concentración medida. Lo amplié con un aclaramiento que aumenta a concentraciones bajas, calibrado con dos estudios en perros anestesiados: el sesgo baja de −50 % a −11 %. Ese ajuste descansa en medias de grupo de solo dos estudios. Por eso necesito un ensayo con muestreo que lo ponga a prueba y permita reestimar el modelo. Busco su ayuda en el diseño del muestreo, el análisis poblacional y la elección del laboratorio.

## Sobre el trabajo y la metodología

Lo más probable es que pregunten por la base de la corrección: medias de grupo, dos estudios y un parámetro que supera el flujo hepático. Debajo de cada pregunta va una respuesta sugerida, con sus cifras.

**1. ¿Por qué medias de grupo y no datos individuales?**

Porque esos estudios no publican datos individuales. El error de Varvel se define por individuo y las medias ocultan la variabilidad entre perros: es la principal limitación y la reconozco. Por eso el ensayo es imprescindible; además, pedí sus datos individuales al Dr. Levionnois.

**2. ¿Es fiable la digitalización de las figuras?**

Calibré los ejes con sus marcas y comparé con las medias publicadas: en Pascoe, 0,205 y 1,92 ng/mL frente a 0,198 y 1,903. El error de lectura es de unos ±0,01 ng/mL (±0,02 en los puntos tapados de Lin).

**3. ¿No es poco calibrar con dos estudios y 20 puntos?**

Sí, y la validación cruzada es limitada. Calibrado solo con Pascoe (Cl0 3,00; C50 0,55), predice Lin con un MDPE de −32 %, frente a −51 % del modelo original. Al revés no sirve: Lin solo tiene concentraciones de unos 0,4 ng/mL y C50 no es identificable. Por eso el ensayo usa tres objetivos (0,5, 1 y 2 ng/mL).

**4. ¿Por qué un aclaramiento que depende de la concentración y no otra explicación?**

Porque el efecto aparece dentro de un mismo estudio, sin diferencias de laboratorio ni de técnica. En van Oostrom (perros despiertos) el aclaramiento aparente pasa de 2,0 a 1,6 y 1,1 L/h/kg con 1, 3 y 5 µg/kg/h; en Pascoe (anestesiados), de 2,5 a 1,6 L/h/kg. Es coherente con un fármaco de extracción alta cuyo aclaramiento depende del flujo hepático, que la propia dexmedetomidina reduce. En humanos, Alvarez-Jiménez et al. (2022) describieron que el aclaramiento baja al aumentar la exposición.

**5. ¿Consideraste que en anestesia cambie el volumen central?**

Sí. Con un V1 2,8 veces mayor, el MDAPE baja de 23,7 % a 7,3 % y se reproduce la subida de la Cp en las primeras 2–3 h. No lo adopté porque obliga a cargas casi tres veces mayores, es inestable con un solo estudio y empeora cuando los perros ya están despiertos. Añadí las muestras de 15 y 20 min para poder estimar V1 en el ensayo.

**6. Cl0 = 3,15 L/h/kg supera el flujo hepático del perro. ¿Es plausible?**

Cl0 es el valor extrapolado a concentración cero. Con concentraciones clínicas (0,5–2 ng/mL) el modelo da 1,8–2,5 L/h/kg, en el límite del flujo hepático (unos 1,8–2,4 L/h/kg en sangre). Podría deberse a una relación sangre/plasma distinta de 1, a eliminación extrahepática o a diferencias de método (Pascoe midió en suero). Es una de las preguntas que quiero hacerles.

**7. ¿El modelo corregido no contradice los datos del propio Levionnois?**

En parte. Tras 10 µg/kg predice un AUC de 6,0 frente a 8,65 h·ng/mL (−31 %), sobre todo por la parte final de la curva. Pero los estudios con la misma dosis y raza discrepan entre sí: a los 120 min Kuusela midió 0,75 ng/mL y el modelo de Levionnois da 1,35. Un ajuste que incluye su curva da Cl0 3,49 y C50 0,54 y cambia las dosis solo un 3–8 %. La forma correcta de integrarlos es un análisis poblacional con sus datos individuales.

**8. ¿Qué pasa con Dent et al. (2019)?**

Midió concentraciones unas cuatro veces mayores que los demás con dosis parecidas (aclaramiento de unos 0,48 L/h/kg) y no he sabido explicarlo. Lo trato como atípico: está informado y fuera de la calibración. Si un perro se comportara así, con 0,5 ng/mL alcanzaría unas cinco veces más; por eso los límites de dosis y la regla de parada.

**9. ¿Por qué mínimos cuadrados y no un modelo de efectos mixtos?**

Con medias de grupo no hay variabilidad individual que estimar. Usé mínimos cuadrados en escala logarítmica, con el mismo peso por grupo. Estoy abierto a un metaanálisis basado en modelos con efectos mixtos: es justo donde su grupo puede aportar más.

**10. ¿Por qué escalado lineal con el peso y no alométrico?**

Seguí el modelo publicado, que escala linealmente. Pero el modelo viene de Beagles de 8–20 kg y el ensayo incluye perros de 10–40 kg, así que el peso debe evaluarse como covariable. El exponente 0,75 es otra pregunta abierta para ellos.

**11. ¿Son comparables los estudios entre sí?**

No del todo: plasma o suero, GC-MS o LC-MS/MS, distintos sitios de muestreo. Lin dosificó por superficie corporal (25 µg/m²), que convertí a unos 1,06 µg/kg con su peso mediano de 13,7 kg. Todo está documentado en las notas de los datos.

**12. ¿Quién verificó el software?**

Yo, con ayuda de herramientas de IA: 944 escenarios frente a una implementación de referencia independiente, con un error numérico máximo del 0,06 %. No es una verificación por otra persona, y acepto que la revisen.

## Sobre cómo aprovechar mejor los datos del ensayo

Lo más probable es que propongan que el ensayo, además de validar el modelo, sirva para construir uno nuevo: un modelo poblacional y PK/PD. Debajo de cada propuesta va la postura sugerida.

**1. «Si reestimás el modelo con estos datos, ya no podés validarlo con ellos.»**

Es cierto, y conviene llevarlo pensado. El análisis principal es la validación prospectiva del modelo actual, definido antes de empezar; la reestimación es secundaria. El modelo nuevo necesitaría datos nuevos o validación interna (bootstrap, VPC, validación cruzada). Pregúnteles cómo lo plantearían.

**2. Diseño óptimo del muestreo.**

Quizá propongan calcular los tiempos de muestreo con diseño óptimo (PopED o PFIM), usando como punto de partida los modelos publicados. Postura: de acuerdo, con un límite de unas 10 muestras (30 mL) por perro, porque son perros de propietario.

**3. Cambiar el objetivo dentro de cada perro.**

Por ejemplo, empezar en 0,5 ng/mL y subir a 2 ng/mL. Así cada perro aporta un rango de concentraciones y el aclaramiento dependiente de la concentración se estima dentro del individuo. Postura: buena idea, y el simulador v1.3.0 ya permite cambiar el objetivo en cualquier momento. El coste es una infusión más larga, que exige anestesias de más duración.

**4. Más perros o muestreo disperso.**

Con 18 perros y 8 muestras se valida, pero puede no bastar para estimar bien la variabilidad entre perros de varios parámetros. Podrían proponer 2–3 muestras en los 12 perros sin muestreo, o más perros. Postura: abierto. Pregunte cuánto suma al presupuesto (cada muestra es un análisis de LC-MS/MS).

**5. Componente PK/PD y ke0.**

Las variables de efecto se registran cada 5 minutos, y eso probablemente es poco para estimar la ke0, que puede ser de pocos minutos. Pregunte si convendría descargar del monitor la FC y la presión arterial minuto a minuto. Otras variables posibles: la reducción de la FE'Iso o un índice de profundidad (BIS). El isoflurano interfiere con todas ellas.

**6. Covariables.**

Ya se registran peso, edad, condición corporal, hematocrito, proteínas, FE'Iso y sitio de muestreo. El gasto cardíaco no se mide, y explicaría el mecanismo. Pregunte si vale la pena medirlo y cómo.

**7. Un estudio experimental en Beagles, antes o en lugar del clínico.**

Permite un muestreo más rico y controlado, en la misma raza que el modelo de Levionnois, y es la mejor opción para estimar la ke0. Postura: lo valoro, pero el estudio clínico sigue siendo necesario para validar el uso real. Pregunte si ellos podrían hacerlo y con qué coste.

**8. Usar el modelo publicado como información previa.**

En un análisis bayesiano o con priors (por ejemplo, $PRIOR en NONMEM), el modelo de Levionnois serviría de punto de partida. Postura: interesante, porque integra formalmente su trabajo. Pregunte qué software usan (NONMEM, Monolix).

**Algo a su favor que conviene mencionar**

El simulador exporta la tasa real de la bomba segundo a segundo, con la hora de cada muestra. La historia de dosificación de cada perro queda exacta, que es justo lo que necesita un análisis de efectos mixtos.

## Sobre presupuesto, laboratorio y colaboración

Para presupuestar necesitarán saber qué parte del trabajo harían ellos, con qué dinero y en qué país se toman y analizan las muestras.

**1. «¿Qué necesitás exactamente de nosotros?»**

Dos etapas, como en el primer correo. La primera, asesoramiento en el diseño antes de empezar: muestreo, número de perros, identificabilidad y variables de efecto. La segunda, el análisis poblacional (y PK/PD) cuando lleguen los datos. Además, que le recomienden un laboratorio. Pregunte qué entregarían en cada etapa: un informe, los modelos, el manuscrito.

**2. «¿Cómo se financia?»**

Responda según la situación real. Si todavía no hay financiación, dígalo: necesita el presupuesto por etapas precisamente para buscarla. No se comprometa a cifras en la reunión.

**3. «¿Y la empresa?»**

Ya lo declaró en el correo y en el protocolo (sección 13.3). Diga con precisión en qué punto está: si hay o no un acuerdo y si la empresa financiaría el ensayo. Si no quiere dar el nombre de la empresa, basta con decir que es un interés preliminar. Recuerde que, según el protocolo, ninguna empresa interviene en el diseño, el análisis ni la publicación.

**4. «¿Dónde se hace el ensayo y quién es el responsable?»**

El protocolo aún tiene en blanco el centro y el comité de ética, y figura usted como investigador principal «MV». Si todavía es estudiante, dígalo usted antes de que lo noten, y nombre al docente o veterinario que supervisaría el ensayo. Defina antes de la reunión quién sería.

**5. «¿Dónde se analizan las muestras?»**

Son unas 190 muestras de plasma, con un límite de cuantificación de 0,05 ng/mL o menos. Si el ensayo se hace en Perú y el laboratorio está en Argentina, las muestras viajan en hielo seco con permisos sanitarios de exportación e importación (SENASA de los dos países). Eso suma tiempo y coste. Pregunte si conocen algún laboratorio en Perú o cuál es el circuito de envío que usan.

**6. «¿Qué plazos tenés?»**

El protocolo prevé 12 meses: 2 de preparación, 8 de reclutamiento y 2 de análisis. Pregunte cuándo podrían empezar y cómo se pagaría (por etapas o al final).

**7. Autoría y datos.**

Si participan en el diseño y el análisis, lo normal es que sean coautores de las publicaciones. Diga que le parece bien. El simulador es suyo; los datos del ensayo son del estudio. Si hace falta, se firma un acuerdo de confidencialidad. Si sale el tema, mencione que también escribió al Dr. Levionnois, autor del modelo base, para pedirle sus datos individuales.

## Preguntas para hacerles

Hacer buenas preguntas muestra que entiende el problema y le da lo que necesita para decidir. Puede marcarlas durante la reunión.

- [ ] ¿Qué cambiarían del muestreo: tiempos, número de muestras, número de perros? ¿Bastan 18 perros para un modelo poblacional?
- [ ] Si validamos el modelo actual y lo reestimamos con los mismos datos, ¿cómo separan las dos cosas?
- [ ] ¿Recomiendan cambiar el objetivo dentro de cada perro (por ejemplo, de 0,5 a 2 ng/mL)?
- [ ] ¿Qué variable de efecto usarían para la ke0 y con qué frecuencia de registro?
- [ ] ¿Conviene un estudio experimental en Beagles antes del clínico? ¿Podrían hacerlo ustedes?
- [ ] ¿Harían antes un metaanálisis con efectos mixtos de los datos publicados?
- [ ] ¿Cómo interpretan que el aclaramiento a concentraciones bajas llegue al flujo hepático o lo supere?
- [ ] ¿Qué laboratorio de LC-MS/MS recomiendan, cuánto cuesta cada muestra y cómo se envían desde Perú?
- [ ] ¿Qué software usan y qué entregarían en cada etapa?
- [ ] ¿Plazos, forma de pago y autoría?
- [ ] ¿Cuál es el siguiente paso después de esta reunión?

## Puntos débiles y cifras clave

Si reconoce usted estos límites antes de que se los señalen, la conversación se centra en cómo resolverlos y no en defenderlos.

1. La ampliación del modelo descansa en medias de grupo de dos estudios (20 puntos), sin datos individuales.
2. Con concentraciones bajas, el aclaramiento del modelo llega al flujo hepático o lo supera.
3. No reproduce la subida de la Cp en las primeras 2–3 h de anestesia, que sugiere un volumen central mayor.
4. Tras el bolo de Levionnois predice un AUC un 31 % menor que el suyo.
5. El ensayo incluirá perros de 10–40 kg, y el modelo viene de Beagles de 8–20 kg con escalado lineal.
6. La verificación del software la hizo el autor, con ayuda de IA.

**Cifras para tener a mano**

| Concepto | Valor |
| --- | --- |
| Modelo de Levionnois (2022) | V1 1,03 L/kg · V2 0,41 L/kg · Cl 1,16 L/h/kg · Cl2 1,87 L/h/kg |
| Ampliación para anestesia | Cl(C) = 1,16 + (Cl0 − 1,16)·C50/(C50 + C) · Cl0 3,15 L/h/kg · C50 0,92 ng/mL |
| Error del modelo original | 93 medias de 7 estudios: MDPE −41 %, MDAPE 46 % · anestesiados: MDPE −50 % |
| Error del modelo ampliado | Anestesiados (calibración, n = 20): MDPE −11 %, MDAPE 23 % · despiertos no usados (n = 63): −3 %, 18 % |
| Mantenimiento en equilibrio | 0,5 / 1 / 2 ng/mL: 1,22 / 2,11 / 3,57 µg/kg/h (original: 0,58 / 1,16 / 2,32) |
| Ensayo | 30 perros, 18 con 9 muestras · objetivos 0,5, 1 y 2 ng/mL · criterio MDPE ±20 %, MDAPE ≤ 30 % · IC 95 % del MDPE ±9 puntos |
| Simulador | v1.3.0 · 944 escenarios verificados · error numérico máximo 0,06 % |
