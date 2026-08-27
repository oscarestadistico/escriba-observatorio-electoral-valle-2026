"""Tests de integridad de la base canonica (LOOP 1)."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "data_processed", "canonico.parquet")
FILAS_ESPERADAS = 1_710_766  # suma auditada LOOP 0
CORP_VALIDAS = {"Presidencia", "Senado", "Cámara", "Consultas"}


def _load(cols=None):
    return pd.read_parquet(CANON, columns=cols)


def test_conteo_total():
    n = _load(["votos"]).shape[0]
    assert n == FILAS_ESPERADAS, (n, FILAS_ESPERADAS)


def test_sin_nulos_en_llaves():
    df = _load(["eleccion", "corporacion", "id_mesa", "votos"])
    for c in ["eleccion", "corporacion", "id_mesa"]:
        assert df[c].notna().all(), c
        assert (df[c].astype(str).str.len() > 0).all(), c
    assert df["votos"].notna().all()


def test_votos_enteros_no_negativos():
    v = _load(["votos"])["votos"]
    assert str(v.dtype).startswith("int"), v.dtype
    assert (v >= 0).all()


def test_ceros_a_izquierda_preservados():
    df = _load(["departamento_codigo", "municipio_codigo", "zona"])
    assert (df["departamento_codigo"] == "31").all()
    # municipio como texto de 3 chars con ceros (001, 013, ...)
    assert df["municipio_codigo"].str.match(r"^\d{3}$").all()
    assert df["zona"].str.match(r"^\d{2}$").all()


def test_corporacion_valida():
    c = _load(["corporacion"])["corporacion"].unique()
    assert set(c).issubset(CORP_VALIDAS), set(c)


def test_territorio_fuente_tipo_valido():
    vals = set(_load(["territorio_fuente_tipo"])["territorio_fuente_tipo"].unique())
    esperado = {"comuna", "corregimiento", "nacional_especial", "otro",
                "no_geografico_congreso"}
    assert vals.issubset(esperado), vals


if __name__ == "__main__":
    for fn in [test_conteo_total, test_sin_nulos_en_llaves,
               test_votos_enteros_no_negativos,
               test_ceros_a_izquierda_preservados,
               test_corporacion_valida, test_territorio_fuente_tipo_valido]:
        fn()
        print("PASS", fn.__name__)
