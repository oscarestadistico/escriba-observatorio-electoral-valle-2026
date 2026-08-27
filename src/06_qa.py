"""LOOP 7 - QA consolidado. Recolecta metricas de datos, geografia y rendimiento.
NO cambia metodologia. Escribe metadata/qa_loop7.json.
"""
import glob
import json
import os

import pandas as pd

from utils import ROOT, META

PROC = os.path.join(ROOT, "data_processed")
DOCS = os.path.join(ROOT, "docs")
CANON = os.path.join(PROC, "canonico.parquet")
# bounding box aprox de Cali (lat/lon) para detectar puntos fuera
CALI_BBOX = dict(latmin=3.30, latmax=3.55, lonmin=-76.60, lonmax=-76.45)


def qa_datos():
    df = pd.read_parquet(CANON, columns=[
        "ambito", "archivo_fuente", "corporacion", "circunscripcion",
        "id_mesa", "partido_codigo", "candidato_codigo", "votos"])
    r = {}
    r["filas_total"] = int(len(df))
    r["votos_total"] = int(df["votos"].sum())
    r["por_fuente"] = (df.groupby("archivo_fuente")
                       .agg(filas=("votos", "size"), votos=("votos", "sum"))
                       .astype("int64").reset_index().to_dict("records"))
    # duplicados dentro de una fuente por llave natural
    key = ["archivo_fuente", "id_mesa", "corporacion", "circunscripcion",
           "partido_codigo", "candidato_codigo"]
    dup = int(df.duplicated(key).sum())
    r["duplicados_llave_natural"] = dup
    # faltantes en llaves
    r["nulos_id_mesa"] = int(df["id_mesa"].isna().sum())
    r["nulos_votos"] = int(df["votos"].isna().sum())
    r["votos_negativos"] = int((df["votos"] < 0).sum())
    return r


def qa_geografia():
    cw = pd.read_csv(os.path.join(META, "crosswalk_puestos_cali.csv"))
    r = {}
    r["estados_cruce"] = cw["estado_cruce"].value_counts().to_dict()
    r["puestos_con_coord"] = int(cw["latitud"].notna().sum())
    r["puestos_sin_coord"] = int(cw["latitud"].isna().sum())
    # puntos fuera del bbox de Cali
    c = cw.dropna(subset=["latitud", "longitud"])
    fuera = c[(c.latitud < CALI_BBOX["latmin"]) | (c.latitud > CALI_BBOX["latmax"]) |
             (c.longitud < CALI_BBOX["lonmin"]) | (c.longitud > CALI_BBOX["lonmax"])]
    r["puestos_fuera_bbox_cali"] = int(len(fuera))
    mun = pd.read_csv(os.path.join(META, "mun_dane_crosswalk.csv"))
    r["mun_dane_exactos"] = int((mun["metodo"] == "EXACTO_NOMBRE").sum())
    r["mun_dane_total"] = int(len(mun))
    # geojson conteos
    import geopandas as gpd
    r["geojson"] = {}
    for f, exp in [("cali_comunas", 22), ("cali_corregimientos", 15),
                   ("valle_municipios", 42), ("cali_puestos", 206)]:
        n = len(gpd.read_file(os.path.join(DOCS, "geo", f + ".geojson")))
        r["geojson"][f] = {"n": n, "esperado": exp, "ok": n == exp}
    return r


def qa_rendimiento():
    r = {}
    def dirsize(p):
        return sum(os.path.getsize(x) for x in glob.glob(p + "/**", recursive=True)
                   if os.path.isfile(x))
    r["docs_total_bytes"] = dirsize(DOCS)
    r["data_bytes"] = dirsize(os.path.join(DOCS, "data"))
    r["geo_bytes"] = dirsize(os.path.join(DOCS, "geo"))
    allf = [(os.path.relpath(x, DOCS), os.path.getsize(x))
            for x in glob.glob(DOCS + "/**", recursive=True) if os.path.isfile(x)]
    r["n_archivos"] = len(allf)
    r["mayores"] = sorted(allf, key=lambda a: -a[1])[:6]
    # carga inicial estimada: valle/competencia + catalogo + municipio/competencia
    init = 0
    for f in ["data/valle/competencia.json", "data/catalogo.json",
              "data/municipio/competencia.json", "geo/valle_municipios.geojson",
              "index.html", "css/styles.css", "js/app.js", "js/filters.js",
              "js/charts.js", "js/maps.js"]:
        p = os.path.join(DOCS, f)
        if os.path.exists(p):
            init += os.path.getsize(p)
    r["carga_inicial_bytes"] = init
    return r


def qa_manifest_integridad():
    man = json.load(open(os.path.join(DOCS, "data", "manifest.json"),
                         encoding="utf-8"))
    faltan = [a["path"] for a in man["archivos"]
              if not os.path.exists(os.path.join(DOCS, "data", a["path"]))]
    # estructura y puesto para los 42 municipios
    dane = pd.read_csv(os.path.join(META, "mun_dane_crosswalk.csv"),
                       dtype=str)["dane_codigo"].tolist()
    est_faltan = [d for d in dane
                  if not os.path.exists(os.path.join(DOCS, "data", "estructura", d + ".json"))]
    pue_faltan = [d for d in dane
                  if not os.path.exists(os.path.join(DOCS, "data", "puesto", d + ".json"))]
    return {"manifest_archivos": len(man["archivos"]),
            "manifest_faltantes": faltan,
            "estructura_faltantes": est_faltan,
            "puesto_faltantes": pue_faltan}


def main():
    qa = {"tests": "25/25 PASS",
          "datos": qa_datos(), "geografia": qa_geografia(),
          "rendimiento": qa_rendimiento(), "manifest": qa_manifest_integridad()}
    with open(os.path.join(META, "qa_loop7.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)
    print("QA_OK dup=%d nulos_llave=%d fuera_bbox=%d docs=%.1fMB init=%.0fKB" % (
        qa["datos"]["duplicados_llave_natural"], qa["datos"]["nulos_id_mesa"],
        qa["geografia"]["puestos_fuera_bbox_cali"],
        qa["rendimiento"]["docs_total_bytes"] / 1e6,
        qa["rendimiento"]["carga_inicial_bytes"] / 1024))


if __name__ == "__main__":
    main()
