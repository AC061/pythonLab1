"""Sensor de red: tráfico de bajada/subida (bytes/s) y capacidad del enlace.

Este módulo solo mide el tráfico; no determina si el equipo tiene conexión.
"""
from __future__ import annotations

import time

import psutil

import config
from hardware import ProveedorLHM, temperatura_psutil
from modelos import LecturaRed


def _interfaces_elegibles() -> list[str]:
    try:
        estados = psutil.net_if_stats()
    except Exception:
        return []
    return [
        nombre for nombre, estado in estados.items()
        if estado.isup and not nombre.startswith(config.RED_INTERFACES_IGNORADAS)
    ]


class SensorRed:
    def __init__(self, lhm: ProveedorLHM) -> None:
        self._lhm = lhm
        self._previo: tuple[float, int, int] | None = None  # (t, recibidos, enviados)

    def leer(self) -> LecturaRed:
        elegibles = _interfaces_elegibles()
        contadores = psutil.net_io_counters(pernic=True)
        usadas = {n: contadores[n] for n in elegibles if n in contadores}

        recibidos = sum(c.bytes_recv for c in usadas.values())
        enviados = sum(c.bytes_sent for c in usadas.values())
        principal = max(usadas, key=lambda n: usadas[n].bytes_recv + usadas[n].bytes_sent, default=None)

        ahora = time.monotonic()
        previo, self._previo = self._previo, (ahora, recibidos, enviados)
        bajada = subida = 0.0
        if previo is not None and ahora > previo[0]:
            delta_t = ahora - previo[0]
            bajada = max(recibidos - previo[1], 0) / delta_t
            subida = max(enviados - previo[2], 0) / delta_t

        capacidad = None
        if principal is not None:
            velocidad = psutil.net_if_stats()[principal].speed
            capacidad = float(velocidad) if velocidad > 0 else None
        escala_mbps = capacidad if capacidad else config.RED_ESCALA_REFERENCIA_MBPS
        bits_por_s = max(bajada, subida) * config.BITS_POR_BYTE
        uso = min(bits_por_s / (escala_mbps * config.BITS_POR_MBIT) * config.PORCENTAJE_MAX,
                  config.PORCENTAJE_MAX)

        return LecturaRed(
            interfaz=principal or config.RED_SIN_INTERFAZ,
            bajada_bps=bajada,
            subida_bps=subida,
            capacidad_mbps=capacidad,
            uso_enlace_pct=uso,
            temperatura=temperatura_psutil(config.LINUX_CHIPS_RED),
        )
