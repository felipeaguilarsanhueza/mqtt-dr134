import paho.mqtt.client as mqtt
import json
import os
import time
from queue import Queue
from database import SessionLocal
from models import Device
from crud import get_device_by_mac, save_reading

MQTT_BROKER = "35.188.202.130"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "ehive2024"

response_queue = Queue()

def on_message(client, userdata, msg):
    mac = msg.topic.strip("/").replace("-response-topic", "")
    response_queue.put((mac, msg.payload.decode()))

def process_json(payload):
    try:
        data = json.loads(payload)
        result = {}
        for item in data["params"]["r_data"]:
            if item["name"] == "voltaje":
                result["voltage"] = round(float(item["value"]) / 10, 1)
            elif item["name"] == "corriente":
                result["current"] = round(float(item["value"]) / 1000, 3)
        return result
    except Exception as e:
        return None

def mqtt_worker():
    db = SessionLocal()
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Suscribirse a todos los dispositivos conocidos
    devices = db.query(Device).all()
    for device in devices:
        topic = f"/{device.mac}-response-topic"
        client.subscribe(topic)

    client.loop_start()

    while True:
        try:
            mac, payload = response_queue.get(timeout=5)
            result = process_json(payload)
            if result:
                device = get_device_by_mac(db, mac)
                if device:
                    save_reading(db, result["voltage"], result["current"], device.id)
        except Exception:
            time.sleep(1)
