"""Línea de comandos: python -m pronostico <comando>"""
import argparse
from pathlib import Path

from . import config


def main(argv=None):
    p = argparse.ArgumentParser(prog="pronostico", description=__doc__)
    sub = p.add_subparsers(dest="comando", required=True)

    d = sub.add_parser("descargar", help="Descarga los NetCDF del modelo ETA desde el FTP de SENAMHI")
    d.add_argument("--destino", type=Path, default=config.DIR_ETA)
    d.add_argument("--usuario", default=config.FTP_USUARIO)
    d.add_argument("--password", default=config.FTP_PASSWORD)
    d.add_argument("--anonimo", action="store_true", help="usa 'anonymous' sin preguntar")
    d.add_argument("--dias", type=int, default=config.DIAS_DESCARGA_ETA, help="días hacia atrás")

    e = sub.add_parser("estaciones", help="Gráficos de estaciones: observado + ETA + ECMWF + GFS")
    e.add_argument("--coordenadas", type=Path, default=config.CSV_COORDENADAS)
    e.add_argument("--salida", type=Path, default=config.DIR_GRAFICOS)
    e.add_argument("--unir-con", type=str.lower, choices=config.MODELOS_DISPONIBLES, metavar="MODELO",
                   help="pasado solo con observaciones; la línea observada (negra) continúa con el "
                        "pronóstico de este modelo (los demás no se grafican): %s" % ", ".join(config.MODELOS_DISPONIBLES))
    e.add_argument("--pasado-del-modelo", action="store_true",
                   help="con --unir-con: el pasado también sale de ese modelo, sin observaciones")

    m = sub.add_parser("modelos", help="Gráficos solo de modelos para puntos de interés")
    m.add_argument("--puntos", type=Path, default=config.CSV_PUNTOS)
    m.add_argument("--salida", type=Path, default=config.DIR_GRAFICOS_MODELOS)
    m.add_argument("--modelos", nargs="+", type=str.lower, choices=config.MODELOS_DISPONIBLES,
                   default=list(config.MODELOS_DISPONIBLES), metavar="MODELO",
                   help="uno o más de: %s (por defecto, todos)" % ", ".join(config.MODELOS_DISPONIBLES))

    for sp in (e, m):
        sp.add_argument("--estilo", choices=config.ESTILOS_GRAFICO, default="clasico",
                        help="diseño de los gráficos (por defecto: clasico)")
        sp.add_argument("--mapa", action="store_true",
                        help="genera además un mapa con las ubicaciones utilizadas")

    a = p.parse_args(argv)
    if a.comando == "estaciones" and a.pasado_del_modelo and not a.unir_con:
        p.error("--pasado-del-modelo requiere --unir-con MODELO")

    if a.comando == "descargar":
        from .descarga_eta import descargar_eta
        descargar_eta(destino=a.destino, usuario=a.usuario, password=a.password,
                       dias_atras=a.dias, anonimo=a.anonimo)
    elif a.comando == "estaciones":
        from .monitoreo import ejecutar_estaciones
        ejecutar_estaciones(a.coordenadas, a.salida, a.unir_con, a.pasado_del_modelo, a.estilo, a.mapa)
    else:
        from .monitoreo import ejecutar_modelos
        ejecutar_modelos(a.puntos, a.salida, a.modelos, a.estilo, a.mapa)


if __name__ == "__main__":
    main()
