"""Punto de entrada del monitor de sistema.

Uso:
    python main.py                  # interfaz gráfica (customtkinter)
    python main.py --consola        # resumen en texto, sin interfaz gráfica
    python main.py --silencioso     # sin sonido (modo para el salón de clases)
"""
from __future__ import annotations

import argparse
import logging
import sys

import config  # LABORATORIO


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor de sistema con tarjetas por componente")
    parser.add_argument("--consola", action="store_true", help="modo texto, sin interfaz gráfica")
    parser.add_argument("--silencioso", action="store_true",  # LABORATORIO
                        default=config.ALERTAS_SILENCIOSO_POR_DEFECTO,
                        help="no emitir alertas sonoras (los eventos se siguen registrando)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    if args.consola:
        import consola
        consola.ejecutar(silencioso=args.silencioso)  # LABORATORIO: + silencioso
        return 0

    try:
        from dashboard import Dashboard
    except ImportError as error:
        print(f"No se pudo cargar la interfaz gráfica: {error}\n"
              "Instale las dependencias (pip install -r requirements.txt) y, en Linux, "
              "el paquete del sistema con tkinter (Arch/Garuda: sudo pacman -S tk).",
              file=sys.stderr)
        return 1

    from alertas import crear_reproductor  # LABORATORIO
    from eventos import BusEventos
    from nodo import NodoTelemetria

    bus = BusEventos()
    reproductor = crear_reproductor(bus, silencioso=args.silencioso)  # LABORATORIO
    nodo = NodoTelemetria(bus, reproductor)                           # LABORATORIO: + reproductor
    app = Dashboard(nodo, bus)
    nodo.iniciar()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
