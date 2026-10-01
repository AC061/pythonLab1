"""Sensor de CPU: uso total, uso por núcleo, temperatura y capacidad."""
from __future__ import annotations

import platform

import psutil

import config
from hardware import ProveedorLHM, temperatura_psutil
from modelos import LecturaCPU


def _nombre_del_sistema() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as archivo:
            for linea in archivo:
                if linea.startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


class SensorCPU:
    def __init__(self, lhm: ProveedorLHM) -> None:
        self._lhm = lhm
        self._nombre_sistema = _nombre_del_sistema()
        self._logicos = psutil.cpu_count(logical=True) or 1
        self._fisicos = psutil.cpu_count(logical=False) or self._logicos
        psutil.cpu_percent(percpu=True)  # el primer llamado solo inicializa el contador

    def leer(self) -> LecturaCPU:
        dispositivos = self._lhm.dispositivos("cpu")
        dispositivo = dispositivos[0] if dispositivos else None

        nucleos = psutil.cpu_percent(percpu=True)
        total = sum(nucleos) / len(nucleos) if nucleos else 0.0

        temperatura = None
        if dispositivo is not None:
            temperatura = dispositivo.valor("Temperature", config.LHM_TEMP_CPU_PREFERIDAS)
        if temperatura is None:
            temperatura = temperatura_psutil(config.LINUX_CHIPS_CPU, config.LINUX_ETIQUETAS_CPU)

        frecuencia = psutil.cpu_freq()
        return LecturaCPU(
            nombre=dispositivo.nombre if dispositivo else self._nombre_sistema,
            uso_total=total,
            nucleos_uso=nucleos,
            temperatura=temperatura,
            nucleos_fisicos=self._fisicos,
            nucleos_logicos=self._logicos,
            frecuencia_mhz=frecuencia.current if frecuencia else None,
        )
