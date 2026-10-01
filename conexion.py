# LABORATORIO: archivo nuevo completo.
"""Sensor de conexión: indica si el equipo está conectado a una red.

Se considera conectado si existe al menos una interfaz activa (no loopback ni
virtual) con una dirección IP que no sea de loopback ni de enlace local. Es una
comprobación local: no envía tráfico, por lo que no puede bloquear el ciclo.
No garantiza que haya salida a Internet.
"""
from __future__ import annotations

import ipaddress
import socket

import psutil

import config
from modelos import LecturaConexion


# LABORATORIO
def _direccion_util(direccion: str) -> bool:
    try:
        ip = ipaddress.ip_address(direccion.split("%")[0])  # IPv6 puede traer "%interfaz"
    except ValueError:
        return False
    return not (ip.is_loopback or ip.is_link_local or ip.is_unspecified)


# LABORATORIO
class SensorConexion:
    def __init__(self) -> None:
        self._familias = {getattr(socket, nombre) for nombre in config.CONEXION_FAMILIAS_DIRECCION}

    def leer(self) -> LecturaConexion:
        try:
            estados = psutil.net_if_stats()
            direcciones = psutil.net_if_addrs()
        except Exception:
            return LecturaConexion(conectada=False, interfaz=None)
        for nombre, estado in estados.items():
            if not estado.isup or nombre.startswith(config.RED_INTERFACES_IGNORADAS):
                continue
            for direccion in direcciones.get(nombre, ()):
                if direccion.family in self._familias and _direccion_util(direccion.address):
                    return LecturaConexion(conectada=True, interfaz=nombre)
        return LecturaConexion(conectada=False, interfaz=None)
