# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 15:15:17 2026
@author: oreaj
"""
import paho.mqtt.client as mqtt
import csv
import os
from datetime import datetime

# Archivo de salida
csv_file = "datos_sensores"

# Estructura para almacenar los últimos valores recibidos
# para que cada dato caiga en su columna correspondiente
current_data = {
    "fecha": "",
    "Pot/uno": "",
    "Pot/dos": "",
    "Pot/tres": "",
    "LM35/uno": "",
    "Led/estado": ""
}

def conectarMQTT(client, userdata, flags, rc):
    print("Conectando al servidor - " + str(rc))
    # Nos suscribimos a todos los tópicos necesarios
    client.subscribe("pot/uno")
    client.subscribe("pot/dos")
    client.subscribe("pot/tres")
    client.subscribe("LM35/uno")
    client.subscribe("led/estado")

def MensajeMQTT(client, userdata, msg):
    topic = msg.topic
    mensaje = msg.payload.decode()
    print(f"MSJ: {topic} - {mensaje}")
    
    # Actualizamos la estampa de tiempo
    current_data["fecha"] = datetime.now().strftime("%H:%M:%S")
    
    if topic == "pot/uno":
        current_data["Pot/uno"] = mensaje
    elif topic == "pot/dos":
        current_data["Pot/dos"] = mensaje
    elif topic == "pot/tres":
        current_data["Pot/tres"] = mensaje
    elif topic == "LM35/uno":
        current_data["LM35/uno"] = mensaje
    elif topic == "led/estado":
        current_data["Led/estado"] = mensaje

    # Guardamos la fila completa en el CSV
    save_to_csv(current_data)

def save_to_csv(data_dict):
    file_exists = os.path.isfile(csv_file)
    # Definimos el orden exacto de las columnas
    headers = ["fecha", "Pot/uno", "Pot/dos", "Pot/tres", "LM35/uno", "Led/estado"]
    
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # Si el archivo es nuevo, escribimos la cabecera
        if not file_exists:
            writer.writeheader()
            
        # Escribimos los valores actuales
        writer.writerow(data_dict)

def SubcribiendoMQTT(client, obj, mid, granted_qos):
    print(f"Suscrito con éxito: {mid}")

# Configuración del Cliente
MiMQTT = mqtt.Client()
MiMQTT.on_connect = conectarMQTT
MiMQTT.on_message = MensajeMQTT
MiMQTT.on_subscribe = SubcribiendoMQTT

broker = "10.165.252.191"
MiMQTT.connect(broker, 1883, 60)

MiMQTT.loop_forever()