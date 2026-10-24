"""Mapa de ubicación de las estaciones (o puntos) usadas en los gráficos.

Usa cartopy con capas de Natural Earth (se descargan una vez a la caché de cartopy).
Si una capa no está disponible, el mapa se genera igual sin ella.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from .graficos_modernos import EJE, REJILLA, SUPERFICIE, TINTA, TINTA_SECUNDARIA, TINTA_TENUE
from .ventana import Ventana

TIERRA = "#f4f3ef"
MAR = "#e3edf7"
LIMITE_PAIS = "#9a998f"
LIMITE_DEP = "#cfcdc4"
# Tipo de estación -> (color, marcador, etiqueta)
TIPOS = {
    "automática": ("#2a78d6", "o", "Automática"),
    "convencional": ("#eb6834", "^", "Convencional"),
}
SIN_TIPO = (TINTA, "D", "Punto de interés")


def _capa(escala, categoria, nombre, **estilo):
    """Feature de Natural Earth, o None si no se puede obtener (sin conexión, etc.)."""
    try:
        shpreader.natural_earth(resolution=escala, category=categoria, name=nombre)
    except Exception as e:  # noqa: BLE001 - el mapa sigue sin esa capa
        print(f"  -> Aviso: capa '{nombre}' no disponible ({e}).")
        return None
    return cfeature.NaturalEarthFeature(categoria, nombre, escala, **estilo)


def _extension(lats, lons, margen=1.0, minimo=4.0):
    """[lon_min, lon_max, lat_min, lat_max] con margen y un tamaño mínimo."""
    def rango(vals):
        lo, hi = min(vals) - margen, max(vals) + margen
        if hi - lo < minimo:
            c = (lo + hi) / 2
            lo, hi = c - minimo / 2, c + minimo / 2
        return lo, hi
    lon0, lon1 = rango(lons)
    lat0, lat1 = rango(lats)
    return [lon0, lon1, lat0, lat1]


# Posiciones candidatas de la etiqueta respecto al punto: (dx, dy, alineación), en puntos
CANDIDATAS = [(10, 0, "left"), (-10, 0, "right"), (0, 24, "center"), (0, -24, "center"),
              (8, 18, "left"), (8, -18, "left"), (-8, 18, "right"), (-8, -18, "right")]


def _cajas_se_cruzan(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _colocar_etiquetas(ax, puntos, textos, escala) -> list:
    """Elige para cada punto la primera posición candidata cuya etiqueta no tape otras
    etiquetas ni marcadores. `textos` = [(nombre, detalle)]; `escala` = píxeles por punto."""
    xy = ax.projection.transform_points(ccrs.PlateCarree(), puntos["Longitud"].to_numpy(),
                                        puntos["Latitud"].to_numpy())[:, :2]
    px = ax.transData.transform(xy)
    r = 8 * escala  # radio de exclusión alrededor de cada marcador
    ocupadas = [(x - r, y - r, x + r, y + r) for x, y in px]
    marco = ax.bbox.extents
    elegidas = []
    for (x, y), (nombre, detalle) in zip(px, textos):
        ancho = max(len(nombre) * 7.2, len(detalle) * 5.4) * escala
        alto_arriba, alto_abajo = 15 * escala, (13 if detalle else 2) * escala
        mejor = None
        for dx, dy, ha in CANDIDATAS:
            cx, cy = x + dx * escala, y + dy * escala
            x0 = {"left": cx, "right": cx - ancho, "center": cx - ancho / 2}[ha]
            caja = (x0, cy - alto_abajo, x0 + ancho, cy + alto_arriba)
            dentro = caja[0] >= marco[0] and caja[2] <= marco[2] and caja[1] >= marco[1] and caja[3] <= marco[3]
            if dentro and not any(_cajas_se_cruzan(caja, o) for o in ocupadas):
                mejor = (dx, dy, ha, caja)
                break
        if mejor is None:  # sin hueco libre: a la derecha
            dx, dy, ha = CANDIDATAS[0]
            mejor = (dx, dy, ha, (x, y, x, y))
        ocupadas.append(mejor[3])
        elegidas.append(mejor[:3])
    return elegidas


def _estilo_tipo(tipo):
    return TIPOS.get(str(tipo).strip().lower(), SIN_TIPO)


def generar_mapa(puntos: pd.DataFrame, dir_salida: Path, ventana: Ventana,
                 metadata: pd.DataFrame = None, titulo: str = "Estaciones utilizadas",
                 nombre_archivo: str = "mapa_estaciones") -> Path:
    """Genera el mapa con `puntos` (columnas Lugar, Latitud, Longitud). Si `metadata` trae
    Tipo/Altitud/Dep, se usan para el símbolo y la etiqueta de cada punto."""
    puntos = puntos.copy().reset_index(drop=True)
    puntos["Lugar"] = puntos["Lugar"].astype(str).str.strip()
    if metadata is not None and not metadata.empty and "Lugar" in metadata.columns:
        cols = [c for c in ("Lugar", "Altitud", "Dep", "Tipo") if c in metadata.columns]
        meta = metadata[cols].copy()
        meta["Lugar"] = meta["Lugar"].astype(str).str.strip()
        puntos = puntos.merge(meta, on="Lugar", how="left")
    for c in ("Altitud", "Dep", "Tipo"):
        if c not in puntos.columns:
            puntos[c] = pd.NA

    ext = _extension(puntos["Latitud"], puntos["Longitud"])
    proy = ccrs.PlateCarree()

    # Tamaño de la figura (en pulgadas) según la forma de la zona, para no dejar huecos
    dpi = 170
    ancho_fig, margen_izq, ancho_mapa = 10, 0.6, 8.8
    alto_mapa = ancho_mapa * min(max((ext[3] - ext[2]) / (ext[1] - ext[0]), 0.45), 1.4)
    cabecera, pie = 2.4, 0.8
    alto_fig = cabecera + alto_mapa + pie
    fig = plt.figure(figsize=(ancho_fig, alto_fig), facecolor=SUPERFICIE, dpi=dpi)
    ax = fig.add_axes([margen_izq / ancho_fig, pie / alto_fig, ancho_mapa / ancho_fig,
                       alto_mapa / alto_fig], projection=proy)
    ax.set_extent(ext, crs=proy)
    ax.set_facecolor(MAR)
    ax.spines["geo"].set_edgecolor(EJE)

    for capa in (
        _capa("10m", "physical", "land", facecolor=TIERRA, edgecolor="none"),
        _capa("10m", "physical", "lakes", facecolor=MAR, edgecolor="none"),
        _capa("10m", "cultural", "admin_1_states_provinces_lines", facecolor="none",
              edgecolor=LIMITE_DEP, linewidth=0.7),
        _capa("10m", "cultural", "admin_0_boundary_lines_land", facecolor="none",
              edgecolor=LIMITE_PAIS, linewidth=1.1),
        _capa("10m", "physical", "coastline", facecolor="none", edgecolor=LIMITE_PAIS, linewidth=0.8),
    ):
        if capa is not None:
            ax.add_feature(capa, zorder=1)

    gl = ax.gridlines(crs=proy, draw_labels=True, color=REJILLA, linewidth=0.6, zorder=0.5)
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = dict(size=9, color=TINTA_TENUE)

    # Estaciones
    textos = []
    for _, p in puntos.iterrows():
        detalle = []
        if pd.notna(p["Altitud"]):
            detalle.append(f"{float(p['Altitud']):,.0f} m".replace(",", " "))
        if pd.notna(p["Dep"]):
            detalle.append(str(p["Dep"]))
        textos.append((p["Lugar"].replace("_", " ").title(), " · ".join(detalle)))

    posiciones = _colocar_etiquetas(ax, puntos, textos, dpi / 72)
    for (_, p), (nombre, detalle), (dx, dy, ha) in zip(puntos.iterrows(), textos, posiciones):
        color, marcador, _ = _estilo_tipo(p["Tipo"])
        ax.plot(p["Longitud"], p["Latitud"], marker=marcador, markersize=11, color=color,
                markeredgecolor=SUPERFICIE, markeredgewidth=1.8, transform=proy, zorder=5)
        xy = (p["Longitud"], p["Latitud"])
        ax.annotate(nombre, xy, xycoords=proy._as_mpl_transform(ax), xytext=(dx, dy + 1),
                    textcoords="offset points", ha=ha, va="bottom",
                    fontsize=10.5, fontweight="bold", color=TINTA, zorder=6)
        if detalle:
            ax.annotate(detalle, xy, xycoords=proy._as_mpl_transform(ax), xytext=(dx, dy - 1),
                        textcoords="offset points", ha=ha, va="top",
                        fontsize=8.5, color=TINTA_SECUNDARIA, zorder=6)

    # Leyenda por tipo (solo los tipos presentes)
    presentes = []
    for tipo in puntos["Tipo"]:
        est = _estilo_tipo(tipo)
        if est not in presentes:
            presentes.append(est)
    handles = [Line2D([0], [0], linestyle="none", marker=m, markersize=10, color=c,
                      markeredgecolor=SUPERFICIE, label=f"{lbl} ({sum(_estilo_tipo(t) == (c, m, lbl) for t in puntos['Tipo'])})")
               for c, m, lbl in presentes]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.01), ncol=len(handles),
              frameon=False, fontsize=10.5, labelcolor=TINTA_SECUNDARIA, borderaxespad=0,
              handletextpad=0.4, columnspacing=1.6)

    # Mapa de ubicación (Perú y el recuadro de la zona)
    # Fuera del área del mapa (arriba a la derecha) para no tapar ninguna estación
    inset = fig.add_axes([(margen_izq + ancho_mapa - 1.4) / ancho_fig, (alto_fig - 2.05) / alto_fig,
                          1.4 / ancho_fig, 1.8 / alto_fig], projection=proy)
    inset.set_extent([-82, -68, -18.6, 0.2], crs=proy)
    inset.set_facecolor(MAR)
    inset.spines["geo"].set_edgecolor(EJE)
    paises = _capa("50m", "cultural", "admin_0_countries", facecolor=TIERRA,
                   edgecolor=LIMITE_DEP, linewidth=0.5)
    if paises is not None:
        inset.add_feature(paises, zorder=1)
        try:
            ruta = shpreader.natural_earth("50m", "cultural", "admin_0_countries")
            peru = [r.geometry for r in shpreader.Reader(ruta).records()
                    if r.attributes.get("ADM0_A3") == "PER"]
            inset.add_geometries(peru, crs=proy, facecolor="#e6e4dc", edgecolor=LIMITE_PAIS,
                                 linewidth=0.8, zorder=2)
        except Exception:  # noqa: BLE001
            pass
    inset.plot([ext[0], ext[1], ext[1], ext[0], ext[0]], [ext[2], ext[2], ext[3], ext[3], ext[2]],
               color=TINTA, linewidth=1.3, transform=proy, zorder=3)

    # Títulos y pie
    fig.text(margen_izq / ancho_fig, (alto_fig - 0.3) / alto_fig, titulo, fontsize=18, fontweight="bold", color=TINTA, ha="left", va="top")
    fig.text(margen_izq / ancho_fig, (alto_fig - 0.72) / alto_fig, f"{len(puntos)} ubicaciones · monitoreo del {ventana.hoy:%d/%m/%Y}",
             fontsize=11, color=TINTA_SECUNDARIA, ha="left", va="top")
    fig.text(margen_izq / ancho_fig, 0.15 / alto_fig, "Cartografía: Natural Earth · límites departamentales referenciales",
             fontsize=8.5, color=TINTA_TENUE, ha="left", va="bottom")

    carpeta = Path(dir_salida) / ventana.hoy_str
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre_archivo}_{ventana.hoy_str}.png"
    fig.savefig(ruta, dpi=170, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta
