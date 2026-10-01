"""Ventana principal: encabezado, tarjetas por componente y registro de eventos."""
from __future__ import annotations

import platform
import queue
import time

import customtkinter as ctk
import psutil

import config
from eventos import BusEventos, Evento
from formatos import formato_duracion
from nodo import NodoTelemetria
from tarjetas import TarjetaCPU, TarjetaDisco, TarjetaGPU, TarjetaRed


class Dashboard(ctk.CTk):
    def __init__(self, nodo: NodoTelemetria, bus: BusEventos) -> None:
        ctk.set_appearance_mode(config.APARIENCIA_INICIAL)
        ctk.set_default_color_theme(config.TEMA_COLOR)
        super().__init__()
        self.title(config.TITULO_APP)
        self.geometry(config.GEOMETRIA_INICIAL)
        self.minsize(config.ANCHO_MINIMO, config.ALTO_MINIMO)

        self._nodo = nodo
        self._secuencia = 0
        self._eventos: queue.Queue[Evento] = queue.Queue()
        bus.suscribir(config.EVENTO_TODOS, self._eventos.put)  # seguro entre hilos

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._crear_encabezado()
        self._crear_tarjetas()
        self._crear_registro()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(config.INTERVALO_REFRESCO_UI_MS, self._refrescar)

    # ------------------------------------------------------------------ construcción
    def _crear_encabezado(self) -> None:
        marco = ctk.CTkFrame(self, fg_color="transparent")
        marco.grid(row=0, column=0, sticky="ew", padx=config.PAD_VENTANA, pady=(config.PAD_VENTANA, 0))
        marco.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            marco, text=config.TITULO_APP, anchor="w",
            font=ctk.CTkFont(size=config.FUENTE_TITULO_APP, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self._sistema = ctk.CTkLabel(
            marco, anchor="w", text_color=config.COLOR_NEUTRO,
            font=ctk.CTkFont(size=config.FUENTE_SUBTITULO),
            text=f"{platform.node()} · {platform.system()} {platform.release()} · "
                 f"Fuente: {self._nodo.descripcion_fuente}",
        )
        self._sistema.grid(row=1, column=0, sticky="w")

        derecha = ctk.CTkFrame(marco, fg_color="transparent")
        derecha.grid(row=0, column=1, rowspan=2, sticky="e")
        self._estado = ctk.CTkLabel(derecha, text="Esperando datos…", anchor="e",
                                    font=ctk.CTkFont(size=config.FUENTE_SUBTITULO))
        self._estado.grid(row=0, column=0, sticky="e")
        self._encendido = ctk.CTkLabel(derecha, text="", anchor="e", text_color=config.COLOR_NEUTRO,
                                       font=ctk.CTkFont(size=config.FUENTE_SUBTITULO))
        self._encendido.grid(row=1, column=0, sticky="e")
        self._interruptor = ctk.CTkSwitch(derecha, text="Modo oscuro", command=self._cambiar_tema)
        if config.APARIENCIA_INICIAL == "dark":
            self._interruptor.select()
        self._interruptor.grid(row=0, column=1, rowspan=2, padx=(config.PAD_VENTANA, 0))
        self._crear_barra_alertas(marco)  # LABORATORIO

    # LABORATORIO: indicador de conexión + controles del sonido
    def _crear_barra_alertas(self, marco: ctk.CTkFrame) -> None:
        barra = ctk.CTkFrame(marco, fg_color="transparent")
        barra.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(config.PAD_INTERNO, 0))
        barra.grid_columnconfigure(0, weight=1)

        self._conexion = ctk.CTkLabel(barra, text=config.TEXTO_NO_DISPONIBLE, anchor="w",
                                      text_color=config.COLOR_NEUTRO,
                                      font=ctk.CTkFont(size=config.FUENTE_VALOR, weight="bold"))
        self._conexion.grid(row=0, column=0, sticky="w")

        reproductor = self._nodo.reproductor
        if reproductor is None:
            return
        self._sonido = ctk.CTkSwitch(barra, text=config.TEXTO_SONIDO_ACTIVO, command=self._cambiar_sonido)
        if not reproductor.silenciado:
            self._sonido.select()
        self._sonido.grid(row=0, column=1, padx=config.PAD_VENTANA)

        self._prueba = ctk.StringVar(value=reproductor.nombres[0])
        ctk.CTkOptionMenu(barra, values=reproductor.nombres, variable=self._prueba,
                          width=config.ANCHO_MENU_PRUEBA).grid(row=0, column=2, padx=config.PAD_INTERNO)
        ctk.CTkButton(barra, text=config.TEXTO_BOTON_PROBAR, command=self._probar_alerta,
                      width=config.ANCHO_BOTON_PRUEBA).grid(row=0, column=3)

    # LABORATORIO
    def _cambiar_sonido(self) -> None:
        self._nodo.reproductor.silenciado = not self._sonido.get()

    # LABORATORIO
    def _probar_alerta(self) -> None:
        self._nodo.reproductor.encolar(self._prueba.get())

    def _crear_tarjetas(self) -> None:
        marco = ctk.CTkFrame(self, fg_color="transparent")
        marco.grid(row=1, column=0, sticky="nsew", padx=config.PAD_VENTANA, pady=config.PAD_VENTANA)
        self._tarjetas = [TarjetaCPU(marco), TarjetaGPU(marco), TarjetaDisco(marco), TarjetaRed(marco)]
        filas = -(-len(self._tarjetas) // config.TARJETAS_COLUMNAS)
        for columna in range(config.TARJETAS_COLUMNAS):
            marco.grid_columnconfigure(columna, weight=1, uniform="tarjetas")
        for fila in range(filas):
            marco.grid_rowconfigure(fila, weight=1, uniform="filas")
        for indice, tarjeta in enumerate(self._tarjetas):
            fila, columna = divmod(indice, config.TARJETAS_COLUMNAS)
            tarjeta.grid(row=fila, column=columna, sticky="nsew",
                         padx=config.PAD_INTERNO, pady=config.PAD_INTERNO)

    def _crear_registro(self) -> None:
        marco = ctk.CTkFrame(self, corner_radius=config.RADIO_TARJETA)
        marco.grid(row=2, column=0, sticky="ew", padx=config.PAD_VENTANA, pady=(0, config.PAD_VENTANA))
        marco.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(marco, text="Registro de eventos", anchor="w",
                     font=ctk.CTkFont(size=config.FUENTE_VALOR, weight="bold"),
                     ).grid(row=0, column=0, sticky="w", padx=config.PAD_TARJETA, pady=(config.PAD_INTERNO, 0))
        self._registro = ctk.CTkTextbox(marco, height=config.ALTO_LOG,
                                        font=ctk.CTkFont(size=config.FUENTE_LOG))
        self._registro.grid(row=1, column=0, sticky="ew", padx=config.PAD_TARJETA, pady=config.PAD_INTERNO)
        self._registro.tag_config(config.SEVERIDAD_ALERTA, foreground=config.COLOR_ALTO)
        self._registro.tag_config(config.SEVERIDAD_INFO, foreground=config.COLOR_INFO)
        self._registro.configure(state="disabled")

    # ------------------------------------------------------------------ ciclo de la UI
    def _refrescar(self) -> None:
        secuencia, inst = self._nodo.ultima()
        if inst is not None and secuencia != self._secuencia:
            self._secuencia = secuencia
            for tarjeta in self._tarjetas:
                tarjeta.actualizar(inst)
            hora = time.strftime("%H:%M:%S", time.localtime(inst.marca_tiempo))
            self._estado.configure(text=f"Actualizado {hora}")
            self._mostrar_conexion(inst)  # LABORATORIO
            self._encendido.configure(
                text=f"Encendido hace {formato_duracion(time.time() - psutil.boot_time())}")
        self._vaciar_eventos()
        self.after(config.INTERVALO_REFRESCO_UI_MS, self._refrescar)

    # LABORATORIO
    def _mostrar_conexion(self, inst) -> None:
        if inst.conexion is None:
            return
        if inst.conexion.conectada:
            self._conexion.configure(text=f"{config.TEXTO_CONECTADO} ({inst.conexion.interfaz})",
                                     text_color=config.COLOR_OK)
        else:
            self._conexion.configure(text=config.TEXTO_DESCONECTADO, text_color=config.COLOR_ALTO)

    def _vaciar_eventos(self) -> None:
        while True:
            try:
                evento = self._eventos.get_nowait()
            except queue.Empty:
                return
            self._agregar_evento(evento)

    def _agregar_evento(self, evento: Evento) -> None:
        hora = time.strftime("%H:%M:%S", time.localtime(evento.marca_tiempo))
        self._registro.configure(state="normal")
        self._registro.insert("end", f"[{hora}] {evento.componente}: {evento.mensaje}\n", evento.severidad)
        lineas = int(self._registro.index("end-1c").split(".")[0])
        if lineas > config.MAX_LINEAS_LOG:
            self._registro.delete("1.0", "2.0")
        self._registro.see("end")
        self._registro.configure(state="disabled")

    def _cambiar_tema(self) -> None:
        ctk.set_appearance_mode("dark" if self._interruptor.get() else "light")

    def _cerrar(self) -> None:
        self._nodo.detener()
        self.destroy()
