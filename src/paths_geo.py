"""Rutas resueltas de cartografia (los ZIP originales usaron subcarpetas y, en
puestos/perimetro nuevo, un backslash literal en el nombre)."""
import glob
import os

from utils import RAW


def find(name):
    hits = glob.glob(os.path.join(RAW, "**", "*" + name), recursive=True)
    if not hits:
        raise FileNotFoundError(name)
    return hits[0]


PATHS = {
    "puestos": find("Puestos_votacion.shp"),
    "comunas": find("Comunas.shp"),
    "corregimientos": find("Corregimientos.shp"),
    "perimetro": find("Perimetro_municipal.shp"),
    "mpios_dane": find("MGN_ANM_MPIOS.shp"),
    "dptos_dane": find("MGN_ANM_DPTOS.shp"),
}
CRS_ORIG_CALI = "EPSG:6249"
CRS_ORIG_DANE = "EPSG:4686"
CRS_WEB = "EPSG:4326"
