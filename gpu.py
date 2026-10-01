"""Sensor de GPU: uso, temperatura y VRAM.

Orden de fuentes: HardwareMonitor (Windows) -> nvidia-smi -> sysfs (AMD en Linux).
Si no hay ninguna disponible, `leer()` devuelve None.
"""
from __future__ import annotations

import glob
import os
import re
import shlex
import shutil
import subprocess

import config
from hardware import ProveedorLHM, temperatura_psutil
from modelos import LecturaGPU


def _leer_texto(ruta: str) -> str | None:
    try:
        with open(ruta, encoding="utf-8") as archivo:
            return archivo.read().strip()
    except OSError:
        return None


def _leer_entero(ruta: str) -> int | None:
    texto = _leer_texto(ruta)
    try:
        return int(texto) if texto is not None else None
    except ValueError:
        return None


def _ejecutar(comando: list[str]) -> str | None:
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True,
            timeout=config.TIMEOUT_SUBPROCESO_S, check=True,
        )
        return resultado.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _numero(texto: str) -> float | None:
    try:
        return float(texto)
    except ValueError:  # nvidia-smi devuelve "[N/A]" cuando no hay dato
        return None


class SensorGPU:
    def __init__(self, lhm: ProveedorLHM) -> None:
        self._lhm = lhm
        self._nvidia = shutil.which(config.NVIDIA_SMI)
        self._lspci = shutil.which(config.LSPCI)
        self._tarjeta_amd = self._buscar_tarjeta_amd()
        self._nombre_amd: str | None = None

    # ---------------------------------------------------------------- HardwareMonitor
    def _leer_lhm(self) -> LecturaGPU | None:
        dispositivos = self._lhm.dispositivos("gpu")
        if not dispositivos:
            return None

        def vram_total(d):
            return d.valor("SmallData", (config.LHM_GPU_VRAM_TOTAL,), estricto=True) or 0.0

        dispositivo = max(dispositivos, key=vram_total)
        total = dispositivo.valor("SmallData", (config.LHM_GPU_VRAM_TOTAL,), estricto=True)
        usada = dispositivo.valor("SmallData", (config.LHM_GPU_VRAM_USADA,), estricto=True)
        return LecturaGPU(
            nombre=dispositivo.nombre,
            uso_pct=dispositivo.valor("Load", config.LHM_GPU_CARGA, estricto=True),
            temperatura=dispositivo.valor("Temperature", config.LHM_GPU_TEMP, estricto=True),
            vram_usada_bytes=int(usada * config.LHM_MB_A_BYTES) if usada is not None else None,
            vram_total_bytes=int(total * config.LHM_MB_A_BYTES) if total is not None else None,
        )

    # ---------------------------------------------------------------- NVIDIA (nvidia-smi)
    def _leer_nvidia(self) -> LecturaGPU | None:
        if not self._nvidia:
            return None
        salida = _ejecutar([self._nvidia, *config.NVIDIA_SMI_ARGS])
        if not salida:
            return None
        campos = [c.strip() for c in salida.splitlines()[0].split(config.SEPARADOR_CSV)]
        if len(campos) < config.NVIDIA_SMI_CAMPOS:
            return None
        nombre, uso, temperatura, usada, total = campos[:config.NVIDIA_SMI_CAMPOS]
        usada_mb, total_mb = _numero(usada), _numero(total)  # nvidia-smi informa MiB
        return LecturaGPU(
            nombre=nombre,
            uso_pct=_numero(uso),
            temperatura=_numero(temperatura),
            vram_usada_bytes=int(usada_mb * config.BYTES_MB) if usada_mb is not None else None,
            vram_total_bytes=int(total_mb * config.BYTES_MB) if total_mb is not None else None,
        )

    # ---------------------------------------------------------------- AMD (sysfs)
    def _buscar_tarjeta_amd(self) -> str | None:
        mejor, mejor_vram = None, -1
        try:
            entradas = os.listdir(config.DRM_RUTA)
        except OSError:
            return None
        for entrada in entradas:
            if not re.match(config.DRM_PATRON_TARJETA, entrada):
                continue
            dispositivo = os.path.join(config.DRM_RUTA, entrada, "device")
            if _leer_texto(os.path.join(dispositivo, "vendor")) != config.DRM_VENDOR_AMD:
                continue
            vram = _leer_entero(os.path.join(dispositivo, "mem_info_vram_total")) or 0
            if vram > mejor_vram:
                mejor, mejor_vram = dispositivo, vram
        return mejor

    def _nombre_pci(self, dispositivo: str) -> str:
        identificador = _leer_texto(os.path.join(dispositivo, "device")) or ""
        ranura = os.path.basename(os.path.realpath(dispositivo))
        if self._lspci:
            salida = _ejecutar([self._lspci, "-mm", "-s", ranura])
            if salida:
                partes = shlex.split(salida)
                if len(partes) > config.LSPCI_COLUMNA_DISPOSITIVO:
                    return partes[config.LSPCI_COLUMNA_DISPOSITIVO]
        return f"GPU AMD ({identificador})"

    def _leer_amd(self) -> LecturaGPU | None:
        dispositivo = self._tarjeta_amd
        if dispositivo is None:
            return None
        if self._nombre_amd is None:
            self._nombre_amd = self._nombre_pci(dispositivo)
        usada = _leer_entero(os.path.join(dispositivo, "mem_info_vram_used"))
        total = _leer_entero(os.path.join(dispositivo, "mem_info_vram_total"))
        uso = _leer_entero(os.path.join(dispositivo, "gpu_busy_percent"))

        temperatura = None
        for archivo in glob.glob(os.path.join(dispositivo, "hwmon", "hwmon*", "temp1_input")):
            milis = _leer_entero(archivo)
            if milis is not None:
                temperatura = milis / config.MILIGRADOS_POR_GRADO
                break
        if temperatura is None:
            temperatura = temperatura_psutil(config.LINUX_CHIPS_GPU)

        if uso is None and total is None and temperatura is None:
            return None
        return LecturaGPU(
            nombre=self._nombre_amd,
            uso_pct=float(uso) if uso is not None else None,
            temperatura=temperatura,
            vram_usada_bytes=usada,
            vram_total_bytes=total,
        )

    def leer(self) -> LecturaGPU | None:
        for fuente in (self._leer_lhm, self._leer_nvidia, self._leer_amd):
            lectura = fuente()
            if lectura is not None:
                return lectura
        return None
