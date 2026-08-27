"""Tests del data mart web (LOOP 4)."""
import glob
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "docs", "data")
IND = os.path.join(ROOT, "data_processed", "indicadores")


def _man():
    return json.load(open(os.path.join(WEB, "manifest.json"), encoding="utf-8"))


def test_manifest_archivos_existen():
    m = _man()
    for a in m["archivos"]:
        assert os.path.exists(os.path.join(WEB, a["path"])), a["path"]
    assert m["total_bytes"] > 0


def test_ningun_archivo_excesivo():
    m = _man()
    mx = max(a["bytes"] for a in m["archivos"])
    assert mx < 1_200_000, mx  # ningun archivo web > ~1.2 MB


def test_catalogo_paleta():
    cat = json.load(open(os.path.join(WEB, "catalogo.json"), encoding="utf-8"))
    for corp in ["PRE1", "PRE2", "SEN", "CAM", "CON"]:
        assert corp in cat and cat[corp]["unidades"]
    assert cat["PRE1"]["colores"]["IVÁN CEPEDA CASTRO"] == "#6a3d9a"
    assert cat["PRE1"]["colores"]["ABELARDO DE LA ESPRIELLA"] == "#f59e0b"


def test_mesa_reconcilia_con_municipio():
    # suma de votos de candidatos en archivos mesa de Cali (PRE2) == cand_total
    # de la competencia municipal de Cali (76001) PRE2
    tot = 0
    for f in glob.glob(os.path.join(WEB, "mesa", "76001_*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for key, votos in d["votos"].items():
            if key.endswith("|PRE2"):
                tot += sum(votos.values())
    m = pd.read_csv(os.path.join(IND, "competencia_municipio.csv"),
                    keep_default_na=False, dtype={"municipio_codigo": str})
    cali = m[(m.municipio_codigo == "001") & (m.corporacion == "Presidencia") &
             (m.vuelta == "2V")]["cand_total"].iloc[0]
    assert tot == int(cali), (tot, int(cali))


if __name__ == "__main__":
    for fn in [test_manifest_archivos_existen, test_ningun_archivo_excesivo,
               test_catalogo_paleta, test_mesa_reconcilia_con_municipio]:
        fn()
        print("PASS", fn.__name__)
