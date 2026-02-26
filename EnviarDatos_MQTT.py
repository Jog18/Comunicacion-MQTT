# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 15:32:20 2026

@author: oreaj
"""

import paho.mqtt.client as mqtt
import time

def enviar_mensaje(client):
    topic = input("Ingrese el topic al que desea enviar: ")
    mensaje = input("Ingrese el mensaje: ")

    client.publish(topic, mensaje)
    print("Mensaje enviado correctamente.\n")
    
def menu(client):
    while True:
        print("1. Enviar mensaje")
        print("2. Salir")
        opcion = input("Seleccione una opcion: ")

        if opcion == "1":
            enviar_mensaje(client)

        elif opcion == "2":
            print("Saliendo...")
            client.loop_stop()
            client.disconnect()
            break
        

MiMQTT = mqtt.Client()

broker = "10.165.252.191"
MiMQTT.connect(broker, 1883, 60)

MiMQTT.loop_start()

time.sleep(1)

menu(MiMQTT)

