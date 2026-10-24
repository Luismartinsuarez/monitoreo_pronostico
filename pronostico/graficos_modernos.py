"""Gráficos con estilo moderno: misma información que `graficos`, con un diseño más limpio.

Usa las mismas series (`graficos._series`), así que respeta las opciones `unir_con` y
`pasado_del_modelo`. Los colores de los modelos son los tres primeros de una paleta
categórica validada para daltonismo; lo observado (o la línea unida) va en tinta negra.
"""
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .graficos import _series
from .ventana import Ventana

# Paleta
SUPERFICIE = "#fcfcfb"
FRANJA_PASADO = "#f0efec"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"
COLOR_MODELO = {"ETA": "#2a78d6", "ECMWF": "#eb6834", "GFS": "#1baf7a"}
NOMBRE_MODELO = {"ETA": "ETA (SENAMHI)", "ECMWF": "ECMWF", "GFS": "GFS"}

TITULOS = {
    "T_Max": "Temperatura máxima (°C)",
    "T_Min": "Temperatura mínima (°C)",
    "PP": "Precipitación diaria (mm, 12–12 UTC)",
}
DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Noto Sans", "DejaVu Sans"],
})


def _modelo_de(serie) -> str:
    """'ETA' / 'ECMWF' / 'GFS' según la columna de la serie, o None si es observado/unida."""
    col = serie["col"]
    if col == "ETA":
        return "ETA"
    for m in ("ECMWF", "GFS"):
        if col.endswith(f"_{m}"):
            return m
    return None


def _estilo(serie) -> dict:
    modelo = _modelo_de(serie)
    if modelo:
        return dict(color=COLOR_MODELO[modelo], nombre=NOMBRE_MODELO[modelo], principal=False)
    nombre = serie["lbl_linea"].replace("ETA/Senamhi", NOMBRE_MODELO["ETA"]).replace(
        "ECMWF/IFS", NOMBRE_MODELO["ECMWF"])
    return dict(color=TINTA, nombre=nombre, principal=True)


def _lineas(ax, series, ventana):
    for s in series:
        e = _estilo(s)
        df = s["df"].dropna(subset=[s["col"]]).sort_values("Fecha")
        if df.empty:
            continue
        ax.plot(df["Fecha"], df[s["col"]], color=e["color"],
                linewidth=2.8 if e["principal"] else 2.2,
                solid_capstyle="round", solid_joinstyle="round",
                marker="o", markersize=7 if e["principal"] else 6,
                markerfacecolor=e["color"], markeredgecolor=SUPERFICIE, markeredgewidth=1.6,
                zorder=4 if e["principal"] else 3)


def _barras(ax, series, ventana):
    n = max(len(series), 1)
    ancho_grupo = 0.72
    ancho = ancho_grupo / n
    for i, s in enumerate(series):
        e = _estilo(s)
        df = s["df"].dropna(subset=[s["col"]])
        x = mdates.date2num(df["Fecha"]) + (i - (n - 1) / 2) * ancho
        ax.bar(x, df[s["col"]], width=ancho, color=e["color"],
               edgecolor=SUPERFICIE, linewidth=1.5, zorder=3)


def _leyenda(fig, ax, series, var_tipo, ventana):
    elementos = []
    for s in series:
        e = _estilo(s)
        texto = e["nombre"]
        if var_tipo == "PP":
            futuro = s["df"][s["df"]["Fecha"] >= ventana.hoy_date][s["col"]]
            if not futuro.dropna().empty:
                texto += f"  ·  {futuro.sum():.0f} mm pronosticados"
            elementos.append(Patch(facecolor=e["color"], edgecolor="none", label=texto))
        else:
            elementos.append(Line2D([0], [0], color=e["color"], lw=2.6, marker="o", markersize=6,
                                    markeredgecolor=SUPERFICIE, label=texto))
    if elementos:
        ax.legend(handles=elementos, loc="lower left", bbox_to_anchor=(0, 1.02),
                  ncol=len(elementos), frameon=False, fontsize=10.5,
                  labelcolor=TINTA_SECUNDARIA, handlelength=1.6, columnspacing=1.8,
                  borderaxespad=0, handletextpad=0.6)


def plotar_grafico(ventana: Ventana, var_tipo: str, lugar: str,
                   df_eta: pd.DataFrame, df_ecmwf: pd.DataFrame, df_gfs: pd.DataFrame,
                   dir_salida: Path, df_obs: pd.DataFrame = None,
                   metadata_str: str = "", prefijo_titulo: str = "Estación",
                   sufijo_archivo: str = "", unir_con: str = None,
                   pasado_del_modelo: bool = False) -> Path:
    series = _series(var_tipo, df_obs, df_eta, df_ecmwf, df_gfs, ventana, unir_con,
                     pasado_del_modelo)

    fig, ax = plt.subplots(figsize=(12, 6.75), facecolor=SUPERFICIE)
    fig.subplots_adjust(left=0.07, right=0.97,
                        top=0.78, bottom=0.17)
    ax.set_facecolor(SUPERFICIE)

    # Franja del pasado y marca de hoy
    corte = ventana.hoy_date - timedelta(days=0.5)
    x_ini = ventana.inicio - timedelta(days=0.5)
    x_fin = ventana.fin + timedelta(days=0.5)
    ax.axvspan(x_ini, corte, color=FRANJA_PASADO, zorder=0, lw=0)
    ax.axvline(corte, color=TINTA_TENUE, lw=1, zorder=2)

    if var_tipo == "PP":
        _barras(ax, series, ventana)
        _, ymax = ax.get_ylim()
        ax.set_ylim(0, max(ymax * 1.08, 5))
    else:
        todas = [s["df"][s["col"]].dropna() for s in series]
        valores = pd.concat(todas) if todas else pd.Series(dtype=float)
        if not valores.empty:
            rango = max(valores.max() - valores.min(), 2)
            ax.set_ylim(valores.min() - rango * 0.15, valores.max() + rango * 0.15)
        _lineas(ax, series, ventana)

    ax.set_xlim(x_ini, x_fin)

    # Rótulos de zona
    trans = ax.get_xaxis_transform()
    for x, texto in (((x_ini + (corte - x_ini) / 2), "PASADO"), ((corte + (x_fin - corte) / 2), "PRONÓSTICO")):
        ax.text(x, 0.97, texto, transform=trans, ha="center", va="top", fontsize=9,
                color=TINTA_TENUE, fontweight="bold")

    # Ejes: solo línea base, rejilla horizontal fina
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(EJE)
    ax.grid(axis="y", color=REJILLA, linewidth=0.9, zorder=1)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", length=0, labelsize=10.5, colors=TINTA_TENUE, pad=6)

    fechas = pd.date_range(ventana.inicio, ventana.fin)
    ax.set_xticks(fechas)
    ax.set_xticklabels([f"{DIAS_SEMANA[f.weekday()]}\n{f:%d/%m}" for f in fechas])
    for etiqueta, f in zip(ax.get_xticklabels(), fechas):
        if f == ventana.hoy_date:
            etiqueta.set_color(TINTA)
            etiqueta.set_fontweight("bold")

    # Títulos (alineados a la izquierda) y pie
    lugar_fmt = lugar.replace("_", " ").title()
    fig.text(0.07, 0.95, f"{prefijo_titulo}: {lugar_fmt}", fontsize=18, fontweight="bold",
             color=TINTA, ha="left", va="top")
    subtitulo = TITULOS[var_tipo] + (f"   ·   {metadata_str}" if metadata_str else "")
    fig.text(0.07, 0.895, subtitulo, fontsize=11, color=TINTA_SECUNDARIA, ha="left", va="top")
    _leyenda(fig, ax, series, var_tipo, ventana)

    hay_obs = df_obs is not None and not df_obs.empty and not pasado_del_modelo
    fig.text(0.07, 0.03, "Fuentes: ETA/SENAMHI · ECMWF/IFS y GFS"
             + (" · Observaciones: estaciones SENAMHI" if hay_obs else ""),
             fontsize=8.5, color=TINTA_TENUE, ha="left", va="bottom")
    fig.text(0.97, 0.03,
             f"Emitido el {ventana.hoy:%d/%m/%Y}", fontsize=8.5, color=TINTA_TENUE,
             ha="right", va="bottom")

    carpeta = Path(dir_salida) / ventana.hoy_str
    carpeta.mkdir(parents=True, exist_ok=True)
    extra = f"_{sufijo_archivo}" if sufijo_archivo else ""
    ruta = carpeta / f"{var_tipo}_{lugar}_{ventana.hoy_str}{extra}.png"
    fig.savefig(ruta, dpi=170, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta
