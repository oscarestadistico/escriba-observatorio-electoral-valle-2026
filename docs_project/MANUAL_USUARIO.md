# Manual de usuario — Observatorio Electoral Valle 2026

El tablero se abre en el navegador (GitHub Pages o local). No requiere instalación.

## Pestañas
- **Panorama Valle:** elija corporación, vuelta y circunscripción. Verá KPIs (ganador, %, margen, NEP), el mapa municipal coloreado por ganador, el ranking municipal y la votación departamental.
- **Presidencia:** compare 1ª y 2ª vuelta; barras por candidato, mapa municipal y el **cambio agregado 1V→2V** (no es transferencia de votos).
- **Congreso:** Senado / Cámara / Consultas por circunscripción; votación por lista, concentración (HHI, NEP, fragmentación) y ranking municipal.
- **Cali:** mapa por comuna, ranking territorial y resultado por comuna. Incluye el aviso de validación de comunas.
- **Explorador:** cascada Municipio → Zona → Puesto → Mesa para consultar resultados de una mesa concreta.
- **Sobre los datos:** fuente, cobertura, advertencias y límites de interpretación.

## Cómo ejecutarlo localmente
```bash
python -m http.server 8000 -d docs
```
Luego abra `http://localhost:8000`.

## Lectura correcta
Los resultados son **agregados y descriptivos**. Las diferencias territoriales no permiten inferir el comportamiento individual de electores ni causalidad. No se reporta participación/abstención por falta de un denominador de censo en la fuente.
