# Manual de publicación en GitHub Pages

Guía paso a paso para publicar el tablero. Se explican **dos métodos**: la interfaz web de GitHub (sin instalar nada) y Git desde Windows. Reemplace los textos entre `< >` por sus valores; no incluya los signos `< >`.

> Importante: **no suba la carpeta `data_raw/`** (fuentes originales pesadas). Ya está excluida en `.gitignore`. El sitio se sirve desde la carpeta `docs/`.

---

## Antes de empezar
1. Tener una cuenta en https://github.com
2. Verificar que existe `docs/index.html` y que el tablero funciona localmente:
   ```bash
   python -m http.server 8000 -d docs
   ```
   Abrir http://localhost:8000 y comprobar las pestañas.

---

## MÉTODO A — Interfaz web de GitHub (recomendado si no usa Git)

1. Inicie sesión en GitHub.
2. Botón **New** (o https://github.com/new) para crear un repositorio.
3. **Repository name:** `observatorio-electoral-valle-2026` (o el que prefiera).
4. Visibilidad: **Public** (Pages es gratuito en repos públicos) o según corresponda.
5. Cree el repositorio (sin README, para no generar conflictos).
6. En la página del repo vacío, use **uploading an existing file**.
7. Arrastre el contenido del proyecto **excepto `data_raw/`**. Suba al menos: `docs/`, `src/`, `tests/`, `metadata/`, `docs_project/`, `README.md`, `requirements.txt`, `.gitignore`.
   - Si la interfaz no deja arrastrar carpetas grandes de una vez, súbalas por partes (primero `docs/`, luego el resto).
8. Confirme con **Commit changes**.
9. Verifique que en el repo aparece `docs/index.html`.
10. Vaya a **Settings** (del repositorio).
11. En el menú lateral, **Pages**.
12. En **Source**, elija **Deploy from a branch**.
13. **Branch:** `main`.
14. **Folder:** `/docs`.
15. **Save**.
16. Espere 1–3 minutos al despliegue (recargue la página de Pages).
17. Copie la **URL** que aparece (formato `https://<usuario>.github.io/<repositorio>/`).
18. Ábrala y pruebe el tablero. Si algo no carga, vea *Solución de problemas*.

---

## MÉTODO B — Git desde Windows

Requisitos: instalar Git (https://git-scm.com/download/win). Abrir **Git Bash** en la carpeta del proyecto.

Primera publicación:
```bash
git init
git add .
git commit -m "Versión inicial Observatorio Electoral Valle 2026"
git branch -M main
git remote add origin <URL_REPOSITORIO>
git push -u origin main
```
- `<URL_REPOSITORIO>` es la que da GitHub al crear el repo, por ejemplo `https://github.com/<usuario>/<repositorio>.git`.
- Como `.gitignore` excluye `data_raw/`, esas fuentes no se subirán.

Luego, active Pages igual que en el Método A, pasos 10–18.

Actualizaciones posteriores:
```bash
git add .
git commit -m "Actualización dashboard electoral"
git push
```

---

## Solución de problemas comunes
- **La página sale en blanco / 404 tras habilitar Pages:** espere unos minutos y confirme Branch=`main`, Folder=`/docs`. La URL debe terminar en `/` .
- **Los mapas o gráficos no cargan:** normalmente es una ruta incorrecta. El sitio usa rutas **relativas** (`data/…`, `geo/…`); no mueva `index.html` fuera de `docs/`.
- **`error: remote origin already exists`:** ejecute `git remote set-url origin <URL_REPOSITORIO>`.
- **`failed to push … updates were rejected`:** haga `git pull --rebase origin main` y luego `git push`.
- **Rechazo por archivo >100 MB:** no suba `data_raw/`; verifique que `.gitignore` lo excluye (`git status` no debe listar esos archivos).
- **Autenticación:** GitHub pide un **token personal** en vez de contraseña. Créelo en Settings → Developer settings → Personal access tokens y úselo como contraseña al hacer `push`.
- **Cambios que no aparecen en el sitio:** Pages puede tardar; recargue con caché limpia (Ctrl+F5).

> No se asume ningún usuario de GitHub: use siempre su propio `<usuario>` y `<URL_REPOSITORIO>`.
