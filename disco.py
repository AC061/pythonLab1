"""Sensor de disco: espacio, actividad, velocidad de E/S y temperatura."""
from __future__ import annotations

import os
import time

import psutil

import config
from hardware import DispositivoLHM, ProveedorLHM, temperatura_psutil
from modelos import LecturaDisco


def _raiz_sistema() -> str:
    unidad = os.environ.get("SystemDrive")
    return unidad + os.sep if unidad else os.sep


def _particion_de(raiz: str):
    mejor = None
    for particion in psutil.disk_partitions(all=False):
        if particion.mountpoint == raiz:
            return particion
        mejor = mejor or particion
    return mejor


class SensorDisco:
    def __init__(self, lhm: ProveedorLHM) -> None:
        self._lhm = lhm
        self._raiz = _raiz_sistema()
        particion = _particion_de(self._raiz)
        self._dispositivo = particion.device if particion else self._raiz
        self._clave_io = self._dispositivo.removeprefix(config.DISCO_DEV_PREFIJO)
        self._previo: tuple[float, int, int, float] | None = None  # (t, lectura, escritura, ocupado_ms)

    def _contadores(self):
        try:
            por_disco = psutil.disk_io_counters(perdisk=True) or {}
            return por_disco.get(self._clave_io) or psutil.disk_io_counters()
        except Exception:
            return None

    def _dispositivo_lhm(self) -> DispositivoLHM | None:
        discos = self._lhm.dispositivos("disco")
        for disco in discos:
            if disco.valor("Temperature", config.LHM_DISCO_TEMP, estricto=True) is not None:
                return disco
        return discos[0] if discos else None

    def _velocidades(self) -> tuple[float, float, float | None]:
        """Devuelve (lectura B/s, escritura B/s, actividad %) según el delta desde la lectura previa."""
        contadores = self._contadores()
        if contadores is None:
            return 0.0, 0.0, None
        ahora = time.monotonic()
        ocupado = float(getattr(contadores, "busy_time", 0.0)) if hasattr(contadores, "busy_time") else None
        actual = (ahora, contadores.read_bytes, contadores.write_bytes, ocupado)
        previo, self._previo = self._previo, actual
        if previo is None:
            return 0.0, 0.0, None
        delta_t = ahora - previo[0]
        if delta_t <= 0:
            return 0.0, 0.0, None
        lectura = max(actual[1] - previo[1], 0) / delta_t
        escritura = max(actual[2] - previo[2], 0) / delta_t
        actividad = None
        if ocupado is not None and previo[3] is not None:
            actividad = min((ocupado - previo[3]) / (delta_t * config.MS_POR_S) * config.PORCENTAJE_MAX,
                            config.PORCENTAJE_MAX)
        return lectura, escritura, max(actividad, 0.0) if actividad is not None else None

    def leer(self) -> LecturaDisco:
        uso = psutil.disk_usage(self._raiz)
        lectura, escritura, actividad = self._velocidades()
        dispositivo = self._dispositivo_lhm()

        temperatura = None
        nombre = self._dispositivo
        if dispositivo is not None:
            nombre = dispositivo.nombre
            temperatura = dispositivo.valor("Temperature", config.LHM_DISCO_TEMP, estricto=True)
            carga = dispositivo.valor("Load", config.LHM_DISCO_ACTIVIDAD, estricto=True)
            actividad = carga if carga is not None else actividad
            tasa_l = dispositivo.valor("Throughput", config.LHM_DISCO_LECTURA, estricto=True)
            tasa_e = dispositivo.valor("Throughput", config.LHM_DISCO_ESCRITURA, estricto=True)
            lectura = tasa_l if tasa_l is not None else lectura
            escritura = tasa_e if tasa_e is not None else escritura
        if temperatura is None:
            temperatura = temperatura_psutil(config.LINUX_CHIPS_DISCO, config.LINUX_ETIQUETAS_DISCO)

        return LecturaDisco(
            nombre=nombre,
            uso_espacio_pct=uso.percent,
            usado_bytes=uso.used,
            total_bytes=uso.total,
            libre_bytes=uso.free,
            actividad_pct=actividad,
            lectura_bps=lectura,
            escritura_bps=escritura,
            temperatura=temperatura,
        )
