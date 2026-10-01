"""Componentes visuales reutilizables de customtkinter."""
from __future__ import annotations

import customtkinter as ctk

import config
from formatos import color_temperatura, color_uso


class Metrica(ctk.CTkFrame):
    """Título + valor a la derecha + barra de progreso."""

    def __init__(self, master, titulo: str, grande: bool = False) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._etiqueta = ctk.CTkLabel(
            self, text=titulo, anchor="w",
            font=ctk.CTkFont(size=config.FUENTE_ETIQUETA),
        )
        tamano = config.FUENTE_VALOR_GRANDE if grande else config.FUENTE_VALOR
        self._valor = ctk.CTkLabel(
            self, text=config.TEXTO_NO_DISPONIBLE, anchor="e",
            font=ctk.CTkFont(size=tamano, weight="bold"),
        )
        self._barra = ctk.CTkProgressBar(
            self, height=config.ALTO_BARRA_GRANDE if grande else config.ALTO_BARRA,
        )
        self._barra.set(0)
        self._etiqueta.grid(row=0, column=0, sticky="w")
        self._valor.grid(row=0, column=1, sticky="e")
        self._barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(config.PAD_MICRO, 0))

    def actualizar(self, texto: str, fraccion: float | None, color: str) -> None:
        self._valor.configure(text=texto, text_color=color)
        self._barra.set(min(max(fraccion or 0.0, 0.0), 1.0))
        self._barra.configure(progress_color=color)

    # Atajos para los casos más comunes ------------------------------------
    def mostrar_porcentaje(self, pct: float | None, texto: str | None = None) -> None:
        etiqueta = texto if texto is not None else (
            config.TEXTO_NO_DISPONIBLE if pct is None else f"{pct:.0f}%")
        fraccion = None if pct is None else pct / config.PORCENTAJE_MAX
        self.actualizar(etiqueta, fraccion, color_uso(pct))

    def mostrar_temperatura(self, grados: float | None) -> None:
        texto = config.TEXTO_NO_DISPONIBLE if grados is None else f"{grados:.0f} °C"
        fraccion = None if grados is None else grados / config.TEMP_ESCALA_MAX
        self.actualizar(texto, fraccion, color_temperatura(grados))


class Tarjeta(ctk.CTkFrame):
    """Marco base de cada componente: encabezado + nombre del dispositivo + contenido."""

    def __init__(self, master, titulo: str) -> None:
        super().__init__(master, corner_radius=config.RADIO_TARJETA)
        self.grid_columnconfigure(0, weight=1)
        self._fila = 0

        self._titulo = ctk.CTkLabel(
            self, text=titulo, anchor="w",
            font=ctk.CTkFont(size=config.FUENTE_TITULO_TARJETA, weight="bold"),
        )
        self._nombre = ctk.CTkLabel(
            self, text="", anchor="w", justify="left",
            wraplength=config.ANCHO_NOMBRE_DISPOSITIVO, text_color=config.COLOR_NEUTRO,
            font=ctk.CTkFont(size=config.FUENTE_SUBTITULO),
        )
        self.agregar(self._titulo, padx=config.PAD_TARJETA, pady=(config.PAD_TARJETA, 0))
        self.agregar(self._nombre, padx=config.PAD_TARJETA, pady=(0, config.PAD_INTERNO))

    def agregar(self, widget, padx: int = config.PAD_TARJETA, pady=config.PAD_INTERNO) -> None:
        widget.grid(row=self._fila, column=0, sticky="ew", padx=padx, pady=pady)
        self._fila += 1

    def crear_metrica(self, titulo: str, grande: bool = False) -> Metrica:
        metrica = Metrica(self, titulo, grande)
        self.agregar(metrica)
        return metrica

    def crear_texto(self, inicial: str = "") -> ctk.CTkLabel:
        etiqueta = ctk.CTkLabel(
            self, text=inicial, anchor="w", justify="left",
            font=ctk.CTkFont(size=config.FUENTE_ETIQUETA),
        )
        self.agregar(etiqueta)
        return etiqueta

    def poner_nombre(self, nombre: str) -> None:
        self._nombre.configure(text=nombre)

    def actualizar(self, inst) -> None:  # pragma: no cover - lo implementa cada tarjeta
        raise NotImplementedError
