"""LOOP 2 - Homologacion geografica.
1) Crosswalk MUN Registraduria -> DANE (Valle, 42) por nombre.
2) Crosswalk de puestos de Cali (electoral x cartografia) con cruce EXACTO por
   codigo = DEP+MUN+ZONA+PUESTO, validacion por contencion espacial, y ambas
   numeraciones de comuna conservadas (NO se resuelve el conflicto en silencio).
3) Reconstruccion de comuna/corregimiento para Congreso via ID_PUESTO.
4) GeoJSON web (EPSG:4326) simplificado: perimetro, comunas, corregimientos,
   puestos, municipios del Valle (DANE 76).
Salidas: metadata/mun_dane_crosswalk.csv, metadata/crosswalk_puestos_cali.csv,
metadata/auditoria_cruces.csv, metadata/homologacion_loop2.json,
docs/geo/*.geojson
NO fuerza coincidencias. NO altera fuentes.
"""
import json
import os
import re
import unicodedata

import geopandas as gpd
import pandas as pd

from utils import ROOT, META
from paths_geo import PATHS, CRS_WEB

PROCESSED = os.path.join(ROOT, "data_processed")
GEO_WEB = os.path.join(ROOT, "docs", "geo")
CANON = os.path.join(PROCESSED, "canonico.parquet")
ART = {"EL", "LA", "LOS", "LAS", "DE", "DEL"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9 ]", " ", s).upper()
    return re.sub(r"\s+", " ", s).strip()


def norm_corr(s):
    toks = [t for t in norm(s).replace("CORREGIMIENTO", "").split() if t not in ART]
    return " ".join(toks)


# alias homologados (decision registrada): nombre electoral -> DANE, cuando el
# nombre difiere por denominacion oficial (no por acentos/encoding)
MUN_ALIAS = {
    "BUGA": "GUADALAJARA DE BUGA",
    "CALIMA DARIEN": "CALIMA",
}


# ---------------------------------------------------------------- 1) MUN->DANE
def build_mun_dane(report):
    c = pd.read_parquet(CANON, columns=["ambito", "municipio_codigo", "municipio"])
    ele = (c[c["ambito"] == "Valle"][["municipio_codigo", "municipio"]]
           .drop_duplicates().copy())
    ele["norm"] = ele["municipio"].map(norm)
    ele["norm"] = ele["norm"].map(lambda x: norm(MUN_ALIAS.get(x, x)))

    d = gpd.read_file(PATHS["mpios_dane"], columns=["DPTO_CCDGO", "MPIO_CDPMP",
                                                    "MPIO_CNMBR"],
                      encoding="latin-1")
    d = d[d["DPTO_CCDGO"] == "76"].copy()
    d["norm"] = d["MPIO_CNMBR"].map(norm)
    m = ele.merge(d[["MPIO_CDPMP", "MPIO_CNMBR", "norm"]], on="norm", how="left")
    m["metodo"] = m["MPIO_CDPMP"].notna().map(
        {True: "EXACTO_NOMBRE", False: "NO_ENCONTRADO"})
    m = m.rename(columns={"MPIO_CDPMP": "dane_codigo",
                          "MPIO_CNMBR": "dane_nombre"})
    out = m[["municipio_codigo", "municipio", "dane_codigo", "dane_nombre",
             "metodo"]].sort_values("municipio_codigo")
    out.to_csv(os.path.join(META, "mun_dane_crosswalk.csv"), index=False)
    report["mun_dane"] = dict(
        total=len(out), exactos=int((out.metodo == "EXACTO_NOMBRE").sum()),
        no_encontrados=out.loc[out.metodo == "NO_ENCONTRADO", "municipio"].tolist())
    return out


# ------------------------------------------------------- 2) puestos Cali cruce
def build_puestos_cali(report):
    pu = gpd.read_file(PATHS["puestos"], encoding="utf-8")
    pu["codigo"] = pu["codigo"].astype(str)
    co = gpd.read_file(PATHS["comunas"]).to_crs(pu.crs)
    co["comuna_poly"] = pd.to_numeric(co["comuna"], errors="coerce").astype("Int64")
    cr = gpd.read_file(PATHS["corregimientos"]).to_crs(pu.crs)
    cr["idc"] = pd.to_numeric(cr["id_correg"], errors="coerce").astype("Int64")

    # contencion espacial: comuna y corregimiento del poligono que contiene el punto
    sj_c = gpd.sjoin(pu[["codigo", "geometry"]], co[["comuna_poly", "geometry"]],
                     predicate="within", how="left").drop_duplicates("codigo")
    sj_r = gpd.sjoin(pu[["codigo", "geometry"]], cr[["idc", "geometry"]],
                     predicate="within", how="left").drop_duplicates("codigo")
    puc = pu.copy()
    puc = puc.merge(sj_c[["codigo", "comuna_poly"]], on="codigo", how="left")
    puc = puc.merge(sj_r[["codigo", "idc"]].rename(columns={"idc": "correg_poly"}),
                    on="codigo", how="left")
    puc_wgs = puc.to_crs(CRS_WEB)
    puc["lon"] = puc_wgs.geometry.x
    puc["lat"] = puc_wgs.geometry.y

    # universo electoral de puestos Cali (union de todas las corporaciones)
    c = pd.read_parquet(CANON, columns=["municipio_codigo", "id_puesto", "zona",
                                        "puesto", "puesto_nombre",
                                        "comunombre_orig", "corporacion"])
    cali = c[c["municipio_codigo"] == "001"].copy()
    ele = (cali[["id_puesto", "zona", "puesto", "puesto_nombre",
                 "comunombre_orig"]]
           # el nombre/comuna electoral se toma de Presidencia cuando exista
           .assign(_pri=(cali["corporacion"] == "Presidencia").astype(int)))
    ele = (ele.sort_values("_pri", ascending=False)
           .drop_duplicates("id_puesto").drop(columns="_pri"))
    ele["cod"] = ele["id_puesto"].str.replace("-", "", regex=False)

    # territorio ELECTORAL (autoridad para reconciliar resultados)
    cn = ele["comunombre_orig"].fillna("")
    is_com = cn.str.startswith("COMUNA")
    is_cor = cn.str.startswith("CORREGIMIENTO")
    ele["terr_tipo_ele"] = "especial"
    ele.loc[is_com, "terr_tipo_ele"] = "comuna"
    ele.loc[is_cor, "terr_tipo_ele"] = "corregimiento"
    ele["comuna_ele"] = pd.to_numeric(
        cn.str.extract(r"COMUNA (\d+)")[0], errors="coerce").astype("Int64")

    # mapa corregimiento electoral -> id_correg carto
    carto_corr = {norm_corr(r.corregimie): int(r.id_correg)
                  for _, r in cr.iterrows()}
    ele["correg_ele"] = pd.NA
    ele.loc[is_cor, "correg_ele"] = cn[is_cor].map(
        lambda x: carto_corr.get(norm_corr(x)))
    ele["correg_ele"] = ele["correg_ele"].astype("Int64")

    x = ele.merge(puc[["codigo", "nombre", "barrio", "comuna", "comuna_poly",
                       "correg_poly", "lat", "lon"]],
                  left_on="cod", right_on="codigo", how="outer", indicator=True)

    def eq(a, b):
        return pd.notna(a) and pd.notna(b) and int(a) == int(b)

    def clasificar(r):
        if r["_merge"] == "right_only":
            return "CARTO_SIN_ELECTORAL"
        if r["_merge"] == "left_only":
            return "NO_ENCONTRADO"          # electoral sin cartografia
        if r["terr_tipo_ele"] == "comuna":
            return "EXACTO" if eq(r["comuna_ele"], r["comuna_poly"]) else "REQUIERE_VALIDACION"
        if r["terr_tipo_ele"] == "corregimiento":
            return "EXACTO" if eq(r["correg_ele"], r["correg_poly"]) else "REQUIERE_VALIDACION"
        return "ESPACIAL"                     # especial/nacional con punto

    x["estado_cruce"] = x.apply(clasificar, axis=1)
    x["metodo_cruce"] = x["_merge"].map({
        "both": "ID_EXACTO+ESPACIAL", "left_only": "SOLO_ELECTORAL",
        "right_only": "SOLO_CARTOGRAFIA"})

    # territorio final expuesto = electoral (reconciliable con resultados)
    def terr_nombre(r):
        if r["terr_tipo_ele"] == "comuna" and pd.notna(r["comuna_ele"]):
            return f"Comuna {int(r['comuna_ele'])}"
        if r["terr_tipo_ele"] == "corregimiento":
            return str(r["comunombre_orig"]).title()
        return str(r["comunombre_orig"])

    x["territorio_tipo"] = x["terr_tipo_ele"]
    x["territorio_codigo"] = x.apply(
        lambda r: (f"{int(r['comuna_ele']):02d}" if r["terr_tipo_ele"] == "comuna"
                   and pd.notna(r["comuna_ele"]) else
                   (str(int(r["correg_ele"])) if r["terr_tipo_ele"] ==
                    "corregimiento" and pd.notna(r["correg_ele"]) else "")), axis=1)
    x["territorio_nombre"] = x.apply(terr_nombre, axis=1)
    x["DEP"] = "31"
    x["MUN"] = "001"
    x["ZONA"] = x["zona"]
    x["PUESTO"] = x["puesto"]
    x["ID_PUESTO"] = x["id_puesto"]
    x["PUESNOMBRE"] = x["puesto_nombre"].fillna(x["nombre"])

    cols = ["DEP", "MUN", "ZONA", "PUESTO", "ID_PUESTO", "PUESNOMBRE",
            "territorio_tipo", "territorio_codigo", "territorio_nombre",
            "barrio", "lat", "lon", "metodo_cruce", "estado_cruce",
            "comuna_electoral", "comuna_cartografica", "correg_electoral",
            "correg_cartografico"]
    x["comuna_electoral"] = x["comuna_ele"]
    x["comuna_cartografica"] = x["comuna_poly"]
    x["correg_electoral"] = x["correg_ele"]
    x["correg_cartografico"] = x["correg_poly"]
    x = x.rename(columns={"lat": "latitud", "lon": "longitud"})
    cols = [c.replace("lat", "latitud").replace("lon", "longitud") for c in cols]

    cw = x[["DEP", "MUN", "ZONA", "PUESTO", "ID_PUESTO", "PUESNOMBRE",
            "territorio_tipo", "territorio_codigo", "territorio_nombre",
            "barrio", "latitud", "longitud", "metodo_cruce", "estado_cruce",
            "comuna_electoral", "comuna_cartografica", "correg_electoral",
            "correg_cartografico"]].copy()
    cw.to_csv(os.path.join(META, "crosswalk_puestos_cali.csv"), index=False)

    # auditoria_cruces.csv (resumen por estado)
    aud = (cw.groupby("estado_cruce").size().rename("n").reset_index())
    aud.to_csv(os.path.join(META, "auditoria_cruces.csv"), index=False)

    report["puestos_cali"] = dict(
        universo_electoral=int((x["_merge"] != "right_only").sum()),
        cartografia_puntos=int((x["_merge"] != "left_only").sum()),
        estados=cw["estado_cruce"].value_counts().to_dict(),
        conflicto_comuna_electoral_vs_geografia=int(
            (cw["estado_cruce"] == "REQUIERE_VALIDACION").sum()),
        corregimientos_no_mapeados=int(
            (is_cor & ele["correg_ele"].isna()).sum()),
    )
    return cw


# ------------------------------------------ 3) reconstruccion Congreso via ID
def reconstruir_congreso(cw, report):
    c = pd.read_parquet(CANON, columns=["municipio_codigo", "corporacion",
                                        "id_puesto"])
    cong = c[(c["municipio_codigo"] == "001") &
             (c["corporacion"].isin(["Senado", "Cámara", "Consultas"]))]
    ids_cong = set(cong["id_puesto"].unique())
    ids_cw = set(cw["ID_PUESTO"].dropna().unique())
    cubiertos = ids_cong & ids_cw
    report["congreso_cali"] = dict(
        puestos_congreso=len(ids_cong),
        con_territorio_homologado=len(cubiertos),
        sin_territorio=len(ids_cong - ids_cw))


# -------------------------------------------------- 4) GeoJSON web (4326)
def export_geojson(report):
    os.makedirs(GEO_WEB, exist_ok=True)
    sizes = {}

    def dump(gdf, name, tol=None, cols=None):
        g = gdf.to_crs(CRS_WEB)
        if cols:
            g = g[cols + ["geometry"]]
        if tol:
            g["geometry"] = g["geometry"].simplify(tol, preserve_topology=True)
        p = os.path.join(GEO_WEB, name)
        g.to_file(p, driver="GeoJSON")
        sizes[name] = os.path.getsize(p)

    per = gpd.read_file(PATHS["perimetro"])
    dump(per, "cali_perimetro.geojson", tol=0.0002)
    co = gpd.read_file(PATHS["comunas"])
    dump(co, "cali_comunas.geojson", tol=0.0001,
         cols=["comuna", "nombre"])
    cr = gpd.read_file(PATHS["corregimientos"])
    dump(cr, "cali_corregimientos.geojson", tol=0.0002,
         cols=["id_correg", "corregimie"])
    pu = gpd.read_file(PATHS["puestos"], encoding="utf-8")
    dump(pu, "cali_puestos.geojson", cols=["codigo", "nombre", "barrio", "comuna"])

    mp = gpd.read_file(PATHS["mpios_dane"],
                       columns=["DPTO_CCDGO", "MPIO_CDPMP", "MPIO_CNMBR"],
                       encoding="latin-1")
    mp = mp[mp["DPTO_CCDGO"] == "76"]
    dump(mp, "valle_municipios.geojson", tol=0.0008,
         cols=["MPIO_CDPMP", "MPIO_CNMBR"])
    report["geojson_web_bytes"] = sizes


def main():
    os.makedirs(GEO_WEB, exist_ok=True)
    report = {}
    build_mun_dane(report)
    cw = build_puestos_cali(report)
    reconstruir_congreso(cw, report)
    export_geojson(report)
    with open(os.path.join(META, "homologacion_loop2.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print("GEO_OK", json.dumps(report.get("puestos_cali", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
