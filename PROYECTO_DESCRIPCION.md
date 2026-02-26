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
- Un **Dashboard Web** (Flask + SocketIO) permite visualizar los datos en tiempo real y controlar el LED desde el navegador.
- Un **script de envío** Python (`EnviarDatos_MQTT.py`) permite publicar mensajes MQTT de forma interactiva desde consola.

### Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        RED LOCAL WiFi                             │
│                      (INFINITUM6DD1)                              │
│                                                                  │
│  ┌──────────┐   publica sensores     ┌────────────────────────┐  │
│  │          │ ──────────────────────>│                        │  │
│  │  ESP32   │                        │     Raspberry Pi       │  │
│  │          │ <──────────────────────│   (Mosquitto Broker)   │  │
│  │ GPIO4,   │   comandos LED         │   IP: 10.165.252.191   │  │
│  │ 34,35,36 │                        │      Puerto: 1883      │  │
│  └──────────┘                        │                        │  │
│                                      └───────────┬────────────┘  │
│                                                  │               │
│                      ┌───────────────────────────┤               │
│                      ▼                           ▼               │
│            ┌──────────────────┐     ┌───────────────────────┐   │
│            │ RecepcionDatos   │     │  Dashboard Web        │   │
│            │  _MQTT.py        │     │  (dashboard.py)       │   │
│            │  Guarda CSV      │     │  Flask + SocketIO     │   │
│            └──────────────────┘     │  http://localhost:5000│   │
│                                     └───────────────────────┘   │
│            ┌──────────────────┐                                  │
│            │ EnviarDatos      │                                  │
│            │  _MQTT.py        │                                  │
│            │  Publica mensajes│                                  │
│            │  (interactivo)   │                                  │
│            └──────────────────┘                                  │
└──────────────────────────────────────────────────────────────────┘
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
broker = "10.165.252.191"   # IP del broker MQTT (Raspberry Pi en red del laboratorio)
puerto = 1883
```

#### Tópicos suscritos
```python
client.subscribe("LM35/uno")
client.subscribe("pot/uno")
client.subscribe("pot/dos")
client.subscribe("pot/tres")
client.subscribe("led/estado")   # Añadido en último commit: registra estado del LED
```

#### Archivo CSV generado

El archivo CSV se guarda con el nombre definido en `csv_file`. Actualmente el valor es `"Hoy"` (sin extensión `.csv`), por lo que el archivo generado se llama literalmente **`Hoy`**.

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

### 4. Publicador Interactivo – Python (`EnviarDatos_MQTT.py`)

**Lenguaje:** Python 3
**Librerías usadas:**
- `paho.mqtt.client` – Cliente MQTT
- `time` – Espera de conexión

#### Descripción

Script de consola que permite enviar mensajes MQTT de forma manual e interactiva. Al ejecutarse, muestra un menú con las opciones de enviar un mensaje o salir.

#### Configuración de conexión
```python
broker = "10.165.252.191"
puerto = 1883
```

#### Flujo de funcionamiento
```
Inicio ──> Conectar al broker ──> loop_start() ──> Espera 1 seg
             │
             ▼
           menu()
             ├── Opción 1: enviar_mensaje()
             │     ├── Solicita topic al usuario
             │     ├── Solicita mensaje al usuario
             │     └── client.publish(topic, mensaje)
             └── Opción 2: Salir
                   ├── client.loop_stop()
                   └── client.disconnect()
```

#### Diferencia clave con `RecepcionDatos_MQTT.py`

| Característica | `RecepcionDatos_MQTT.py` | `EnviarDatos_MQTT.py` |
|----------------|--------------------------|------------------------|
| Rol | Suscriptor / Logger | Publicador |
| Tópicos | Fijos (sensores + LED estado) | Libres (ingresados por el usuario) |
| Modo de ejecución | `loop_forever()` (bloqueante) | `loop_start()` (no bloqueante) + menú |
| Salida | Archivo CSV | Sin salida a archivo |

---

### 5. Dashboard Web – Flask + SocketIO (`dashboard.py` + `templates/index.html`)

**Lenguaje:** Python 3 (backend) + HTML/CSS/JavaScript (frontend)
**Librerías usadas:**
- `flask` – Servidor web
- `flask-socketio` – WebSockets en tiempo real
- `paho.mqtt.client` – Cliente MQTT en hilo separado

#### Instalación de dependencias
```bash
pip install -r requirements_dashboard.txt
# Contenido: flask, flask-socketio, paho-mqtt
```

#### Ejecución
```bash
python dashboard.py
# Acceder en el navegador: http://localhost:5000
```

#### Configuración
```python
BROKER_HOST = "10.165.252.191"
BROKER_PORT = 1883
```

#### Arquitectura interna

El dashboard usa dos hilos de ejecución concurrentes:

| Hilo | Responsabilidad |
|------|----------------|
| `mqtt_thread` (daemon) | Conecta al broker, suscribe a tópicos, recibe mensajes y los reenvía al frontend vía SocketIO |
| Hilo principal Flask | Sirve la interfaz web y gestiona los eventos WebSocket del navegador |

#### Tópicos MQTT que maneja

| Tópico | Dirección | Acción |
|--------|-----------|--------|
| `pot/uno` | Recibe | Muestra voltaje en tarjeta azul con barra de progreso |
| `pot/dos` | Recibe | Muestra voltaje en tarjeta morada con barra de progreso |
| `pot/tres` | Recibe | Muestra voltaje en tarjeta naranja con barra de progreso |
| `LM35/uno` | Recibe | Muestra temperatura en tarjeta roja con barra de progreso |
| `led/estado` | Recibe | Actualiza indicador visual del LED (encendido/apagado) |
| `led/uno` | Publica | Envía `"ON"` o `"OFF"` cuando el usuario presiona los botones |

#### Flujo de datos

```
[ESP32] ──publica──> [Broker MQTT]
                          │
                    [dashboard.py]
                    on_message() ──> socketio.emit("mqtt_message")
                          │
                    [Navegador]
                    socket.on("mqtt_message") ──> updateSensor() / updateLed()

[Navegador]
  Botón ON/OFF ──> socket.emit("led_command")
                          │
                    [dashboard.py]
                    handle_led_command() ──> mqtt_client.publish("led/uno", "ON"/"OFF")
                          │
                    [Broker MQTT] ──> [ESP32] ──> controla LED GPIO4
```

#### Interfaz web (`templates/index.html`)

La página web incluye:
- **Header** con indicador de estado del broker (punto verde = conectado, rojo = desconectado)
- **4 tarjetas de sensores** (Pot 1, Pot 2, Pot 3, LM35) con valor numérico y barra de progreso animada
- **Sección de control LED** con indicador visual circular (amarillo brillante = ON) y botones Encender/Apagar
- **Timestamp** de la última actualización recibida

Tecnologías frontend: HTML5, CSS3 (grid layout, transiciones), JavaScript, Socket.IO v4.7.5 (CDN).

---

### 6. Archivo de datos registrados (`Hoy`)

Archivo CSV generado automáticamente por `RecepcionDatos_MQTT.py` durante la sesión de práctica realizada el **24 de febrero de 2026**. Contiene 365 registros de mediciones.

#### Formato
```
timestamp,Publicador,Mensaje
2026-02-24 15:48:27,pot/dos,2.576
2026-02-24 15:48:27,LM35/uno,25.275
2026-02-24 15:48:51,led/estado,ON
...
```

#### Tópicos registrados en el archivo

| Tópico | Tipo de dato | Rango observado |
|--------|-------------|-----------------|
| `pot/uno` | Voltaje (V) | 0.000 (fijo en esta sesión) |
| `pot/dos` | Voltaje (V) | ~2.566 – 2.585 V |
| `pot/tres` | Voltaje (V) | 3.300 V (fijo, máximo) |
| `LM35/uno` | Temperatura (°C) | ~24.6 – 27.35 °C |
| `led/estado` | Estado LED | `"ON"` |

> **Nota:** El archivo no tiene extensión `.csv` porque `csv_file = "Hoy"` en el script (sin agregar `.csv`).

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
        ▼ publica cada 1 seg (pot/uno, pot/dos, pot/tres, LM35/uno, led/estado)
   [Broker MQTT]
   Raspberry Pi: 10.165.252.191:1883
        │
        ├─────────────────────┬──────────────────────┐
        ▼                     ▼                      ▼
  [RecepcionDatos       [dashboard.py]         [Otros clientes]
   _MQTT.py]            Dashboard Web          (mosquitto_sub,
  Guarda en CSV "Hoy"   Flask + SocketIO       EnviarDatos, etc.)
                         http://localhost:5000

[PC / Usuario]
  ├─▶ Botones del dashboard ──▶ socket.emit("led_command")
  │                              ▼
  │                         dashboard.py publica en "led/uno"
  │
  └─▶ EnviarDatos_MQTT.py (consola interactiva)
        ▼ publica en cualquier topic ingresado por el usuario
  [Broker MQTT]
        ▼
  [ESP32] → enciende/apaga LED en GPIO4 (si topic = "led/uno")
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
- [x] Publicación del estado del LED (`led/estado`)
- [x] Script Python receptor y logger de datos en CSV (`RecepcionDatos_MQTT.py`)
- [x] Timestamps en los registros CSV
- [x] Suscripción a `led/estado` en el script receptor (agregado en último commit)
- [x] Script Python publicador interactivo (`EnviarDatos_MQTT.py`)
- [x] Dashboard web en tiempo real con Flask + SocketIO (`dashboard.py`)
- [x] Interfaz HTML con tarjetas de sensores, barras de progreso y control LED
- [x] Sesión de prueba registrada (archivo `Hoy`, 365 registros del 24-Feb-2026)
- [x] Actualización del broker a IP `10.165.252.191` en todos los scripts

### Pendiente / Observaciones

- [ ] **Bug en Python (ambos scripts):** `csv_file = "Hoy"` — falta la extensión `.csv`. El archivo se crea sin extensión. Debería ser `"Hoy.csv"` (antes era `"Practica1"`, también sin extensión).
- [ ] El ESP32 suscribe al tópico `"led/uno"` pero el callback responde a cualquier mensaje en ese tópico (no valida que el tópico sea exactamente `"led/uno"` antes de actuar).
- [ ] La fórmula del LM35 usa referencia de 5V (`adcTemp * 5 / 4095.0`) pero el ESP32 opera a 3.3V — puede generar lecturas incorrectas de temperatura si el LM35 está alimentado a 3.3V.
- [ ] No hay manejo de autenticación MQTT (`allow_anonymous true` — válido para pruebas, no recomendado en producción).
- [ ] El script `RecepcionDatos_MQTT.py` no tiene manejo de errores de conexión ni reconexión automática.
- [ ] El `dashboard.py` captura la excepción de conexión pero no implementa reintentos automáticos.

---

## Archivos del Repositorio

```
Comunicacion-MQTT/
├── 8AB_AUTOMAT_AC01_OG_Josue.pdf         # Reporte de la práctica (PDF)
├── Practica1Seguimiento_MQTT/
│   └── Practica1Seguimiento_MQTT.ino     # Código Arduino para ESP32
├── templates/
│   └── index.html                        # Interfaz web del dashboard
├── EnviarDatos_MQTT.py                   # Script Python publicador interactivo (nuevo)
├── RecepcionDatos_MQTT.py                # Script Python receptor/logger CSV
├── dashboard.py                          # Dashboard web Flask + SocketIO
├── requirements_dashboard.txt            # Dependencias del dashboard (flask, flask-socketio, paho-mqtt)
├── Hoy                                   # CSV con datos registrados el 24-Feb-2026 (365 filas)
├── README.md                             # (Solo título, sin contenido)
└── PROYECTO_DESCRIPCION.md              # Este archivo
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
| Python 3 | Scripts de recepción, publicación y dashboard |
| paho-mqtt | Librería MQTT para Python |
| Flask | Framework web para el dashboard |
| Flask-SocketIO | WebSockets para actualización en tiempo real |
| Socket.IO (JS) | Cliente WebSocket en el navegador |
| CSV | Formato de almacenamiento de datos de sensores |
| Raspberry Pi | Hardware del broker |
| LM35 | Sensor de temperatura analógico |
| Potenciómetros | Simulación de señales analógicas variables |
