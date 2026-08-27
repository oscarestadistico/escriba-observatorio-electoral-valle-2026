"""LOOP 1 - ETL canonico. Lee las 6 bases CSV auditadas y produce una estructura
canonica unica en Parquet, preservando columnas originales y normalizando tipos,
espacios y ceros a la izquierda. NO modifica sustantivamente nombres politicos.
NO homologa geografia (eso es LOOP 2).

Salidas:
  data_processed/canonico.parquet         (base canonica unica)
  data_processed/resumen_canonico.csv     (control: filas y votos por fuente)
  metadata/etl_log.json                   (diagnostico de la transformacion)
Regla de creditos: solo procesa CSV cuyo hash figure en project_state; si el hash
no cambia respecto a un canonico previo, no reprocesa.
"""
import json
import os

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils import ROOT, RAW, META

PROCESSED = os.path.join(ROOT, "data_processed")
SEP = ";"
CHUNK = 300_000
BASES_DIR = os.path.join(RAW, "raw_Bases_elecciones_2026")

# archivo -> (eleccion, es_presidencia, vuelta, ambito)
FILES = {
    "Presidenciales/Presidenciales 2026 PV CALI.csv":  ("Presidencia 2026", True, "1V", "Cali"),
    "Presidenciales/Presidenciales 2026 PV VALLE.csv": ("Presidencia 2026", True, "1V", "Valle"),
    "Presidenciales/Presidenciales 2026 SV CALI.csv":  ("Presidencia 2026", True, "2V", "Cali"),
    "Presidenciales/Presidenciales 2026 SV  VALLE.csv":("Presidencia 2026", True, "2V", "Valle"),
    "Camara y Senado/Senado y Camara Cali.csv":  ("Congreso 2026", False, "NA", "Cali"),
    "Camara y Senado/Senado y Camara Valle.csv": ("Congreso 2026", False, "NA", "Valle"),
}

CORP_MAP = {"SENADO": "Senado", "CAMARA": "Cámara", "CÁMARA": "Cámara",
            "CONSULTAS": "Consultas"}
CODE_COLS = ["DEP", "MUN", "ZONA", "PUESTO", "MESA", "COMUCODIGO",
             "CORCODIGO", "PAR", "CAN", "CIR"]
TXT_COLS = ["DEPNOMBRE", "MUNNOMBRE", "PUESNOMBRE", "COMUNOMBRE",
            "CORNOMBRE", "PARNOMBRE", "CANNOMBRE"]

CANON_ORDER = ["eleccion", "corporacion", "vuelta", "ambito",
               "departamento_codigo", "departamento", "municipio_codigo",
               "municipio", "zona", "territorio_fuente_tipo", "puesto",
               "puesto_nombre", "mesa", "id_puesto", "id_mesa",
               "circunscripcion", "partido_codigo", "partido",
               "candidato_codigo", "candidato", "es_voto_especial", "votos",
               "comuna_fuente", "corregimiento_fuente", "comucodigo_orig",
               "comunombre_orig", "corcodigo_orig", "cornombre_orig",
               "archivo_fuente", "tipo_fuente"]


def norm_txt(s):
    # colapsa espacios internos y recorta; NO altera contenido sustantivo
    return (s.fillna("").astype(str).str.strip()
            .str.replace(r"\s+", " ", regex=True))


def territorio_fuente_tipo(comunombre, es_pres):
    """Clasifica el territorio SEGUN el campo COMUNOMBRE de la fuente, sin
    inferir nada desde ZONA (ZONA no es clasificador territorial: una comuna
    abarca varias zonas y hay ZONA=99 con etiqueta de comuna).
    En Congreso COMUNOMBRE no es geografia de Cali -> no_geografico_congreso.
    """
    if not es_pres:
        return pd.Series("no_geografico_congreso", index=comunombre.index)
    out = pd.Series("otro", index=comunombre.index)
    out[comunombre.str.startswith("COMUNA")] = "comuna"
    out[comunombre.str.startswith("CORREGIMIENTO")] = "corregimiento"
    out[comunombre == "NACIONAL"] = "nacional_especial"
    return out


def transform(ch, eleccion, es_pres, vuelta, ambito, archivo):
    for c in CODE_COLS:
        if c in ch:
            ch[c] = ch[c].astype(str).str.strip()
    for c in TXT_COLS:
        if c in ch:
            ch[c] = norm_txt(ch[c])

    out = pd.DataFrame(index=ch.index)
    out["eleccion"] = eleccion
    if es_pres:
        out["corporacion"] = "Presidencia"
    else:
        out["corporacion"] = ch["CORNOMBRE"].str.upper().map(CORP_MAP).fillna("Otro")
    out["vuelta"] = vuelta
    out["ambito"] = ambito
    out["departamento_codigo"] = ch["DEP"]          # Registraduria (31); DANE en LOOP2
    out["departamento"] = ch["DEPNOMBRE"]
    out["municipio_codigo"] = ch["MUN"]             # Registraduria; DANE en LOOP2
    out["municipio"] = ch["MUNNOMBRE"]
    out["zona"] = ch["ZONA"]
    out["territorio_fuente_tipo"] = territorio_fuente_tipo(ch["COMUNOMBRE"], es_pres)
    out["puesto"] = ch["PUESTO"]
    out["puesto_nombre"] = ch["PUESNOMBRE"]
    out["mesa"] = ch["MESA"]
    out["id_puesto"] = ch["DEP"] + "-" + ch["MUN"] + "-" + ch["ZONA"] + "-" + ch["PUESTO"]
    out["id_mesa"] = out["id_puesto"] + "-" + ch["MESA"]
    out["circunscripcion"] = ch["CIR"]
    out["partido_codigo"] = ch["PAR"]
    out["partido"] = ch["PARNOMBRE"]
    out["candidato_codigo"] = ch["CAN"]
    out["candidato"] = ch["CANNOMBRE"]
    can_num = pd.to_numeric(ch["CAN"], errors="coerce")
    out["es_voto_especial"] = can_num.isin([996, 997, 998])
    out["votos"] = pd.to_numeric(ch["VOTOS"], errors="coerce").fillna(0).astype("int64")

    cn = ch["COMUNOMBRE"]
    is_com = cn.str.startswith("COMUNA")
    is_cor = cn.str.startswith("CORREGIMIENTO")
    out["comuna_fuente"] = cn.where(is_com, "")
    out["corregimiento_fuente"] = cn.where(is_cor, "")
    out["comucodigo_orig"] = ch["COMUCODIGO"]
    out["comunombre_orig"] = ch["COMUNOMBRE"]
    out["corcodigo_orig"] = ch["CORCODIGO"]
    out["cornombre_orig"] = ch["CORNOMBRE"]
    out["archivo_fuente"] = archivo
    out["tipo_fuente"] = "base_procesada_csv"
    return out[CANON_ORDER]


def main():
    os.makedirs(PROCESSED, exist_ok=True)
    writer = None
    out_path = os.path.join(PROCESSED, "canonico.parquet")
    resumen = []
    log = {"archivos": {}, "corporacion_conteo": {},
           "territorio_fuente_tipo_conteo": {},
           "nota": ("ZONA no es clasificador territorial: una comuna abarca "
                    "varias ZONA (23-37 -> COMUNA 15-22) y hay ZONA=99 con "
                    "etiqueta de comuna. Territorio en Presidencia proviene de "
                    "COMUNOMBRE; en Congreso se reconstruye en LOOP 2.")}
    total = 0
    for rel, (elec, es_pres, vuelta, ambito) in FILES.items():
        path = os.path.join(BASES_DIR, rel)
        base = os.path.basename(path)
        f_rows, f_votos = 0, 0
        for ch in pd.read_csv(path, sep=SEP, dtype=str, encoding="utf-8",
                              chunksize=CHUNK):
            t = transform(ch, elec, es_pres, vuelta, ambito, base)
            f_rows += len(t)
            f_votos += int(t["votos"].sum())
            for k, v in t["corporacion"].value_counts().items():
                log["corporacion_conteo"][k] = log["corporacion_conteo"].get(k, 0) + int(v)
            for k, v in t["territorio_fuente_tipo"].value_counts().items():
                log["territorio_fuente_tipo_conteo"][k] = \
                    log["territorio_fuente_tipo_conteo"].get(k, 0) + int(v)
            table = pa.Table.from_pandas(t, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema, compression="zstd")
            writer.write_table(table)
        resumen.append(dict(archivo=base, eleccion=elec, vuelta=vuelta,
                            ambito=ambito, filas=f_rows, votos=f_votos))
        log["archivos"][base] = dict(filas=f_rows, votos=f_votos)
        total += f_rows
    if writer:
        writer.close()

    pd.DataFrame(resumen).to_csv(
        os.path.join(PROCESSED, "resumen_canonico.csv"), index=False)
    log["total_filas"] = total
    with open(os.path.join(META, "etl_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print("ETL_OK filas=%d -> %s" % (total, out_path))


if __name__ == "__main__":
    main()
