"""Tests de coherencia geografica de fuente (LOOP 1).
La homologacion real (comuna numerica, coordenadas) es LOOP 2. Aqui se verifica
que los campos _fuente reflejen fielmente COMUNOMBRE y no inventen geografia,
y se documenta que ZONA NO es clasificador territorial.
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "data_processed", "canonico.parquet")


def _c(cols):
    return pd.read_parquet(CANON, columns=cols)


def test_comuna_fuente_refleja_comunombre():
    df = _c(["comuna_fuente", "comunombre_orig", "territorio_fuente_tipo"])
    m = df["comuna_fuente"] != ""
    assert df.loc[m, "comunombre_orig"].str.startswith("COMUNA").all()
    assert (df.loc[m, "territorio_fuente_tipo"] == "comuna").all()


def test_corregimiento_fuente_refleja_comunombre():
    df = _c(["corregimiento_fuente", "comunombre_orig"])
    m = df["corregimiento_fuente"] != ""
    assert df.loc[m, "comunombre_orig"].str.startswith("CORREGIMIENTO").all()


def test_congreso_sin_geografia_en_campos_fuente():
    df = _c(["corporacion", "comuna_fuente", "corregimiento_fuente",
             "territorio_fuente_tipo"])
    cong = df[df["corporacion"].isin(["Senado", "Cámara", "Consultas"])]
    assert (cong["comuna_fuente"] == "").all()
    assert (cong["corregimiento_fuente"] == "").all()
    assert (cong["territorio_fuente_tipo"] == "no_geografico_congreso").all()


def test_zona_no_es_clasificador_territorial():
    df = _c(["zona", "comuna_fuente"])
    com = df[df["comuna_fuente"] != ""]
    zonas_por_comuna = com.groupby("comuna_fuente")["zona"].nunique()
    assert (zonas_por_comuna > 1).any(), "esperado: comunas en multiples zonas"


if __name__ == "__main__":
    for fn in [test_comuna_fuente_refleja_comunombre,
               test_corregimiento_fuente_refleja_comunombre,
               test_congreso_sin_geografia_en_campos_fuente,
               test_zona_no_es_clasificador_territorial]:
        fn()
        print("PASS", fn.__name__)
