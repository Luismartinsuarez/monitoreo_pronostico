"""Ventana temporal de análisis (días pasados observados + días de pronóstico)."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd

from . import config


@dataclass(frozen=True)
class Ventana:
    hoy: datetime = field(default_factory=datetime.now)
    dias_pasados: int = config.DIAS_PASADOS
    dias_futuros: int = config.DIAS_FUTUROS

    @property
    def hoy_date(self) -> pd.Timestamp:
        return pd.to_datetime(self.hoy.date())

    @property
    def dia_antes_hoy(self) -> pd.Timestamp:
        return self.hoy_date - timedelta(days=1)

    @property
    def fechas_pasadas(self) -> list:
        return [self.hoy_date - timedelta(days=i) for i in range(self.dias_pasados, 0, -1)]

    @property
    def inicio(self) -> pd.Timestamp:
        return self.hoy_date - timedelta(days=self.dias_pasados)

    @property
    def fin(self) -> pd.Timestamp:
        return self.hoy_date + timedelta(days=self.dias_futuros)

    @property
    def fecha_inicio(self) -> str:
        return self.inicio.strftime("%Y-%m-%d")

    @property
    def fecha_fin(self) -> str:
        return self.fin.strftime("%Y-%m-%d")

    @property
    def hoy_str(self) -> str:
        return self.hoy.strftime("%d-%m-%Y")
