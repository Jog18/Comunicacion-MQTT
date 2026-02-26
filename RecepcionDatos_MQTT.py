# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 15:15:17 2026

@author: oreaj
"""
import paho.mqtt.client as mqtt
import csv
import os
from datetime import datetime

def conectarMQTT(client, userdata, flags, rc):
    print("Conectandi al servidor - " +str(rc))
    client.subscribe("LM35/uno")
    client.subscribe("pot/uno")
    client.subscribe("pot/dos")
    client.subscribe("pot/tres")
    client.subscribe("led/estado")
    

def MensajeMQTT(client, userdata, msg):
    print(f"MSJ: {msg.topic} - {msg.payload.decode()}")
    mensaje = msg.payload.decode()
    publicador = msg.topic
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_csv(timestamp, publicador, mensaje)

def EnviandoMQTT(client, obj, mid):
    print("mensaje: " + str(mid))
    
def SubcribiendoMQTT(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    
def LogMQTT(client, obj, level, string):
    print(f"Log: {string}")
    
def save_csv(timestamp, publicador, mensaje):
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline= '') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            writer.writerow(["timestamp", "Publicador", "Mensaje"])
            
        writer.writerow([timestamp, publicador, mensaje])
        

csv_file = "Hoy"
            
MiMQTT = mqtt.Client()
MiMQTT.on_connect = conectarMQTT

MiMQTT.on_message = MensajeMQTT
MiMQTT.on_subscribe = SubcribiendoMQTT

broker = "10.165.252.191"
MiMQTT.connect(broker, 1883, 60)

MiMQTT.loop_forever()

