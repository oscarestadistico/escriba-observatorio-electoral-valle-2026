# Diccionario de datos — Observatorio Electoral Valle 2026

## 1. Variables de las bases originales (Registraduría)

| Variable | Tipo | Descripción y significado por corporación |
|---|---|---|
| `DEP` | texto | Código departamental Registraduría (31=Valle). NO es DANE (76). |
| `DEPNOMBRE` | texto | Nombre del departamento (VALLE). |
| `MUN` | texto | Código municipal Registraduría (001=Cali…). NO es DANE; mapear con crosswalk (42). |
| `MUNNOMBRE` | texto | Nombre del municipio. |
| `ZONA` | texto | Zona electoral. NO clasifica territorio por sí sola (una comuna abarca varias zonas). |
| `PUESTO` | texto | Código de puesto secuencial por zona; no único global. |
| `PUESNOMBRE` | texto | Nombre del puesto de votación (para homologar con cartografía). |
| `MESA` | texto | Número de mesa dentro del puesto; no único global. |
| `COMUCODIGO / COMUNOMBRE` | texto | Presidencia: geografía (COMUNA/CORREGIMIENTO/NACIONAL). Congreso: NACIONAL/circunscripción (NO geografía de Cali). |
| `CORCODIGO / CORNOMBRE` | texto | Presidencia: etiqueta 'PRESIDENTE'. Congreso: SENADO/CÁMARA/CONSULTAS (tipo de corporación, no geografía). |
| `CIR` | texto | Circunscripción (0/1 ordinaria; 4/5 especiales). No mezclar circunscripciones. |
| `PAR / PARNOMBRE` | texto | Código y nombre de partido/lista. |
| `CAN / CANNOMBRE` | texto | Código y nombre de candidato. 996=blanco, 997=nulos, 998=no marcados. |
| `CANCEDULA` | texto | Cédula del candidato (puede venir vacía). |
| `VOTOS` | entero | Votos; 100% numérico, sin negativos ni nulos. Texto con ceros en origen. |

## 2. Esquema canónico (`data_processed/canonico.parquet`)

| Campo | Contenido |
|---|---|
| `eleccion` | Presidencia 2026 / Congreso 2026 |
| `corporacion` | Presidencia / Senado / Cámara / Consultas (derivada de CORNOMBRE en Congreso) |
| `vuelta` | 1V / 2V (Presidencia); NA (Congreso) |
| `ambito` | Cali / Valle (Valle = universo con 42 municipios, recomendado para agregar) |
| `departamento_codigo / departamento` | 31 / VALLE (Registraduría; DANE en crosswalk) |
| `municipio_codigo / municipio` | código Registraduría / nombre |
| `zona` | zona electoral (no clasificador territorial por sí sola) |
| `territorio_fuente_tipo` | comuna / corregimiento / nacional_especial / otro (Pres.); no_geografico_congreso |
| `puesto / puesto_nombre` | código secuencial por zona / nombre del sitio |
| `mesa` | número de mesa dentro del puesto |
| `id_puesto / id_mesa` | DEP+MUN+ZONA+PUESTO (+MESA): llaves únicas globales |
| `circunscripcion` | CIR (0/1 ordinaria; 4/5 especiales) |
| `partido_codigo / partido` | código / nombre de partido o lista |
| `candidato_codigo / candidato` | código / nombre; 996 blanco, 997 nulos, 998 no marcados |
| `es_voto_especial` | True si 996/997/998 |
| `votos` | entero ≥ 0 |
| `comuna_fuente / corregimiento_fuente` | etiqueta territorial de la fuente (Presidencia) |
| `*_orig` | columnas originales preservadas (comucodigo/comunombre/corcodigo/cornombre) |
| `archivo_fuente / tipo_fuente` | procedencia / tipo (base_procesada_csv) |

## 3. Indicadores derivados (tablas `competencia_*`)

Definiciones formales en `METODOLOGIA.md`. Campos: `ganador`, `votos_ganador`, `segundo`, `votos_segundo`, `cand_total`, `validos`, `total_marcas`, `blancos`, `nulos`, `no_marcados`, `margen_abs`, `margen_pp`, `top1_pp`, `blanco_pp`, `hhi` (0–1), `nep` (=1/hhi), `fragmentacion` (=1−hhi), `n_unidades`.

## 4. Crosswalks y auditorías

- `metadata/mun_dane_crosswalk.csv`: MUN Registraduría → código DANE (42).
- `metadata/crosswalk_puestos_cali.csv`: puesto electoral ↔ cartografía (territorio, barrio, lat/lon, `metodo_cruce`, `estado_cruce`, comuna electoral y cartográfica).
- `metadata/auditoria_cruces.csv`: conteo por `estado_cruce`.
- `metadata/diccionario_variables.csv`: versión tabular de la sección 1.