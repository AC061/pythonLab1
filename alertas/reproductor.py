# LABORATORIO: archivo nuevo completo.
"""Reproductor de alertas no bloqueante.

Las alertas se encolan en un `deque` junto con su marca de tiempo. En cada
vuelta del ciclo de monitoreo se llama a `actualizar()`, que:

1. no hace nada si todavía suena la alerta anterior (compara el reloj con la
   marca de tiempo en la que terminará);
2. descarta las alertas que caducaron esperando en la cola;
3. inicia la siguiente de forma asíncrona y anota cuándo terminará.

Nunca hay `sleep` ni esperas: `actualizar()` siempre devuelve de inmediato.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable

import config
from eventos import BusEventos, Evento
from alertas.sonidos import Sonido, construir_catalogo


# LABORATORIO
class ReproductorAlertas:
    def __init__(
        self,
        bus: BusEventos,
        backend,
        catalogo: dict[str, Sonido] | None = None,
        reloj: Callable[[], float] = time.monotonic,
        silenciado: bool = config.ALERTAS_SILENCIOSO_POR_DEFECTO,
    ) -> None:
        self._bus = bus
        self._backend = backend
        self._catalogo = catalogo if catalogo is not None else construir_catalogo()
        self._reloj = reloj
        self.silenciado = silenciado
        self._cola: deque[tuple[str, float]] = deque(maxlen=config.ALERTAS_COLA_MAX)  # (nombre, marca_tiempo)
        self._cerrojo = threading.Lock()
        self._fin_actual = 0.0           # marca de tiempo en la que termina la alerta en curso

    # ------------------------------------------------------------------ propiedades
    @property
    def nombres(self) -> list[str]:
        return list(self._catalogo)

    @property
    def pendientes(self) -> int:
        with self._cerrojo:
            return len(self._cola)

    @property
    def reproduciendo(self) -> bool:
        return self._reloj() < self._fin_actual

    @property
    def nombre_backend(self) -> str:
        return self._backend.nombre

    # ------------------------------------------------------------------ cola
    def conectar(self) -> None:
        """Se suscribe al bus para cada evento que tenga un sonido asignado."""
        for nombre in self._catalogo:
            self._bus.suscribir(nombre, self._al_evento)

    def _al_evento(self, evento: Evento) -> None:
        self.encolar(evento.nombre)

    def encolar(self, nombre: str) -> bool:
        """Agrega una alerta a la cola. Devuelve False si se ignora (desconocida o repetida)."""
        if nombre not in self._catalogo:
            return False
        with self._cerrojo:
            if any(pendiente == nombre for pendiente, _ in self._cola):
                return False
            self._cola.append((nombre, self._reloj()))   # con maxlen, descarta la más antigua si está llena
        return True

    # ------------------------------------------------------------------ ciclo
    def actualizar(self) -> str | None:
        """Avanza la cola un paso. Devuelve el nombre de la alerta iniciada, si hubo."""
        ahora = self._reloj()
        if ahora < self._fin_actual:
            return None
        with self._cerrojo:
            while self._cola:
                nombre, marca = self._cola.popleft()
                if ahora - marca <= config.ALERTAS_CADUCIDAD_S:
                    break
            else:
                return None
        self._iniciar(nombre, ahora)
        return nombre

    def _iniciar(self, nombre: str, ahora: float) -> None:
        sonido = self._catalogo[nombre]
        if self.silenciado:
            self._fin_actual = ahora          # sin sonido no hay nada que esperar
        else:
            self._backend.reproducir(nombre, sonido.wav)
            self._fin_actual = ahora + sonido.duracion_s + config.ALERTAS_PAUSA_ENTRE_S
        estado = " (silenciada)" if self.silenciado else ""
        self._bus.emitir(Evento(
            nombre=config.EVENTO_ALERTA_SONORA,
            componente=config.ALERTAS_COMPONENTE,
            mensaje=f"♪ {nombre}{estado}",
            severidad=config.SEVERIDAD_INFO,
        ))

    def cerrar(self) -> None:
        self._backend.cerrar()


# LABORATORIO
def crear_reproductor(bus: BusEventos, silencioso: bool = config.ALERTAS_SILENCIOSO_POR_DEFECTO,
                      ) -> ReproductorAlertas:
    """Crea el reproductor con el mejor backend disponible y lo suscribe al bus.

    En modo silencioso el backend real queda listo, pero no se emite sonido;
    se puede reactivar después cambiando `reproductor.silenciado`.
    """
    from alertas.backends import crear_backend
    reproductor = ReproductorAlertas(bus, crear_backend(), silenciado=silencioso)
    reproductor.conectar()
    return reproductor
