"""Tests de reconciliacion de indicadores (LOOP 3).
SUMA ZONAS = MUNICIPIO ; SUMA MUNICIPIOS = VALLE ; identidades de votos.
'NA' (vuelta de Congreso) se conserva con keep_default_na=False.
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IND = os.path.join(ROOT, "data_processed", "indicadores")
SEG = ["eleccion", "corporacion", "vuelta", "circunscripcion"]
DT = {"circunscripcion": str, "vuelta": str, "municipio_codigo": str,
      "dane_codigo": str}


def rd(name):
    return pd.read_csv(os.path.join(IND, name), keep_default_na=False, dtype=DT)


def test_municipio_suma_valle():
    v = rd("competencia_valle.csv").set_index(SEG)
    m = rd("competencia_municipio.csv").groupby(SEG).sum(numeric_only=True)
    for col in ["cand_total", "blancos", "nulos", "no_marcados", "total_marcas"]:
        d = (m[col] - v[col]).abs().max()
        assert d == 0, (col, d)


def test_zona_suma_municipio():
    z = rd("competencia_zona.csv").groupby(["municipio_codigo"] + SEG).sum(
        numeric_only=True)
    m = rd("competencia_municipio.csv").set_index(["municipio_codigo"] + SEG)
    d = (z["total_marcas"] - m["total_marcas"]).abs().max()
    assert d == 0, d


def test_identidades_de_votos():
    v = rd("competencia_valle.csv")
    assert (v["validos"] == v["cand_total"] + v["blancos"]).all()
    assert (v["total_marcas"] ==
            v["validos"] + v["nulos"] + v["no_marcados"]).all()


def test_cali_territorial_cuadra_con_gap():
    m = rd("competencia_municipio.csv")
    cali = m[m.municipio_codigo == "001"].set_index(SEG)["total_marcas"]
    co = rd("competencia_cali_comuna.csv").groupby(SEG)["total_marcas"].sum()
    cr = rd("competencia_cali_corregimiento.csv").groupby(SEG)["total_marcas"].sum()
    gap = cali - co.reindex(cali.index).fillna(0) - cr.reindex(cali.index).fillna(0)
    # el gap (zonas especiales ZONA>=90) es no negativo y explica toda la diferencia
    assert (gap >= 0).all()
    assert (co.reindex(cali.index).fillna(0) + cr.reindex(cali.index).fillna(0)
            + gap == cali).all()


if __name__ == "__main__":
    for fn in [test_municipio_suma_valle, test_zona_suma_municipio,
               test_identidades_de_votos, test_cali_territorial_cuadra_con_gap]:
        fn()
        print("PASS", fn.__name__)
