# Acta de la reunión con IRNASUS UCC-CONICET

**Fecha:** martes 27 de octubre de 2026, 10:00 h de Córdoba (08:00 h de Perú), por Google Meet.
**Participantes:** Dr. Matías Lorenzutti, Dr. Nicolás Litterio y Francisco Carvajal Sánchez.

## Observaciones de los revisores (notas del autor)

- Limitación: el trabajo usa medias de otros estudios. Es un buen trabajo, pero tiene un error muy grande.
- **Problema principal:** las variables fisiológicas no siempre son constantes.
- **Principal limitante:** el modelo de aclaramiento dependiente de la concentración no necesariamente representa lo que sucedería en realidad, porque el trabajo usa medias.
- **Población de los estudios:** todos usan Beagles, con muy poca variabilidad de peso. Son perros jóvenes y hay más machos que hembras.
- **Volúmenes:** hay que corregir el volumen central o el periférico, porque su error perjudica la estimación del aclaramiento.
- **Validez de las ecuaciones de aclaramiento:** solo sirven cuando se alcanza una estabilidad relativa (estado estacionario). Después de ese punto, sobrestiman el aclaramiento.
- **Propuesta:**
  - una modelización farmacodinámica;
  - un nuevo modelo farmacocinético que incluya variables como el peso y el sexo.

## Interpretación técnica

1. **Medias de grupo.** La curva media de varios perros no es la curva de un perro medio cuando el sistema no es lineal.
   - Una dependencia de la concentración ajustada sobre medias puede deberse en parte a la mezcla de perros distintos y no a un efecto real dentro de cada perro.
   - Solo los datos individuales permiten separar las dos cosas.
2. **Fisiología que cambia en el tiempo.** El aclaramiento de la dexmedetomidina depende del flujo hepático, y por tanto del gasto cardíaco.
   - Ese gasto cambia con la dosis, con el tiempo de infusión, con la profundidad del isoflurano y con la temperatura.
   - El modelo actual hace depender el aclaramiento de la Cp en cada instante, sin memoria. Es una simplificación de ese mecanismo.
3. **Sobrestimación fuera del estado estacionario.**
   - La calibración se hizo con mesetas de infusión (Pascoe: 1–7 h; Lin: 5–120 min).
   - Cuando la Cp baja (al detener la infusión o tras un bolo), el modelo sube el aclaramiento hasta 2,95 L/h/kg con 0,1 ng/mL, frente a 1,16 L/h/kg en Levionnois. Así predice una eliminación demasiado rápida.
   - Esto coincide con el AUC un 31 % menor que predice tras el bolo de Levionnois.
   - En la realidad, el gasto cardíaco tarda en recuperarse, es decir, hay histéresis.
4. **Volúmenes y aclaramiento están acoplados.**
   - Al fijar V1 y V2 de Levionnois y ajustar solo el aclaramiento, cualquier error de volumen se traslada al aclaramiento.
   - En la Fase 1, un V1 2,8 veces mayor bajaba el MDAPE de 23,7 % a 7,3 %.
   - Para estimar volúmenes y aclaramiento a la vez hacen falta muestras tempranas (5–20 min) y de la fase de eliminación tras detener la infusión.
5. **Población.**
   - Con Beagles jóvenes de 8–20 kg, mayoría de machos, no se puede estimar el efecto del peso, la edad ni el sexo.
   - El ensayo previsto incluye perros de 10–40 kg de varias razas: esa extrapolación no está respaldada.

## Consecuencias para el proyecto

- **Modelo ampliado:** debe presentarse como hipótesis, no como modelo validado. El ensayo sirve para ponerlo a prueba frente al publicado.
- **Ambos modelos se pueden evaluar** con los mismos datos, sea cual sea el que dirija la bomba. El simulador registra la tasa real segundo a segundo, y `reconstruir_cp.py` calcula después la Cp de cada modelo.
- **Seguridad del ensayo:** conducirlo con el modelo publicado de Levionnois es la opción prudente. Como sobrestima la Cp, administra dosis menores.
- **Cambio de objetivo del ensayo:** pasa de validar un modelo a construir un modelo poblacional PK/PD. Eso exige:
  - **Población heterogénea y equilibrada:** estratificar por sexo (≈ 50 %) y por peso; registrar la edad y la raza.
  - **Muestreo:** tempranas (5–20 min) para V1, en la meseta, y tras detener la infusión (para el aclaramiento fuera del estado estacionario y para V2).
  - **Varios objetivos dentro de cada perro** (por ejemplo, de 0,5 a 2 ng/mL), para separar el efecto de la concentración de la variabilidad entre perros.
  - **Farmacodinamia:**
    - FC y presión arterial minuto a minuto, descargadas del monitor;
    - si es posible, gasto cardíaco;
    - FE'Iso y temperatura.
    - Así el modelo puede enlazar el efecto hemodinámico con el aclaramiento: un modelo PK/PD con retroalimentación, en el que el gasto cardíaco reduce el aclaramiento.
  - **Tamaño muestral y número de muestras:** definirlos con diseño óptimo (PopED o PFIM) para estimar el peso y el sexo como covariables.

## Pendiente

- [ ] Recibir de los revisores la propuesta formal y el presupuesto del modelo poblacional PK/PD.
- [ ] Confirmar con ellos esta interpretación del punto sobre el estado estacionario.
- [ ] Reescribir el protocolo (TCI-DEX-01 v2.0) con el nuevo objetivo, la población estratificada, el muestreo y las variables farmacodinámicas.
- [ ] Decidir qué modelo conduce la bomba durante el ensayo.
- [ ] Insistir en los datos individuales del Dr. Levionnois.
