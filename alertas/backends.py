# LABORATORIO: archivo nuevo completo.
"""Formas de emitir un sonido. Todas devuelven de inmediato (no bloquean).

- Winsound (Windows): `PlaySound` con SND_ASYNC desde memoria.
- Proceso externo (Linux/macOS): lanza `pw-play`, `paplay`, `aplay` o `afplay`
  con `Popen`, que no espera a que termine.
- Campana del sistema: último recurso si no hay reproductor.
- Silencioso: no emite nada.

No se usa `winsound.Beep` porque bloquea durante todo el tono.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

import config


# LABORATORIO
class BackendSilencioso:
    nombre = "silencioso"

    def reproducir(self, clave: str, wav: bytes) -> None:
        return None

    def cerrar(self) -> None:
        return None


# LABORATORIO
class BackendWinsound:
    nombre = "winsound"

    def __init__(self) -> None:
        import winsound  # solo existe en Windows
        self._winsound = winsound

    def reproducir(self, clave: str, wav: bytes) -> None:
        self._winsound.PlaySound(wav, self._winsound.SND_MEMORY | self._winsound.SND_ASYNC)

    def cerrar(self) -> None:
        self._winsound.PlaySound(None, self._winsound.SND_PURGE)


# LABORATORIO
class BackendProceso:
    nombre = "proceso externo"

    def __init__(self, ejecutable: str) -> None:
        self._ejecutable = ejecutable
        self.nombre = f"proceso externo ({os.path.basename(ejecutable)})"
        self._carpeta = tempfile.mkdtemp(prefix=config.ALERTAS_PREFIJO_TEMP)
        self._rutas: dict[str, str] = {}
        self._proceso: subprocess.Popen | None = None

    def reproducir(self, clave: str, wav: bytes) -> None:
        ruta = self._rutas.get(clave)
        if ruta is None:
            ruta = os.path.join(self._carpeta, f"{clave}.wav")
            with open(ruta, "wb") as archivo:
                archivo.write(wav)
            self._rutas[clave] = ruta
        if self._proceso is not None and self._proceso.poll() is None:
            self._proceso.terminate()
        # Popen devuelve de inmediato; el sonido se reproduce en otro proceso.
        self._proceso = subprocess.Popen(
            [self._ejecutable, ruta],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def cerrar(self) -> None:
        if self._proceso is not None and self._proceso.poll() is None:
            self._proceso.terminate()
        shutil.rmtree(self._carpeta, ignore_errors=True)


# LABORATORIO
class BackendCampana:
    nombre = "campana del sistema"

    def reproducir(self, clave: str, wav: bytes) -> None:
        sys.stdout.write(config.ALERTAS_CAMPANA)
        sys.stdout.flush()

    def cerrar(self) -> None:
        return None


# LABORATORIO
def crear_backend():
    """Elige el mejor backend disponible en este sistema."""
    if sys.platform.startswith("win"):
        try:
            return BackendWinsound()
        except ImportError:
            pass
    for candidato in config.ALERTAS_REPRODUCTORES_EXTERNOS:
        ruta = shutil.which(candidato)
        if ruta:
            return BackendProceso(ruta)
    return BackendCampana()
