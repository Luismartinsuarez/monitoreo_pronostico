from datetime import datetime

import pandas as pd

from pronostico.descarga_eta import fechas_descarga, nombres_archivos
from pronostico.graficos import plotar_grafico
from pronostico.ventana import Ventana


def test_nombres_archivos():
    nombres = nombres_archivos(["20260101"], "eqm")
    assert nombres == ["pp_20260101_eqm.nc", "tn_20260101_eqm.nc", "tx_20260101_eqm.nc"]


def test_fechas_descarga():
    f = fechas_descarga(datetime(2026, 1, 10), 4)
    assert f[0] == "20260106" and f[-1] == "20260110" and len(f) == 5


def test_ventana():
    v = Ventana(hoy=datetime(2026, 1, 10, 15))
    assert v.fecha_inicio == "2026-01-07"
    assert v.fecha_fin == "2026-01-16"
    assert len(v.fechas_pasadas) == 3


def test_grafico_smoke(tmp_path):
    v = Ventana(hoy=datetime(2026, 1, 10))
    fechas = pd.date_range(v.inicio, v.fin)
    df_eta = pd.DataFrame({"Fecha": fechas, "ETA": range(len(fechas))})
    df_ec = pd.DataFrame({"Fecha": fechas, "PP_ECMWF": range(len(fechas))})
    df_gf = pd.DataFrame({"Fecha": fechas, "PP_GFS": range(len(fechas))})
    ruta = plotar_grafico(v, "PP", "lima", df_eta, df_ec, df_gf, tmp_path)
    assert ruta.exists()
