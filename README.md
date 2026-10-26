# Simulador TCI de dexmedetomidina en perros

Simulador de infusión controlada por objetivo (TCI) de dexmedetomidina para caninos. El repositorio incluye también:

- el protocolo de validación TCI-DEX-01;
- la verificación del código (Fase 0);
- la validación farmacocinética (Fase 1);
- el peritaje del código.

**Autor:** Francisco Carvajal Sánchez, estudiante de Medicina Veterinaria, Universidad Privada Antenor Orrego (UPAO), Trujillo, Perú.

**Para usar el simulador:** abra `simulador/simulador_tci_dexmedetomidina.html` en Chrome, Edge o Firefox. Funciona sin conexión.

## Estado actual (26/10/2026)

- **Versión vigente:** v1.3.0. El código fuente y el HTML del repositorio son idénticos byte a byte a la v1.3.0 entregada (ver «Cómo se recuperó»).
- **Reunión con CONICET** (Dra. Litterio y Dr. Lorenzutti): martes 27/10/2026, 18:30 h Córdoba (16:30 h Perú), por Google Meet. La guía de preparación está en `documentos/`.
- **Paquete enviado a revisión** (correo a Litterio del 13/10/2026): `revision_farmacocinetica.zip` (v1.2.1) y `Protocolo_TCI-DEX-01_v1.2.pdf`. Ambos están en el repositorio.

## Estructura

| Carpeta | Contenido |
|---|---|
| `simulador/` | **v1.3.0**: código fuente (`tci_dexmedetomidina_perros.jsx`) y página lista para usar (`simulador_tci_dexmedetomidina.html`). |
| `compilar/` | Compilación del HTML a partir del jsx, con dependencias fijadas (salida idéntica byte a byte). |
| `documentos/` | Protocolo TCI-DEX-01 v1.2 (PDF y Markdown), dossier para el revisor farmacocinético y guía de la reunión con CONICET. |
| `informes/` | Informe técnico v1.2.1 (español e inglés), Fase 1 v4, verificación Fase 0 v1.2.1, figuras y el LEEME del paquete. |
| `validacion_fase1/` | Datos publicados (99 medias), scripts de la Fase 1, resultados y `modelo_integrado.py` (ajuste conjunto con Levionnois). |
| `verificacion/motor/` | `referencia.py` (implementación independiente de los dos modelos) y `reconstruir_cp.py` (Cp desde el CSV de un caso). |
| `verificacion/peritaje/` | Prueba de estrés (`estres_motor.mjs`) y pruebas de hallazgos H-01 a H-09 (`pruebas_hallazgos.mjs`). |
| `versiones/v1.2.1/` | Simulador v1.2.1 y el zip exacto enviado a revisión (base de la regresión). |
| `reconstruccion/` | Script que convierte el jsx v1.2.1 en v1.3.0 aplicando los nueve pasos de cambio registrados. |

## Uso rápido

**Compilar el HTML** (requiere Node.js 22). La primera vez instala las dependencias fijadas:

```
sh compilar/compilar_html.sh
```

**Pruebas del peritaje** (requieren las dependencias de `compilar/`):

```
node verificacion/peritaje/pruebas_hallazgos.mjs simulador/tci_dexmedetomidina_perros.jsx /tmp/hallazgos
node verificacion/peritaje/estres_motor.mjs simulador/tci_dexmedetomidina_perros.jsx /tmp/estres 4991
```

**Scripts de la Fase 1:** requieren Python 3 con numpy, scipy, matplotlib y reportlab. Se ejecutan desde `validacion_fase1/`.

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

**Huellas SHA-256 de v1.3.0**

| Archivo | SHA-256 |
|---|---|
| `simulador/tci_dexmedetomidina_perros.jsx` | `a1e4a98914e06f5800561889dad599b83af843e16354552f6c12becfd08a1e8a` |
| `simulador/simulador_tci_dexmedetomidina.html` | `191c627f2443f42bc36a61d1b5eb8d26cc3f609613b95779934e37c05c717320` |
| Instalador Windows (no incluido) | `d34b6adbb6e64ebaa1fb744a5ffe5f73a9bcb995a22b08ba9a12969075d325a5` |
| Ejecutable (no incluido) | `5a48d370ae3d08efbe8d571bce8756b8ce5d5d7e3b065d8bad7a2f83753b709d` |

## Cómo se recuperó (26/10/2026)

El contenedor de trabajo se reinició el 24/10/2026 y se perdieron los archivos locales. La recuperación siguió estos pasos:

1. **Paquete v1.2.1:** el zip se extrajo del correo enviado a Litterio el 13/10.
2. **Código v1.3.0:** `reconstruccion/v1.2.1_a_v1.3.0.py` aplicó los nueve pasos de cambio registrados en el historial de la sesión. El jsx resultante tiene la huella original `a1e4a989…`.
3. **Compilación:** se reprodujo la cadena original (esbuild 0.28.2, React 18.3.1, Recharts 2.15.4, fast-equals 5.4.4).
   - Se comprobó primero con la v1.2.1: el HTML generado coincide con el del zip (`40195eca…`).
   - El HTML de la v1.3.0 coincide con su huella original (`191c627f…`).
4. **Comprobaciones tras la recuperación:**
   - pruebas H-01 a H-09: 9/9;
   - prueba de estrés: 4991 casos, 0 fallos;
   - `modelo_integrado.py` reproduce el ajuste conjunto (Cl0 3.49, C50 0.54);
   - el HTML abre en Chromium mostrando la versión 1.3.0, sin errores.

## Pendiente

**Aún no está en el repositorio**

- El instalador y el ejecutable de Windows v1.3.0. El autor los tiene, y conviene subirlos como *Release* de GitHub porque son archivos binarios grandes.
- El código de escritorio para Windows (Go).
- El PDF del peritaje del código.
- El arnés completo de la Fase 0: `verificar_motor.mjs`, `pruebas_ui.mjs`, `pruebas_exe.py` y `generar_informe.py`.

**Documentos por actualizar**

- Protocolo, informes y paquete a la v1.3.0.
- En el protocolo, corregir «Investigador principal … MV».

## Documentos en Claude Docs

- [Dossier de revisión farmacocinética](https://claude.ai/artifact/KnP9wuM6jAVFn4e4LMNzYg)
- [Preparación de la reunión con CONICET](https://claude.ai/artifact/1bFz5TWexKQVz1PpBuhgPQ)
- Protocolo TCI-DEX-01 v1.2: disponible en Claude Docs de la cuenta del autor.

## Referencias clave

- Levionnois OL et al. (2022): farmacocinética de dexmedetomidina en perros (modelo base).
- Alvarez-Jiménez R et al. (2022) y el editorial de Henthorn TK, *Anesthesiology* 2022;136:258: aclaramiento dependiente del estado.
- Shafer SL, Gregg KM (1992): algoritmo TCI.
