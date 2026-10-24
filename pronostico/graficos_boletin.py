"""Gráficos con estilo boletín: pensados para insertarse en un boletín (impreso o PDF).

Fondo blanco, cabecera con barra de color, formato compacto y 300 ppp. Cada serie se
distingue también por marcador, tipo de línea o trama, para que se lea en blanco y negro.

Usa las mismas series que los otros estilos (`graficos._series`), así que respeta
`unir_con` y `pasado_del_modelo`.
"""
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from .graficos import _series
from .graficos_modernos import DIAS_SEMANA, NOMBRE_MODELO, _modelo_de
from .ventana import Ventana

BLANCO = "#ffffff"
CABECERA = "#184f95"
FRANJA_PASADO = "#eef0f3"
TINTA = "#1a1a1a"
TINTA_SECUNDARIA = "#4a4a4a"
TINTA_TENUE = "#7a7a7a"
REJILLA = "#dcdfe3"
# Color, marcador, tipo de línea y trama de cada serie (legibles también en gris)
ESTILO_MODELO = {
    "ETA": dict(color="#2a78d6", marker="s", ls="-", hatch=""),
    "ECMWF": dict(color="#eb6834", marker="^", ls="--", hatch="////"),
    "GFS": dict(color="#1baf7a", marker="D", ls=":", hatch="...."),
}
ESTILO_PRINCIPAL = dict(color=TINTA, marker="o", ls="-", hatch="")

TITULOS = {
    "T_Max": "TEMPERATURA MÁXIMA (°C)",
    "T_Min": "TEMPERATURA MÍNIMA (°C)",
    "PP": "PRECIPITACIÓN DIARIA (mm)",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Noto Sans", "DejaVu Sans"],
    "hatch.linewidth": 0.8,
})


def _estilo(serie) -> dict:
    modelo = _modelo_de(serie)
    if modelo:
        return dict(ESTILO_MODELO[modelo], nombre=NOMBRE_MODELO[modelo], principal=False)
    nombre = serie["lbl_linea"].replace("ETA/Senamhi", NOMBRE_MODELO["ETA"]).replace(
        "ECMWF/IFS", NOMBRE_MODELO["ECMWF"])
    return dict(ESTILO_PRINCIPAL, nombre=nombre, principal=True)


def _lineas(ax, series, ventana):
    for s in series:
        e = _estilo(s)
        df = s["df"].dropna(subset=[s["col"]]).sort_values("Fecha")
        if df.empty:
            continue
        ax.plot(df["Fecha"], df[s["col"]], color=e["color"], ls=e["ls"],
                lw=2.6 if e["principal"] else 2.0, marker=e["marker"],
                markersize=7.5 if e["principal"] else 6.5, markerfacecolor=e["color"],
                markeredgecolor=BLANCO, markeredgewidth=0.8, zorder=4 if e["principal"] else 3)


def _barras(ax, series):
    n = max(len(series), 1)
    ancho = 0.76 / n
    for i, s in enumerate(series):
        e = _estilo(s)
        df = s["df"].dropna(subset=[s["col"]])
        x = mdates.date2num(df["Fecha"]) + (i - (n - 1) / 2) * ancho
        ax.bar(x, df[s["col"]], width=ancho * 0.9, color=e["color"], hatch=e["hatch"],
               edgecolor=BLANCO if not e["hatch"] else "#ffffffb0", linewidth=0, zorder=3)


def plotar_grafico(ventana: Ventana, var_tipo: str, lugar: str,
                   df_eta: pd.DataFrame, df_ecmwf: pd.DataFrame, df_gfs: pd.DataFrame,
                   dir_salida: Path, df_obs: pd.DataFrame = None,
                   metadata_str: str = "", prefijo_titulo: str = "Estación",
                   sufijo_archivo: str = "", unir_con: str = None,
                   pasado_del_modelo: bool = False) -> Path:
    series = _series(var_tipo, df_obs, df_eta, df_ecmwf, df_gfs, ventana, unir_con,
                     pasado_del_modelo)

    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=BLANCO)
    fig.subplots_adjust(left=0.09, right=0.975, top=0.72, bottom=0.27)
    ax.set_facecolor(BLANCO)

    corte = ventana.hoy_date - timedelta(days=0.5)
    x_ini = ventana.inicio - timedelta(days=0.5)
    x_fin = ventana.fin + timedelta(days=0.5)
    ax.axvspan(x_ini, corte, color=FRANJA_PASADO, zorder=0, lw=0)
    ax.axvline(corte, color=TINTA_SECUNDARIA, lw=0.9, zorder=2)

    if var_tipo == "PP":
        _barras(ax, series)
        _, ymax = ax.get_ylim()
        ax.set_ylim(0, max(ymax * 1.1, 5))
    else:
        todas = [s["df"][s["col"]].dropna() for s in series]
        valores = pd.concat(todas) if todas else pd.Series(dtype=float)
        if not valores.empty:
            r = max(valores.max() - valores.min(), 2)
            ax.set_ylim(valores.min() - r * 0.15, valores.max() + r * 0.2)
        _lineas(ax, series, ventana)
    ax.set_xlim(x_ini, x_fin)

    trans = ax.get_xaxis_transform()
    hay_obs = df_obs is not None and not df_obs.empty and not pasado_del_modelo
    ax.text(x_ini + (corte - x_ini) / 2, 0.97, "Observado" if hay_obs else "Pasado",
            transform=trans, ha="center", va="top", fontsize=10, color=TINTA_TENUE, style="italic")
    ax.text(corte + (x_fin - corte) / 2, 0.97, "Pronóstico", transform=trans, ha="center",
            va="top", fontsize=10, color=TINTA_TENUE, style="italic")

    # Ejes: izquierdo e inferior, con marcas hacia afuera
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA_SECUNDARIA)
        ax.spines[lado].set_linewidth(0.8)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6, zorder=0.5)
    ax.tick_params(axis="both", direction="out", length=4, width=0.9, labelsize=11,
                   colors=TINTA_SECUNDARIA)
    fechas = pd.date_range(ventana.inicio, ventana.fin)
    ax.set_xticks(fechas)
    ax.set_xticklabels([f"{DIAS_SEMANA[f.weekday()]}\n{f:%d/%m}" for f in fechas])
    for etiqueta, f in zip(ax.get_xticklabels(), fechas):
        if f == ventana.hoy_date:
            etiqueta.set_fontweight("bold")
            etiqueta.set_color(TINTA)

    # Cabecera: barra de color con el título y, debajo, el lugar y sus datos
    fig.add_artist(Rectangle((0, 0.88), 1, 0.12, transform=fig.transFigure,
                             facecolor=CABECERA, edgecolor="none"))
    lugar_fmt = lugar.replace("_", " ").title()
    fig.text(0.02, 0.94, f"{TITULOS[var_tipo]}  ·  {lugar_fmt.upper()}", fontsize=14.5,
             fontweight="bold", color=BLANCO, ha="left", va="center")
    # Datos de la estación en dos líneas: ubicación (Lat/Lon/Alt) y el resto
    partes = [x.strip() for x in metadata_str.split("|") if x.strip()] if metadata_str else []
    ubicacion = [x for x in partes if x.split(":")[0] in ("Lat", "Lon", "Alt")]
    resto = [x for x in partes if x not in ubicacion]
    lineas = [f"{prefijo_titulo}: " + ("  |  ".join(ubicacion) if ubicacion else lugar_fmt)]
    if resto:
        lineas.append("  |  ".join(resto))
    fig.text(0.02, 0.855, "\n".join(lineas), fontsize=10.5, color=TINTA_SECUNDARIA,
             ha="left", va="top", linespacing=1.5)

    # Leyenda bajo el gráfico, en una fila
    elementos = []
    for s in series:
        e = _estilo(s)
        if var_tipo == "PP":
            elementos.append(Patch(facecolor=e["color"], hatch=e["hatch"], edgecolor="#ffffffb0",
                                   linewidth=0, label=e["nombre"]))
        else:
            elementos.append(Line2D([0], [0], color=e["color"], ls=e["ls"], lw=2.2,
                                    marker=e["marker"], markersize=6.5, markeredgecolor=BLANCO,
                                    markeredgewidth=0.6, label=e["nombre"]))
    if elementos:
        fig.legend(handles=elementos, loc="lower center", bbox_to_anchor=(0.5, 0.075),
                   ncol=len(elementos), frameon=False, fontsize=11, labelcolor=TINTA,
                   handlelength=2.4, columnspacing=1.4, borderaxespad=0)

    # Pie: fuentes y línea separadora
    fig.add_artist(Line2D([0.02, 0.98], [0.06, 0.06], transform=fig.transFigure,
                          color=REJILLA, lw=0.8))
    nota = "Fuente: ETA/SENAMHI; ECMWF/IFS y GFS."
    if var_tipo == "PP":
        nota += " Acumulado diario de 12 a 12 UTC."
    fig.text(0.02, 0.02, nota, fontsize=8.5, color=TINTA_TENUE, ha="left", va="bottom",
             style="italic")

    carpeta = Path(dir_salida) / ventana.hoy_str
    carpeta.mkdir(parents=True, exist_ok=True)
    extra = f"_{sufijo_archivo}" if sufijo_archivo else ""
    ruta = carpeta / f"{var_tipo}_{lugar}_{ventana.hoy_str}{extra}.png"
    fig.savefig(ruta, dpi=300, facecolor=BLANCO)
    plt.close(fig)
    return ruta
