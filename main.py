# main.py
import paho.mqtt.client as mqtt
import queue
import json
import csv
import logging
import os
import signal
import sys
from datetime import datetime
import time

# --- Configuración ---
MQTT_BROKER = "35.188.202.130"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "ehive2024"

MAC = "d4-ad-20-b6-05-a0"
PUBLISH_TOPIC = f"/{MAC}-response-topic"
SUBSCRIBE_TOPIC = f"/{MAC}-query-topic"
CSV_FILE = "data_dr134.csv"

response_queue = queue.Queue()
running = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- Callbacks ---
def on_message(client, userdata, msg):
    if msg.topic == PUBLISH_TOPIC:
        payload = msg.payload.decode('utf-8', errors='ignore')
        response_queue.put(payload)

# --- Procesamiento JSON ---
def process_json_data(json_string):
    try:
        data = json.loads(json_string)
        results = {}
        for item in data["params"]["r_data"]:
            if item["name"] == "voltaje":
                results["voltage"] = round(float(item["value"]) / 10, 1)
            elif item["name"] == "corriente":
                results["current"] = round(float(item["value"]) / 1000, 3)
        return results
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logging.error(f"Error procesando JSON: {e}")
        return None

# --- Guardar en CSV ---
def save_to_csv(data):
    if not data:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['timestamp', 'voltage', 'current'])
        if not file_exists:
            writer.writeheader()
        row = {'timestamp': timestamp, **data}
        writer.writerow(row)

# --- Signal handler para apagar el script ---
def handle_sigterm(sig, frame):
    global running
    logging.info("Deteniendo el servicio...")
    running = False

# --- Main ---
def main():
    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(PUBLISH_TOPIC)
    client.loop_start()

    logging.info("Servicio MQTT iniciado.")

    try:
        while running:
            try:
                json_data = response_queue.get(timeout=10)
                results = process_json_data(json_data)
                if results:
                    logging.info(f"Voltage: {results['voltage']} V | Current: {results['current']} A")
                    save_to_csv(results)
                else:
                    logging.warning("No se pudieron procesar los datos")
            except queue.Empty:
                logging.warning("No se recibieron datos en 10 segundos")
            time.sleep(1)
    finally:
        client.loop_stop()
        client.disconnect()
        logging.info("Servicio detenido.")

if __name__ == "__main__":
    main()
