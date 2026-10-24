# Monitoreo de pronósticos meteorológicos

Compara el pronóstico del modelo **ETA (SENAMHI, corrección eqm)** con **ECMWF/IFS** y **GFS**
(vía [Open-Meteo](https://open-meteo.com/)) y, opcionalmente, con las **observaciones** de estaciones
de los últimos 3 días. Genera gráficos de **T. máxima**, **T. mínima** y **precipitación** (acumulada de 12 a 12 UTC)
para una ventana de 3 días pasados + 6 días de pronóstico.

## Estructura

```
.
├── pronostico/
│   ├── config.py          # rutas, URLs, parámetros
│   ├── ventana.py         # ventana temporal (pasado/futuro)
│   ├── descarga_eta.py    # descarga NetCDF del FTP de SENAMHI
│   ├── eta.py             # lectura del ETA en un punto (xarray)
│   ├── openmeteo.py       # ECMWF / GFS vía Open-Meteo
│   ├── observaciones.py   # CSV de estaciones automáticas/convencionales + metadatos
│   ├── graficos.py        # gráficos estilo clásico (matplotlib)
│   ├── graficos_modernos.py  # gráficos estilo moderno (--estilo moderno)
│   ├── graficos_boletin.py   # gráficos estilo boletín (--estilo boletin)
│   ├── mapa.py            # mapa de ubicación de estaciones/puntos (--mapa, cartopy)
│   ├── monitoreo.py       # orquestación de los dos modos
│   └── cli.py             # línea de comandos
├── datos/                 # entradas (ver datos/README.md)
├── eta/                   # NetCDF descargados (ignorado por git)
├── graficos/              # salidas modo estaciones (ignorado por git)
├── graficos_modelos/      # salidas modo modelos (ignorado por git)
└── tests/
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
# 1) Descargar los NetCDF del ETA (pide usuario y contraseña)
python -m pronostico descargar

# 2a) Estaciones: observado + ETA + ECMWF + GFS
python -m pronostico estaciones

# 2a') Temperaturas: pasado solo con observaciones; la línea observada (negra) continúa con el
#      pronóstico de un modelo; los demás modelos no se grafican (la precipitación usa barras)
python -m pronostico estaciones --unir-con ecmwf      # o eta, gfs
python -m pronostico estaciones --unir-con eta --pasado-del-modelo   # pasado también del modelo, sin observaciones

# Cualquiera de los dos modos con otro diseño (los PNG llevan el sufijo _moderno / _boletin)
python -m pronostico estaciones --estilo moderno
python -m pronostico estaciones --estilo boletin      # para boletines: 300 ppp, letra grande, legible en B/N

# Añadir un mapa con las estaciones/puntos utilizados (requiere cartopy)
python -m pronostico estaciones --mapa

# 2b) Solo modelos para puntos arbitrarios (datos/puntos_interes.csv)
python -m pronostico modelos
```

Al descargar, el programa pide el usuario (Enter = `anonymous`) y la contraseña (oculta; puede quedar en blanco).
Para no responder cada vez: variables de entorno `SENAMHI_FTP_USER` y `SENAMHI_FTP_PASS`, las opciones
`--usuario` / `--password`, o `--anonimo`. Usa `python -m pronostico <comando> --help` para ver más opciones.

Los gráficos se guardan en `graficos/<dd-mm-YYYY>/<VAR>_<lugar>_<dd-mm-YYYY>.png`.

## Datos de entrada

Ver [`datos/README.md`](datos/README.md) para los formatos esperados. Los datos reales no se versionan.

## Pruebas

```bash
pip install pytest
pytest
```