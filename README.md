# Simulador TCI de dexmedetomidina en perros

Simulador de infusión controlada por objetivo (TCI) de dexmedetomidina para caninos, con su protocolo de validación (TCI-DEX-01), la verificación del código (Fase 0) y la validación farmacocinética (Fase 1).

**Autor:** Francisco Carvajal Sánchez, estudiante de Medicina Veterinaria, Universidad Privada Antenor Orrego (UPAO), Trujillo, Perú.

> Este repositorio se creó para que el proyecto no se pierda al cerrarse la sesión de trabajo. El contenedor de trabajo se reinició el 24/10/2026 y se perdieron los archivos locales. Lo que aquí figura se rescató del historial de la sesión y de los documentos en Claude Docs. La sección «Lo que falta subir» explica cómo completar el resto.

## Estado actual (26/10/2026)

- **Versión vigente del simulador:** v1.3.0.
- **Reunión con CONICET** (Dra. Litterio y Dr. Lorenzutti): martes 27/10/2026, 18:30 h Córdoba (16:30 h Perú), por Google Meet. La guía de preparación está en `documentos/`.
- **Paquete enviado a revisión** (correo a Litterio del 13/10/2026): `revision_farmacocinetica.zip` (v1.2.1) y `Protocolo_TCI-DEX-01_v1.2.pdf`.

## Modelo y algoritmo

**Modelos farmacocinéticos**

- **Publicado (Levionnois 2022):** bicompartimental. V1 1.03 L/kg, V2 0.41 L/kg, Cl 1.16 L/h/kg, Cl2 1.87 L/h/kg.
- **Ampliado para anestesia (predeterminado):** igual que el anterior, pero con aclaramiento dependiente de la concentración: Cl(C) = 1.16 + (Cl0 − 1.16)·C50/(C50 + C), con Cl0 = 3.15 L/h/kg y C50 = 0.92 ng/mL.
  - Recupera el valor de Levionnois a concentraciones altas.
  - Describe el aclaramiento mayor observado a concentraciones bajas o durante la anestesia.
  - En el código, los identificadores internos siguen siendo `anestesiado` y `publicado`.

**Algoritmo:** TCI plasmático de Shafer–Gregg. La carga se administra en 10 min; el paso de bomba es de 0.1 mL/h y la banda de ajuste es de ±5 %.

**Límites de seguridad**

- **Duros (bloquean):** objetivo ≤ 4 ng/mL; velocidad ≤ 30 µg/kg/h (si hace falta, la carga se alarga); ≤ 12 µg/kg en cualquier ventana de 60 min.
- **Blandos (piden confirmación):** objetivo > 2.5 ng/mL; carga > 3 µg/kg; velocidad > 20 µg/kg/h; > 6 µg/kg en 60 min; subida del objetivo > +1 ng/mL.

## Historial de versiones

| Versión | Cambios principales |
|---|---|
| v1.1.1 | Base de la regresión REG-01. |
| v1.2.1 | Paquete enviado a revisión (13/10). Incluye Fase 0 (944 escenarios contra una referencia independiente) y Fase 1 v4. |
| v1.2.2 | Integra el modelo de Levionnois con la corrección para anestesia. Nombres de modelo: «Publicado» y «Ampliado para anestesia». |
| v1.3.0 | Hace el simulador menos restrictivo por debajo de 4 ng/mL; corrige los defectos D-03 a D-06; añade el peritaje del código (detalles abajo). |

**Novedades de v1.3.0**

- Subir el objetivo durante una carga ya no bloquea: es un aviso blando que recalcula la carga desde la Cp actual.
- El objetivo puede cambiarse durante una pausa y se aplica al reanudar.
- Al reanudar se revisan los límites contra la línea base tomada al pausar:
  - un límite duro nuevo o peor bloquea;
  - un aviso blando nuevo o peor pide un segundo clic.
- Los avisos de seguridad pasan a ser estructurados (nivel, código, valor).
- Defectos corregidos:
  - **D-03:** la pausa en modo manual reescribía el historial.
  - **D-04:** se podía reanudar sin revisar límites, y había una carrera en el mismo segundo.
  - **D-05:** se atribuía mal el límite entre bomba y dosis.
  - **D-06:** los avisos se comparaban por texto exacto y por paso en coma flotante.
- **Verificación**
  - Regresión: REG-02 contra v1.2.1, 1844/1844 idénticos; REG-01 contra v1.1.1, 922/922.
  - Interfaz: 26/26 pruebas en el HTML y en el .exe; Windows 9/9.
  - Peritaje: prueba de estrés de 4991 casos aleatorios sin fallos, y pruebas de hallazgos H-01 a H-09 superadas.

**Huellas SHA-256 de v1.3.0 (para validar una reconstrucción)**

| Archivo | SHA-256 |
|---|---|
| JSX | `a1e4a98914e06f58…` |
| HTML | `191c627f2443f42b…` |
| Instalador Windows | `d34b6adbb6e64ebaa1fb744a5ffe5f73a9bcb995a22b08ba9a12969075d325a5` |
| Ejecutable | `5a48d370ae3d08efbe8d571bce8756b8ce5d5d7e3b065d8bad7a2f83753b709d` |

## Contenido del repositorio

**`documentos/`**

- `protocolo_TCI-DEX-01_v1.2.md`: protocolo de validación. El texto aún menciona v1.2.1; está pendiente actualizarlo a v1.3.0.
- `dossier_revision_farmacocinetica_v1.2.1.md`: dossier para el revisor farmacocinético.
- `preparacion_reunion_CONICET_2026-10-27.md`: preguntas probables y respuestas para la reunión.

**`reconstruccion/v1.2.1_a_v1.3.0.py`**

Aplica, en orden, los nueve pasos de cambio registrados para pasar el código fuente de v1.2.1 a v1.3.0:

```
python3 reconstruccion/v1.2.1_a_v1.3.0.py <jsx v1.2.1> <jsx v1.3.0 de salida>
```

**Otros directorios**

- `validacion_fase1/modelo_integrado.py`: ajuste conjunto con la curva de Levionnois (Cl0 3.49, C50 0.54). Las dosis cambian entre 3 % y 8 %. Necesita `modelo_corregido.py`, que viene en el zip de v1.2.1.
- `verificacion/peritaje/`: `estres_motor.mjs` (prueba de estrés) y `pruebas_hallazgos.mjs` (H-01 a H-09).
  - Requieren Node y esbuild.
  - Ajuste pendiente: la ruta de importación de esbuild apunta a `/home/user/verificacion/node_modules` y debe corregirse.

## Lo que falta subir

**Dónde siguen existiendo los archivos perdidos**

| Archivo | Dónde está |
|---|---|
| `revision_farmacocinetica.zip` (v1.2.1) | Adjunto al correo a Litterio del 13/10/2026 |
| `Protocolo_TCI-DEX-01_v1.2.pdf` | Mismo correo |
| Informe técnico en PDF | Correo del 9/10/2026 |
| HTML e instalador de v1.3.0, PDF del peritaje | Archivos enviados al autor durante la sesión |

El zip contiene el código fuente v1.2.1 (jsx y HTML), los informes en español e inglés, los datos, scripts y resultados de la Fase 1, `fase0/referencia.py`, `reconstruir_cp.py` y los PDF de la Fase 0 y la Fase 1.

**Pasos para completar el repositorio**

1. Descomprimir `revision_farmacocinetica.zip` en el repositorio.
2. Ejecutar `reconstruccion/v1.2.1_a_v1.3.0.py` sobre el jsx de v1.2.1.
3. Comparar el resultado con la huella SHA-256 de v1.3.0, o con el HTML de v1.3.0.
4. Subir el HTML y el instalador de v1.3.0, preferiblemente como *Release* de GitHub, porque son archivos grandes.

**Pendiente y opcional**

- Reconstruir el arnés completo de verificación de la Fase 0 (motor, interfaz, .exe e informe).
- Reconstruir el código de escritorio para Windows.
- Actualizar el protocolo, los informes y el paquete a v1.3.0; corregir «Investigador principal … MV».

## Documentos en Claude Docs

- [Dossier de revisión farmacocinética](https://claude.ai/artifact/KnP9wuM6jAVFn4e4LMNzYg)
- [Preparación de la reunión con CONICET](https://claude.ai/artifact/1bFz5TWexKQVz1PpBuhgPQ)
- Protocolo TCI-DEX-01 v1.2: disponible en Claude Docs de la cuenta del autor.

## Referencias clave

- Levionnois OL et al. (2022): farmacocinética de dexmedetomidina en perros (modelo base).
- Alvarez-Jiménez R et al. (2022) y el editorial de Henthorn TK, *Anesthesiology* 2022;136:258: aclaramiento dependiente del estado.
- Shafer SL, Gregg KM (1992): algoritmo TCI.
