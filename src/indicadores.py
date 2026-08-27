"""Funciones reutilizables de indicadores electorales (LOOP 3).
Definiciones (ver docs_project/METODOLOGIA.md):
  total_marcas   = todas las marcas (candidatos + blanco + nulos + no marcados)
  votos_candidatos = marcas por candidatos/listas (excluye 996/997/998)
  blancos=996, nulos=997, no_marcados=998 (por circunscripcion)
  validos        = votos_candidatos + blancos
  pct (de una unidad) = votos_unidad / validos * 100
  margen_pp      = (v1 - v2) / validos * 100
  HHI            = sum(s_i^2), s_i = v_i / votos_candidatos   (rango 0..1)
  NEP            = 1 / HHI ; fragmentacion (Rae) = 1 - HHI
Precision completa en calculo; el redondeo es responsabilidad de la vista.
Participacion/abstencion: NO se calcula (no hay denominador de censo en la fuente).
"""
import numpy as np
import pandas as pd

SEG = ["eleccion", "corporacion", "vuelta", "circunscripcion"]


def unidad_col(df):
    """Unidad de competencia: candidato en Presidencia; partido en Congreso."""
    return np.where(df["corporacion"] == "Presidencia",
                    df["candidato"], df["partido"])


def _especiales(df, keys):
    esp = df[df["es_voto_especial"]]
    piv = (esp.assign(tipo=esp["candidato_codigo"].map(
        {"996": "blancos", "997": "nulos", "998": "no_marcados"}))
        .groupby(keys + ["tipo"])["votos"].sum().unstack("tipo", fill_value=0))
    for c in ["blancos", "nulos", "no_marcados"]:
        if c not in piv:
            piv[c] = 0
    return piv[["blancos", "nulos", "no_marcados"]].reset_index()


def resultados(df, level_cols):
    """Tabla larga: votos por unidad y % sobre validos, por territorio y seg."""
    keys = level_cols + SEG
    cand = df[~df["es_voto_especial"]].copy()
    cand["unidad"] = unidad_col(cand)
    r = cand.groupby(keys + ["unidad"], observed=True)["votos"].sum().reset_index()
    esp = _especiales(df, keys)
    cand_tot = cand.groupby(keys, observed=True)["votos"].sum().rename(
        "votos_candidatos").reset_index()
    r = r.merge(cand_tot, on=keys).merge(esp, on=keys, how="left").fillna(
        {"blancos": 0})
    r["validos"] = r["votos_candidatos"] + r["blancos"]
    r["pct_validos"] = np.where(r["validos"] > 0,
                                r["votos"] / r["validos"] * 100, np.nan)
    return r.drop(columns=["nulos", "no_marcados"], errors="ignore")


def competencia(df, level_cols):
    """Una fila por territorio×seg con ganador, margen, HHI, NEP, fragmentacion."""
    keys = level_cols + SEG
    cand = df[~df["es_voto_especial"]].copy()
    cand["unidad"] = unidad_col(cand)
    u = cand.groupby(keys + ["unidad"], observed=True)["votos"].sum().reset_index()
    tot = u.groupby(keys, observed=True)["votos"].sum().rename("cand_total")
    u = u.join(tot, on=keys)
    u["s"] = np.where(u["cand_total"] > 0, u["votos"] / u["cand_total"], 0)
    hhi = u.assign(s2=u["s"] ** 2).groupby(keys, observed=True)["s2"].sum().rename("hhi")
    nunid = u.groupby(keys, observed=True)["unidad"].nunique().rename("n_unidades")

    us = u.sort_values("votos", ascending=False)
    g1 = us.groupby(keys, observed=True).head(1).set_index(keys)[["unidad", "votos"]]
    g1 = g1.rename(columns={"unidad": "ganador", "votos": "votos_ganador"})
    g2 = (us.groupby(keys, observed=True).nth(1).set_index(keys)[["unidad", "votos"]]
          .rename(columns={"unidad": "segundo", "votos": "votos_segundo"}))

    esp = _especiales(df, keys).set_index(keys)
    # base = union de territorios con candidatos y territorios con solo especiales
    # (asi NO se pierden votos especiales de territorios sin candidatos)
    base = tot.index.union(esp.index)
    out = (pd.DataFrame(index=base)
           .join(tot.rename("cand_total")).join(hhi).join(nunid)
           .join(g1).join(g2).join(esp).reset_index())
    out["cand_total"] = out["cand_total"].fillna(0)
    out["hhi"] = out["hhi"].fillna(0)
    out["n_unidades"] = out["n_unidades"].fillna(0).astype(int)
    out["votos_ganador"] = out["votos_ganador"].fillna(0)
    out["ganador"] = out["ganador"].fillna("")
    for c in ["blancos", "nulos", "no_marcados", "votos_segundo"]:
        out[c] = out[c].fillna(0)
    out["segundo"] = out["segundo"].fillna("")
    out["validos"] = out["cand_total"] + out["blancos"]
    out["total_marcas"] = out["validos"] + out["nulos"] + out["no_marcados"]
    out["margen_abs"] = out["votos_ganador"] - out["votos_segundo"]
    out["margen_pp"] = np.where(out["validos"] > 0,
                                out["margen_abs"] / out["validos"] * 100, np.nan)
    out["top1_pp"] = np.where(out["validos"] > 0,
                              out["votos_ganador"] / out["validos"] * 100, np.nan)
    out["blanco_pp"] = np.where(out["validos"] > 0,
                                out["blancos"] / out["validos"] * 100, np.nan)
    out["nep"] = np.where(out["hhi"] > 0, 1 / out["hhi"], np.nan)
    out["fragmentacion"] = 1 - out["hhi"]
    return out
