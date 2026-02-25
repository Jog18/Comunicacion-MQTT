# Proyecto: Comunicación MQTT con Raspberry Pi y ESP32

## Información Académica

| Campo | Detalle |
|-------|---------|
| **Institución** | Tecnológico Nacional de México – Campus Atlixco |
| **Carrera** | Ingeniería Mecatrónica |
| **Materia** | Automatización |
| **Grupo** | 8AB |
| **Periodo** | Enero – Junio 2026 |
| **Docente** | Mtro. Raul Eusebio Grande |
| **Fecha** | 19 de Febrero de 2026 |

### Equipo de trabajo

| Nombre | Matrícula |
|--------|-----------|
| Orea Guerrero Josue | IM221466 |
| Genis Sanchez Joaquin | IM221438 |
| Romero de los Santos Julieta | IM221472 |
| Cruz Morales Juan Carlos | IM231556 |

---

## Descripción General del Proyecto

El proyecto implementa un sistema de comunicación IoT basado en el protocolo **MQTT** (Message Queuing Telemetry Transport), donde:

- Una **Raspberry Pi** actúa como **broker MQTT** (servidor intermediario) usando Mosquitto.
- Un **ESP32** actúa como **publicador** de datos de sensores y como **suscriptor** para recibir comandos de control.
- Una **PC con Python** actúa como **suscriptor** que recibe y almacena los datos en un archivo CSV.

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                     RED LOCAL WiFi                       │
│                   (INFINITUM6DD1)                        │
│                                                         │
│  ┌──────────┐   publica sensores    ┌───────────────┐   │
│  │          │ ─────────────────────>│               │   │
│  │  ESP32   │                       │  Raspberry Pi │   │
│  │          │ <─────────────────────│  (Mosquitto   │   │
│  │ GPIO4,   │   comandos LED        │   Broker)     │   │
│  │ 34,35,36 │                       │  IP:192.168   │   │
│  └──────────┘                       │     .1.82     │   │
│                                     │  Puerto: 1883 │   │
│  ┌──────────┐   recibe datos        │               │   │
│  │  PC /    │ <─────────────────────│               │   │
│  │  Python  │                       └───────────────┘   │
│  │  Script  │                                           │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Componentes del Proyecto

### 1. Broker MQTT – Raspberry Pi (Mosquitto)

**Software:** Mosquitto v2.0.21-1

#### Configuración aplicada (`/etc/mosquitto/mosquitto.conf`)
```
listener 1883 0.0.0.0
allow_anonymous true
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `listener` | `1883 0.0.0.0` | Escucha en puerto 1883 desde cualquier IP |
| `allow_anonymous` | `true` | Permite conexiones sin autenticación |

#### Comandos de configuración ejecutados
```bash
# Instalar Mosquitto
sudo apt install mosquitto

# Instalar clientes MQTT para pruebas
sudo apt install mosquitto-clients

# Verificar estado del servicio
sudo systemctl status mosquitto.service

# Editar configuración
sudo nano /etc/mosquitto/mosquitto.conf

# Reiniciar servicio para aplicar cambios
sudo systemctl restart mosquitto.service
```

#### Prueba de funcionamiento (comprobación básica)
```bash
# Terminal 1 - Suscriptor
mosquitto_sub -t alumno/nombre

# Terminal 2 - Publicador
mosquitto_pub -t alumno/nombre -m "HOLA"
# Resultado esperado: "HOLA" aparece en Terminal 1
```

---

### 2. Publicador / Suscriptor – ESP32 (`Practica1Seguimiento_MQTT.ino`)

**Lenguaje:** C++ (Arduino Framework)
**Librerías usadas:**
- `WiFi.h` – Conexión a red WiFi
- `PubSubClient.h` – Comunicación MQTT

#### Configuración de red
```cpp
const char* ssid         = "INFINITUM6DD1";
const char* password     = "Qm3Gc1Aw4q";
const char* mqtt_server  = "192.168.1.82";  // IP de la Raspberry Pi
```

#### Pines utilizados

| GPIO | Componente | Función |
|------|-----------|---------|
| GPIO4 | LED | Salida digital controlable vía MQTT |
| GPIO34 | Potenciómetro 1 | Entrada analógica (ADC) |
| GPIO35 | Potenciómetro 2 | Entrada analógica (ADC) |
| GPIO32 | Potenciómetro 3 | Entrada analógica (ADC) |
| GPIO36 | Sensor LM35 | Temperatura (entrada analógica) |

#### Conversión de señales

**Potenciómetros (0–3.3V):**
```
voltaje = (valorADC * 3.3) / 4095.0
```
- Resolución ADC: 12 bits (0–4095)
- Atenuación: ADC_11db (permite leer hasta ~3.3V)

**Sensor de temperatura LM35 (fórmula implementada):**
```
voltajeLM35 = (adcTemp * 5) / 4095.0
temperatura = voltajeLM35 * 100.0
```
> Nota: El LM35 produce 10mV/°C. La fórmula asume referencia de 5V.

#### Tópicos MQTT del ESP32

| Tópico | Dirección | Frecuencia | Contenido |
|--------|-----------|-----------|-----------|
| `pot/uno` | Publica | Cada 1 segundo | Voltaje Potenciómetro 1 (float, 3 decimales) |
| `pot/dos` | Publica | Cada 1 segundo | Voltaje Potenciómetro 2 (float, 3 decimales) |
| `pot/tres` | Publica | Cada 1 segundo | Voltaje Potenciómetro 3 (float, 3 decimales) |
| `LM35/uno` | Publica | Cada 1 segundo | Temperatura en °C (float, 3 decimales) |
| `led/estado` | Publica | Continuo | Estado del LED: `"ON"` o `"OFF"` |
| `led/uno` | Suscrito | - | Recibe `"ON"` o `"OFF"` para controlar el LED |

#### Flujo de funcionamiento del ESP32
```
setup() ──> setup_wifi() ──> connect MQTT broker
              │
loop() ──────┤
              ├── ¿Conectado? ──No──> reconnect() ──> subscribe("led/uno")
              ├── client.loop()
              ├── Leer ADC: pot1, pot2, pot3, LM35
              ├── Cada 1 seg: publicar voltajes y temperatura
              └── Publicar estado LED continuamente

callback() ──> Si recibe "ON"  en "led/uno" → LED HIGH
            └── Si recibe "OFF" en "led/uno" → LED LOW
```

---

### 3. Receptor y Logger – Python (`RecepcionDatos_MQTT.py`)

**Lenguaje:** Python 3
**Librerías usadas:**
- `paho.mqtt.client` – Cliente MQTT
- `csv` – Escritura de archivos CSV
- `os` – Verificación de archivos
- `datetime` – Marcas de tiempo

#### Configuración de conexión
```python
broker = "192.168.1.82"   # IP de la Raspberry Pi
puerto = 1883
```

#### Tópicos suscritos
```python
client.subscribe("LM35/uno")
client.subscribe("pot/uno")
client.subscribe("pot/dos")
client.subscribe("pot/tres")
```

#### Estructura del CSV generado

| timestamp | Publicador | Mensaje |
|-----------|-----------|---------|
| 2026-02-20 15:16:00 | LM35/uno | 25.400 |
| 2026-02-20 15:16:00 | pot/uno | 1.623 |
| 2026-02-20 15:16:00 | pot/dos | 0.812 |
| 2026-02-20 15:16:00 | pot/tres | 3.289 |

#### Callbacks implementados

| Función | Evento |
|---------|--------|
| `conectarMQTT` | Al conectarse al broker → suscribe a todos los tópicos |
| `MensajeMQTT` | Al recibir mensaje → imprime y guarda en CSV |
| `EnviandoMQTT` | Al enviar mensaje → imprime ID |
| `SubcribiendoMQTT` | Al suscribirse → confirma suscripción |
| `LogMQTT` | Logs internos del cliente |

---

## Flujo General del Sistema

```
[Sensores físicos]
  Pot1, Pot2, Pot3, LM35
        │
        ▼
   [ESP32 lee ADC]
   convierte a voltaje/temperatura
        │
        ▼ publica cada 1 seg
   [Broker MQTT]
   Raspberry Pi: 192.168.1.82:1883
        │
        ├──────────────────────────┐
        ▼                          ▼
  [Python Script]            [Otros clientes]
  Guarda datos en CSV        (mosquitto_sub, etc.)

[PC / Usuario]
  ▼ envía "ON" o "OFF" a "led/uno"
  [Broker MQTT]
  ▼
  [ESP32] → enciende/apaga LED en GPIO4
```

---

## Estado de Avance del Proyecto

### Completado

- [x] Configuración del broker Mosquitto en Raspberry Pi
- [x] Habilitación de conexiones externas (puerto 1883, anonymous access)
- [x] Verificación del servicio Mosquitto (active/running)
- [x] Prueba básica publicador/suscriptor en la Raspberry Pi
- [x] Código ESP32 con lectura de 3 potenciómetros y sensor LM35
- [x] Publicación de datos de sensores vía MQTT (cada 1 segundo)
- [x] Control de LED por MQTT (recepción de comandos ON/OFF)
- [x] Publicación del estado del LED
- [x] Script Python receptor y logger de datos en CSV
- [x] Timestamps en los registros CSV

### Pendiente / Observaciones

- [ ] **Bug en Python:** `csv_file = "Practica1"` — falta la extensión `.csv`. El archivo se crea sin extensión. Debería ser `"Practica1.csv"`.
- [ ] El ESP32 suscribe al tópico `"led/uno"` pero el callback responde a cualquier mensaje en ese tópico (no valida que el tópico sea exactamente `"led/uno"` antes de actuar).
- [ ] La fórmula del LM35 usa referencia de 5V (`adcTemp * 5 / 4095.0`) pero el ESP32 opera a 3.3V — puede generar lecturas incorrectas de temperatura si el LM35 está alimentado a 3.3V.
- [ ] No hay interfaz gráfica (dashboard) para visualización en tiempo real (Node-RED, Grafana, etc.).
- [ ] No hay manejo de autenticación MQTT (`allow_anonymous true` — válido para pruebas, no recomendado en producción).
- [ ] El script Python no tiene manejo de errores de conexión ni reconexión automática.

---

## Archivos del Repositorio

```
Comunicacion-MQTT/
├── 8AB_AUTOMAT_AC01_OG_Josue.pdf         # Reporte de la práctica (PDF)
├── Practica1Seguimiento_MQTT/
│   └── Practica1Seguimiento_MQTT.ino     # Código Arduino para ESP32
├── RecepcionDatos_MQTT.py                 # Script Python receptor/logger
├── README.md                              # (Solo título, sin contenido)
└── PROYECTO_DESCRIPCION.md               # Este archivo
```

---

## Tecnologías y Herramientas

| Tecnología | Uso |
|-----------|-----|
| MQTT (protocolo) | Comunicación ligera Publicador/Suscriptor |
| Mosquitto 2.0.21 | Broker MQTT sobre Raspberry Pi |
| ESP32 | Microcontrolador con WiFi integrado |
| Arduino C++ | Firmware del ESP32 |
| PubSubClient | Librería MQTT para Arduino |
| Python 3 | Script de recepción y almacenamiento |
| paho-mqtt | Librería MQTT para Python |
| CSV | Formato de almacenamiento de datos |
| Raspberry Pi | Hardware del broker |
| LM35 | Sensor de temperatura analógico |
| Potenciómetros | Simulación de señales analógicas variables |
