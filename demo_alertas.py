# LABORATORIO: archivo nuevo completo.
"""Prueba en vivo de las alertas sonoras.

Simula un ciclo de monitoreo que "late" cada DEMO_PERIODO_S mientras suenan
todas las alertas, una tras otra. Si el sonido bloqueara, los latidos se
detendrían durante cada alerta; aquí se imprimen sin interrupción y se mide
cuánto tarda `actualizar()` en cada vuelta.

Uso:
    python demo_alertas.py                # con sonido
    python demo_alertas.py --silencioso   # sin sonido
"""
from __future__ import annotations

import argparse
import time

import config
from alertas import crear_reproductor
from eventos import BusEventos, Evento


def ejecutar(silencioso: bool) -> None:
    bus = BusEventos()
    reproductor = crear_reproductor(bus, silencioso)
    bus.suscribir(config.EVENTO_ALERTA_SONORA, lambda e: print(f"      {e.mensaje}"))
    print(f"Backend: {reproductor.nombre_backend}{' [SILENCIOSO]' if silencioso else ''}")

    for nombre in reproductor.nombres:      # todos los eventos llegan de golpe
        bus.emitir(Evento(nombre, config.DEMO_COMPONENTE, nombre))
    print(f"Alertas en cola: {reproductor.pendientes}\n")

    inicio = time.monotonic()
    ciclo = 0
    peor_actualizar = 0.0
    while reproductor.pendientes or reproductor.reproduciendo:
        ciclo += 1
        t0 = time.monotonic()
        reproductor.actualizar()
        peor_actualizar = max(peor_actualizar, time.monotonic() - t0)
        print(f"[ciclo {ciclo:>3}] t={t0 - inicio:5.2f} s  pendientes={reproductor.pendientes}  "
              f"sonando={'sí' if reproductor.reproduciendo else 'no'}")
        time.sleep(config.DEMO_PERIODO_S)   # hace de "resto del ciclo de monitoreo"

    reproductor.cerrar()
    print(f"\nCiclos ejecutados mientras sonaban las alertas: {ciclo}")
    print(f"Mayor duración de actualizar(): {peor_actualizar * config.MS_POR_S:.2f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba en vivo de las alertas sonoras")
    parser.add_argument("--silencioso", action="store_true", help="no emitir sonido")
    ejecutar(parser.parse_args().silencioso)


if __name__ == "__main__":
    main()
