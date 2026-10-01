"""Nodo de telemetría: ciclo de monitoreo en un hilo propio.

El hilo muestrea los sensores, evalúa los detectores y publica los eventos en el
bus. La interfaz nunca toca el hardware: solo consulta la última instantánea,
así que un sensor lento no congela la ventana.
"""
from __future__ import annotations

import logging
import threading
import time

import config
from conexion import SensorConexion                          # LABORATORIO
from cpu import SensorCPU
from detectores import DetectorConexion, crear_detectores   # LABORATORIO: + DetectorConexion
from disco import SensorDisco
from eventos import BusEventos
from gpu import SensorGPU
from hardware import ProveedorLHM
from memoria import SensorMemoria
from modelos import Instantanea
from red import SensorRed

registro = logging.getLogger(__name__)


class NodoTelemetria:
    def __init__(self, bus: BusEventos, reproductor=None, sensores: dict | None = None) -> None:  # LABORATORIO: + reproductor, sensores
        self.bus = bus
        self.reproductor = reproductor                       # LABORATORIO: puede ser None
        self.lhm = ProveedorLHM()
        self._sensores = {
            "cpu": SensorCPU(self.lhm),
            "memoria": SensorMemoria(),
            "disco": SensorDisco(self.lhm),
            "gpu": SensorGPU(self.lhm),
            "red": SensorRed(self.lhm),
            "conexion": SensorConexion(),                    # LABORATORIO
        }
        if sensores is not None:                             # LABORATORIO: permite inyectar sensores (pruebas)
            self._sensores.update(sensores)
        self._detectores = crear_detectores()
        self._detectores.append(DetectorConexion())          # LABORATORIO
        self._ultima: Instantanea | None = None
        self._secuencia = 0
        self._cerrojo = threading.Lock()
        self._detener = threading.Event()
        self._hilo: threading.Thread | None = None

    @property
    def descripcion_fuente(self) -> str:
        return self.lhm.descripcion

    # ------------------------------------------------------------------ muestreo
    def muestrear(self) -> Instantanea:
        """Lee todos los sensores una vez. Un sensor que falle queda en None."""
        self.lhm.actualizar()
        inst = Instantanea()
        for nombre, sensor in self._sensores.items():
            try:
                setattr(inst, nombre, sensor.leer())
            except Exception:
                registro.exception("Fallo del sensor %s", nombre)
        return inst

    def procesar(self, inst: Instantanea) -> None:
        """Evalúa los detectores y publica sus eventos."""
        for detector in self._detectores:
            evento = detector.evaluar(inst)
            if evento is not None:
                self.bus.emitir(evento)

    # ------------------------------------------------------------------ hilo
    def iniciar(self) -> None:
        if self._hilo is not None and self._hilo.is_alive():
            return
        self._detener.clear()
        self._hilo = threading.Thread(target=self._ciclo, name="monitoreo", daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._detener.set()
        if self._hilo is not None:
            self._hilo.join(timeout=config.ESPERA_CIERRE_HILO_S)
        if self.reproductor is not None:                     # LABORATORIO
            self.reproductor.cerrar()                        # LABORATORIO
        self.lhm.cerrar()

    def _ciclo(self) -> None:
        while not self._detener.is_set():
            inicio = time.monotonic()
            try:
                inst = self.muestrear()
                with self._cerrojo:
                    self._ultima = inst
                    self._secuencia += 1
                self.procesar(inst)
                if self.reproductor is not None:             # LABORATORIO: avanza la cola de sonidos sin esperar
                    self.reproductor.actualizar()            # LABORATORIO
            except Exception:
                registro.exception("Fallo en el ciclo de monitoreo")
            restante = config.INTERVALO_MONITOREO_S - (time.monotonic() - inicio)
            self._detener.wait(max(restante, 0.0))

    # ------------------------------------------------------------------ consulta (UI)
    def ultima(self) -> tuple[int, Instantanea | None]:
        """(número de secuencia, última instantánea). La UI compara la secuencia."""
        with self._cerrojo:
            return self._secuencia, self._ultima
