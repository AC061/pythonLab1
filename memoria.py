"""Sensor de memoria RAM del sistema."""
from __future__ import annotations

import psutil

from modelos import LecturaMemoria


class SensorMemoria:
    def leer(self) -> LecturaMemoria:
        info = psutil.virtual_memory()
        return LecturaMemoria(
            uso_pct=info.percent,
            usada_bytes=info.total - info.available,
            total_bytes=info.total,
        )
