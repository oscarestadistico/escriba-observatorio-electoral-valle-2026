# Control de calidad — LOOP 7

**Observatorio Electoral Valle del Cauca 2026** · Fecha de corte: 2026-08-26

QA integral sin cambios de metodología. Detalle en `metadata/qa_loop7.json`.

## Resumen
| Área | Resultado |
|---|---|
| Pruebas automatizadas | **25 / 25 PASS** |
| Recursos web probados | **293 / 293 → HTTP 200** (0 errores 404) |
| Errores de runtime JS (headless) | **0** |
| Peso total `docs/` | 14.5 MB · 293 archivos |
| Carga inicial estimada | ~598 KB |

## Datos
- Filas canónicas: 1 710 766. Votos: sin negativos, sin nulos.
- **Duplicados por llave natural (archivo·id_mesa·corporación·circunscripción·partido·candidato): 0.** El solape Cali⊆Valle es entre archivos distintos, no intra-archivo; la agregación usa un único universo (archivos VALLE), por lo que no hay doble conteo.
- Faltantes en llaves (`id_mesa`, `votos`): 0.
- Reconciliación verificada por pruebas: `Σ zonas = municipio`, `Σ municipios = Valle` (exacto); identidades `validos = candidatos + blancos` y `total = validos + nulos + no marcados`.

## Geografía
- MUN Registraduría→DANE: **42 / 42 exactos**.
- Cruce de puestos de Cali: EXACTO 100 · REQUIERE_VALIDACION 102 · NO_ENCONTRADO 15 · ESPACIAL 4.
- Puestos con coordenadas: 206; sin coordenadas (electorales sin cartografía): 15 (no se les fuerza posición).
- Posiciones fuera del recuadro urbano estricto: 7, **todas corregimientos rurales legítimos** (Pance, Pichindé, El Saladito, Golondrinas, Los Andes, La Buitrera) en los Farallones; no son anomalías.
- GeoJSON web con conteos correctos: comunas 22, corregimientos 15, municipios Valle 42, puestos 206.
- **Hallazgo abierto (no es un error de software):** 102 puestos con conflicto entre la comuna del rótulo electoral y la comuna geográfica (`REQUIERE_VALIDACION`). El tablero lo advierte explícitamente y conserva ambas numeraciones; requiere validación con DIVIPOL.

## Web
- Manifest íntegro: 0 archivos faltantes; estructura y puesto presentes para los 42 municipios.
- Todos los enlaces de datos, geografía, scripts y estilos responden 200.
- Filtros en cascada y por segmento verificados en prueba headless (Valle, Presidencia, Congreso, Cali, Explorador) sin errores de consola.
- Responsive: los grids colapsan a una columna ≤860 px; foco visible en controles; `prefers-reduced-motion` respetado.

## Rendimiento
- Ningún archivo web supera ~0.9 MB. Mayores: `puesto/76001.json` (908 KB), `municipio/resultados.json` (869 KB), `zona/competencia.json` (794 KB).
- Carga inicial ~598 KB (HTML/CSS/JS + agregados de arranque + cartografía municipal). El detalle de mesa/puesto se descarga bajo demanda.

## Límites declarados
- No se calcula participación/abstención: la fuente no incluye potencial electoral/censo.
- El cambio 1V→2V es agregado; no es transferencia de votos (falacia ecológica).
- Fuente actual: base procesada; los MMV (escrutinio/preconteo oficiales) quedan disponibles para prelación superior una vez decodificados.
