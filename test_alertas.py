# LABORATORIO: archivo nuevo completo.
"""Pruebas unitarias del paquete alertas (sonidos, backends y reproductor)."""
import io
import time
import unittest
import wave
from unittest import mock

import config
from alertas import (BackendCampana, BackendProceso, BackendSilencioso, ReproductorAlertas,
                     construir_catalogo, crear_backend, crear_reproductor, duracion_patron_s,
                     sintetizar_wav)
from eventos import BusEventos, Evento


class RelojFalso:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora

    def avanzar(self, segundos):
        self.ahora += segundos


class BackendFalso:
    nombre = "falso"

    def __init__(self):
        self.reproducidas = []
        self.cerrado = False

    def reproducir(self, clave, wav):
        self.reproducidas.append(clave)

    def cerrar(self):
        self.cerrado = True


class PruebasSonidos(unittest.TestCase):
    def test_el_wav_es_valido_y_dura_lo_esperado(self):
        patron = ((600, 100), (0, 50), (800, 100))
        with wave.open(io.BytesIO(sintetizar_wav(patron))) as archivo:
            self.assertEqual(archivo.getframerate(), config.AUDIO_TASA_HZ)
            self.assertEqual(archivo.getnchannels(), config.AUDIO_CANALES)
            self.assertEqual(archivo.getsampwidth(), config.AUDIO_BYTES_POR_MUESTRA)
            duracion = archivo.getnframes() / archivo.getframerate()
        self.assertAlmostEqual(duracion, duracion_patron_s(patron), places=2)

    def test_el_silencio_genera_muestras_en_cero(self):
        with wave.open(io.BytesIO(sintetizar_wav(((config.AUDIO_SILENCIO_HZ, 50),)))) as archivo:
            self.assertEqual(set(archivo.readframes(archivo.getnframes())), {0})

    def test_un_tono_no_supera_el_volumen_configurado(self):
        datos = sintetizar_wav(((800, 100),))
        with wave.open(io.BytesIO(datos)) as archivo:
            crudo = archivo.readframes(archivo.getnframes())
        muestras = [int.from_bytes(crudo[i:i + 2], "little", signed=True) for i in range(0, len(crudo), 2)]
        limite = config.AUDIO_VOLUMEN * config.AUDIO_AMPLITUD_MAX
        self.assertLessEqual(max(abs(m) for m in muestras), limite)
        self.assertGreater(max(abs(m) for m in muestras), 0)

    def test_cada_sonido_es_distinto(self):
        patrones = list(config.ALERTAS_SONORAS.values())
        self.assertEqual(len(patrones), len({tuple(p) for p in patrones}))

    def test_hay_sonido_para_cpu_memoria_trafico_y_conexion(self):
        for nombre in ("cpu_alto", "memoria_alta", "red_trafico_alto", *config.CONEXION_EVENTOS.values()):
            self.assertIn(nombre, config.ALERTAS_SONORAS)

    def test_los_sonidos_corresponden_a_eventos_con_mensaje(self):
        for nombre in config.ALERTAS_SONORAS:
            self.assertIn(nombre, config.MENSAJES_EVENTOS)

    def test_el_catalogo_trae_wav_y_duracion(self):
        catalogo = construir_catalogo()
        self.assertEqual(set(catalogo), set(config.ALERTAS_SONORAS))
        for sonido in catalogo.values():
            self.assertTrue(sonido.wav.startswith(b"RIFF"))
            self.assertGreater(sonido.duracion_s, 0)


class PruebasReproductor(unittest.TestCase):
    def setUp(self):
        self.reloj = RelojFalso()
        self.backend = BackendFalso()
        self.bus = BusEventos()
        self.repro = ReproductorAlertas(self.bus, self.backend, reloj=self.reloj, silenciado=False)

    def test_sin_alertas_no_hace_nada(self):
        self.assertIsNone(self.repro.actualizar())
        self.assertEqual(self.backend.reproducidas, [])

    def test_inicia_la_alerta_encolada(self):
        self.assertTrue(self.repro.encolar("cpu_alto"))
        self.assertEqual(self.repro.actualizar(), "cpu_alto")
        self.assertEqual(self.backend.reproducidas, ["cpu_alto"])
        self.assertTrue(self.repro.reproduciendo)

    def test_ignora_alertas_desconocidas(self):
        self.assertFalse(self.repro.encolar("no_existe"))
        self.assertEqual(self.repro.pendientes, 0)

    def test_no_encola_duplicados_pendientes(self):
        self.assertTrue(self.repro.encolar("cpu_alto"))
        self.assertFalse(self.repro.encolar("cpu_alto"))
        self.assertEqual(self.repro.pendientes, 1)

    def test_no_solapa_alertas_y_respeta_el_orden(self):
        self.repro.encolar("cpu_alto")
        self.repro.encolar("memoria_alta")
        self.assertEqual(self.repro.actualizar(), "cpu_alto")
        self.reloj.avanzar(config.INTERVALO_MONITOREO_S / 10)     # aún suena la primera
        self.assertIsNone(self.repro.actualizar())
        self.assertEqual(self.backend.reproducidas, ["cpu_alto"])
        self.reloj.avanzar(10)                                    # ya terminó
        self.assertEqual(self.repro.actualizar(), "memoria_alta")
        self.assertEqual(self.backend.reproducidas, ["cpu_alto", "memoria_alta"])

    def test_la_pausa_entre_alertas_se_respeta(self):
        self.repro.encolar("cpu_alto")
        self.repro.actualizar()
        duracion = construir_catalogo()["cpu_alto"].duracion_s
        self.repro.encolar("memoria_alta")
        self.reloj.avanzar(duracion + config.ALERTAS_PAUSA_ENTRE_S / 2)
        self.assertIsNone(self.repro.actualizar())
        self.reloj.avanzar(config.ALERTAS_PAUSA_ENTRE_S)
        self.assertEqual(self.repro.actualizar(), "memoria_alta")

    def test_descarta_alertas_caducadas(self):
        self.repro.encolar("cpu_alto")
        self.reloj.avanzar(config.ALERTAS_CADUCIDAD_S + 1)
        self.repro.encolar("memoria_alta")
        self.assertEqual(self.repro.actualizar(), "memoria_alta")
        self.assertEqual(self.backend.reproducidas, ["memoria_alta"])

    def test_si_todas_caducaron_no_suena_nada(self):
        self.repro.encolar("cpu_alto")
        self.reloj.avanzar(config.ALERTAS_CADUCIDAD_S + 1)
        self.assertIsNone(self.repro.actualizar())
        self.assertEqual(self.backend.reproducidas, [])
        self.assertEqual(self.repro.pendientes, 0)

    def test_la_cola_tiene_tamano_maximo(self):
        catalogo = {f"evento_{i}": construir_catalogo()["cpu_alto"]
                    for i in range(config.ALERTAS_COLA_MAX + 3)}
        repro = ReproductorAlertas(self.bus, self.backend, catalogo=catalogo, reloj=self.reloj)
        for nombre in catalogo:
            repro.encolar(nombre)
        self.assertEqual(repro.pendientes, config.ALERTAS_COLA_MAX)
        self.assertEqual(repro.actualizar(), "evento_3")          # las más antiguas se descartaron

    def test_modo_silencioso_no_suena_pero_consume_y_avisa(self):
        avisos = []
        self.bus.suscribir(config.EVENTO_ALERTA_SONORA, avisos.append)
        self.repro.silenciado = True
        self.repro.encolar("cpu_alto")
        self.repro.encolar("memoria_alta")
        self.assertEqual(self.repro.actualizar(), "cpu_alto")
        self.assertEqual(self.repro.actualizar(), "memoria_alta")    # sin esperas
        self.assertEqual(self.backend.reproducidas, [])
        self.assertEqual(len(avisos), 2)
        self.assertIn("silenciada", avisos[0].mensaje)

    def test_se_puede_reactivar_el_sonido(self):
        self.repro.silenciado = True
        self.repro.silenciado = False
        self.repro.encolar("cpu_alto")
        self.repro.actualizar()
        self.assertEqual(self.backend.reproducidas, ["cpu_alto"])

    def test_reacciona_a_los_eventos_del_bus(self):
        self.repro.conectar()
        self.bus.emitir(Evento("cpu_alto", "CPU", "x"))
        self.bus.emitir(Evento("cpu_normal", "CPU", "x"))        # no tiene sonido asignado
        self.assertEqual(self.repro.pendientes, 1)

    def test_emitir_el_aviso_no_provoca_nuevas_alertas(self):
        self.repro.conectar()
        self.bus.emitir(Evento("cpu_alto", "CPU", "x"))
        self.repro.actualizar()                                  # emite "alerta_sonora" al bus
        self.assertEqual(self.repro.pendientes, 0)

    def test_actualizar_no_espera_a_que_termine_el_sonido(self):
        """El backend vuelve de inmediato; actualizar() no debe tardar lo que dura el sonido."""
        repro = ReproductorAlertas(self.bus, self.backend, silenciado=False)   # reloj real
        repro.encolar("memoria_alta")
        inicio = time.monotonic()
        repro.actualizar()
        transcurrido = time.monotonic() - inicio
        self.assertLess(transcurrido, construir_catalogo()["memoria_alta"].duracion_s / 10)

    def test_cerrar_cierra_el_backend(self):
        self.repro.cerrar()
        self.assertTrue(self.backend.cerrado)


class PruebasBackends(unittest.TestCase):
    def test_el_backend_silencioso_no_hace_nada(self):
        backend = BackendSilencioso()
        backend.reproducir("x", b"")
        backend.cerrar()

    def test_la_campana_escribe_el_caracter_de_campana(self):
        with mock.patch("sys.stdout", new=io.StringIO()) as salida:
            BackendCampana().reproducir("x", b"")
        self.assertEqual(salida.getvalue(), config.ALERTAS_CAMPANA)

    def test_el_proceso_externo_se_lanza_sin_esperar(self):
        with mock.patch("alertas.backends.tempfile.mkdtemp", return_value="/tmp/alertas_prueba"), \
                mock.patch("alertas.backends.subprocess.Popen") as popen, \
                mock.patch("builtins.open", mock.mock_open()):
            backend = BackendProceso("/usr/bin/reproductor")
            backend.reproducir("cpu_alto", b"RIFF")
        popen.assert_called_once()
        self.assertEqual(popen.call_args.args[0][0], "/usr/bin/reproductor")

    def test_crear_backend_usa_campana_si_no_hay_reproductor(self):
        with mock.patch("alertas.backends.sys.platform", "linux"), \
                mock.patch("alertas.backends.shutil.which", return_value=None):
            self.assertIsInstance(crear_backend(), BackendCampana)

    def test_crear_reproductor_queda_conectado_al_bus(self):
        bus = BusEventos()
        with mock.patch("alertas.backends.shutil.which", return_value=None), \
                mock.patch("alertas.backends.sys.platform", "linux"):
            repro = crear_reproductor(bus, silencioso=True)
        self.assertTrue(repro.silenciado)
        bus.emitir(Evento("red_desconectada", "Red", "x"))
        self.assertEqual(repro.pendientes, 1)


if __name__ == "__main__":
    unittest.main()
