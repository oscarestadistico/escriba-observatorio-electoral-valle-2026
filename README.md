# Observatorio Electoral Valle del Cauca 2026

Tablero web **estático, reproducible y publicable en GitHub Pages** para el análisis territorial **agregado** de las elecciones de 2026 en el Valle del Cauca y Santiago de Cali: Presidencia (1ª y 2ª vuelta), Senado y Cámara de Representantes.

> Herramienta de análisis agregado del comportamiento electoral. **No** identifica personas ni infiere el voto individual. Las diferencias territoriales no permiten inferir comportamiento individual ni causalidad sin análisis adicional.

## Objetivos
- Integrar y visualizar resultados oficiales por territorio: departamento, municipio, zona, puesto y mesa; y en Cali por comuna y corregimiento.
- Ofrecer indicadores comparables y trazables (resultados, márgenes, concentración, fragmentación, cambio agregado entre vueltas).
- Mantener la trazabilidad de cada cifra hasta su fuente, sin inventar datos ni equivalencias territoriales.

## Fuentes
- **Resultados:** Registraduría Nacional (bases procesadas CSV, separador `;`, UTF-8). Presidencia 1V/2V y Congreso (Senado, Cámara, Consultas) para Cali y Valle.
- **Escrutinio/preconteo oficial (MMV):** disponibles para prelación superior una vez decodificado su formato posicional.
- **Cartografía:** perímetro, comunas (22), corregimientos (15) y puestos (206) de Cali; Marco Geoestadístico Nacional MGN 2018 (DANE) para municipios del Valle.

## Metodología (resumen)
- Universo único de agregación: archivos VALLE (incluyen Cali a nivel de mesa); los archivos Cali son subconjunto idéntico y no se suman.
- Votos: `total = candidatos + blanco + nulos + no marcados`; `válidos = candidatos + blanco`; porcentajes sobre válidos.
- Indicadores: margen 1º–2º, HHI, número efectivo de listas (NEP), fragmentación; cambio agregado 1V→2V (no transferencia de votos).
- **No** se calcula participación/abstención (la fuente no trae denominador de censo).
- Geografía de Cali: el territorio usa la etiqueta electoral (reconciliable con resultados); coordenadas/barrio provienen de la cartografía. Existe un conflicto documentado de numeración de comuna (102 puestos, `REQUIERE_VALIDACION`).
- Detalle en [`docs_project/METODOLOGIA.md`](docs_project/METODOLOGIA.md) y [`docs_project/CONTROL_CALIDAD.md`](docs_project/CONTROL_CALIDAD.md).

## Estructura del repositorio
```
analisis-electoral-valle/
├── README.md, LICENSE, .gitignore, requirements.txt, CLAUDE.md, project_state.json
├── config/
├── data_raw/              (NO se versiona; fuentes originales)
├── data_processed/        (canonico.parquet + indicadores/)
├── metadata/              (manifest, fuentes, diccionario, crosswalks, auditorías, QA)
├── src/                   (01_auditoria … 06_qa, indicadores, utils)
├── tests/                 (integridad, totales, geografía, homologación, reconciliación, web_mart)
├── docs/                  (SITIO WEB: index.html, css, js, data/, geo/)  ← GitHub Pages
└── docs_project/          (METODOLOGIA, DICCIONARIO, CONTROL_CALIDAD, MANUAL_USUARIO, MANUAL_GITHUB)
```

## Cómo reproducirlo
Requisitos: Python 3.10+ y `pip install -r requirements.txt`.
Coloque los ZIP originales en `data_raw/` y ejecute en orden:
```bash
python src/01_auditoria.py      # inventario y metadatos
python src/02_etl_electoral.py  # base canónica (data_processed/canonico.parquet)
python src/03_geografia.py      # homologación y GeoJSON web
python src/04_indicadores.py    # marts de indicadores
python src/05_web_mart.py       # data mart web (docs/data/)
python src/06_qa.py             # control de calidad
```
Ver el tablero localmente:
```bash
python -m http.server 8000 -d docs
# abrir http://localhost:8000
```
Pruebas: `python tests/test_integridad.py` (y demás en `tests/`).

## Cómo actualizarlo con nuevas bases
Ver **LOOP 10** del contrato y [`docs_project/MANUAL_GITHUB.md`](docs_project/MANUAL_GITHUB.md). En síntesis: recalcular hashes, reprocesar solo las fuentes que cambiaron, correr pruebas, regenerar `docs/data/` y actualizar la fecha de corte.

## Publicación
Ver [`docs_project/MANUAL_GITHUB.md`](docs_project/MANUAL_GITHUB.md): GitHub Pages sirviendo la carpeta `/docs` de la rama `main`.

## Licencia
Ver `LICENSE`. Los datos originales pertenecen a sus fuentes (Registraduría Nacional, DANE, Alcaldía de Cali).
