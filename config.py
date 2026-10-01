"""Configuración central del monitor de sistema.

Todos los umbrales, tiempos, tamaños, colores y nombres de sensores se definen
aquí. Ningún otro módulo debe contener números literales (se exceptúan los
valores estructurales 0, 1 y -1 usados como índices o comparaciones).
"""

# --------------------------------------------------------------------------
# Aplicación / ventana
# --------------------------------------------------------------------------
TITULO_APP = "Monitor de Sistema"
GEOMETRIA_INICIAL = "1180x860"
ANCHO_MINIMO = 1000
ALTO_MINIMO = 760
APARIENCIA_INICIAL = "dark"          # "dark" | "light" | "system"
TEMA_COLOR = "blue"

# --------------------------------------------------------------------------
# Temporización
# --------------------------------------------------------------------------
INTERVALO_MONITOREO_S = 1.0          # periodo del ciclo de muestreo
INTERVALO_REFRESCO_UI_MS = 250       # cada cuánto la UI revisa datos nuevos
ESPERA_CIERRE_HILO_S = 3.0           # tiempo máx. esperando al hilo al cerrar
TIMEOUT_SUBPROCESO_S = 2.0           # tiempo máx. para nvidia-smi / lspci

# --------------------------------------------------------------------------
# Unidades y conversiones
# --------------------------------------------------------------------------
BYTES_KB = 1024
BYTES_MB = BYTES_KB * BYTES_KB
BYTES_GB = BYTES_MB * BYTES_KB
MHZ_POR_GHZ = 1000.0
MILIGRADOS_POR_GRADO = 1000.0
BITS_POR_BYTE = 8
BITS_POR_MBIT = 1_000_000
PORCENTAJE_MAX = 100.0
SEGUNDOS_POR_MINUTO = 60
SEGUNDOS_POR_HORA = 3600
SEGUNDOS_POR_DIA = 86400
MS_POR_S = 1000.0

UNIDADES_BYTES = ("B", "KB", "MB", "GB", "TB")
UNIDADES_VELOCIDAD = ("B/s", "KB/s", "MB/s", "GB/s")

# --------------------------------------------------------------------------
# Niveles visuales (colores de barras y textos)
# --------------------------------------------------------------------------
USO_NIVEL_MEDIO = 60.0
USO_NIVEL_ALTO = 85.0
TEMP_NIVEL_TIBIO = 60.0
TEMP_NIVEL_CALIENTE = 80.0
TEMP_ESCALA_MAX = 100.0              # 100 °C = barra completa

COLOR_OK = "#2ecc71"
COLOR_MEDIO = "#f1c40f"
COLOR_ALTO = "#e74c3c"
COLOR_NEUTRO = "#7f8c8d"
COLOR_INFO = "#3498db"

# --------------------------------------------------------------------------
# Detectores de eventos (por flanco, con histéresis)
#   alto   -> se emite evento_alto cuando valor >= alto (una sola vez)
#   normal -> se emite evento_normal cuando valor <= normal (una sola vez)
# --------------------------------------------------------------------------
SEVERIDAD_ALERTA = "alerta"
SEVERIDAD_INFO = "info"
EVENTO_TODOS = "*"

DETECTORES = (
    {
        "id": "cpu_uso", "componente": "CPU", "magnitud": "cpu_uso",
        "alto": 90.0, "normal": 75.0,
        "evento_alto": "cpu_alto", "evento_normal": "cpu_normal",
    },
    {
        "id": "cpu_temp", "componente": "CPU", "magnitud": "cpu_temp",
        "alto": 85.0, "normal": 75.0,
        "evento_alto": "cpu_temp_alta", "evento_normal": "cpu_temp_normal",
    },
    {
        "id": "memoria_uso", "componente": "Memoria", "magnitud": "memoria_uso",
        "alto": 90.0, "normal": 80.0,
        "evento_alto": "memoria_alta", "evento_normal": "memoria_normal",
    },
    {
        "id": "gpu_uso", "componente": "GPU", "magnitud": "gpu_uso",
        "alto": 95.0, "normal": 80.0,
        "evento_alto": "gpu_alto", "evento_normal": "gpu_normal",
    },
    {
        "id": "gpu_temp", "componente": "GPU", "magnitud": "gpu_temp",
        "alto": 85.0, "normal": 75.0,
        "evento_alto": "gpu_temp_alta", "evento_normal": "gpu_temp_normal",
    },
    {
        "id": "disco_espacio", "componente": "Disco", "magnitud": "disco_espacio",
        "alto": 90.0, "normal": 85.0,
        "evento_alto": "disco_lleno", "evento_normal": "disco_espacio_normal",
    },
    {
        "id": "disco_temp", "componente": "Disco", "magnitud": "disco_temp",
        "alto": 70.0, "normal": 60.0,
        "evento_alto": "disco_temp_alta", "evento_normal": "disco_temp_normal",
    },
    {
        "id": "red_trafico", "componente": "Red", "magnitud": "red_trafico_kbs",
        "alto": 10240.0, "normal": 5120.0,          # KB/s (bajada + subida)
        "evento_alto": "red_trafico_alto", "evento_normal": "red_trafico_normal",
    },
)

# Plantillas de mensajes; {valor} es la magnitud medida al cruzar el umbral.
MENSAJES_EVENTOS = {
    "cpu_alto": "Uso de CPU alto: {valor:.0f}%",
    "cpu_normal": "Uso de CPU normalizado: {valor:.0f}%",
    "cpu_temp_alta": "Temperatura de CPU alta: {valor:.0f} °C",
    "cpu_temp_normal": "Temperatura de CPU normalizada: {valor:.0f} °C",
    "memoria_alta": "Memoria casi agotada: {valor:.0f}%",
    "memoria_normal": "Memoria normalizada: {valor:.0f}%",
    "gpu_alto": "Uso de GPU alto: {valor:.0f}%",
    "gpu_normal": "Uso de GPU normalizado: {valor:.0f}%",
    "gpu_temp_alta": "Temperatura de GPU alta: {valor:.0f} °C",
    "gpu_temp_normal": "Temperatura de GPU normalizada: {valor:.0f} °C",
    "disco_lleno": "Disco casi lleno: {valor:.0f}% usado",
    "disco_espacio_normal": "Espacio en disco normalizado: {valor:.0f}%",
    "disco_temp_alta": "Temperatura de disco alta: {valor:.0f} °C",
    "disco_temp_normal": "Temperatura de disco normalizada: {valor:.0f} °C",
    "red_trafico_alto": "Tráfico de red alto: {valor:.0f} KB/s",
    "red_trafico_normal": "Tráfico de red normalizado: {valor:.0f} KB/s",
    # LABORATORIO: {valor} es el tiempo (s) que la red lleva desconectada
    "red_desconectada": "Se perdió la conexión de red",
    "red_conectada": "Conexión de red recuperada tras {valor:.0f} s",
    "red_sigue_desconectada": "La red sigue desconectada desde hace {valor:.0f} s",
}

# LABORATORIO ---------------------------------------------------------------
# Detección de conexión de red (eventos por flanco + recordatorio por tiempo)
# ---------------------------------------------------------------------------
RED_RECORDATORIO_S = 30.0            # LABORATORIO: cada cuánto se repite "sigue desconectada"
CONEXION_EVENTOS = {                 # LABORATORIO
    "desconectada": "red_desconectada",
    "conectada": "red_conectada",
    "recordatorio": "red_sigue_desconectada",
}
CONEXION_COMPONENTE = "Red"          # LABORATORIO
CONEXION_FAMILIAS_DIRECCION = ("AF_INET", "AF_INET6")   # LABORATORIO: nombres en el módulo socket

# LABORATORIO ---------------------------------------------------------------
# Alertas sonoras
#   Cada sonido es una tupla de segmentos (frecuencia_hz, duracion_ms).
#   Una frecuencia igual a AUDIO_SILENCIO_HZ es una pausa.
# ---------------------------------------------------------------------------
AUDIO_TASA_HZ = 22050                # LABORATORIO
AUDIO_CANALES = 1                    # LABORATORIO
AUDIO_BYTES_POR_MUESTRA = 2          # LABORATORIO: 16 bits
AUDIO_AMPLITUD_MAX = 32767           # LABORATORIO: máximo de un entero de 16 bits con signo
AUDIO_VOLUMEN = 0.5                  # LABORATORIO: 0.0 a 1.0
AUDIO_FADE_MS = 8                    # LABORATORIO: rampa de entrada/salida (evita "clics")
AUDIO_SILENCIO_HZ = 0                # LABORATORIO

ALERTAS_SILENCIOSO_POR_DEFECTO = False   # LABORATORIO: True = modo silencioso al iniciar
ALERTAS_PAUSA_ENTRE_S = 0.4          # LABORATORIO: pausa entre dos alertas consecutivas
ALERTAS_COLA_MAX = 8                 # LABORATORIO: si se llena, se descarta la más antigua
ALERTAS_CADUCIDAD_S = 20.0           # LABORATORIO: una alerta que espera más que esto se descarta
EVENTO_ALERTA_SONORA = "alerta_sonora"   # LABORATORIO
ALERTAS_COMPONENTE = "Sonido"        # LABORATORIO
ALERTAS_REPRODUCTORES_EXTERNOS = ("pw-play", "paplay", "aplay", "afplay")   # LABORATORIO: Linux / macOS
ALERTAS_CAMPANA = "\a"               # LABORATORIO: campana del sistema (último recurso)
ALERTAS_PREFIJO_TEMP = "alertas_"    # LABORATORIO
DEMO_PERIODO_S = 0.25                # LABORATORIO: latido del ciclo simulado en demo_alertas.py
DEMO_COMPONENTE = "Demo"             # LABORATORIO

ALERTAS_SONORAS = {                  # LABORATORIO: evento -> patrón de sonido
    # CPU: tres tonos ascendentes, "acelerando"
    "cpu_alto": ((600, 110), (800, 110), (1000, 110)),
    # Memoria: dos pulsos graves y largos, "pesado / lleno"
    "memoria_alta": ((300, 350), (0, 100), (300, 350)),
    # Tráfico: ráfaga rápida que alterna dos tonos, "paquetes"
    "red_trafico_alto": ((900, 70), (700, 70), (900, 70), (700, 70), (900, 70), (700, 70)),
    # Conexión: caída (descendente), recuperación (ascendente) y recordatorio (dos pitidos graves)
    "red_desconectada": ((900, 200), (600, 200), (300, 350)),
    "red_conectada": ((500, 180), (900, 320)),
    "red_sigue_desconectada": ((400, 150), (0, 120), (400, 150)),
}

# --------------------------------------------------------------------------
# Selección de sensores
# --------------------------------------------------------------------------
# Correspondencia HardwareType (LibreHardwareMonitor) -> categoría interna
LHM_CATEGORIAS = {
    "Cpu": "cpu",
    "GpuNvidia": "gpu",
    "GpuAmd": "gpu",
    "GpuIntel": "gpu",
    "Storage": "disco",
    "Network": "red",
    "Memory": "memoria",
}
LHM_TEMP_CPU_PREFERIDAS = (
    "Core (Tctl/Tdie)", "CPU Package", "Core (Tdie)", "Core Average", "Core Max",
)
LHM_GPU_CARGA = ("GPU Core",)
LHM_GPU_TEMP = ("GPU Core",)
LHM_GPU_VRAM_TOTAL = "GPU Memory Total"
LHM_GPU_VRAM_USADA = "GPU Memory Used"
LHM_DISCO_TEMP = ("Temperature",)
LHM_DISCO_ACTIVIDAD = ("Total Activity",)
LHM_DISCO_LECTURA = ("Read Rate",)
LHM_DISCO_ESCRITURA = ("Write Rate",)
LHM_MB_A_BYTES = BYTES_MB            # LHM reporta la VRAM en MB

# Chips de temperatura en Linux (psutil.sensors_temperatures)
LINUX_CHIPS_CPU = ("k10temp", "coretemp", "zenpower", "cpu_thermal")
LINUX_ETIQUETAS_CPU = ("Tctl", "Tdie", "Package id 0")
LINUX_CHIPS_DISCO = ("nvme", "drivetemp")
LINUX_ETIQUETAS_DISCO = ("Composite",)
LINUX_CHIPS_RED = ("iwlwifi", "mt7921", "ath10k", "ath11k", "rtw", "r8169", "atlantic")
LINUX_CHIPS_GPU = ("amdgpu", "nouveau", "radeon")

# GPU en Linux
NVIDIA_SMI = "nvidia-smi"
NVIDIA_SMI_ARGS = (
    "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
    "--format=csv,noheader,nounits",
)
NVIDIA_SMI_CAMPOS = 5                # name, uso, temperatura, vram usada, vram total
SEPARADOR_CSV = ","
DRM_RUTA = "/sys/class/drm"
DRM_PATRON_TARJETA = r"^card\d+$"
DRM_VENDOR_AMD = "0x1002"
LSPCI = "lspci"
LSPCI_COLUMNA_DISPOSITIVO = 3        # ranura "clase" "fabricante" "dispositivo"

# Red
RED_INTERFACES_IGNORADAS = (
    "lo", "docker", "veth", "br-", "virbr", "tun", "tap", "vmnet", "vboxnet", "Loopback",
)
RED_ESCALA_REFERENCIA_MBPS = 100.0   # se usa si el SO no informa la velocidad del enlace
RED_SIN_INTERFAZ = "Sin interfaz activa"

# Disco
DISCO_DEV_PREFIJO = "/dev/"

# --------------------------------------------------------------------------
# Estilo de la interfaz
# --------------------------------------------------------------------------
TARJETAS_COLUMNAS = 2
PAD_VENTANA = 12
PAD_TARJETA = 14
PAD_INTERNO = 6
PAD_MICRO = 3
RADIO_TARJETA = 16
ALTO_BARRA = 12
ALTO_BARRA_NUCLEO = 6
ALTO_BARRA_GRANDE = 18
NUCLEOS_COLUMNAS = 4
ALTO_LOG = 120
MAX_LINEAS_LOG = 200
ANCHO_NOMBRE_DISPOSITIVO = 380       # wraplength del nombre del dispositivo

FUENTE_TITULO_APP = 24
FUENTE_TITULO_TARJETA = 18
FUENTE_SUBTITULO = 12
FUENTE_VALOR_GRANDE = 34
FUENTE_VALOR = 14
FUENTE_ETIQUETA = 12
FUENTE_NUCLEO = 11
FUENTE_LOG = 12

# LABORATORIO: elementos de la interfaz para la conexión y el sonido
TEXTO_CONECTADO = "● Conectado"
TEXTO_DESCONECTADO = "● Sin conexión"
TEXTO_SONIDO_ACTIVO = "Alertas sonoras"
TEXTO_BOTON_PROBAR = "Probar"
ANCHO_MENU_PRUEBA = 190
ANCHO_BOTON_PRUEBA = 95
TEXTO_NO_DISPONIBLE = "N/D"
