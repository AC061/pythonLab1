"""Bus de eventos sencillo (publicar / suscribir)."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

import config

registro = logging.getLogger(__name__)


@dataclass(frozen=True)
class Evento:
    nombre: str
    componente: str
    mensaje: str
    severidad: str = config.SEVERIDAD_INFO
    valor: float | None = None
    marca_tiempo: float = field(default_factory=time.time)


class BusEventos:
    """Entrega cada evento a los suscriptores de su nombre y a los comodín."""

    def __init__(self) -> None:
        self._suscriptores: dict[str, list[Callable[[Evento], None]]] = defaultdict(list)

    def suscribir(self, nombre: str, manejador: Callable[[Evento], None]) -> None:
        self._suscriptores[nombre].append(manejador)

    def emitir(self, evento: Evento) -> None:
        manejadores = (
            *self._suscriptores.get(evento.nombre, ()),
            *self._suscriptores.get(config.EVENTO_TODOS, ()),
        )
        for manejador in manejadores:
            try:
                manejador(evento)
            except Exception:  # un suscriptor defectuoso no debe afectar a los demás
                registro.exception("Error en manejador del evento %s", evento.nombre)
