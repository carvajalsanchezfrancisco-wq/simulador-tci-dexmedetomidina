# Notas sobre los datos extraídos

- **Kuusela et al. 2000** (J Vet Pharmacol Ther 23:15-20). Valores a 15 y 45 min tomados del texto
  (5,5 y 2,7 ng/mL con 10 µg/kg; 14,0 y 6,2 ng/mL con 20 µg/kg); el resto, digitalizado de la Fig. 3
  (escala logarítmica). Duración del bolo no indicada: se asume 30 s.
- **Honkavaara et al. 2012** (Drug Metab Dispos 40:445-449), grupo D (dexmedetomidina sola, 10 µg/kg en 30 s).
  Digitalizado de la Fig. 1. Comprobación: AUC0-90 de los puntos digitalizados = 418 ng·min/mL frente a 421 publicado.
- **de Sant'Ana Alves et al. 2024** (Res Vet Sci 171:105229). La Fig. 1 está en pg/mL. Los parámetros de su
  Tabla 1 son internamente incoherentes (unidades) y no se usan; solo la curva medida. Puntos de 60 y 90 min
  marcados como no fiables: el artículo indica que solo el 60 % de los perros era cuantificable a 60 min
  y el 20 % a 90 min.
- **van Oostrom et al. 2011** (Vet J 190:338-344), texto completo. Bolo de 1, 3 o 5 µg/kg en 1 min seguido de
  infusión de 1, 3 o 5 µg/kg/h; 8 Beagles despiertos (12,9 kg); LC-MS/MS (LLOQ 0,020 ng/mL). Fig. 3 digitalizada
  (5 muestras por dosis). Tiempos reconstruidos del protocolo: la infusión empieza tras 5 registros basales de
  10 min (≈ min 50 de la sesión); a los 30 min (min 80) se inician 5 registros de 10 min y se extrae sangre tras
  cada SEP (≈ 6,5 min después del inicio de cada registro) → ≈ 37, 47, 57, 67 y 77 min desde el inicio de la
  infusión (incertidumbre ± 3 min). Comprobación: medias digitalizadas 0,54 / 1,88 / 4,03 ng/mL frente a
  0,533 / 1,869 / 4,017 publicadas.
- **Lin et al. 2008** (Vet Anaesth Analg 35:141-153). 10 Beagles (13,7 kg; 11,4-17,6), cruzado: 2 h de anestesia
  con isoflurano (ISO) o propofol (PRO) y después despiertos. Bolo de 25 µg/m² + infusión de 25 µg/m²/h durante 24 h.
  Conversión a µg/kg con la superficie corporal canina (0,101·peso^(2/3) m²) para 13,7 kg: **1,055 µg/kg y 1,055 µg/kg/h**
  (los autores indican «≈ 1 µg/kg»). Duración del bolo no indicada: se asume 1 min. LC-MS/MS, LLOQ 0,030 ng/mL; sangre
  venosa (yugular). **Fig. 2 digitalizada** (captura en `figuras/lin2008_fig2_captura.jpg`, 720×1600 px): ejes
  calibrados con sus marcas (x: 0 h = 130,2 px, 20,886 px/h; y: 0 = 913 px, 304 px por ng/mL). Tiempos de muestreo del
  texto: 5, 15, 30, 45, 60, 90 y 120 min (anestesia) y 3, 4, 6, 8, 10, 12, 16, 20, 24, 24,25, 24,5, 24,75, 25 y 26 h.
  ISO (círculos rellenos): centro de cada marcador en la columna de su tiempo. PRO (cuadrados abiertos): por plantilla;
  los que tapa el marcador de ISO (45 min, 3, 8 y 10 h, 24,25 y 24,5 h) se leen por sus bordes visibles y se marcan
  como aproximados (±0,02 ng/mL); los de 24,75 y 25 h no son legibles (no fiables). 26 h: por debajo del LLOQ (no fiable).
  Comprobación con el texto: 5 min ISO 0,64 / PRO 0,37; rango en anestesia ISO 0,40-0,47 / PRO 0,33-0,41; 24 h ISO 0,23
  / PRO 0,28: coinciden. La infusión se detiene a los 1440 min (columna `fin_infusion_min`). Estado: anestesiados solo
  hasta 120 min; después, despiertos. AUC 0-26 h: 8,61 (ISO) y 8,53 (PRO) h·ng/mL; T½ tras la infusión 0,45-0,46 h.
- **Pascoe et al. 2006** (Vet Anaesth Analg 33:97-103). 6 Beagles (13,0-17,7 kg) anestesiados con isoflurano. Carga de
  0,1, 0,5 o 3 µg/kg en 6 min + infusión de 0,1, 0,5 o 3 µg/kg/h durante ≈ 5-7 h. **Suero** (no plasma), GC-MS, límite de
  detección 0,05 ng/mL; sangre arterial. Medias publicadas de la infusión: 0,198 ± 0,081 (0,5) y 1,903 ± 0,621 ng/mL (3);
  con 0,1 µg/kg/h, no detectable (< 0,05). **Fig. 1 digitalizada** (captura en `figuras/pascoe2006_fig1_captura.jpg`):
  ejes calibrados con sus marcas (x: 0 h = 162 px, 50,22 px/h; y: 0 = 780 px, 106,6 px por ng/mL). Cuatro tomas por
  dosis en el tiempo medio de cada una (las barras horizontales son la DE del tiempo): 0,5 µg/kg/h a 1,14, 2,51, 3,93 y
  5,32 h (0,182, 0,197, 0,230, 0,211 ng/mL); 3 µg/kg/h a 1,17, 3,00, 4,84 y 6,86 h (1,520, 2,176, 1,989, 1,994 ng/mL).
  Comprobación: medias 0,205 y 1,92 frente a 0,198 y 1,903 publicadas. Todos los puntos, con el perro anestesiado.
- **Dent et al. 2019** (Am J Vet Res 80:969-975). 6 perros mestizos (hound) de 9 meses y 25,2 kg, despiertos; 5 µg/kg IV
  (rama IV del estudio). UPLC-MS/MS, LLOQ 0,25 ng/mL; venosa (safena). Solo hay parámetros no compartimentales: C0
  extrapolada 18,6 ng/mL, Cl 8,0 mL/min/kg (0,48 L/h/kg), Vss 0,37 L/kg, AUC0-∞ 655 min·ng/mL, Clast 1,4 ng/mL a
  110 ± 15 min (se usa como único punto, tiempo aproximado). La Fig. 1 no es legible en el texto recibido.
- **Akashi et al. 2020** (Vet Anaesth Analg 47:490-498) y **Pascoe 2015** (Vet Anaesth Analg 42:360-368): **no midieron
  concentraciones** (Pascoe 2015 remite a las de Pascoe 2006). No sirven para validar la farmacocinética; sí aportan
  efecto clínico (reducción de la CAM y efectos cardiovasculares) para la Fase 2.
- **Hector et al. 2017 y 2021** y **Pavlica et al. 2022**: pendientes (el archivo «hector2021.pdf» recibido era un artículo
  de literatura en portugués, Cacciari 2005; Pavlica no se ha recibido).

## Columnas del CSV

`fin_infusion_min`: minuto en que se detuvo la infusión (vacío: no se detuvo durante el muestreo). `fiable`: «no» para los
puntos excluidos (por debajo del LLOQ, ilegibles o con menos del 60 % de los perros cuantificables). En `fuente`, «aproximado»
marca los puntos con incertidumbre de lectura o de tiempo (análisis de sensibilidad «sin_puntos_aproximados»).
