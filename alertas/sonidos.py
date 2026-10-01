# LABORATORIO: archivo nuevo completo.
"""Síntesis de los sonidos de alerta a partir de los patrones de config.py.

Cada patrón se convierte en un WAV en memoria (onda senoidal de 16 bits) con
una pequeña rampa de entrada y salida para evitar "clics". Solo usa la
biblioteca estándar.
"""
from __future__ import annotations

import io
import math
import sys
import wave
from array import array
from dataclasses import dataclass
from typing import Iterable, Mapping

import config

Patron = tuple[tuple[int, int], ...]   # LABORATORIO: ((frecuencia_hz, duracion_ms), ...)


# LABORATORIO
@dataclass(frozen=True)
class Sonido:
    nombre: str
    patron: Patron
    wav: bytes
    duracion_s: float


# LABORATORIO
def duracion_patron_s(patron: Patron) -> float:
    return sum(duracion for _, duracion in patron) / config.MS_POR_S


# LABORATORIO
def _muestras_segmento(frecuencia: int, duracion_ms: int) -> array:
    tasa = config.AUDIO_TASA_HZ
    total = int(tasa * duracion_ms / config.MS_POR_S)
    rampa = int(tasa * config.AUDIO_FADE_MS / config.MS_POR_S)
    amplitud = config.AUDIO_VOLUMEN * config.AUDIO_AMPLITUD_MAX
    muestras = array("h")
    for i in range(total):
        if frecuencia == config.AUDIO_SILENCIO_HZ:
            muestras.append(0)
            continue
        envolvente = min(1.0, i / rampa, (total - 1 - i) / rampa) if rampa else 1.0
        muestras.append(int(amplitud * envolvente * math.sin(math.tau * frecuencia * i / tasa)))
    return muestras


# LABORATORIO
def sintetizar_wav(patron: Patron) -> bytes:
    muestras = array("h")
    for frecuencia, duracion_ms in patron:
        muestras.extend(_muestras_segmento(frecuencia, duracion_ms))
    if sys.byteorder == "big":          # WAV siempre es little-endian
        muestras.byteswap()
    memoria = io.BytesIO()
    with wave.open(memoria, "wb") as archivo:
        archivo.setnchannels(config.AUDIO_CANALES)
        archivo.setsampwidth(config.AUDIO_BYTES_POR_MUESTRA)
        archivo.setframerate(config.AUDIO_TASA_HZ)
        archivo.writeframes(muestras.tobytes())
    return memoria.getvalue()


# LABORATORIO
def construir_catalogo(
    definiciones: Mapping[str, Iterable[tuple[int, int]]] = config.ALERTAS_SONORAS,
) -> dict[str, Sonido]:
    catalogo: dict[str, Sonido] = {}
    for nombre, segmentos in definiciones.items():
        patron: Patron = tuple((int(f), int(d)) for f, d in segmentos)
        catalogo[nombre] = Sonido(nombre, patron, sintetizar_wav(patron), duracion_patron_s(patron))
    return catalogo
