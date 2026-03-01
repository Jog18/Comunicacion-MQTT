# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 15:15:17 2026
@author: oreaj
"""
import csv
import os
import threading
from datetime import datetime
import paho.mqtt.client as mqtt


class MQTTClient:

    BROKER_HOST = "10.180.31.191"
    BROKER_PORT = 1883

    SUBSCRIBE_TOPICS = [
        "pot/uno",
        "pot/dos",
        "pot/tres",
        "LM35/uno",
        "led/estado",
    ]

    CSV_FILE = "DATOS.csv"

    def __init__(self, on_message_cb=None, on_connect_cb=None, on_disconnect_cb=None):

        self.on_message_cb = on_message_cb
        self.on_connect_cb = on_connect_cb
        self.on_disconnect_cb = on_disconnect_cb
        self.connected = False

        self.current_data = {
            "fecha": "",
            "Pot/uno": "",
            "Pot/dos": "",
            "Pot/tres": "",
            "LM35/uno": "",
            "Led/estado": ""
        }

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._client.on_message = self._handle_message

    def _handle_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"Conectado a {self.BROKER_HOST}:{self.BROKER_PORT}")

            for topic in self.SUBSCRIBE_TOPICS:
                client.subscribe(topic)
                print(f"Suscrito a: {topic}")

            if self.on_connect_cb:
                self.on_connect_cb(True)
        else:
            self.connected = False
            print(f"[MQTT] Error de conexión: {rc}")
            if self.on_connect_cb:
                self.on_connect_cb(False)


    def _handle_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[MQTT] Desconectado")
        if self.on_disconnect_cb:
            self.on_disconnect_cb()


    def _handle_message(self, client, userdata, msg):

        topic = msg.topic
        payload = msg.payload.decode("utf-8").strip()

        print(f"[MQTT] {topic}: {payload}")

        # Actualizamos fecha
        self.current_data["fecha"] = datetime.now().strftime("%H:%M:%S")

        # Guardamos según topic
        if topic == "pot/uno":
            self.current_data["Pot/uno"] = payload
        elif topic == "pot/dos":
            self.current_data["Pot/dos"] = payload
        elif topic == "pot/tres":
            self.current_data["Pot/tres"] = payload
        elif topic == "LM35/uno":
            self.current_data["LM35/uno"] = payload
        elif topic == "led/estado":
            self.current_data["Led/estado"] = payload

        # Guardar fila completa
        self._save_csv(self.current_data)

        if self.on_message_cb:
            self.on_message_cb(topic, payload)

    def _save_csv(self, data_dict):

        file_exists = os.path.isfile(self.CSV_FILE)

        headers = ["fecha", "Pot/uno", "Pot/dos",
                   "Pot/tres", "LM35/uno", "Led/estado"]

        with open(self.CSV_FILE, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)

            if not file_exists:
                writer.writeheader()

            writer.writerow(data_dict)


    def start(self):
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def _loop(self):
        try:
            self._client.connect(self.BROKER_HOST, self.BROKER_PORT, keepalive=60)
            self._client.loop_forever()
        except Exception as e:
            print(f"[MQTT] No se pudo conectar: {e}")
            if self.on_connect_cb:
                self.on_connect_cb(False)

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()


    def publish(self, topic: str, message: str):
        self._client.publish(topic, message)
        print(f"[MQTT] Publicado → {topic}: {message}")