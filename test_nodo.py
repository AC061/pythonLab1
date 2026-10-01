"""Pruebas del nodo de telemetría (usan sensores reales del equipo)."""
import time
import unittest

import config
from eventos import BusEventos
from formatos import formato_bytes, formato_velocidad, color_uso
from nodo import NodoTelemetria


class PruebasNodo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bus = BusEventos()
        cls.nodo = NodoTelemetria(cls.bus)

    def test_muestrear_devuelve_cpu_memoria_y_disco(self):
        inst = self.nodo.muestrear()
        self.assertIsNotNone(inst.cpu)
        self.assertIsNotNone(inst.memoria)
        self.assertIsNotNone(inst.disco)
        self.assertEqual(len(inst.cpu.nucleos_uso), inst.cpu.nucleos_logicos)

    def test_un_sensor_que_falla_no_rompe_el_muestreo(self):
        class Roto:
            def leer(self):
                raise RuntimeError("fallo simulado")

        original = self.nodo._sensores["gpu"]
        self.nodo._sensores["gpu"] = Roto()
        try:
            with self.assertLogs("nodo", level="ERROR"):
                inst = self.nodo.muestrear()
        finally:
            self.nodo._sensores["gpu"] = original
        self.assertIsNone(inst.gpu)
        self.assertIsNotNone(inst.cpu)

    def test_el_hilo_publica_instantaneas_y_se_detiene(self):
        nodo = NodoTelemetria(BusEventos())
        nodo.iniciar()
        try:
            limite = time.monotonic() + config.INTERVALO_MONITOREO_S * 3
            while nodo.ultima()[1] is None and time.monotonic() < limite:
                time.sleep(config.INTERVALO_REFRESCO_UI_MS / config.MS_POR_S)
            self.assertIsNotNone(nodo.ultima()[1])
        finally:
            nodo.detener()
        self.assertFalse(nodo._hilo.is_alive())


class PruebasFormatos(unittest.TestCase):
    def test_formato_bytes(self):
        self.assertEqual(formato_bytes(config.BYTES_GB * 2), "2.0 GB")
        self.assertEqual(formato_bytes(None), config.TEXTO_NO_DISPONIBLE)

    def test_formato_velocidad(self):
        self.assertEqual(formato_velocidad(config.BYTES_MB), "1.0 MB/s")

    def test_color_uso_por_niveles(self):
        self.assertEqual(color_uso(config.USO_NIVEL_MEDIO - 1), config.COLOR_OK)
        self.assertEqual(color_uso(config.USO_NIVEL_MEDIO), config.COLOR_MEDIO)
        self.assertEqual(color_uso(config.USO_NIVEL_ALTO), config.COLOR_ALTO)


if __name__ == "__main__":
    unittest.main()
