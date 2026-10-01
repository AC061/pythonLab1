# LABORATORIO: archivo nuevo completo.
"""Paquete `alertas`: sonidos de alerta que reaccionan a los eventos del nodo."""
from alertas.backends import (BackendCampana, BackendProceso, BackendSilencioso,
                              BackendWinsound, crear_backend)
from alertas.reproductor import ReproductorAlertas, crear_reproductor
from alertas.sonidos import Sonido, construir_catalogo, duracion_patron_s, sintetizar_wav

__all__ = [
    "BackendCampana", "BackendProceso", "BackendSilencioso", "BackendWinsound",
    "ReproductorAlertas", "Sonido", "construir_catalogo", "crear_backend",
    "crear_reproductor", "duracion_patron_s", "sintetizar_wav",
]
