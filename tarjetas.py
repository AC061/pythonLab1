"""Una tarjeta por componente: CPU, GPU, Disco y Red."""
from __future__ import annotations

import customtkinter as ctk

import config
from componentes import Tarjeta
from formatos import (color_uso, formato_bytes, formato_frecuencia,
                      formato_velocidad)
from modelos import Instantanea


class _CeldaNucleo(ctk.CTkFrame):
    """Mini barra de un núcleo (hilo lógico)."""

    def __init__(self, master, indice: int) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._indice = indice
        self._texto = ctk.CTkLabel(self, text="", anchor="w",
                                   font=ctk.CTkFont(size=config.FUENTE_NUCLEO))
        self._barra = ctk.CTkProgressBar(self, height=config.ALTO_BARRA_NUCLEO)
        self._barra.set(0)
        self._texto.grid(row=0, column=0, sticky="w")
        self._barra.grid(row=1, column=0, sticky="ew")

    def actualizar(self, pct: float) -> None:
        self._texto.configure(text=f"Núcleo {self._indice}: {pct:.0f}%")
        self._barra.set(pct / config.PORCENTAJE_MAX)
        self._barra.configure(progress_color=color_uso(pct))


class TarjetaCPU(Tarjeta):
    def __init__(self, master) -> None:
        super().__init__(master, "CPU")
        self._uso = self.crear_metrica("Uso total", grande=True)
        self._temp = self.crear_metrica("Temperatura")
        self._ram = self.crear_metrica("Memoria RAM")
        self._capacidad = self.crear_texto()
        self._contenedor = ctk.CTkFrame(self, fg_color="transparent")
        for columna in range(config.NUCLEOS_COLUMNAS):
            self._contenedor.grid_columnconfigure(columna, weight=1, uniform="nucleos")
        self.agregar(self._contenedor, pady=(config.PAD_INTERNO, config.PAD_TARJETA))
        self._celdas: list[_CeldaNucleo] = []

    def actualizar(self, inst: Instantanea) -> None:
        cpu, ram = inst.cpu, inst.memoria
        if cpu is not None:
            self.poner_nombre(cpu.nombre)
            self._uso.mostrar_porcentaje(cpu.uso_total)
            self._temp.mostrar_temperatura(cpu.temperatura)
            self._capacidad.configure(
                text=f"Capacidad: {cpu.nucleos_fisicos} núcleos físicos · "
                     f"{cpu.nucleos_logicos} lógicos · {formato_frecuencia(cpu.frecuencia_mhz)}")
            self._actualizar_nucleos(cpu.nucleos_uso)
        if ram is not None:
            self._ram.mostrar_porcentaje(
                ram.uso_pct, f"{formato_bytes(ram.usada_bytes)} / {formato_bytes(ram.total_bytes)}")

    def _actualizar_nucleos(self, usos: list[float]) -> None:
        while len(self._celdas) < len(usos):
            celda = _CeldaNucleo(self._contenedor, len(self._celdas))
            fila, columna = divmod(len(self._celdas), config.NUCLEOS_COLUMNAS)
            celda.grid(row=fila, column=columna, sticky="ew",
                       padx=config.PAD_MICRO, pady=config.PAD_MICRO)
            self._celdas.append(celda)
        for celda, pct in zip(self._celdas, usos):
            celda.actualizar(pct)


class TarjetaGPU(Tarjeta):
    def __init__(self, master) -> None:
        super().__init__(master, "GPU")
        self._uso = self.crear_metrica("Uso", grande=True)
        self._temp = self.crear_metrica("Temperatura")
        self._vram = self.crear_metrica("Memoria de video (VRAM)")
        self._capacidad = self.crear_texto()

    def actualizar(self, inst: Instantanea) -> None:
        gpu = inst.gpu
        if gpu is None:
            self.poner_nombre("GPU no detectada")
            self._uso.mostrar_porcentaje(None)
            self._temp.mostrar_temperatura(None)
            self._vram.mostrar_porcentaje(None)
            self._capacidad.configure(text="Capacidad (VRAM): N/D")
            return
        self.poner_nombre(gpu.nombre)
        self._uso.mostrar_porcentaje(gpu.uso_pct)
        self._temp.mostrar_temperatura(gpu.temperatura)
        if gpu.vram_total_bytes:
            self._vram.mostrar_porcentaje(
                gpu.vram_pct,
                f"{formato_bytes(gpu.vram_usada_bytes)} / {formato_bytes(gpu.vram_total_bytes)}")
        else:
            self._vram.mostrar_porcentaje(None)
        self._capacidad.configure(text=f"Capacidad (VRAM): {formato_bytes(gpu.vram_total_bytes)}")


class TarjetaDisco(Tarjeta):
    def __init__(self, master) -> None:
        super().__init__(master, "Disco")
        self._uso = self.crear_metrica("Espacio usado", grande=True)
        self._temp = self.crear_metrica("Temperatura")
        self._actividad = self.crear_metrica("Actividad")
        self._velocidad = self.crear_texto()
        self._capacidad = self.crear_texto()

    def actualizar(self, inst: Instantanea) -> None:
        disco = inst.disco
        if disco is None:
            return
        self.poner_nombre(disco.nombre)
        self._uso.mostrar_porcentaje(disco.uso_espacio_pct)
        self._temp.mostrar_temperatura(disco.temperatura)
        self._actividad.mostrar_porcentaje(disco.actividad_pct)
        self._velocidad.configure(
            text=f"Lectura: {formato_velocidad(disco.lectura_bps)}   ·   "
                 f"Escritura: {formato_velocidad(disco.escritura_bps)}")
        self._capacidad.configure(
            text=f"Capacidad: {formato_bytes(disco.total_bytes)} "
                 f"(usado {formato_bytes(disco.usado_bytes)}, libre {formato_bytes(disco.libre_bytes)})")


class TarjetaRed(Tarjeta):
    def __init__(self, master) -> None:
        super().__init__(master, "Red")
        self._uso = self.crear_metrica("Uso del enlace", grande=True)
        self._temp = self.crear_metrica("Temperatura")
        self._bajada = self.crear_texto()
        self._subida = self.crear_texto()
        self._capacidad = self.crear_texto()

    def actualizar(self, inst: Instantanea) -> None:
        red = inst.red
        if red is None:
            return
        self.poner_nombre(red.interfaz)
        self._uso.mostrar_porcentaje(red.uso_enlace_pct)
        self._temp.mostrar_temperatura(red.temperatura)
        self._bajada.configure(text=f"↓ Bajada: {formato_velocidad(red.bajada_bps)}")
        self._subida.configure(text=f"↑ Subida: {formato_velocidad(red.subida_bps)}")
        if red.capacidad_mbps:
            self._capacidad.configure(text=f"Capacidad del enlace: {red.capacidad_mbps:.0f} Mbps")
        else:
            self._capacidad.configure(
                text=f"Capacidad del enlace: N/D (escala de referencia "
                     f"{config.RED_ESCALA_REFERENCIA_MBPS:.0f} Mbps)")
