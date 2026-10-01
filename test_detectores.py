"""Pruebas unitarias de detectores, bus de eventos y configuración."""
import unittest

import config
from detectores import EXTRACTORES, DetectorUmbral, crear_detectores
from eventos import BusEventos, Evento
from modelos import Instantanea, LecturaCPU

DEFINICION = {
    "id": "prueba", "componente": "CPU", "magnitud": "cpu_uso",
    "alto": 90.0, "normal": 75.0,
    "evento_alto": "cpu_alto", "evento_normal": "cpu_normal",
}


def instantanea_cpu(uso, temperatura=None):
    cpu = LecturaCPU("CPU de prueba", uso, [uso], temperatura, 1, 1, None)
    return Instantanea(cpu=cpu)


class PruebasDetectorUmbral(unittest.TestCase):
    def setUp(self):
        self.detector = DetectorUmbral(DEFINICION, EXTRACTORES["cpu_uso"])

    def test_no_emite_bajo_el_umbral(self):
        self.assertIsNone(self.detector.evaluar(instantanea_cpu(DEFINICION["alto"] - 1)))

    def test_emite_alto_una_sola_vez(self):
        primero = self.detector.evaluar(instantanea_cpu(DEFINICION["alto"]))
        self.assertEqual(primero.nombre, "cpu_alto")
        self.assertEqual(primero.severidad, config.SEVERIDAD_ALERTA)
        self.assertIsNone(self.detector.evaluar(instantanea_cpu(DEFINICION["alto"] + 5)))

    def test_histeresis_no_emite_normal_en_zona_intermedia(self):
        self.detector.evaluar(instantanea_cpu(DEFINICION["alto"]))
        intermedio = (DEFINICION["alto"] + DEFINICION["normal"]) / 2
        self.assertIsNone(self.detector.evaluar(instantanea_cpu(intermedio)))
        self.assertTrue(self.detector.activo)

    def test_emite_normal_al_recuperarse_y_rearma(self):
        self.detector.evaluar(instantanea_cpu(DEFINICION["alto"]))
        normal = self.detector.evaluar(instantanea_cpu(DEFINICION["normal"]))
        self.assertEqual(normal.nombre, "cpu_normal")
        self.assertEqual(normal.severidad, config.SEVERIDAD_INFO)
        self.assertEqual(self.detector.evaluar(instantanea_cpu(DEFINICION["alto"])).nombre, "cpu_alto")

    def test_sin_dato_no_emite_ni_cambia_estado(self):
        self.assertIsNone(self.detector.evaluar(Instantanea()))
        self.assertFalse(self.detector.activo)

    def test_umbrales_invertidos_son_rechazados(self):
        invalida = {**DEFINICION, "alto": 50.0, "normal": 60.0}
        with self.assertRaises(ValueError):
            DetectorUmbral(invalida, EXTRACTORES["cpu_uso"])

    def test_el_evento_usa_la_marca_de_tiempo_de_la_instantanea(self):
        inst = instantanea_cpu(DEFINICION["alto"])
        self.assertEqual(self.detector.evaluar(inst).marca_tiempo, inst.marca_tiempo)


class PruebasConfiguracion(unittest.TestCase):
    def test_todos_los_detectores_se_crean(self):
        self.assertEqual(len(crear_detectores()), len(config.DETECTORES))

    def test_cada_evento_tiene_mensaje(self):
        for d in config.DETECTORES:
            self.assertIn(d["evento_alto"], config.MENSAJES_EVENTOS)
            self.assertIn(d["evento_normal"], config.MENSAJES_EVENTOS)

    def test_ids_y_eventos_son_unicos(self):
        ids = [d["id"] for d in config.DETECTORES]
        eventos = [e for d in config.DETECTORES for e in (d["evento_alto"], d["evento_normal"])]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(eventos), len(set(eventos)))


class PruebasBusEventos(unittest.TestCase):
    def test_entrega_a_suscriptor_del_evento_y_al_comodin(self):
        bus, directo, comodin = BusEventos(), [], []
        bus.suscribir("cpu_alto", directo.append)
        bus.suscribir(config.EVENTO_TODOS, comodin.append)
        bus.emitir(Evento("cpu_alto", "CPU", "x"))
        bus.emitir(Evento("otro", "CPU", "y"))
        self.assertEqual(len(directo), 1)
        self.assertEqual(len(comodin), 2)

    def test_un_manejador_defectuoso_no_afecta_a_los_demas(self):
        bus, recibidos = BusEventos(), []

        def defectuoso(_):
            raise RuntimeError("fallo simulado")

        bus.suscribir("x", defectuoso)
        bus.suscribir("x", recibidos.append)
        with self.assertLogs("eventos", level="ERROR"):
            bus.emitir(Evento("x", "CPU", "m"))
        self.assertEqual(len(recibidos), 1)


if __name__ == "__main__":
    unittest.main()
