"""Modo consola: imprime un resumen por ciclo (útil sin entorno gráfico)."""
from __future__ import annotations

import time

import config
from alertas import crear_reproductor   # LABORATORIO
from eventos import BusEventos, Evento
from formatos import (formato_bytes, formato_porcentaje, formato_temperatura,
                      formato_velocidad)
from modelos import Instantanea
from nodo import NodoTelemetria


def resumen(inst: Instantanea) -> str:
    lineas = []
    if inst.cpu:
        c = inst.cpu
        lineas.append(f"CPU   {formato_porcentaje(c.uso_total):>6}  {formato_temperatura(c.temperatura):>7}  "
                      f"{c.nucleos_logicos} hilos / {c.nucleos_fisicos} núcleos  [{c.nombre}]")
    if inst.memoria:
        m = inst.memoria
        lineas.append(f"RAM   {formato_porcentaje(m.uso_pct):>6}  {formato_bytes(m.usada_bytes)} / "
                      f"{formato_bytes(m.total_bytes)}")
    if inst.disco:
        d = inst.disco
        lineas.append(f"DISCO {formato_porcentaje(d.uso_espacio_pct):>6}  {formato_temperatura(d.temperatura):>7}  "
                      f"{formato_bytes(d.usado_bytes)} / {formato_bytes(d.total_bytes)}  "
                      f"L {formato_velocidad(d.lectura_bps)}  E {formato_velocidad(d.escritura_bps)}")
    if inst.gpu:
        g = inst.gpu
        vram = (f"{formato_bytes(g.vram_usada_bytes)} / {formato_bytes(g.vram_total_bytes)}"
                if g.vram_total_bytes else config.TEXTO_NO_DISPONIBLE)
        lineas.append(f"GPU   {formato_porcentaje(g.uso_pct):>6}  {formato_temperatura(g.temperatura):>7}  "
                      f"VRAM {vram}  [{g.nombre}]")
    else:
        lineas.append("GPU   no detectada")
    if inst.red:
        r = inst.red
        lineas.append(f"RED   ↓ {formato_velocidad(r.bajada_bps)}  ↑ {formato_velocidad(r.subida_bps)}  [{r.interfaz}]")
    return "\n".join(lineas)


def ejecutar(silencioso: bool = False) -> None:  # LABORATORIO: + silencioso
    bus = BusEventos()
    bus.suscribir(config.EVENTO_TODOS, lambda e: imprimir_evento(e))
    reproductor = crear_reproductor(bus, silencioso)        # LABORATORIO
    nodo = NodoTelemetria(bus, reproductor)                 # LABORATORIO: + reproductor
    print(f"Fuente de datos: {nodo.descripcion_fuente}")
    print(f"Sonido: {reproductor.nombre_backend}{' [SILENCIOSO]' if silencioso else ''}")  # LABORATORIO
    nodo.iniciar()
    ultima_secuencia = 0
    try:
        while True:
            secuencia, inst = nodo.ultima()
            if inst is not None and secuencia != ultima_secuencia:
                ultima_secuencia = secuencia
                print(f"\n--- {time.strftime('%H:%M:%S', time.localtime(inst.marca_tiempo))} ---")
                print(resumen(inst))
            time.sleep(config.INTERVALO_REFRESCO_UI_MS / config.MS_POR_S)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.detener()


def imprimir_evento(evento: Evento) -> None:
    print(f"  >> [{evento.severidad.upper()}] {evento.componente}: {evento.mensaje}")
