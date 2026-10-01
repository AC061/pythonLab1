"""Detectores de eventos por flanco con histéresis.

Un detector emite el evento "alto" solo al cruzar hacia arriba el umbral alto y
el evento "normal" solo al volver por debajo del umbral normal; mientras tanto
no repite nada. No conoce los sensores: solo lee la `Instantanea`.
"""
from __future__ import annotations

from typing import Callable, Iterable

import config
from eventos import Evento
from modelos import Instantanea


def _de(objeto, atributo: str):
    return getattr(objeto, atributo) if objeto is not None else None


def _trafico_kbs(inst: Instantanea) -> float | None:
    if inst.red is None:
        return None
    return (inst.red.bajada_bps + inst.red.subida_bps) / config.BYTES_KB


EXTRACTORES: dict[str, Callable[[Instantanea], float | None]] = {
    "cpu_uso": lambda i: _de(i.cpu, "uso_total"),
    "cpu_temp": lambda i: _de(i.cpu, "temperatura"),
    "memoria_uso": lambda i: _de(i.memoria, "uso_pct"),
    "gpu_uso": lambda i: _de(i.gpu, "uso_pct"),
    "gpu_temp": lambda i: _de(i.gpu, "temperatura"),
    "disco_espacio": lambda i: _de(i.disco, "uso_espacio_pct"),
    "disco_temp": lambda i: _de(i.disco, "temperatura"),
    "red_trafico_kbs": _trafico_kbs,
}


class DetectorUmbral:
    def __init__(self, definicion: dict, extractor: Callable[[Instantanea], float | None]) -> None:
        if definicion["normal"] >= definicion["alto"]:
            raise ValueError(f"Detector {definicion['id']}: 'normal' debe ser menor que 'alto'")
        self.definicion = definicion
        self._extractor = extractor
        self.activo = False

    def evaluar(self, inst: Instantanea) -> Evento | None:
        valor = self._extractor(inst)
        if valor is None:
            return None
        d = self.definicion
        if not self.activo and valor >= d["alto"]:
            self.activo = True
            return self._evento(d["evento_alto"], valor, config.SEVERIDAD_ALERTA, inst)
        if self.activo and valor <= d["normal"]:
            self.activo = False
            return self._evento(d["evento_normal"], valor, config.SEVERIDAD_INFO, inst)
        return None

    def _evento(self, nombre: str, valor: float, severidad: str, inst: Instantanea) -> Evento:
        return Evento(
            nombre=nombre,
            componente=self.definicion["componente"],
            mensaje=config.MENSAJES_EVENTOS[nombre].format(valor=valor),
            severidad=severidad,
            valor=valor,
            marca_tiempo=inst.marca_tiempo,
        )


def crear_detectores(definiciones: Iterable[dict] = config.DETECTORES) -> list[DetectorUmbral]:
    return [DetectorUmbral(d, EXTRACTORES[d["magnitud"]]) for d in definiciones]


# LABORATORIO: detector de pérdida/recuperación de conexión
class DetectorConexion:
    """Emite `red_desconectada` y `red_conectada` por flanco y, mientras la red
    siga caída, `red_sigue_desconectada` cada `recordatorio_s` segundos.

    El tiempo se toma de la marca de tiempo de la instantánea, no de un reloj
    propio ni de `sleep`, así que nunca bloquea y es fácil de probar.
    """

    def __init__(self, recordatorio_s: float = config.RED_RECORDATORIO_S) -> None:
        self._recordatorio_s = recordatorio_s
        self._conectada: bool | None = None     # None = aún sin observaciones
        self._desde = 0.0                       # instante en que se perdió la conexión
        self._ultimo_aviso = 0.0

    @property
    def conectada(self) -> bool | None:
        return self._conectada

    def evaluar(self, inst: Instantanea) -> Evento | None:
        if inst.conexion is None:
            return None
        ahora = inst.marca_tiempo
        nombres = config.CONEXION_EVENTOS

        if inst.conexion.conectada:
            recuperada = self._conectada is False
            self._conectada = True
            if recuperada:
                return self._evento(nombres["conectada"], ahora - self._desde,
                                    config.SEVERIDAD_INFO, ahora)
            return None

        if self._conectada is not False:                   # flanco: se perdió la conexión
            self._conectada = False
            self._desde = self._ultimo_aviso = ahora
            return self._evento(nombres["desconectada"], 0.0, config.SEVERIDAD_ALERTA, ahora)

        if ahora - self._ultimo_aviso >= self._recordatorio_s:   # recordatorio por tiempo
            self._ultimo_aviso = ahora
            return self._evento(nombres["recordatorio"], ahora - self._desde,
                                config.SEVERIDAD_ALERTA, ahora)
        return None

    def _evento(self, nombre: str, valor: float, severidad: str, ahora: float) -> Evento:
        return Evento(
            nombre=nombre,
            componente=config.CONEXION_COMPONENTE,
            mensaje=config.MENSAJES_EVENTOS[nombre].format(valor=valor),
            severidad=severidad,
            valor=valor,
            marca_tiempo=ahora,
        )
