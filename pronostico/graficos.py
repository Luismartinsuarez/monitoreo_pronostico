"""Gráficos comparativos de pronóstico (líneas para temperatura, barras para precipitación)."""
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from .ventana import Ventana

ESTILOS = {
    "T_Max": dict(fondo_hist="salmon", fondo_pron="#ffe6e6", alpha_hist=0.4,
                  ylabel="Temperatura Máxima (°C)", col_obs="T_Max_Obs", col_modelo="T_Max"),
    "T_Min": dict(fondo_hist="lightblue", fondo_pron="#e6f2ff", alpha_hist=0.4,
                  ylabel="Temperatura Mínima (°C)", col_obs="T_Min_Obs", col_modelo="T_Min"),
    "PP": dict(fondo_hist="lightgreen", fondo_pron="#e6ffe6", alpha_hist=0.5,
               ylabel="Precipitación (mm)", col_obs="PP_Obs", col_modelo="PP"),
}


def _series(var_tipo, df_obs, df_eta, df_ecmwf, df_gfs):
    est = ESTILOS[var_tipo]
    m = est["col_modelo"]
    series = []
    if df_obs is not None and not df_obs.empty and est["col_obs"] in df_obs.columns:
        series.append(dict(df=df_obs, col=est["col_obs"], color="blue", edge="darkblue",
                           marker="o", ls="-", lw=3.5, lbl_barra="Observado", lbl_linea="Observado"))
    if not df_eta.empty:
        series.append(dict(df=df_eta, col="ETA", color="red", edge="darkred",
                           marker="s", ls="--", lw=3, lbl_barra="ETA/Senamhi", lbl_linea="Modelo ETA (eqm)"))
    if not df_ecmwf.empty:
        series.append(dict(df=df_ecmwf, col=f"{m}_ECMWF", color="green", edge="darkgreen",
                           marker="s", ls="-.", lw=3, lbl_barra="ECMWF/IFS", lbl_linea="Modelo ECMWF (IFS)"))
    if not df_gfs.empty:
        series.append(dict(df=df_gfs, col=f"{m}_GFS", color="orange", edge="darkorange",
                           marker="s", ls=":", lw=3, lbl_barra="GFS", lbl_linea="Modelo GFS"))
    return series


def plotar_grafico(ventana: Ventana, var_tipo: str, lugar: str,
                   df_eta: pd.DataFrame, df_ecmwf: pd.DataFrame, df_gfs: pd.DataFrame,
                   dir_salida: Path, df_obs: pd.DataFrame = None,
                   metadata_str: str = "", prefijo_titulo: str = "Estación",
                   sufijo_archivo: str = "") -> Path:
    est = ESTILOS[var_tipo]
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.set_facecolor(est["fondo_pron"])
    ax.axvspan(ventana.inicio - timedelta(days=1), ventana.dia_antes_hoy,
               color=est["fondo_hist"], alpha=est["alpha_hist"])

    series = _series(var_tipo, df_obs, df_eta, df_ecmwf, df_gfs)

    if var_tipo == "PP":
        n = len(series)
        ancho = 0.72 / max(n, 1)
        for i, s in enumerate(series):
            x = mdates.date2num(s["df"]["Fecha"]) + (i - (n - 1) / 2) * ancho
            ax.bar(x, s["df"][s["col"]], width=ancho, color=s["color"], edgecolor=s["edge"],
                   alpha=0.85, label=s["lbl_barra"], zorder=3)
    else:
        for s in series:
            ax.plot(s["df"]["Fecha"], s["df"][s["col"]], marker=s["marker"], linestyle=s["ls"],
                    color=s["color"], linewidth=s["lw"], markersize=10,
                    markeredgecolor=s["edge"], markeredgewidth=1.5, label=s["lbl_linea"], zorder=3)

    ax.axvline(x=ventana.dia_antes_hoy, color="black", linestyle="-", alpha=0.5, linewidth=2, zorder=4)

    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    y_ini, y_fin = ventana.inicio.year, ventana.fin.year
    ax.set_xlabel(f"{y_ini}" if y_ini == y_fin else f"{y_ini} - {y_fin}", fontsize=14, labelpad=10)

    lugar_fmt = lugar.replace("_", " ").title()
    ax.set_title(f"{prefijo_titulo}: {lugar_fmt}", fontsize=15, fontweight="bold", pad=25)
    if metadata_str:
        ax.text(0.5, 1.02, metadata_str, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=11, color="#444444")

    ax.set_ylabel(est["ylabel"], fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.6, color="#d9d9d9" if var_tipo == "PP" else "white",
            linewidth=1, zorder=0)
    ax.set_xlim([ventana.inicio - timedelta(days=0.5), ventana.fin + timedelta(days=0.5)])

    if var_tipo == "PP":
        _, ymax = ax.get_ylim()
        ax.set_ylim([0, max(ymax, 5)])

    plt.xticks(fontsize=13, rotation=0)
    plt.yticks(fontsize=15)
    if series:
        ax.legend(loc="upper left" if var_tipo == "PP" else "best", fontsize=11,
                  facecolor="white", framealpha=0.9)
    plt.tight_layout()

    carpeta = Path(dir_salida) / ventana.hoy_str
    carpeta.mkdir(parents=True, exist_ok=True)
    extra = f"_{sufijo_archivo}" if sufijo_archivo else ""
    ruta = carpeta / f"{var_tipo}_{lugar}_{ventana.hoy_str}{extra}.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta
