"""Extracción de pronósticos ECMWF/IFS y GFS vía Open-Meteo."""
import pandas as pd
import requests

from . import config


def _get(url: str, params: dict):
    try:
        r = requests.get(url, params=params, timeout=config.TIMEOUT_HTTP)
        if r.status_code == 200:
            return r.json()
        print(f"  -> Aviso: {url} respondió {r.status_code}")
    except requests.RequestException as e:
        print(f"  -> Aviso: error de conexión con {url}: {e}")
    return None


def temperaturas(url: str, lat: float, lon: float, inicio: str, fin: str, sufijo: str) -> pd.DataFrame:
    """T_Max / T_Min diarias. Columnas: Fecha, T_Max_<sufijo>, T_Min_<sufijo>."""
    datos = _get(url, {
        "latitude": lat, "longitude": lon,
        "start_date": inicio, "end_date": fin,
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "auto",
    })
    cols = ["Fecha", f"T_Max_{sufijo}", f"T_Min_{sufijo}"]
    if not datos:
        return pd.DataFrame(columns=cols)
    d = datos["daily"]
    return pd.DataFrame({
        cols[0]: pd.to_datetime(d["time"]),
        cols[1]: d["temperature_2m_max"],
        cols[2]: d["temperature_2m_min"],
    })


def precipitacion(url: str, lat: float, lon: float, inicio: str, fin: str, sufijo: str) -> pd.DataFrame:
    """PP diaria acumulada de 12 a 12 UTC. Columnas: Fecha, PP_<sufijo>."""
    col = f"PP_{sufijo}"
    inicio_req = (pd.to_datetime(inicio) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    fin_req = (pd.to_datetime(fin) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    datos = _get(url, {
        "latitude": lat, "longitude": lon,
        "start_date": inicio_req, "end_date": fin_req,
        "hourly": ["precipitation"],
        "timezone": "GMT",
    })
    if not datos:
        return pd.DataFrame(columns=["Fecha", col])

    horario = pd.DataFrame({
        "Hora_UTC": pd.to_datetime(datos["hourly"]["time"]),
        "PP_Hora": datos["hourly"]["precipitation"],
    })
    # Desfase de 12 h para que el día comience a las 12 UTC
    horario["Fecha"] = (horario["Hora_UTC"] - pd.Timedelta(hours=12)).dt.normalize()
    diario = horario.groupby("Fecha")["PP_Hora"].sum().reset_index().rename(columns={"PP_Hora": col})
    mask = (diario["Fecha"] >= pd.to_datetime(inicio)) & (diario["Fecha"] <= pd.to_datetime(fin))
    return diario[mask].reset_index(drop=True)
