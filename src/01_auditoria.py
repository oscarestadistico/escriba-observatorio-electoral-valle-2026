"""LOOP 0 - Auditoria e inventario. NO construye dashboard, NO modifica fuentes.
Genera: metadata/manifest.json, metadata/fuentes.csv,
metadata/diccionario_variables.csv, project_state.json,
docs_project/AUDITORIA_LOOP0.md
Lectura eficiente (chunks) para CSV grandes; geopandas para cartografia.
"""
import csv
import glob
import json
import os
from collections import OrderedDict

import pandas as pd

from utils import ROOT, RAW, META, DOCS_PROJECT, sha256_file, human

UPLOADS = "/mnt/user-data/uploads"
SEP = ";"
CHUNK = 300_000
KEYCOLS = ["DEP", "DEPNOMBRE", "MUN", "MUNNOMBRE", "ZONA", "PUESTO",
           "MESA", "COMUCODIGO", "COMUNOMBRE", "CORCODIGO", "CORNOMBRE",
           "CIR", "PAR", "PARNOMBRE", "CAN", "CANNOMBRE"]

# ---- clasificacion declarativa de cada CSV (eleccion/corp/vuelta/nivel) ----
CSV_META = {
    "Presidenciales 2026 PV CALI.csv":  ("Presidencia 2026", "Presidencia", "1V", "Cali"),
    "Presidenciales 2026 PV VALLE.csv": ("Presidencia 2026", "Presidencia", "1V", "Valle"),
    "Presidenciales 2026 SV CALI.csv":  ("Presidencia 2026", "Presidencia", "2V", "Cali"),
    "Presidenciales 2026 SV  VALLE.csv":("Presidencia 2026", "Presidencia", "2V", "Valle"),
    "Senado y Camara Cali.csv":  ("Congreso 2026", "Senado+Camara", "NA", "Cali"),
    "Senado y Camara Valle.csv": ("Congreso 2026", "Senado+Camara", "NA", "Valle"),
}


def detect_encoding(path):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                for _ in range(2000):
                    f.readline()
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def audit_csv(path):
    enc = detect_encoding(path)
    header = pd.read_csv(path, sep=SEP, nrows=0, dtype=str, encoding=enc)
    cols = list(header.columns)
    use = [c for c in KEYCOLS if c in cols]

    nunique = {c: set() for c in use}
    nrows = 0
    votos_nonnum = 0
    votos_neg = 0
    votos_null = 0
    can_special = {}  # CAN -> CANNOMBRE para codigos no numericos de candidato
    cir_vals = set()
    zona_99 = 0  # corregimientos
    for ch in pd.read_csv(path, sep=SEP, dtype=str, encoding=enc,
                          chunksize=CHUNK, usecols=lambda c: c in use + ["VOTOS"]):
        nrows += len(ch)
        for c in use:
            nunique[c].update(ch[c].dropna().unique().tolist())
        v = pd.to_numeric(ch["VOTOS"], errors="coerce")
        votos_nonnum += int(v.isna().sum() - ch["VOTOS"].isna().sum())
        votos_null += int(ch["VOTOS"].isna().sum())
        votos_neg += int((v < 0).sum())
        if "ZONA" in ch:
            zona_99 += int((ch["ZONA"] == "99").sum())
        if "CIR" in ch:
            cir_vals.update(ch["CIR"].dropna().unique().tolist())
        if "CAN" in ch and "CANNOMBRE" in ch:
            m = ch[pd.to_numeric(ch["CAN"], errors="coerce") >= 900]
            for cc, nn in zip(m["CAN"], m["CANNOMBRE"]):
                can_special.setdefault(cc, nn)

    res = OrderedDict()
    res["archivo"] = os.path.basename(path)
    res["encoding"] = enc
    res["separador"] = SEP
    res["filas"] = nrows
    res["columnas"] = len(cols)
    res["campos"] = cols
    res["distintos"] = {c: len(v) for c, v in nunique.items()}
    res["DEP_valores"] = sorted(nunique.get("DEP", []))
    res["muestra_MUN"] = sorted(nunique.get("MUN", []))[:6]
    res["n_municipios"] = len(nunique.get("MUN", []))
    res["n_zonas"] = len(nunique.get("ZONA", []))
    res["n_puestos"] = len(nunique.get("PUESTO", []))
    res["n_mesas"] = len(nunique.get("MESA", []))
    res["n_partidos"] = len(nunique.get("PAR", []))
    res["n_candidatos"] = len(nunique.get("CAN", []))
    res["zona99_corregimiento_filas"] = zona_99
    res["cir_valores"] = sorted(cir_vals)
    res["votos_no_numericos"] = votos_nonnum
    res["votos_negativos"] = votos_neg
    res["votos_nulos"] = votos_null
    res["candidatos_codigos_especiales"] = can_special
    res["comunombre_muestra"] = sorted(nunique.get("COMUNOMBRE", []))[:8]
    res["cornombre_muestra"] = sorted(nunique.get("CORNOMBRE", []))[:8]
    return res


def audit_shp(path):
    import geopandas as gpd
    gdf = gpd.read_file(path, rows=0)
    full = gpd.read_file(path)
    return OrderedDict(
        archivo=os.path.basename(path),
        n_features=len(full),
        crs=str(full.crs),
        campos=list(gdf.columns.drop("geometry", errors="ignore")),
        geom_types=sorted(full.geom_type.dropna().unique().tolist()),
        bounds=[round(float(x), 5) for x in full.total_bounds],
    )


def main():
    os.makedirs(META, exist_ok=True)
    os.makedirs(DOCS_PROJECT, exist_ok=True)

    manifest = OrderedDict()
    manifest["proyecto"] = "OBSERVATORIO ELECTORAL VALLE DEL CAUCA 2026"
    manifest["loop"] = 0
    manifest["zips_originales"] = []
    manifest["csv"] = []
    manifest["cartografia"] = []
    manifest["otros"] = []

    # 1) hashes de los ZIP originales
    for z in sorted(glob.glob(os.path.join(UPLOADS, "*.zip"))):
        manifest["zips_originales"].append(OrderedDict(
            archivo=os.path.basename(z),
            bytes=os.path.getsize(z),
            tamano=human(os.path.getsize(z)),
            sha256=sha256_file(z),
        ))

    fuentes_rows = []

    # 2) CSV electorales
    for path in sorted(glob.glob(os.path.join(RAW, "raw_Bases_elecciones_2026", "**", "*.csv"), recursive=True)):
        r = audit_csv(path)
        r["sha256"] = sha256_file(path)
        r["bytes"] = os.path.getsize(path)
        manifest["csv"].append(r)
        elec, corp, vuelta, nivel = CSV_META.get(
            r["archivo"], ("?", "?", "?", "?"))
        fuentes_rows.append(dict(
            archivo=r["archivo"], eleccion=elec, corporacion=corp,
            vuelta=vuelta, nivel=nivel, tipo_fuente="base_procesada_csv",
            fecha="2026", filas=r["filas"], columnas=r["columnas"],
            hash=r["sha256"][:16], estado="AUDITADO",
            observaciones="sep=; enc=%s" % r["encoding"]))

    # 3) cartografia (shp)
    for path in sorted(glob.glob(os.path.join(RAW, "raw_*", "**", "*.shp"), recursive=True)):
        r = audit_shp(path)
        r["sha256"] = sha256_file(path)
        r["bytes"] = os.path.getsize(path)
        manifest["cartografia"].append(r)
        fuentes_rows.append(dict(
            archivo=r["archivo"], eleccion="NA", corporacion="NA",
            vuelta="NA", nivel="cartografia", tipo_fuente="shapefile",
            fecha="MGN2018/2025-2026", filas=r["n_features"],
            columnas=len(r["campos"]), hash=r["sha256"][:16],
            estado="AUDITADO", observaciones="crs=%s" % r["crs"]))

    # 4) otros insumos (pdf, txt hash, zips internos)
    for path in sorted(glob.glob(os.path.join(RAW, "raw_MMV_*", "**", "*"), recursive=True)):
        if os.path.isfile(path) and path.lower().endswith((".pdf", ".txt", ".zip", ".csv")):
            manifest["otros"].append(dict(
                archivo=os.path.relpath(path, RAW),
                bytes=os.path.getsize(path),
                tamano=human(os.path.getsize(path))))

    with open(os.path.join(META, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # fuentes.csv
    campos = ["archivo", "eleccion", "corporacion", "vuelta", "nivel",
              "tipo_fuente", "fecha", "filas", "columnas", "hash",
              "estado", "observaciones"]
    with open(os.path.join(META, "fuentes.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(fuentes_rows)

    print("AUDIT_OK", len(manifest["csv"]), "csv",
          len(manifest["cartografia"]), "shp")
    return manifest


if __name__ == "__main__":
    main()
