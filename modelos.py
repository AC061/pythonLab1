"""Estructuras de datos compartidas entre sensores, detectores y dashboard."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class LecturaCPU:
    nombre: str
    uso_total: float
    nucleos_uso: list[float]
    temperatura: float | None
    nucleos_fisicos: int
    nucleos_logicos: int
    frecuencia_mhz: float | None


@dataclass
class LecturaMemoria:
    uso_pct: float
    usada_bytes: int
    total_bytes: int


@dataclass
class LecturaDisco:
    nombre: str
    uso_espacio_pct: float
    usado_bytes: int
    total_bytes: int
    libre_bytes: int
    actividad_pct: float | None
    lectura_bps: float
    escritura_bps: float
    temperatura: float | None


@dataclass
class LecturaGPU:
    nombre: str
    uso_pct: float | None
    temperatura: float | None
    vram_usada_bytes: int | None
    vram_total_bytes: int | None

    @property
    def vram_pct(self) -> float | None:
        if self.vram_usada_bytes is None or not self.vram_total_bytes:
            return None
        return self.vram_usada_bytes / self.vram_total_bytes * 100.0


@dataclass
class LecturaRed:
    interfaz: str
    bajada_bps: float
    subida_bps: float
    capacidad_mbps: float | None       # None si el SO no informa la velocidad
    uso_enlace_pct: float
    temperatura: float | None


# LABORATORIO
@dataclass
class LecturaConexion:
    conectada: bool
    interfaz: str | None               # interfaz que da la conexión (None si no hay)


@dataclass
class Instantanea:
    """Foto completa del sistema en un instante."""
    marca_tiempo: float = field(default_factory=time.time)
    cpu: LecturaCPU | None = None
    memoria: LecturaMemoria | None = None
    disco: LecturaDisco | None = None
    gpu: LecturaGPU | None = None
    red: LecturaRed | None = None
    conexion: LecturaConexion | None = None   # LABORATORIO
