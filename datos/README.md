# Datos de entrada

Esta carpeta **no se sube a GitHub** (salvo los ejemplos). Coloca aquí:

| Archivo | Descripción |
|---|---|
| `coordenadas_convertidas.csv` | Columnas `Lugar,Latitud,Longitud` (ver `.example.csv`) |
| `metadata_estaciones.csv` | Columnas `Lugar,Latitud,Longitud,Altitud,Dist,Prov,Dep,Tipo` |
| `a_<Lugar>.csv` | Observaciones de estación **automática** (horaria; 5 filas de cabecera) |
| `c_<Lugar>.csv` | Observaciones de estación **convencional** (diaria; 7 filas de cabecera; columnas Fecha, TMax, TMin, HR, PP) |
| `puntos_interes.csv` | Puntos para el modo `modelos` (sin observaciones) |

El valor de `Lugar` debe coincidir con el sufijo del archivo de observaciones.
