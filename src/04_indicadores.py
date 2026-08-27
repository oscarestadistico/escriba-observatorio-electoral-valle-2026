"""LOOP 3 - Genera marts de indicadores por nivel territorial.
Universo unico: archivos VALLE (ambito=='Valle'), que incluyen Cali a nivel mesa
(evita el doble conteo Cali+Valle). Territorio de Cali via crosswalk (LOOP 2).
Salidas en data_processed/indicadores/.
"""
import os
import numpy as np
import pandas as pd

from utils import ROOT, META
import indicadores as ind

PROCESSED = os.path.join(ROOT, "data_processed")
OUT = os.path.join(PROCESSED, "indicadores")
CANON = os.path.join(PROCESSED, "canonico.parquet")


def load():
    cols = ["ambito", "eleccion", "corporacion", "vuelta", "circunscripcion",
            "municipio_codigo", "municipio", "zona", "id_puesto",
            "candidato", "partido", "candidato_codigo", "es_voto_especial",
            "votos"]
    df = pd.read_parquet(CANON, columns=cols)
    df = df[df["ambito"] == "Valle"].copy()          # universo unico
    # DANE
    dane = pd.read_csv(os.path.join(META, "mun_dane_crosswalk.csv"),
                       dtype=str)[["municipio_codigo", "dane_codigo"]]
    df = df.merge(dane, on="municipio_codigo", how="left")
    # territorio Cali via crosswalk (electoral, reconciliable)
    cw = pd.read_csv(os.path.join(META, "crosswalk_puestos_cali.csv"),
                     dtype={"ID_PUESTO": str})
    cw = cw[["ID_PUESTO", "territorio_tipo", "territorio_nombre"]].drop_duplicates(
        "ID_PUESTO")
    df = df.merge(cw, left_on="id_puesto", right_on="ID_PUESTO", how="left")
    df["es_cali"] = df["municipio_codigo"] == "001"
    return df


def guardar(dfres, dfcomp, nombre):
    dfres.to_csv(os.path.join(OUT, f"resultados_{nombre}.csv"), index=False)
    dfcomp.to_csv(os.path.join(OUT, f"competencia_{nombre}.csv"), index=False)
    return len(dfcomp)


def cambio_1v_2v(df, level_cols, nombre):
    """Cambio agregado entre resultados territoriales 1V->2V (NO transferencia)."""
    pres = df[df["corporacion"] == "Presidencia"].copy()
    pres["unidad"] = np.where(pres["es_voto_especial"], "VOTO EN BLANCO",
                              pres["candidato"])
    pres = pres[~pres["es_voto_especial"] |
                (pres["candidato"].str.contains("BLANCO", na=False))]
    keys = level_cols + ["unidad"]
    piv = (pres.groupby(keys + ["vuelta"], observed=True)["votos"].sum()
           .unstack("vuelta", fill_value=0).reset_index())
    if "1V" not in piv or "2V" not in piv:
        return 0
    piv["delta_abs"] = piv["2V"] - piv["1V"]
    # pp respecto a validos por territorio y vuelta
    val = (pres[~pres["es_voto_especial"] |
                pres["candidato"].str.contains("BLANCO", na=False)]
           .groupby(level_cols + ["vuelta"], observed=True)["votos"].sum()
           .unstack("vuelta", fill_value=0))
    val.columns = [f"val_{c}" for c in val.columns]
    piv = piv.merge(val.reset_index(), on=level_cols, how="left")
    piv["pp_1v"] = np.where(piv["val_1V"] > 0, piv["1V"] / piv["val_1V"] * 100, np.nan)
    piv["pp_2v"] = np.where(piv["val_2V"] > 0, piv["2V"] / piv["val_2V"] * 100, np.nan)
    piv["delta_pp"] = piv["pp_2v"] - piv["pp_1v"]
    piv = piv.rename(columns={"1V": "votos_1v", "2V": "votos_2v"})
    piv.to_csv(os.path.join(OUT, f"cambio_1v2v_{nombre}.csv"), index=False)
    return len(piv)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load()
    resumen = {}

    # Valle (departamento)
    df["_valle"] = "VALLE DEL CAUCA"
    resumen["valle"] = guardar(ind.resultados(df, ["_valle"]),
                               ind.competencia(df, ["_valle"]), "valle")

    # Municipio
    lm = ["municipio_codigo", "municipio", "dane_codigo"]
    resumen["municipio"] = guardar(ind.resultados(df, lm),
                                   ind.competencia(df, lm), "municipio")

    # Cali por comuna y por corregimiento (usa territorio homologado)
    cali = df[df["es_cali"]].copy()
    com = cali[cali["territorio_tipo"] == "comuna"]
    resumen["cali_comuna"] = guardar(
        ind.resultados(com, ["territorio_nombre"]),
        ind.competencia(com, ["territorio_nombre"]), "cali_comuna")
    cor = cali[cali["territorio_tipo"] == "corregimiento"]
    resumen["cali_corregimiento"] = guardar(
        ind.resultados(cor, ["territorio_nombre"]),
        ind.competencia(cor, ["territorio_nombre"]), "cali_corregimiento")

    # Zona (por municipio)
    lz = ["municipio_codigo", "municipio", "zona"]
    resumen["zona"] = guardar(ind.resultados(df, lz),
                              ind.competencia(df, lz), "zona")

    # Cambio 1V-2V agregado
    resumen["cambio_municipio"] = cambio_1v_2v(df, lm, "municipio")
    resumen["cambio_cali_comuna"] = cambio_1v_2v(
        cali[cali.territorio_tipo == "comuna"], ["territorio_nombre"],
        "cali_comuna")

    import json
    with open(os.path.join(META, "indicadores_loop3.json"), "w",
              encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print("IND_OK", resumen)


if __name__ == "__main__":
    main()
