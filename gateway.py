import time
import requests
import json
import paho.mqtt.client as mqtt
import os
import sys
from pathlib import Path


print("Welcome to Airrohrgateway")

broker = "broker.emqx.io"
port = 1883
topic = os.getenv("topic")

# Beispiel-URL einer öffentlichen API
url = os.getenv("url")
print ("Will read values from: " +url)
print ("Will write data to topic: "+topic)

MAX_WARTEZEIT = 20
MIN_WARTEZEIT = 1
HTTP_TIMEOUT = 10
MQTT_TIMEOUT = 10
# Nach so vielen Sekunden ohne erfolgreiches Lesen und Senden beendet sich das
# Skript, damit Kubernetes den Container neu startet
MAX_OHNE_ERFOLG = 120
# Wird nach jedem Erfolg aktualisiert und von der Liveness-Probe geprueft
HEARTBEAT_DATEI = Path("/tmp/heartbeat")

mydata= {
 "pm25":9999,
 "pm10":9998,
 "pres":9997,
 "rssi":9996,
 "age":9995
}

def lese_und_sende():
  client = mqtt.Client()
  client.connect(broker, port)
  # Netzwerkschleife im Hintergrund: Keepalive, Bestaetigungen, Reconnect
  client.loop_start()
  letzter_erfolg = time.monotonic()
  while(1):
    wartezeit = MAX_WARTEZEIT
    try:
        # Anfrage an die API senden
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        # JSON-Daten extrahieren
        data=json.loads(response.text)
        interval_s=None
        for value in data[u'sensordatavalues']:
            if value[u'value_type']==u'SDS_P1':
                mydata["pm10"]=float(value[u'value'])
            if value[u'value_type']==u'SDS_P2':
                mydata["pm25"]=float(value[u'value'])
            if value[u'value_type']==u'BME280_pressure':
                mydata["pres"]=int(float(value[u'value'])/100.0)
            if value[u'value_type']==u'signal':
                mydata["rssi"]=value[u'value']
            if value[u'value_type']==u'interval':
                interval_s=float(value[u'value'])/1000.0
        mydata["age"]=data["age"]
        mydata["rawpayload"]=data
        # Naechste Messung erwartet nach interval + 1s - age, hoechstens MAX_WARTEZEIT
        if interval_s is not None:
            wartezeit = min(MAX_WARTEZEIT, max(MIN_WARTEZEIT, interval_s + 1 - float(data["age"])))
        json_string = json.dumps(mydata)
        print(json_string)
        # Nachricht veroeffentlichen und auf die Bestaetigung des Brokers warten (QoS 1)
        info = client.publish(topic, json_string, qos=1)
        info.wait_for_publish(MQTT_TIMEOUT)
        if not info.is_published():
            raise RuntimeError("Keine Bestaetigung vom Broker")
        letzter_erfolg = time.monotonic()
        HEARTBEAT_DATEI.touch()
    except Exception as e:
        print(f"Fehler: {e}")
        if time.monotonic() - letzter_erfolg > MAX_OHNE_ERFOLG:
            print(f"Seit {MAX_OHNE_ERFOLG}s kein Erfolg, beende fuer Neustart")
            sys.exit(1)
    time.sleep(wartezeit)


print("Topic: "+topic)
print("URL: "+url)

lese_und_sende()
