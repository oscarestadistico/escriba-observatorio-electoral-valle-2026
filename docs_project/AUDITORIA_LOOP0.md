# AUDITORÍA — LOOP 0

**Observatorio Electoral Valle del Cauca 2026** · Fecha de corte: 2026-08-26

Este documento inventaria las fuentes efectivamente disponibles. No se modificó ninguna fuente. No se construyó el dashboard.

---

## 1. Inventario de insumos (ZIP originales)

| ZIP | Tamaño | Contenido |
|---|---|---|
| `Bases_elecciones_2026.zip` | 13 MB | 6 CSV electorales (Presidencia 1V/2V y Congreso, Cali y Valle) |
| `MMV_Presidente1V_2026.zip` | 16 MB | Escrutinio oficial + preconteo 1V (nacional) + estructuras |
| `MMV_Presidente2V_2026.zip` | 6.2 MB | Escrutinio oficial + preconteo 2V (nacional) + estructuras |
| `SHP_MGN2018_INTGRD_DEPTO.zip` | 12 MB | MGN 2018 departamentos (DANE) |
| `SHP_MGN2018_INTGRD_MPIO__1_.zip` | 64 MB | MGN 2018 municipios (DANE) |
| `2025-12-19_22-30-38...zip` | 108 KB | Perímetro municipal Cali |
| `2025-12-19_22-31-54...zip` | 276 KB | Comunas Cali (22) |
| `2025-12-19_22-37-47...zip` | 568 KB | Corregimientos Cali (15) |
| `2026-08-26_21-04-02...zip` | 12 KB | Puestos de votación Cali (206 puntos) |
| `2026-08-26_21-04-38...zip` | 108 KB | Perímetro municipal Cali (esquema alterno) |

Hashes SHA-256 completos en `metadata/manifest.json` y `project_state.json`.

---

## 2. Bases electorales (CSV) — estructura común

Todos: separador `;`, encoding `utf-8`, 19 columnas idénticas, `VOTOS` como texto con ceros a la izquierda. **Auditoría de votos: 0 no numéricos, 0 negativos, 0 nulos en las seis bases.**

| Archivo | Filas | Municipios | Zonas | Puestos* | Partidos | Candidatos | Filas ZONA=99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Presidenciales PV CALI | 40 437 | 1 | 36 | 30 | 14 | 16 | 1 400 |
| Presidenciales PV VALLE | 86 885 | 42 | 37 | 81 | 12 | 14 | 12 795 |
| Presidenciales SV CALI | 19 128 | 1 | 36 | 30 | 3 | 5 | 655 |
| Presidenciales SV VALLE | 41 675 | 42 | 37 | 81 | 3 | 5 | 6 179 |
| Senado y Cámara CALI | 511 062 | 1 | 36 | 30 | 88 | 126 | 14 930 |
| Senado y Cámara VALLE | 1 011 579 | 42 | 37 | 81 | 88 | 126 | 110 746 |

\* «Puestos» = valores distintos del código `PUESTO`, que es **secuencial por zona**, no un universo global de puestos. El universo real de puestos requiere la llave `ZONA+PUESTO` (ver hallazgo 4).

---

## 3. Cartografía

| Archivo | Rasgos | CRS | Campos clave |
|---|---:|---|---|
| MGN_ANM_DPTOS | 33 | EPSG:4686 | `DPTO_CCDGO`, `DPTO_CNMBR` |
| MGN_ANM_MPIOS | 1 122 | EPSG:4686 | `MPIO_CCDGO`, `MPIO_CDPMP` (DANE 5 díg.), `MPIO_CNMBR` |
| Perímetro Cali | 1 | EPSG:6249 | `id_munici`, `nombre` |
| Comunas Cali | 22 | EPSG:6249 | `comuna`, `nombre` |
| Corregimientos Cali | 15 | EPSG:6249 | `id_correg`, `corregimie`, `acuerdo` |
| Puestos votación Cali | 206 | EPSG:6249 | `codigo`, `nombre`, `barrio`, `comuna` |

- MGN filtra Valle con `DPTO_CCDGO='76'` → **exactamente 42 municipios**, coincide con los 42 `MUN` electorales.
- Cartografía local de Cali en **EPSG:6249** (proyectado, metros); DANE en **EPSG:4686** (grados). Ambos MAGNA-SIRGAS. Para web reproyectar a EPSG:4326 en LOOP 2/4.
- La capa de puestos ya trae `barrio` y `comuna` por punto: es el catálogo base para homologar puestos (206 cartografiados).

---

## 4. Hallazgos críticos

1. **`DEP`/`MUN` NO son códigos DANE.** Electoral `DEP=31` = Valle; DANE = `76`. `MUN=001` = Cali; DANE = `76001`. Se requiere crosswalk de 42 entradas (`MUN` Registraduría → `MPIO_CDPMP`) antes de cualquier cruce espacial con MGN.

2. **`COMUNOMBRE`/`CORNOMBRE` cambian de significado según la corporación.**
   - *Presidencia*: `COMUNOMBRE` = `COMUNA 1..22` (geografía válida de Cali); `CORNOMBRE` = `PRESIDENTE` (solo etiqueta de corporación).
   - *Congreso*: `COMUNOMBRE` = `NACIONAL` / `CIRCUNSCRIPCIÓN …`; `CORNOMBRE` = `SENADO`/`CÁMARA`/`CONSULTAS`. **NO son geografía de Cali.** Confirma la regla del prompt: la comuna/corregimiento de Congreso debe reconstruirse por llave electoral + catálogo de puestos + cartografía, nunca desde estos campos.

3. **El archivo «Senado y Cámara» mezcla tres corporaciones** en `CORNOMBRE`: `SENADO`, `CÁMARA` y `CONSULTAS`. Deben separarse; `CONSULTAS` no es parte del análisis de Senado/Cámara. `CIR` toma valores `{0,1,4,5}` (posibles circunscripciones especiales 4/5): no mezclar circunscripciones.

4. **`PUESTO` y `MESA` no son únicos globalmente** (son secuenciales dentro de zona/puesto). Llaves obligatorias: `ID_PUESTO = DEP+MUN+ZONA+PUESTO`; `ID_MESA = DEP+MUN+ZONA+PUESTO+MESA`. Preservar ceros a la izquierda como texto.

5. **`ZONA` codifica el tipo de territorio en Cali:** `01–22` = comuna, `99` = corregimiento, `>=90` (p. ej. 90) = zona especial con `COMUNOMBRE='NACIONAL'` (exterior/especiales). No asumir `ZONA=COMUNA` fuera del rango 1–22.

6. **Votos especiales:** `CAN` `996` = VOTOS EN BLANCO, `997` = VOTOS NULOS, `998` = VOTOS NO MARCADOS (consistente en las seis bases). Excluir de conteos de «candidatos» y tratar aparte para votos válidos/participación.

7. **Prelación de fuentes pendiente:** las bases CSV son *base procesada*. Los MMV (`_ficheros_MMV_..._ESCRUTINIO.csv` y `PRE..._PRECONTEO.txt`) son *escrutinio oficial* y *preconteo*, de mayor prelación, pero vienen en formato posicional codificado (nacional) que requiere el PDF `Estructuras Basicas` para decodificar. No se mezcló escrutinio con preconteo.

8. **Denominador de participación:** las bases no incluyen potencial electoral / censo por mesa. **Sin denominador verificable no se calculará abstención** hasta confirmar una fuente válida.

9. **Puestos electorales vs cartografiados:** 206 puestos en la capa cartográfica frente al universo `ZONA+PUESTO` de las bases. La homologación (exacto/espacial/no encontrado) se resolverá en LOOP 2 sin forzar coincidencias.

---

## 5. Estado

LOOP 0 cerrado. Fuentes intactas. Metadatos y estado persistidos. Próximo paso: `EJECUTAR LOOP 1` (ETL canónico).
