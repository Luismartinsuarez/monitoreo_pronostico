"""Lectura del modelo ETA (NetCDF) para un punto (lat, lon)."""
from datetime import timedelta
from pathlib import Path

import pandas as pd
import xarray as xr

from . import config
from .ventana import Ventana


def serie_eta(ventana: Ventana, prefijo: str, var_nc: str, lat: float, lon: float,
              dir_eta: Path = config.DIR_ETA) -> pd.DataFrame:
    """Serie diaria ETA (corrección eqm): primer paso de cada corrida pasada + corrida de hoy."""
    dir_eta = Path(dir_eta)
    fechas, valores = [], []

    for fecha in ventana.fechas_pasadas:
        archivo = dir_eta / f"{prefijo}_{fecha.strftime('%Y%m%d')}_eqm.nc"
        if archivo.exists():
            with xr.open_dataset(archivo) as ds:
                punto = ds.sel(latitude=lat, longitude=lon, method="nearest")
                valores.append(float(punto[var_nc].isel(z=0).values))
                fechas.append(fecha)

    archivo_hoy = dir_eta / f"{prefijo}_{ventana.hoy.strftime('%Y%m%d')}_eqm.nc"
    if archivo_hoy.exists():
        with xr.open_dataset(archivo_hoy) as ds:
            punto = ds.sel(latitude=lat, longitude=lon, method="nearest")
            tiempos = pd.to_datetime(punto["z"].values).normalize()
            vals = punto[var_nc].values
            mask = (tiempos >= ventana.hoy_date) & (tiempos <= ventana.hoy_date + timedelta(days=ventana.dias_futuros))
            fechas.extend(tiempos[mask])
            valores.extend(vals[mask])

    df = pd.DataFrame({"Fecha": fechas, "ETA": valores})
    return df.drop_duplicates(subset=["Fecha"]).sort_values("Fecha")
