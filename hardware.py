"""Acceso al hardware.

Usa HardwareMonitor (envoltorio de LibreHardwareMonitor, solo Windows) cuando
está disponible. En otros sistemas, o si falla, los sensores recurren a psutil,
sysfs y nvidia-smi (ver cpu.py, disco.py, red.py y gpu.py).
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Iterable

import psutil

import config

registro = logging.getLogger(__name__)


@dataclass
class DispositivoLHM:
    """Un dispositivo de HardwareMonitor con sus sensores ya convertidos a tipos nativos."""
    nombre: str
    categoria: str
    sensores: list[tuple[str, str, float]] = field(default_factory=list)  # (tipo, nombre, valor)

    def valor(self, tipo: str, preferidos: Iterable[str] = (), estricto: bool = False) -> float | None:
        """Valor del primer sensor `tipo` cuyo nombre esté en `preferidos`.

        Si `estricto` es False y ninguno coincide, devuelve el primer sensor del tipo.
        """
        candidatos = [(n, v) for t, n, v in self.sensores if t == tipo and v is not None]
        for preferido in preferidos:
            for nombre, valor in candidatos:
                if nombre == preferido:
                    return valor
        if estricto or not candidatos:
            return None
        return candidatos[0][1]


class ProveedorLHM:
    """Lee todos los sensores de HardwareMonitor una vez por ciclo."""

    def __init__(self) -> None:
        self.disponible = False
        self.motivo = ""
        self._computadora = None
        self._cache: dict[str, list[DispositivoLHM]] = {}
        if not sys.platform.startswith("win"):
            self.motivo = "HardwareMonitor solo funciona en Windows"
            return
        try:
            from HardwareMonitor.Hardware import Computer  # type: ignore

            pc = Computer()
            pc.IsCpuEnabled = True
            pc.IsGpuEnabled = True
            pc.IsMemoryEnabled = True
            pc.IsStorageEnabled = True
            pc.IsNetworkEnabled = True
            pc.Open()
            self._computadora = pc
            self.disponible = True
        except Exception as error:  # paquete ausente, .NET ausente, sin permisos...
            self.motivo = f"HardwareMonitor no disponible: {error}"
            registro.warning(self.motivo)

    @property
    def descripcion(self) -> str:
        if self.disponible:
            return "HardwareMonitor (LibreHardwareMonitor)"
        return f"psutil / sysfs ({self.motivo})"

    def actualizar(self) -> None:
        if not self.disponible:
            return
        try:
            cache: dict[str, list[DispositivoLHM]] = {}
            for hw in self._computadora.Hardware:
                self._recorrer(hw, cache)
            self._cache = cache
        except Exception:
            registro.exception("Fallo al actualizar HardwareMonitor")

    def dispositivos(self, categoria: str) -> list[DispositivoLHM]:
        return self._cache.get(categoria, [])

    def cerrar(self) -> None:
        if self._computadora is not None:
            try:
                self._computadora.Close()
            except Exception:
                registro.exception("Fallo al cerrar HardwareMonitor")

    def _recorrer(self, hw, cache: dict[str, list[DispositivoLHM]]) -> None:
        hw.Update()
        categoria = config.LHM_CATEGORIAS.get(str(hw.HardwareType))
        if categoria is not None:
            dispositivo = DispositivoLHM(str(hw.Name), categoria)
            for sensor in hw.Sensors:
                if sensor.Value is not None:
                    dispositivo.sensores.append(
                        (str(sensor.SensorType), str(sensor.Name), float(sensor.Value))
                    )
            cache.setdefault(categoria, []).append(dispositivo)
        for sub in hw.SubHardware:
            self._recorrer(sub, cache)


def temperatura_psutil(chips: Iterable[str], etiquetas: Iterable[str] = ()) -> float | None:
    """Temperatura (°C) del primer chip cuyo nombre empiece por alguno de `chips`."""
    funcion = getattr(psutil, "sensors_temperatures", None)
    if funcion is None:
        return None
    try:
        datos = funcion()
    except Exception:
        return None
    for prefijo in chips:
        for chip, entradas in datos.items():
            if not chip.startswith(prefijo) or not entradas:
                continue
            for etiqueta in etiquetas:
                for entrada in entradas:
                    if entrada.label == etiqueta:
                        return float(entrada.current)
            return float(entradas[0].current)
    return None
