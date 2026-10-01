# LABORATORIO: archivo nuevo completo.
"""Pruebas unitarias de la detección de conexión de red y de su integración."""
import socket
import unittest
from collections import namedtuple
from unittest import mock

import config
from alertas import ReproductorAlertas
from conexion import SensorConexion
from detectores import DetectorConexion
from eventos import BusEventos
from modelos import Instantanea, LecturaConexion
from nodo import NodoTelemetria

EV = config.CONEXION_EVENTOS
Estado = namedtuple("Estado", "isup")
Direccion = namedtuple("Direccion", "family address")


def inst(conectada, t):
    return Instantanea(marca_tiempo=t, conexion=LecturaConexion(conectada, "eth0" if conectada else None))


class PruebasDetectorConexion(unittest.TestCase):
    def setUp(self):
        self.detector = DetectorConexion(recordatorio_s=30.0)

    def test_conectado_desde_el_inicio_no_emite_nada(self):
        self.assertIsNone(self.detector.evaluar(inst(True, 0)))
        self.assertIsNone(self.detector.evaluar(inst(True, 1)))

    def test_emite_desconectada_una_sola_vez(self):
        self.detector.evaluar(inst(True, 0))
        evento = self.detector.evaluar(inst(False, 1))
        self.assertEqual(evento.nombre, EV["desconectada"])
        self.assertEqual(evento.severidad, config.SEVERIDAD_ALERTA)
        self.assertIsNone(self.detector.evaluar(inst(False, 2)))

    def test_si_arranca_sin_red_avisa_que_esta_desconectada(self):
        self.assertEqual(self.detector.evaluar(inst(False, 0)).nombre, EV["desconectada"])

    def test_emite_conectada_al_recuperarse_con_el_tiempo_caido(self):
        self.detector.evaluar(inst(True, 0))
        self.detector.evaluar(inst(False, 10))
        evento = self.detector.evaluar(inst(True, 25))
        self.assertEqual(evento.nombre, EV["conectada"])
        self.assertEqual(evento.severidad, config.SEVERIDAD_INFO)
        self.assertAlmostEqual(evento.valor, 15.0)
        self.assertIn("15", evento.mensaje)

    def test_conectada_se_emite_una_sola_vez(self):
        self.detector.evaluar(inst(False, 0))
        self.detector.evaluar(inst(True, 5))
        self.assertIsNone(self.detector.evaluar(inst(True, 6)))

    def test_recordatorio_por_tiempo_mientras_siga_caida(self):
        self.detector.evaluar(inst(False, 0))
        self.assertIsNone(self.detector.evaluar(inst(False, 29)))
        recordatorio = self.detector.evaluar(inst(False, 30))
        self.assertEqual(recordatorio.nombre, EV["recordatorio"])
        self.assertAlmostEqual(recordatorio.valor, 30.0)
        self.assertIsNone(self.detector.evaluar(inst(False, 31)))
        self.assertEqual(self.detector.evaluar(inst(False, 60)).nombre, EV["recordatorio"])

    def test_no_hay_recordatorio_si_la_red_esta_conectada(self):
        self.detector.evaluar(inst(True, 0))
        self.assertIsNone(self.detector.evaluar(inst(True, 300)))

    def test_el_ciclo_se_rearma_tras_recuperarse(self):
        self.detector.evaluar(inst(False, 0))
        self.detector.evaluar(inst(True, 5))
        self.assertEqual(self.detector.evaluar(inst(False, 100)).nombre, EV["desconectada"])
        self.assertIsNone(self.detector.evaluar(inst(False, 120)))      # recordatorio cuenta desde la nueva caída

    def test_sin_dato_de_conexion_no_emite_ni_cambia_estado(self):
        self.assertIsNone(self.detector.evaluar(Instantanea()))
        self.assertIsNone(self.detector.conectada)

    def test_los_tres_eventos_tienen_mensaje_y_sonido(self):
        for nombre in EV.values():
            self.assertIn(nombre, config.MENSAJES_EVENTOS)
            self.assertIn(nombre, config.ALERTAS_SONORAS)

    def test_los_nombres_de_eventos_son_los_del_enunciado(self):
        self.assertEqual(set(EV.values()),
                         {"red_desconectada", "red_conectada", "red_sigue_desconectada"})


class PruebasSensorConexion(unittest.TestCase):
    def leer(self, estados, direcciones):
        with mock.patch("conexion.psutil.net_if_stats", return_value=estados), \
                mock.patch("conexion.psutil.net_if_addrs", return_value=direcciones):
            return SensorConexion().leer()

    def test_conectado_con_ip_valida(self):
        lectura = self.leer({"eth0": Estado(True)},
                            {"eth0": [Direccion(socket.AF_INET, "192.168.1.20")]})
        self.assertTrue(lectura.conectada)
        self.assertEqual(lectura.interfaz, "eth0")

    def test_interfaz_caida_no_cuenta(self):
        lectura = self.leer({"eth0": Estado(False)},
                            {"eth0": [Direccion(socket.AF_INET, "192.168.1.20")]})
        self.assertFalse(lectura.conectada)

    def test_loopback_y_enlace_local_no_cuentan(self):
        lectura = self.leer(
            {"lo": Estado(True), "wlan0": Estado(True)},
            {"lo": [Direccion(socket.AF_INET, "127.0.0.1")],
             "wlan0": [Direccion(socket.AF_INET, "169.254.10.5"),
                       Direccion(socket.AF_INET6, "fe80::1%wlan0")]})
        self.assertFalse(lectura.conectada)

    def test_interfaces_virtuales_se_ignoran(self):
        lectura = self.leer({"docker0": Estado(True)},
                            {"docker0": [Direccion(socket.AF_INET, "172.17.0.1")]})
        self.assertFalse(lectura.conectada)

    def test_ipv6_global_cuenta(self):
        lectura = self.leer({"eth0": Estado(True)},
                            {"eth0": [Direccion(socket.AF_INET6, "2001:db8::10")]})
        self.assertTrue(lectura.conectada)

    def test_un_error_del_sistema_se_interpreta_como_sin_conexion(self):
        with mock.patch("conexion.psutil.net_if_stats", side_effect=OSError):
            self.assertFalse(SensorConexion().leer().conectada)


class SensorConexionFalso:
    """Devuelve una secuencia de estados de conexión, uno por llamada."""

    def __init__(self, estados):
        self._estados = list(estados)

    def leer(self):
        actual = self._estados.pop(0) if len(self._estados) > 1 else self._estados[0]
        return LecturaConexion(actual, "eth0" if actual else None)


class RelojFalso:
    def __init__(self):
        self.ahora = 0.0

    def __call__(self):
        return self.ahora


class BackendFalso:
    nombre = "falso"

    def __init__(self):
        self.reproducidas = []

    def reproducir(self, clave, wav):
        self.reproducidas.append(clave)

    def cerrar(self):
        pass


class PruebasIntegracion(unittest.TestCase):
    """Sensor falso -> detector -> bus -> reproductor, sin tocar sensores ni detectores."""

    def test_la_caida_y_la_recuperacion_hacen_sonar_las_alertas_correctas(self):
        bus, backend, reloj = BusEventos(), BackendFalso(), RelojFalso()
        reproductor = ReproductorAlertas(bus, backend, reloj=reloj, silenciado=False)
        reproductor.conectar()
        nodo = NodoTelemetria(bus, reproductor, sensores={
            "conexion": SensorConexionFalso([True, False, False, True]),
        })
        eventos = []
        bus.suscribir(config.EVENTO_TODOS, eventos.append)

        for _ in range(4):
            nodo.procesar(nodo.muestrear())
            reloj.ahora += 10
            reproductor.actualizar()

        nombres = [e.nombre for e in eventos if e.nombre in EV.values()]
        self.assertEqual(nombres, [EV["desconectada"], EV["conectada"]])
        self.assertEqual(backend.reproducidas, [EV["desconectada"], EV["conectada"]])


if __name__ == "__main__":
    unittest.main()
