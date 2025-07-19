try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    mqtt = None
    MQTT_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(
        "paho-mqtt not installed; MQTT functionality disabled"
    )
import json
import os
import time
import logging
from queue import Queue, Empty
from database import SessionLocal
from models import Device
from crud import (
    get_device_by_identifier,
    save_reading,
    get_devices_by_type,
)

logger = logging.getLogger(__name__)

MQTT_BROKER = "35.188.202.130"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "ehive2024"

response_queue = Queue()

def on_message(client, userdata, msg):
    mac = msg.topic.strip("/").replace("-response-topic", "")
    payload = msg.payload.decode()
    logger.debug("Received MQTT message for %s: %s", mac, payload)
    response_queue.put((mac, payload))

def process_json(payload):
    try:
        data = json.loads(payload)
        logger.debug("Processing JSON payload: %s", payload)
        result = {}
        for item in data["params"]["r_data"]:
            if item["name"] == "voltaje":
                result["voltage_phase_a"] = round(float(item["value"]) / 10, 1)
            elif item["name"] == "corriente":
                result["current_phase_a"] = round(float(item["value"]) / 1000, 3)
        return result
    except Exception as e:
        logger.error("Failed to process JSON payload: %s", e)
        return None

def mqtt_worker():
    if not MQTT_AVAILABLE:
        logger.warning("MQTT worker not started: paho-mqtt not installed")
        return

    db = SessionLocal()
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_message = on_message
    logger.info("Connecting to MQTT broker %s:%s", MQTT_BROKER, MQTT_PORT)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    subscribed_macs = set()

    def subscribe_new_devices():
        devices = get_devices_by_type(db, "dr134")
        for device in devices:
            if device.mac not in subscribed_macs:
                topic = f"/{device.mac}-response-topic"
                logger.info("Subscribing to topic %s", topic)
                client.subscribe(topic)
                subscribed_macs.add(device.mac)

    # Subscribe to existing devices at startup
    subscribe_new_devices()

    client.loop_start()

    while True:
        try:
            # Check if there are new devices to subscribe to
            subscribe_new_devices()

            mac, payload = response_queue.get(timeout=5)
            logger.debug("Processing message for %s", mac)
            result = process_json(payload)
            if result:
                device = get_device_by_identifier(db, mac)
                if device:
                    save_reading(db, result, device.id)
                    logger.info("Saved reading for %s: %s", mac, result)
        except Empty:
            logger.debug("Response queue timed out waiting for messages")
        except Exception:
            logger.exception("Error in MQTT worker loop")
            db.rollback()
            time.sleep(1)
