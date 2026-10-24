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


def test_series_unidas_obs_modelo():
    from pronostico.graficos import _series
    v = Ventana(hoy=datetime(2026, 1, 10))
    fechas = pd.date_range(v.inicio, v.fin)
    obs = pd.DataFrame({"Fecha": v.fechas_pasadas, "T_Max_Obs": [20, 21, 22]})
    eta = pd.DataFrame({"Fecha": fechas, "ETA": range(len(fechas))})
    vacio = pd.DataFrame()
    series = _series("T_Max", obs, eta, vacio, vacio, v, unir_con="eta")
    assert len(series) == 1 and series[0]["color"] == "black"
    unida = series[0]["df"]
    # 3 días observados + hoy y 6 días de pronóstico del ETA
    assert len(unida) == 3 + 7
    assert list(unida["valor"][:3]) == [20, 21, 22]


def test_unir_no_afecta_precipitacion():
    from pronostico.graficos import _series
    v = Ventana(hoy=datetime(2026, 1, 10))
    obs = pd.DataFrame({"Fecha": v.fechas_pasadas, "PP_Obs": [1, 0, 2]})
    eta = pd.DataFrame({"Fecha": pd.date_range(v.inicio, v.fin), "ETA": 1.0})
    vacio = pd.DataFrame()
    series = _series("PP", obs, eta, vacio, vacio, v, unir_con="eta")
    assert [s["lbl_barra"] for s in series] == ["Observado", "ETA/Senamhi"]


def test_series_pasado_del_modelo():
    from pronostico.graficos import _series
    v = Ventana(hoy=datetime(2026, 1, 10))
    fechas = pd.date_range(v.inicio, v.fin)
    eta = pd.DataFrame({"Fecha": fechas, "ETA": range(len(fechas))})
    vacio = pd.DataFrame()
    series = _series("T_Max", None, eta, vacio, vacio, v, unir_con="eta", pasado_del_modelo=True)
    assert len(series) == 1 and series[0]["color"] == "black"
    assert list(series[0]["df"]["valor"]) == list(range(len(fechas)))


def test_grafico_moderno_smoke(tmp_path):
    from pronostico import graficos_boletin, graficos_modernos
    for modulo in (graficos_modernos, graficos_boletin):
        _smoke_estilo(modulo, tmp_path)


def _smoke_estilo(graficos_modernos, tmp_path):
    v = Ventana(hoy=datetime(2026, 1, 10))
    fechas = pd.date_range(v.inicio, v.fin)
    obs = pd.DataFrame({"Fecha": v.fechas_pasadas, "T_Max_Obs": [20, 21, 22], "PP_Obs": [0, 1, 2]})
    df_eta = pd.DataFrame({"Fecha": fechas, "ETA": range(len(fechas))})
    df_ec = pd.DataFrame({"Fecha": fechas, "T_Max_ECMWF": range(len(fechas)),
                          "PP_ECMWF": range(len(fechas))})
    vacio = pd.DataFrame()
    for var in ("T_Max", "PP"):
        ruta = graficos_modernos.plotar_grafico(v, var, "lima", df_eta, df_ec, vacio, tmp_path,
                                                df_obs=obs)
        assert ruta.exists()
    ruta = graficos_modernos.plotar_grafico(v, "T_Max", "lima", df_eta, df_ec, vacio, tmp_path,
                                            df_obs=obs, unir_con="eta", sufijo_archivo="obs-eta")
    assert ruta.exists()


def test_mapa_smoke(tmp_path):
    import pytest
    pytest.importorskip("cartopy")
    from pronostico.mapa import generar_mapa
    puntos = pd.DataFrame({"Lugar": ["a", "b"], "Latitud": [-12.0, -12.1], "Longitud": [-77.0, -76.9]})
    meta = pd.DataFrame({"Lugar": ["a"], "Altitud": [150], "Dep": ["Lima"], "Tipo": ["Automática"]})
    ruta = generar_mapa(puntos, tmp_path, Ventana(hoy=datetime(2026, 1, 10)), meta)
    assert ruta.exists()
