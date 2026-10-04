"""Configuración central del proyecto. Ajusta aquí rutas y parámetros."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Carpetas
DIR_DATOS = RAIZ / "datos"
DIR_ETA = RAIZ / "eta"
DIR_GRAFICOS = RAIZ / "graficos"
DIR_GRAFICOS_MODELOS = RAIZ / "graficos_modelos"

# Archivos de entrada
CSV_COORDENADAS = DIR_DATOS / "coordenadas_convertidas.csv"   # Lugar, Latitud, Longitud
CSV_METADATA = DIR_DATOS / "metadata_estaciones.csv"
CSV_PUNTOS = DIR_DATOS / "puntos_interes.csv"                 # Lugar, Latitud, Longitud

# Ventana temporal
DIAS_PASADOS = 3
DIAS_FUTUROS = 6
DIAS_DESCARGA_ETA = 4  # cuántos días hacia atrás se descargan del FTP

# Modelos disponibles
MODELOS_DISPONIBLES = ("eta", "ecmwf", "gfs")

# Open-Meteo
URL_ECMWF = "https://api.open-meteo.com/v1/ecmwf"
URL_GFS = "https://api.open-meteo.com/v1/gfs"
TIMEOUT_HTTP = 30

# FTP SENAMHI (si no se definen, el programa las pide por consola)
FTP_HOST = "ftp.senamhi.gob.pe"
FTP_DIR = "HIDROLOGIA/ETA22_grilla"
FTP_USUARIO = os.getenv("SENAMHI_FTP_USER")  # None -> se pregunta
FTP_PASSWORD = os.getenv("SENAMHI_FTP_PASS")  # None -> se pregunta
