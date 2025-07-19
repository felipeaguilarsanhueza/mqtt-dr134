try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    mqtt = None
    MQTT_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(
        "paho-mqtt not installed; DR154 worker disabled"
    )

import struct
import logging
import time
from collections import defaultdict
from queue import Queue, Empty

from database import SessionLocal
from models import Device
from crud import get_device_by_mac, save_reading, get_devices_by_type

logger = logging.getLogger(__name__)

MQTT_BROKER = "35.188.202.130"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "ehive2024"

MODBUS_ADDRESSES = {
    "voltage_phase_a": 258,
    "current_phase_a": 256,
}

response_queues = defaultdict(Queue)


def calculate_crc(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


def create_modbus_rtu_command(device_address: int, function_code: int, start_address: int, num_registers: int) -> bytes:
    message = struct.pack(">BBHH", device_address, function_code, start_address, num_registers)
    crc = calculate_crc(message)
    return message + struct.pack("<H", crc)


def on_message(client, userdata, msg):
    imei = msg.topic.strip("/").replace("-response-topic", "")
    logger.debug("Received MQTT message for %s: %s", imei, msg.payload.hex())
    response_queues[imei].put(msg.payload)


def parse_register(payload: bytes) -> int | None:
    if len(payload) < 5:
        return None
    return int.from_bytes(payload[3:5], byteorder="big")


def dr154_worker():
    if not MQTT_AVAILABLE:
        logger.warning("DR154 worker not started: paho-mqtt not installed")
        return

    db = SessionLocal()
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_message = on_message
    logger.info("Connecting DR154 worker to MQTT broker %s:%s", MQTT_BROKER, MQTT_PORT)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    subscribed_imeis: set[str] = set()

    def subscribe_new_devices():
        devices = get_devices_by_type(db, "dr154")
        for device in devices:
            if device.mac not in subscribed_imeis:
                topic = f"/{device.mac}-response-topic"
                logger.info("Subscribing to DR154 topic %s", topic)
                client.subscribe(topic)
                subscribed_imeis.add(device.mac)

    subscribe_new_devices()
    client.loop_start()

    while True:
        try:
            subscribe_new_devices()

            for imei in list(subscribed_imeis):
                results = {}
                for name, address in MODBUS_ADDRESSES.items():
                    command = create_modbus_rtu_command(1, 3, address, 1)
                    query_topic = f"/{imei}-query-topic"
                    client.publish(query_topic, command)
                    try:
                        payload = response_queues[imei].get(timeout=5)
                        value = parse_register(payload)
                        if value is not None:
                            if "voltage" in name:
                                value = round(value / 10, 1)
                            elif "current" in name:
                                value = round(value / 1000, 3)
                        results[name] = value
                    except Empty:
                        logger.warning("Timeout waiting for %s from device %s", name, imei)
                        results[name] = None

                if any(v is not None for v in results.values()):
                    device = get_device_by_mac(db, imei)
                    if device:
                        save_reading(db, results, device.id)
                        logger.info("Saved DR154 reading for %s: %s", imei, results)
        except Exception:
            logger.exception("Error in DR154 worker loop")
            db.rollback()
            time.sleep(1)
