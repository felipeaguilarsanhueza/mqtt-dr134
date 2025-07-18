# main.py
import paho.mqtt.client as mqtt
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from queue import Queue

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Configuracion MQTT ---
MQTT_BROKER = "35.188.202.130"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "ehive2024"

MAC = "d4-ad-20-b6-05-a0"
PUBLISH_TOPIC = f"/{MAC}-response-topic"

response_queue = Queue()
running = True

# --- Configuracion Base de Datos ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EnergyData(Base):
    __tablename__ = "energy_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    voltage = Column(Float)
    current = Column(Float)

Base.metadata.create_all(bind=engine)

# --- MQTT Callbacks ---
def on_message(client, userdata, msg):
    if msg.topic == PUBLISH_TOPIC:
        payload = msg.payload.decode('utf-8', errors='ignore')
        response_queue.put(payload)

# --- Procesar JSON ---
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

# --- Guardar en DB ---
def save_to_db(data):
    if not data:
        return
    db = SessionLocal()
    try:
        record = EnergyData(voltage=data["voltage"], current=data["current"])
        db.add(record)
        db.commit()
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/data")
def read_data(limit: int = 10):
    db = SessionLocal()
    try:
        data = db.query(EnergyData).order_by(EnergyData.timestamp.desc()).limit(limit).all()
        return [{"timestamp": d.timestamp, "voltage": d.voltage, "current": d.current} for d in data]
    finally:
        db.close()

# --- Servicio MQTT como tarea paralela ---
def mqtt_worker():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(PUBLISH_TOPIC)
    client.loop_start()

    while running:
        try:
            json_data = response_queue.get(timeout=10)
            results = process_json_data(json_data)
            if results:
                logging.info(f"Voltage: {results['voltage']} V | Current: {results['current']} A")
                save_to_db(results)
        except Exception as e:
            logging.warning(f"Error: {e}")
        time.sleep(1)

    client.loop_stop()
    client.disconnect()

# --- Lanzar servicio MQTT en segundo plano ---
import threading
mqtt_thread = threading.Thread(target=mqtt_worker, daemon=True)
mqtt_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
