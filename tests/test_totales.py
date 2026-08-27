"""Tests de reconciliacion de totales (LOOP 1).
Verifica canonico vs auditoria y la relacion Cali subset de Valle.
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "data_processed", "canonico.parquet")
RAW = os.path.join(ROOT, "data_raw", "raw_Bases_elecciones_2026")

# votos esperados por archivo (independiente: recomputo desde 2 CSV pequenos)
SPOT = {
    "Presidenciales 2026 SV CALI.csv":
        "Presidenciales/Presidenciales 2026 SV CALI.csv",
    "Presidenciales 2026 PV CALI.csv":
        "Presidenciales/Presidenciales 2026 PV CALI.csv",
}


def _canon(cols):
    return pd.read_parquet(CANON, columns=cols)


def test_votos_por_archivo_reconcilian():
    df = _canon(["archivo_fuente", "votos"])
    can = df.groupby("archivo_fuente")["votos"].sum()
    for base, rel in SPOT.items():
        raw = pd.read_csv(os.path.join(RAW, rel), sep=";", dtype=str)
        raw_sum = pd.to_numeric(raw["VOTOS"], errors="coerce").fillna(0).sum()
        assert int(can[base]) == int(raw_sum), (base, int(can[base]), int(raw_sum))


def test_cali_es_subconjunto_de_valle():
    df = _canon(["eleccion", "vuelta", "archivo_fuente",
                 "municipio_codigo", "votos"])
    pares = [
        ("Presidenciales 2026 PV CALI.csv", "Presidenciales 2026 PV VALLE.csv"),
        ("Presidenciales 2026 SV CALI.csv", "Presidenciales 2026 SV  VALLE.csv"),
        ("Senado y Camara Cali.csv", "Senado y Camara Valle.csv"),
    ]
    for cali_f, valle_f in pares:
        cali = df.loc[df.archivo_fuente == cali_f, "votos"].sum()
        vsub = df.loc[(df.archivo_fuente == valle_f) &
                      (df.municipio_codigo == "001"), "votos"].sum()
        assert int(cali) == int(vsub), (cali_f, int(cali), int(vsub))


def test_valle_tiene_42_municipios():
    df = _canon(["archivo_fuente", "municipio_codigo"])
    for f in ["Presidenciales 2026 PV VALLE.csv",
              "Presidenciales 2026 SV  VALLE.csv",
              "Senado y Camara Valle.csv"]:
        n = df.loc[df.archivo_fuente == f, "municipio_codigo"].nunique()
        assert n == 42, (f, n)


if __name__ == "__main__":
    for fn in [test_votos_por_archivo_reconcilian,
               test_cali_es_subconjunto_de_valle,
               test_valle_tiene_42_municipios]:
        fn()
        print("PASS", fn.__name__)
