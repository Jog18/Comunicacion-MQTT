# -*- coding: utf-8 -*-
"""
Módulo MQTT unificado: recepción y envío de datos.
Combina la funcionalidad de RecepcionDatos_MQTT.py y EnviarDatos_MQTT.py
en una sola clase reutilizable.
"""

import csv
import os
import threading
from datetime import datetime

import paho.mqtt.client as mqtt


class MQTTClient:
    """
    Cliente MQTT que maneja suscripción, recepción y publicación de mensajes.

    Callbacks opcionales:
        on_message_cb(topic: str, payload: str)  — mensaje recibido
        on_connect_cb(connected: bool)            — cambio de estado de conexión
        on_disconnect_cb()                        — desconexión del broker
    """

    BROKER_HOST = "10.165.252.191"
    BROKER_PORT = 1883

    SUBSCRIBE_TOPICS = [
        "pot/uno",
        "pot/dos",
        "pot/tres",
        "LM35/uno",
        "led/estado",
    ]

    CSV_FILE = "Hoy"

    def __init__(self, on_message_cb=None, on_connect_cb=None, on_disconnect_cb=None):
        self.on_message_cb = on_message_cb
        self.on_connect_cb = on_connect_cb
        self.on_disconnect_cb = on_disconnect_cb
        self.connected = False

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._client.on_message = self._handle_message

    # ── Callbacks internos ────────────────────────────────────────────────────

    def _handle_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"[MQTT] Conectado al broker {self.BROKER_HOST}:{self.BROKER_PORT}")
            for topic in self.SUBSCRIBE_TOPICS:
                client.subscribe(topic)
                print(f"[MQTT] Suscrito a: {topic}")
            if self.on_connect_cb:
                self.on_connect_cb(True)
        else:
            self.connected = False
            print(f"[MQTT] Error de conexión, código: {rc}")
            if self.on_connect_cb:
                self.on_connect_cb(False)

    def _handle_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[MQTT] Desconectado del broker")
        if self.on_disconnect_cb:
            self.on_disconnect_cb()

    def _handle_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8").strip()
        print(f"[MQTT] {topic}: {payload}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_csv(timestamp, topic, payload)
        if self.on_message_cb:
            self.on_message_cb(topic, payload)

    # ── CSV ───────────────────────────────────────────────────────────────────

    def _save_csv(self, timestamp, topic, message):
        file_exists = os.path.isfile(self.CSV_FILE)
        with open(self.CSV_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "Publicador", "Mensaje"])
            writer.writerow([timestamp, topic, message])

    # ── Control del cliente ───────────────────────────────────────────────────

    def start(self):
        """Conecta al broker e inicia el loop en un hilo daemon."""
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def _loop(self):
        try:
            self._client.connect(self.BROKER_HOST, self.BROKER_PORT, keepalive=60)
            self._client.loop_forever()
        except Exception as e:
            print(f"[MQTT] No se pudo conectar al broker: {e}")
            if self.on_connect_cb:
                self.on_connect_cb(False)

    def stop(self):
        """Detiene el loop y desconecta del broker."""
        self._client.loop_stop()
        self._client.disconnect()

    # ── Publicación ───────────────────────────────────────────────────────────

    def publish(self, topic: str, message: str):
        """Publica un mensaje en el topic indicado."""
        self._client.publish(topic, message)
        print(f"[MQTT] Publicado → {topic}: {message}")
