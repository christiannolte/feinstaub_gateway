import time
import requests
import json
import paho.mqtt.client as mqtt
import os


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
  while(1):
    wartezeit = MAX_WARTEZEIT
    # Anfrage an die API senden
    response = requests.get(url)
    # Prüfen, ob die Anfrage erfolgreich war
    if response.status_code == 200:
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
        # Nachricht veroeffentlichen
        client.publish(topic, json_string)
    else:
        print(f"Fehler bei der Anfrage: {response.status_code}")
    time.sleep(wartezeit)


print("Topic: "+topic)
print("URL: "+url)

lese_und_sende()
