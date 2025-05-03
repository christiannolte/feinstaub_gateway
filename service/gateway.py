import time
import requests
import json
import paho.mqtt.client as mqtt
import os

broker = "broker.emqx.io"
port = 1883
topic = os.getenv("topic")

# Beispiel-URL einer öffentlichen API
url = os.getenv("url")

mydata= {
 "pm25":9999,
 "pm10":9998,
 "pres":9997,
 "rssi":9996,
 "age":9995
}

def lese_und_sende():
  # MQTT-Client erstellen
  client = mqtt.Client()
  
  # Verbindung herstellen
  client.connect(broker, port)
  
    
  while(1):

    # Anfrage an die API senden
    response = requests.get(url)

    # Prüfen, ob die Anfrage erfolgreich war
    if response.status_code == 200:
        # JSON-Daten extrahieren
        data=json.loads(response.text)
        for value in data[u'sensordatavalues']:
            if value[u'value_type']==u'SDS_P1':
                mydata["pm10"]=float(value[u'value'])
            if value[u'value_type']==u'SDS_P2':
                mydata["pm25"]=float(value[u'value'])
            if value[u'value_type']==u'BME280_pressure':
                mydata["pres"]=int(float(value[u'value'])/100.0)
            if value[u'value_type']==u'signal':
                mydata["rssi"]=value[u'value']

        mydata["age"]=data["age"]
        json_string = json.dumps(mydata)
        print(json_string)
        # Nachricht veroeffentlichen
        client.publish(topic, json_string)
    else:
        print(f"Fehler bei der Anfrage: {response.status_code}")
    time.sleep(20)


print("Topic: "+topic)
print("URL: "+url)

while(1):
  try:
    lese_und_sende()
  except:
    print("Da ist was schiefgegangen")
    time.sleep(60)
