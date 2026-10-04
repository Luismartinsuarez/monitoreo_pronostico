"""Lectura de observaciones (estaciones automáticas `a_` y convencionales `c_`) y metadatos."""
import re
from pathlib import Path

import pandas as pd

from . import config
from .ventana import Ventana


def _leer_convencional(ruta: Path) -> pd.DataFrame:
    """Lee un CSV convencional detectando las filas de datos por su fecha (AAAA-MM-DD),
    sin depender del número de líneas de cabecera."""
    filas = []
    with open(ruta, encoding="utf-8-sig") as f:
        for linea in f:
            partes = [p.strip() for p in linea.strip().split(",")]
            if len(partes) >= 5 and re.match(r"^\d{4}-\d{2}-\d{2}$", partes[0]):
                filas.append(partes[:5])
    df = pd.DataFrame(filas, columns=["Fecha", "T_Max_Obs", "T_Min_Obs", "HR", "PP_Obs"])
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%Y-%m-%d")
    for c in ("T_Max_Obs", "T_Min_Obs"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["PP_Obs"] = pd.to_numeric(df["PP_Obs"].replace({"T": 0, "S/D": pd.NA}), errors="coerce")
    return df


def cargar_observaciones(lugar: str, ventana: Ventana, dir_datos: Path = config.DIR_DATOS) -> pd.DataFrame:
    """Devuelve Fecha, T_Max_Obs, T_Min_Obs, PP_Obs para los días pasados (vacío si no hay archivo)."""
    dir_datos = Path(dir_datos)
    auto = dir_datos / f"a_{lugar}.csv"
    conv = dir_datos / f"c_{lugar}.csv"

    if auto.exists():
        df = pd.read_csv(auto, skiprows=5)
        df["Fecha"] = pd.to_datetime(df["AÑO / MES / DÍA"], format="%Y/%m/%d")
        df["TEMPERATURA (°C)"] = pd.to_numeric(df["TEMPERATURA (°C)"], errors="coerce")
        df["PRECIPITACIÓN (mm/hora)"] = pd.to_numeric(df["PRECIPITACIÓN (mm/hora)"], errors="coerce")
        agrupado = df.groupby("Fecha").agg(
            T_Max_Obs=("TEMPERATURA (°C)", "max"),
            T_Min_Obs=("TEMPERATURA (°C)", "min"),
            PP_Obs=("PRECIPITACIÓN (mm/hora)", "sum"),
        ).reset_index()
        return agrupado[agrupado["Fecha"].isin(ventana.fechas_pasadas)]

    if conv.exists():
        df = _leer_convencional(conv)
        return df[df["Fecha"].isin(ventana.fechas_pasadas)].copy()

    print(f"  -> Aviso: no hay CSV de observaciones para {lugar}. Solo modelos.")
    return pd.DataFrame()


def cargar_metadata(ruta: Path = config.CSV_METADATA) -> pd.DataFrame:
    try:
        df = pd.read_csv(ruta, sep=None, engine="python", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        print("Metadatos cargados. Columnas:", df.columns.tolist())
        return df
    except Exception as e:
        print(f"Aviso: no se pudo cargar los metadatos ({e}).")
        return pd.DataFrame()


def texto_metadata(df_meta: pd.DataFrame, lugar: str, lat, lon) -> str:
    if df_meta.empty or "Lugar" not in df_meta.columns:
        return ""
    info = df_meta[df_meta["Lugar"].astype(str).str.strip().str.lower() == lugar.lower()]
    if info.empty:
        print(f"  -> Aviso: '{lugar}' no está en la tabla de metadatos.")
        return ""
    r = info.iloc[0]
    return (f"Lat: {r.get('Latitud', lat)} | Lon: {r.get('Longitud', lon)} | "
            f"Alt: {r.get('Altitud', 'N/D')} m | Dist: {r.get('Dist', 'N/D')} | "
            f"Prov: {r.get('Prov', 'N/D')} | Dep: {r.get('Dep', 'N/D')} | Tipo: {r.get('Tipo', 'N/D')}")
