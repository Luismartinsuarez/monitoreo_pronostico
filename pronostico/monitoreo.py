"""Orquestación: obtiene datos de todos los orígenes y genera los gráficos por lugar."""
from pathlib import Path

import pandas as pd

from . import config, eta, graficos, graficos_boletin, graficos_modernos, observaciones, openmeteo
from .ventana import Ventana

MODULOS_ESTILO = {"clasico": graficos, "moderno": graficos_modernos, "boletin": graficos_boletin}

PUNTOS_POR_DEFECTO = pd.DataFrame([
    {"Lugar": "Lima", "Latitud": -12.0464, "Longitud": -77.0428},
    {"Lugar": "Cusco", "Latitud": -13.5226, "Longitud": -71.9673},
])


def validar_modelos(modelos) -> tuple:
    """Normaliza y valida la lista de modelos (eta, ecmwf, gfs)."""
    if not modelos:
        return tuple(config.MODELOS_DISPONIBLES)
    elegidos = []
    for m in modelos:
        m = str(m).strip().lower()
        if m not in config.MODELOS_DISPONIBLES:
            raise ValueError(f"Modelo '{m}' no válido. Opciones: {', '.join(config.MODELOS_DISPONIBLES)}")
        if m not in elegidos:
            elegidos.append(m)
    return tuple(elegidos)


def _procesar_lugar(ventana, lugar, lat, lon, dir_salida, con_observaciones,
                    prefijo_titulo="Estación", metadata_str="",
                    modelos=config.MODELOS_DISPONIBLES, sufijo_archivo="", unir_con=None,
                    pasado_del_modelo=False, estilo="clasico"):
    modelos = validar_modelos(modelos)
    modulo = MODULOS_ESTILO[estilo]
    if estilo != "clasico":
        # Sufijo para no pisar los gráficos de los otros estilos
        sufijo_archivo = "_".join(x for x in (sufijo_archivo, estilo) if x)
    vacio = pd.DataFrame()
    df_obs = observaciones.cargar_observaciones(lugar, ventana) if con_observaciones else None

    if "eta" in modelos:
        eta_tx = eta.serie_eta(ventana, "tx", "bc_tx", lat, lon)
        eta_tn = eta.serie_eta(ventana, "tn", "bc_tn", lat, lon)
        eta_pp = eta.serie_eta(ventana, "pp", "bc_pp", lat, lon)
    else:
        eta_tx = eta_tn = eta_pp = vacio

    ini, fin = ventana.fecha_inicio, ventana.fecha_fin
    if "ecmwf" in modelos:
        ec_t = openmeteo.temperaturas(config.URL_ECMWF, lat, lon, ini, fin, "ECMWF")
        ec_p = openmeteo.precipitacion(config.URL_ECMWF, lat, lon, ini, fin, "ECMWF")
    else:
        ec_t = ec_p = vacio
    if "gfs" in modelos:
        gf_t = openmeteo.temperaturas(config.URL_GFS, lat, lon, ini, fin, "GFS")
        gf_p = openmeteo.precipitacion(config.URL_GFS, lat, lon, ini, fin, "GFS")
    else:
        gf_t = gf_p = vacio

    kw = dict(dir_salida=dir_salida, df_obs=df_obs, metadata_str=metadata_str,
              prefijo_titulo=prefijo_titulo, sufijo_archivo=sufijo_archivo, unir_con=unir_con,
              pasado_del_modelo=pasado_del_modelo)
    modulo.plotar_grafico(ventana, "T_Max", lugar, eta_tx, ec_t, gf_t, **kw)
    modulo.plotar_grafico(ventana, "T_Min", lugar, eta_tn, ec_t, gf_t, **kw)
    modulo.plotar_grafico(ventana, "PP", lugar, eta_pp, ec_p, gf_p, **kw)


def _generar_mapa(puntos, dir_salida, ventana, meta, titulo, nombre):
    # Importación diferida: cartopy solo hace falta si se pide el mapa
    try:
        from .mapa import generar_mapa
    except ImportError as e:
        print(f"  -> Aviso: no se puede generar el mapa ({e}). Instala cartopy.")
        return
    ruta = generar_mapa(puntos, dir_salida, ventana, meta, titulo, nombre)
    print(f"Mapa generado: {ruta}")


def ejecutar_estaciones(csv_coordenadas: Path = config.CSV_COORDENADAS,
                        dir_salida: Path = config.DIR_GRAFICOS,
                        unir_con: str = None, pasado_del_modelo: bool = False,
                        estilo: str = "clasico", mapa: bool = False) -> None:
    """Modo 1: estaciones con observaciones + modelos.

    Con `unir_con` (eta/ecmwf/gfs) el pasado muestra solo observaciones y la línea
    observada continúa, en negro, con el pronóstico de ese modelo; los demás modelos
    no se grafican. Con `pasado_del_modelo` el pasado también sale de ese modelo (sin
    observaciones). Con `mapa`, genera además un mapa de las estaciones."""
    if pasado_del_modelo and not unir_con:
        raise ValueError("pasado_del_modelo requiere indicar unir_con")
    modelos = config.MODELOS_DISPONIBLES
    if unir_con:
        modelos = (unir_con,) = validar_modelos([unir_con])
        if pasado_del_modelo:
            print(f"Pasado y pronóstico del modelo: {unir_con.upper()}")
        else:
            print(f"Observado unido al pronóstico de: {unir_con.upper()}")
    # Sufijo para no pisar los gráficos de los otros modos
    if not unir_con:
        sufijo = ""
    elif pasado_del_modelo:
        sufijo = f"solo-{unir_con}"
    else:
        sufijo = f"obs-{unir_con}"
    ventana = Ventana()
    coords = pd.read_csv(csv_coordenadas)
    meta = observaciones.cargar_metadata()
    if mapa:
        _generar_mapa(coords, dir_salida, ventana, meta, "Estaciones utilizadas", "mapa_estaciones")
    for _, row in coords.iterrows():
        lugar = str(row["Lugar"]).strip()
        lat, lon = row["Latitud"], row["Longitud"]
        print(f"\n--- Procesando estación: {lugar} ---")
        texto = observaciones.texto_metadata(meta, lugar, lat, lon)
        _procesar_lugar(ventana, lugar, lat, lon, dir_salida, not pasado_del_modelo,
                        prefijo_titulo="Estación", metadata_str=texto,
                        modelos=modelos, sufijo_archivo=sufijo, unir_con=unir_con,
                        pasado_del_modelo=pasado_del_modelo, estilo=estilo)
    print(f"\nConcluido. Revisa la carpeta '{dir_salida}'.")


def ejecutar_modelos(csv_puntos: Path = config.CSV_PUNTOS,
                     dir_salida: Path = config.DIR_GRAFICOS_MODELOS,
                     modelos=None, estilo: str = "clasico", mapa: bool = False) -> None:
    """Modo 2: solo modelos (a elección) para puntos arbitrarios, sin observaciones.
    Con `mapa`, genera además un mapa de los puntos."""
    modelos = validar_modelos(modelos)
    # Si no se usan todos, se añade sufijo al archivo para no pisar gráficos de otras selecciones
    sufijo = "" if set(modelos) == set(config.MODELOS_DISPONIBLES) else "-".join(modelos)
    print(f"Modelos seleccionados: {', '.join(m.upper() for m in modelos)}")
    ventana = Ventana()
    csv_puntos = Path(csv_puntos)
    puntos = pd.read_csv(csv_puntos) if csv_puntos.exists() else PUNTOS_POR_DEFECTO
    if mapa:
        _generar_mapa(puntos, dir_salida, ventana, None, "Puntos de interés", "mapa_puntos")
    for _, row in puntos.iterrows():
        lugar = str(row["Lugar"]).strip()
        lat, lon = row["Latitud"], row["Longitud"]
        print(f"\n--- Procesando ubicación: {lugar} ---")
        _procesar_lugar(ventana, lugar, lat, lon, dir_salida, False,
                        prefijo_titulo="Ubicación", metadata_str=f"Lat: {lat} | Lon: {lon}",
                        modelos=modelos, sufijo_archivo=sufijo, estilo=estilo)
    print(f"\nConcluido. Revisa la carpeta '{dir_salida}'.")
