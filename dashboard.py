from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mqtt_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

BROKER_HOST = "10.165.252.191"
BROKER_PORT = 1883

SUBSCRIBE_TOPICS = [
    "pot/uno",
    "pot/dos",
    "pot/tres",
    "LM35/uno",
    "led/estado",
]

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
broker_connected = False


def on_connect(client, userdata, flags, rc):
    global broker_connected
    if rc == 0:
        broker_connected = True
        print(f"[MQTT] Conectado al broker {BROKER_HOST}:{BROKER_PORT}")
        for topic in SUBSCRIBE_TOPICS:
            client.subscribe(topic)
            print(f"[MQTT] Suscrito a: {topic}")
        socketio.emit("broker_status", {"connected": True})
    else:
        broker_connected = False
        print(f"[MQTT] Error de conexión, código: {rc}")
        socketio.emit("broker_status", {"connected": False})


def on_disconnect(client, userdata, rc):
    global broker_connected
    broker_connected = False
    print("[MQTT] Desconectado del broker")
    socketio.emit("broker_status", {"connected": False})


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    print(f"[MQTT] {topic}: {payload}")
    socketio.emit("mqtt_message", {"topic": topic, "payload": payload})


def mqtt_thread():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"[MQTT] No se pudo conectar al broker: {e}")
        socketio.emit("broker_status", {"connected": False})


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("[SocketIO] Cliente conectado")
    emit("broker_status", {"connected": broker_connected})


@socketio.on("led_command")
def handle_led_command(data):
    command = data.get("command", "").upper()
    if command in ("ON", "OFF"):
        mqtt_client.publish("led/uno", command)
        print(f"[MQTT] Publicado en led/uno: {command}")


if __name__ == "__main__":
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()
    print("[Flask] Dashboard en http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
