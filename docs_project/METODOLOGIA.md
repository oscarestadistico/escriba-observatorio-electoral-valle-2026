# Metodología de indicadores — Observatorio Electoral Valle 2026

## Universo y unidades
- **Universo único de agregación:** archivos *VALLE* (`ambito='Valle'`), que contienen los 42 municipios —incluida Cali— a nivel de mesa. Los archivos *CALI* son un subconjunto idéntico y **no se suman** para evitar doble conteo.
- **Unidad de competencia:** candidato en Presidencia; partido/lista en Senado, Cámara y Consultas.
- **Segmentación obligatoria:** todo indicador se calcula por `elección · corporación · vuelta · circunscripción`. No se mezclan circunscripciones (Congreso: CIR 0/1 ordinaria, 4/5 especiales indígena/afro) ni escrutinio con preconteo.

## Taxonomía de votos
- `total_marcas` = candidatos + blanco + nulos + no marcados.
- `votos_candidatos` = marcas por candidatos/listas (excluye 996/997/998).
- `blancos` (996), `nulos` (997), `no_marcados` (998), tomados por circunscripción.
- `validos` = `votos_candidatos` + `blancos`.
- No existe fila TOTAL en la fuente; la suma de filas reproduce el total (verificado).

## Fórmulas
- `pct_validos(unidad)` = votos_unidad / validos × 100.
- `margen_abs` = votos(1º) − votos(2º); `margen_pp` = margen_abs / validos × 100.
- `HHI` = Σ sᵢ², con sᵢ = votos_unidadᵢ / votos_candidatos (rango 0–1).
- `NEP` (número efectivo de partidos/candidatos) = 1 / HHI.
- `fragmentacion` (Rae) = 1 − HHI.
- `blanco_pp` = blancos / validos × 100.

## Participación / abstención
**No se calcula.** Las bases no incluyen potencial electoral/censo por mesa; sin denominador verificable, reportar participación o abstención sería inventar. Queda pendiente hasta incorporar una fuente de censo válida.

## Cambio 1V → 2V (Presidencia)
Se reporta como **cambio agregado entre resultados territoriales** (`delta_abs`, `delta_pp`), nunca como “transferencia de votos”. La diferencia agregada por territorio no permite inferir el comportamiento individual de electores (falacia ecológica). Solo son comparables las unidades presentes en ambas vueltas (Cepeda, De La Espriella, voto en blanco).

## Geografía de Cali
El territorio (comuna/corregimiento) usa la **etiqueta electoral** (COMUNOMBRE), que es la que reconcilia con los resultados oficiales. Coordenadas, barrio y geometría provienen de la cartografía. Existe un **conflicto documentado** entre la numeración de comuna electoral y la geográfica (102 puestos, estado `REQUIERE_VALIDACION`): los choropleths por comuna deben marcarse como sujetos a validación DIVIPOL. Las zonas especiales (ZONA≥90: censo especial, exterior) quedan como **no clasificado territorialmente** y se muestran explícitamente, no se ocultan.

## Política de decimales
Cálculo con precisión completa. Redondeo solo en la visualización: votos enteros; porcentajes y puntos porcentuales 1 decimal; indicadores estadísticos (HHI, NEP) hasta 3 decimales.

## Reconciliación (verificada)
`Σ zonas = municipio`, `Σ municipios = Valle` (exacto). En Cali, `comunas + corregimientos + zonas especiales = total municipal`.
