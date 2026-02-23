#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "INFINITUM6DD1"; //nombre de la red
const char* password = "Qm3Gc1Aw4q"; //contraseña de nuestra red
const char* mqtt_server = "192.168.1.82"; // broker

WiFiClient espClient;
PubSubClient client(espClient);

long lastMsg = 0;
const int ledPin = 4; // GPIO4 de la ESP32

const int pinPot1 = 34; //GPI34 para leer el pot 1
int valorADCpot1 = 0; //variable para almacenar la lectura del ADC
float voltaje1 = 0.0; // variable para guardar el voltaje equivalente

const int pinPot2 = 35; //GPI35 para leer el pot 2
int valorADCpot2 = 0; //variable para almacenar la lectura del ADC
float voltaje2 = 0.0; // variable para guardar el voltaje equivalente

const int pinPot3 = 32; //GPI32 para leer el pot 3
int valorADCpot3 = 0; //variable para almacenar la lectura del ADC
float voltaje3 = 0.0; // variable para guardar el voltaje equivalente

const int pinLM35 = 36;//GPI36 para leer LM35
int adcTemp = 0;// //variable para almacenar el valor del ADC del LM35
float voltajeLM35 = 0.0; // voltaje del lm35
float temperatura = 0.0; // temperatura equivalente


// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);

  setup_wifi();

  client.setServer(mqtt_server, 1883); //concetamos al servidor mosquitto en el puerto 1883
  client.setCallback(callback);

  //Potenciometro
  analogReadResolution(12);      // Resolución de 12 bits (0–4095)
  analogSetAttenuation(ADC_11db); // Permite leer hasta ~3.3V

  pinMode(ledPin, OUTPUT); // definimos pinled como salida
}

// ---------- LOOP ----------
void loop() {

  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  //POTENCIOMETRO1
  valorADCpot1 = analogRead(pinPot1); //leemos el ADC del pot1
  voltaje1 = (valorADCpot1 * 3.3) / 4095.0; // Convertir a voltaje 0 - 3.3

  //POTENCIOMETRO2
  valorADCpot2 = analogRead(pinPot2); //leemos el ADC del pot2
  voltaje2 = (valorADCpot2 * 3.3) / 4095.0; // Convertir a voltaje 0 - 3.3

  //POTENCIOMETRO3
  valorADCpot3 = analogRead(pinPot3); //leemos el ADC del pot3
  voltaje3 = (valorADCpot3 * 3.3) / 4095.0; // Convertir a voltaje 0 - 3.3

  //LM35
  adcTemp = analogRead(pinLM35); // lectura del ADC DE LM35
  voltajeLM35 = (adcTemp * 5) / 4095.0; //convertimos a voltaje 
  temperatura = voltajeLM35 * 100.0; //calculamos el equivalente a temperatura

  long now = millis();
  if (now - lastMsg > 1000) {
    lastMsg = now;
    //enviar datos pot
    char vol1[10]; //variable tipo caracter a enviar por MQTT
    dtostrf(voltaje1, 1, 3, vol1); //convertimos el valor de voltaje a tipo char para que se pueda enviar a mosquitto
    client.publish("pot/uno", vol1); // mandamos la variable "mensaje"  al topic "pot/uno"

    char vol2[10]; //variable tipo caracter a enviar por MQTT
    dtostrf(voltaje2, 1, 3, vol2); //convertimos el valor de voltaje a tipo char para que se pueda enviar a mosquitto
    client.publish("pot/dos", vol2); // mandamos la variable "mensaje"  al topic "pot/dos"

    char vol3[10]; //variable tipo caracter a enviar por MQTT
    dtostrf(voltaje3, 1, 3, vol3); //convertimos el valor de voltaje a tipo char para que se pueda enviar a mosquitto
    client.publish("pot/tres", vol3); // mandamos la variable "mensaje"  al topic "pot/tres"

    //enviar datos LM35
    char temp[10]; //variable tipo caracter a enviar por MQTT
    dtostrf(temperatura, 1, 3, temp); //convertimos el valor de temperatura a tipo char para que se pueda enviar a mosquitto
    client.publish("LM35/uno", temp); // mandamos la variable "temp" al topic "LM35/uno"

  }
  if (digitalRead(ledPin) == HIGH) { //leemos el estado de ledPin, si esta en HIGH ejecuta:
  client.publish("led/estado", "ON"); //enviar estado: ON al topic "led/estado"
  }
  else {
  client.publish("led/estado", "OFF"); // si el estado es off, enviar estado: off 
}

  
}

// ---------- WIFI ----------
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ---------- CALLBACK MQTT ----------
void callback(char* topic, byte* message, unsigned int length) {

  Serial.print("Mensaje recibido en topic: ");
  Serial.print(topic);
  Serial.print(". Mensaje: ");

  String messageTemp; //variable para almacenar el dato que recibe el esp32 decodificado

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i]; 
  }
  Serial.println();

  // controlar LED
  if (messageTemp == "ON") { //si el mensaje recibido es ON, enciende led
    digitalWrite(ledPin, HIGH);
  }
  if (messageTemp == "OFF") { //si el mensaje recibido es OFF, apaga el led
    digitalWrite(ledPin, LOW);
  }

  
}

// ---------- RECONNECT MQTT ----------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT... ");

    if (client.connect("ESP32Client")) {
      Serial.println("conectado");
      client.subscribe("led/uno");
    } else {
      Serial.print("falló, rc=");
      Serial.print(client.state());
      Serial.println(" intentando en 5 segundos");
      delay(5000);
    }
  }
}
