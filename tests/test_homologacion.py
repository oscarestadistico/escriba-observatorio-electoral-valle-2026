"""Tests de homologacion geografica (LOOP 2)."""
import os
import geopandas as gpd
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "metadata")
GEO = os.path.join(ROOT, "docs", "geo")


def test_mun_dane_42_exactos():
    d = pd.read_csv(os.path.join(META, "mun_dane_crosswalk.csv"), dtype=str)
    assert len(d) == 42
    assert (d["metodo"] == "EXACTO_NOMBRE").all()
    assert d["dane_codigo"].str.startswith("76").all()
    assert d["dane_codigo"].nunique() == 42
    assert d.loc[d.municipio_codigo == "001", "dane_codigo"].iloc[0] == "76001"


def test_crosswalk_puestos_estados():
    cw = pd.read_csv(os.path.join(META, "crosswalk_puestos_cali.csv"))
    # cartografiados tienen coordenadas; no encontrados no las tienen
    car = cw[cw.estado_cruce.isin(["EXACTO", "REQUIERE_VALIDACION", "ESPACIAL"])]
    assert car["latitud"].notna().all() and car["longitud"].notna().all()
    assert cw.loc[cw.estado_cruce == "NO_ENCONTRADO", "latitud"].isna().all()
    # ningun puesto cartografico quedo sin resultado electoral en este dataset
    assert (cw.estado_cruce == "CARTO_SIN_ELECTORAL").sum() == 0


def test_conflicto_comuna_documentado():
    # el conflicto electoral-vs-geografia debe estar EXPUESTO, no resuelto en silencio
    cw = pd.read_csv(os.path.join(META, "crosswalk_puestos_cali.csv"))
    rv = cw[cw.estado_cruce == "REQUIERE_VALIDACION"]
    assert len(rv) > 0
    # en conflicto, ambas numeraciones estan presentes y difieren
    urb = rv[rv.territorio_tipo == "comuna"].dropna(
        subset=["comuna_electoral", "comuna_cartografica"])
    assert (urb["comuna_electoral"] != urb["comuna_cartografica"]).any()


def test_geojson_web_conteos():
    assert len(gpd.read_file(os.path.join(GEO, "cali_comunas.geojson"))) == 22
    assert len(gpd.read_file(os.path.join(GEO, "cali_corregimientos.geojson"))) == 15
    assert len(gpd.read_file(os.path.join(GEO, "valle_municipios.geojson"))) == 42
    assert len(gpd.read_file(os.path.join(GEO, "cali_puestos.geojson"))) == 206
    g = gpd.read_file(os.path.join(GEO, "cali_comunas.geojson"))
    assert str(g.crs).endswith("4326")


if __name__ == "__main__":
    for fn in [test_mun_dane_42_exactos, test_crosswalk_puestos_estados,
               test_conflicto_comuna_documentado, test_geojson_web_conteos]:
        fn()
        print("PASS", fn.__name__)
