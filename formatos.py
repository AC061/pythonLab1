"""Funciones de formato y de color para mostrar magnitudes."""
from __future__ import annotations

import config


def formato_bytes(valor: float | None) -> str:
    if valor is None:
        return config.TEXTO_NO_DISPONIBLE
    cantidad = float(valor)
    for unidad in config.UNIDADES_BYTES[:-1]:
        if abs(cantidad) < config.BYTES_KB:
            return f"{cantidad:.1f} {unidad}"
        cantidad /= config.BYTES_KB
    return f"{cantidad:.1f} {config.UNIDADES_BYTES[-1]}"


def formato_velocidad(bytes_por_s: float | None) -> str:
    if bytes_por_s is None:
        return config.TEXTO_NO_DISPONIBLE
    cantidad = float(bytes_por_s)
    for unidad in config.UNIDADES_VELOCIDAD[:-1]:
        if abs(cantidad) < config.BYTES_KB:
            return f"{cantidad:.1f} {unidad}"
        cantidad /= config.BYTES_KB
    return f"{cantidad:.1f} {config.UNIDADES_VELOCIDAD[-1]}"


def formato_porcentaje(valor: float | None) -> str:
    return config.TEXTO_NO_DISPONIBLE if valor is None else f"{valor:.0f}%"


def formato_temperatura(valor: float | None) -> str:
    return config.TEXTO_NO_DISPONIBLE if valor is None else f"{valor:.0f} °C"


def formato_frecuencia(mhz: float | None) -> str:
    return config.TEXTO_NO_DISPONIBLE if mhz is None else f"{mhz / config.MHZ_POR_GHZ:.2f} GHz"


def formato_duracion(segundos: float) -> str:
    segundos = int(segundos)
    dias, resto = divmod(segundos, config.SEGUNDOS_POR_DIA)
    horas, resto = divmod(resto, config.SEGUNDOS_POR_HORA)
    minutos = resto // config.SEGUNDOS_POR_MINUTO
    return f"{dias} d {horas} h {minutos} min" if dias else f"{horas} h {minutos} min"


def color_uso(porcentaje: float | None) -> str:
    if porcentaje is None:
        return config.COLOR_NEUTRO
    if porcentaje >= config.USO_NIVEL_ALTO:
        return config.COLOR_ALTO
    if porcentaje >= config.USO_NIVEL_MEDIO:
        return config.COLOR_MEDIO
    return config.COLOR_OK


def color_temperatura(grados: float | None) -> str:
    if grados is None:
        return config.COLOR_NEUTRO
    if grados >= config.TEMP_NIVEL_CALIENTE:
        return config.COLOR_ALTO
    if grados >= config.TEMP_NIVEL_TIBIO:
        return config.COLOR_MEDIO
    return config.COLOR_OK
