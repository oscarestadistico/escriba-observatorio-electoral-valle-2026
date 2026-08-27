"""LOOP 4 - Data mart para web (docs/data/). Genera archivos pequenos y un
manifest para carga perezosa. Agregados completos + detalle mesa particionado
por municipio-zona + catalogo indexado (compacta nombres largos).
Universo: archivos VALLE. Territorio Cali homologado (LOOP 2).
"""
import json
import os

import numpy as np
import pandas as pd

from utils import ROOT, META
import indicadores as ind

PROC = os.path.join(ROOT, "data_processed")
IND = os.path.join(PROC, "indicadores")
WEB = os.path.join(ROOT, "docs", "data")
CANON = os.path.join(PROC, "canonico.parquet")

CORP_COD = {("Presidencia", "1V"): "PRE1", ("Presidencia", "2V"): "PRE2",
            ("Senado", "NA"): "SEN", ("Cámara", "NA"): "CAM",
            ("Consultas", "NA"): "CON"}
# paleta establecida
COLOR_CAND = {"IVÁN CEPEDA CASTRO": "#6a3d9a", "ABELARDO DE LA ESPRIELLA": "#f59e0b"}
PAL = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2",
       "#7f7f7f", "#bcbd22", "#17becf", "#ff7f0e", "#393b79", "#637939"]


def rnd(df):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            if c.endswith(("_pp", "pct_validos", "blanco_pp", "top1_pp")):
                df[c] = df[c].round(1)
            elif c in ("hhi", "nep", "fragmentacion"):
                df[c] = df[c].round(3)
            else:
                df[c] = df[c].round(3)
    return df


def dump(obj, relpath):
    p = os.path.join(WEB, relpath)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return relpath, os.path.getsize(p)


def csv_json(name, rel, files):
    df = pd.read_csv(os.path.join(IND, name), keep_default_na=False,
                     dtype={"circunscripcion": str, "vuelta": str,
                            "municipio_codigo": str, "dane_codigo": str,
                            "zona": str})
    files.append(dump(json.loads(rnd(df).to_json(orient="records")), rel))


def main():
    os.makedirs(WEB, exist_ok=True)
    files = []

    # 1) agregados analiticos
    for src, rel in [
        ("competencia_valle.csv", "valle/competencia.json"),
        ("resultados_valle.csv", "valle/resultados.json"),
        ("competencia_municipio.csv", "municipio/competencia.json"),
        ("resultados_municipio.csv", "municipio/resultados.json"),
        ("competencia_cali_comuna.csv", "cali/comuna_competencia.json"),
        ("resultados_cali_comuna.csv", "cali/comuna_resultados.json"),
        ("competencia_cali_corregimiento.csv", "cali/correg_competencia.json"),
        ("resultados_cali_corregimiento.csv", "cali/correg_resultados.json"),
        ("competencia_zona.csv", "zona/competencia.json"),
        ("cambio_1v2v_municipio.csv", "cambio/municipio.json"),
        ("cambio_1v2v_cali_comuna.csv", "cambio/cali_comuna.json"),
    ]:
        csv_json(src, rel, files)

    # 2) universo para puesto/estructura/mesa
    cols = ["ambito", "eleccion", "corporacion", "vuelta", "circunscripcion",
            "municipio_codigo", "municipio", "zona", "puesto", "puesto_nombre",
            "id_puesto", "mesa", "candidato", "candidato_codigo", "partido",
            "es_voto_especial", "votos"]
    df = pd.read_parquet(CANON, columns=cols)
    df = df[df["ambito"] == "Valle"].copy()
    dane = pd.read_csv(os.path.join(META, "mun_dane_crosswalk.csv"),
                       dtype=str)[["municipio_codigo", "dane_codigo"]]
    df = df.merge(dane, on="municipio_codigo", how="left")
    df["unidad"] = np.where(df["corporacion"] == "Presidencia",
                            df["candidato"], df["partido"])
    df["corpcod"] = [CORP_COD.get((c, v), "?")
                     for c, v in zip(df["corporacion"], df["vuelta"])]

    # 3) catalogo de unidades por corporacion (indexado) + colores
    catalogo = {}
    for corp in df["corpcod"].unique():
        sub = df[(df["corpcod"] == corp) & (~df["es_voto_especial"])]
        unidades = sorted(sub["unidad"].dropna().unique().tolist())
        cols_map = {}
        pi = 0
        for u in unidades:
            if u in COLOR_CAND:
                cols_map[u] = COLOR_CAND[u]
            else:
                cols_map[u] = PAL[pi % len(PAL)]
                pi += 1
        catalogo[corp] = {"unidades": unidades, "colores": cols_map}
    files.append(dump(catalogo, "catalogo.json"))
    uidx = {corp: {u: i for i, u in enumerate(catalogo[corp]["unidades"])}
            for corp in catalogo}

    # 4) puesto competencia por municipio (para mapa de puestos / modulo 5)
    pc = ind.competencia(df, ["municipio_codigo", "dane_codigo", "zona",
                              "puesto", "id_puesto"])
    pc = rnd(pc)
    for dcod, g in pc.groupby("dane_codigo"):
        files.append(dump(json.loads(g.to_json(orient="records")),
                          f"puesto/{dcod}.json"))

    # 5) estructura territorial por municipio (cascada, sin resultados)
    for dcod, g in df.groupby("dane_codigo"):
        tree = {}
        for z, gz in g.groupby("zona"):
            pue = {}
            for p, gp in gz.groupby("puesto"):
                pue[p] = {"n": gp["puesto_nombre"].iloc[0],
                          "mesas": sorted(gp["mesa"].unique().tolist())}
            tree[z] = pue
        files.append(dump({"municipio": g["municipio"].iloc[0], "zonas": tree},
                          f"estructura/{dcod}.json"))

    # 6) detalle mesa por municipio-zona (compacto, unidad->indice)
    det = df[~df["es_voto_especial"]].copy()
    esp = df[df["es_voto_especial"]].copy()
    esp["tipo"] = esp["candidato"].str.extract(
        r"(BLANCO|NULOS|NO MARCADOS)")[0]
    for (dcod, z), g in det.groupby(["dane_codigo", "zona"]):
        rec = {}
        for (p, m, corp), gg in g.groupby(["puesto", "mesa", "corpcod"]):
            key = f"{p}|{m}|{corp}"
            rec[key] = {str(uidx[corp][u]): int(v)
                        for u, v in zip(gg["unidad"], gg["votos"]) if v}
        # especiales de esa zona
        e = esp[(esp["dane_codigo"] == dcod) & (esp["zona"] == z)]
        esprec = {}
        for (p, m, corp), gg in e.groupby(["puesto", "mesa", "corpcod"]):
            esprec[f"{p}|{m}|{corp}"] = {t: int(gg[gg.tipo == t]["votos"].sum())
                                         for t in ["BLANCO", "NULOS", "NO MARCADOS"]}
        files.append(dump({"votos": rec, "especiales": esprec},
                          f"mesa/{dcod}_{z}.json"))

    # 7) manifest
    total = sum(s for _, s in files)
    manifest = {
        "proyecto": "OBSERVATORIO ELECTORAL VALLE 2026",
        "generado": "2026-08-26",
        "fuente": "Registraduria Nacional (base procesada); cartografia Cali + MGN2018 DANE",
        "cobertura": "Valle del Cauca (42 municipios) y Santiago de Cali",
        "elecciones": ["Presidencia 1V", "Presidencia 2V", "Senado", "Cámara",
                       "Consultas"],
        "corp_codigos": {f"{k[0]}|{k[1]}": v for k, v in CORP_COD.items()},
        "niveles": ["valle", "municipio", "zona", "puesto", "mesa",
                    "cali_comuna", "cali_corregimiento"],
        "advertencias": [
            "Resultados agregados; no permiten inferir comportamiento individual (falacia ecologica).",
            "Sin denominador de censo: no se reporta participacion/abstencion.",
            "102 puestos de Cali con conflicto comuna electoral vs geografica (REQUIERE_VALIDACION).",
            "Cambio 1V-2V es cambio agregado, no transferencia de votos.",
        ],
        "archivos": [{"path": p, "bytes": s} for p, s in sorted(files)],
        "total_bytes": total,
    }
    dump(manifest, "manifest.json")
    print("WEB_OK archivos=%d total=%.1f MB max=%.0f KB" % (
        len(files), total / 1e6,
        max(s for _, s in files) / 1024))


if __name__ == "__main__":
    main()
