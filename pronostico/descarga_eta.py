"""Descarga de los NetCDF del modelo ETA desde el FTP de SENAMHI."""
import getpass
import os
from datetime import datetime, timedelta
from ftplib import FTP
from pathlib import Path

from . import config

VARIABLES = ("pp", "tn", "tx")
CORRECCIONES = ("eqm", "scal")


def fechas_descarga(hoy: datetime, dias_atras: int = config.DIAS_DESCARGA_ETA) -> list:
    """Fechas YYYYMMDD desde `dias_atras` días antes de hoy hasta hoy."""
    return [(hoy + timedelta(days=i)).strftime("%Y%m%d") for i in range(-dias_atras, 1)]


def nombres_archivos(fechas: list, correccion: str) -> list:
    return [f"{v}_{f}_{correccion}.nc" for f in fechas for v in VARIABLES]


def pedir_credenciales(usuario=None, password=None, anonimo=False):
    """Completa usuario/contraseña: usa los valores dados y pregunta por los que falten."""
    if anonimo:
        return "anonymous", password or ""
    if usuario is None:
        usuario = input("Usuario FTP (Enter = 'anonymous'): ").strip() or "anonymous"
    if password is None:
        password = getpass.getpass("Contraseña FTP (Enter para dejarla en blanco): ")
    return usuario, password


def _entrar(ftp: FTP, inicio: str, ruta: str) -> None:
    """Entra a `ruta` probando primero relativa al directorio de login y luego absoluta."""
    errores = []
    for candidata in (ruta, f"{inicio.rstrip('/')}/{ruta}", f"/{ruta}"):
        try:
            ftp.cwd(inicio)  # siempre partir del directorio de login
            ftp.cwd(candidata)
            return
        except Exception as e:
            errores.append(f"  {candidata!r}: {e}")
    raise RuntimeError(
        f"No se pudo entrar a '{ruta}' (directorio de login: {inicio}). Intentos:\n"
        + "\n".join(errores)
    )


def _descargar_archivo(ftp: FTP, nombre: str, destino: Path) -> bool:
    """Descarga a un .part y renombra solo si fue exitoso (no deja archivos vacíos)."""
    parcial = destino.with_suffix(destino.suffix + ".part")
    try:
        with open(parcial, "wb") as f:
            ftp.retrbinary(f"RETR {nombre}", f.write)
        os.replace(parcial, destino)
        return True
    except Exception:
        if parcial.exists():
            parcial.unlink()
        return False


def descargar_eta(
    destino: Path = config.DIR_ETA,
    host: str = config.FTP_HOST,
    directorio: str = config.FTP_DIR,
    usuario: str = config.FTP_USUARIO,
    password: str = config.FTP_PASSWORD,
    dias_atras: int = config.DIAS_DESCARGA_ETA,
    anonimo: bool = False,
) -> None:
    usuario, password = pedir_credenciales(usuario, password, anonimo)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)

    fechas = fechas_descarga(datetime.now(), dias_atras)
    print(f"Descargando desde {fechas[0]} hasta {fechas[-1]} ({len(fechas)} días)")
    print(f"Destino: {destino}/")

    with FTP(host, timeout=60) as ftp:
        print(f"Conectando a {host}...")
        ftp.login(user=usuario, passwd=password)
        print("Conexión exitosa.")
        inicio = ftp.pwd()

        for correccion in CORRECCIONES:
            print(f"\n--- Carpeta '{correccion}' ---")
            _entrar(ftp, inicio, f"{directorio}/{correccion}")
            for nombre in nombres_archivos(fechas, correccion):
                if _descargar_archivo(ftp, nombre, destino / nombre):
                    print(f" [OK]      {nombre}")
                else:
                    print(f" [OMITIDO] {nombre} (no encontrado)")

    print("\nProceso finalizado.")
