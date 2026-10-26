Independent pharmacokinetic review · TCI simulator for dexmedetomidine in dogs, version 1.2.1
Author: Francisco Carvajal Sánchez · 12 October 2026

The main document is the technical report: Technical_report_TCI_dexmedetomidine_v1.2.1.pdf.
To try the simulator, open simulador/simulador_tci_dexmedetomidina.html in Chrome, Edge or Firefox
(it runs offline; the interface is in Spanish).

The supporting reports, data notes and code comments are in Spanish:
  Informe_tecnico_TCI_dexmedetomidina_v1.2.1.pdf  Spanish version of the technical report
  figures_en/                                     The three report figures (PNG, English); figuras/ in Spanish
  Informe_Fase1_validacion_externa_v4.pdf         Full external validation report (corrected model: section 7;
                                                  time course and central volume: section 8)
  Informe_verificacion_Fase0_v1.2.1.pdf           Software verification against an independent reference
                                                  implementation, including regression against v1.2.0
  fase1/datos/concentraciones_publicadas.csv      The 99 published mean concentrations (93 used) with their source
                                                  (estudio = study, grupo = group, t_min = time, c_ngml = concentration,
                                                  estado = despiertos/anestesiados (conscious/anaesthetised),
                                                  fiable = si/no (used/excluded), fuente = source)
  fase1/datos/notas_datos.md                      Extraction decisions and digitisation calibration
  fase1/datos/figuras/                            Lin 2008 Fig. 2 and Pascoe 2006 Fig. 1 as used for digitisation
  fase1/modelo_corregido.py                       Calibration and evaluation of the corrected model (~15 s)
  fase1/modelo_volumen.py                         Exploratory fit with a larger central/peripheral volume (~1 min)
  fase1/analisis.py                               Validation of the published model
  fase1/modelo_experimental.py                    Three-parameter model fitted to all studies (not adopted)
  fase1/resultados/*.json                         Numerical results
  fase0/referencia.py                             Reference implementation of both models
  fase0/reconstruir_cp.py                         Cp predicted by both models from the CSV exported for a case
  simulador/tci_dexmedetomidina_perros.jsx        Simulator source code (models and TCI engine at the top)

Requirements: Python 3 with numpy, scipy, matplotlib and reportlab. Run the scripts from fase1/
(they expect datos/ and resultados/ there).
