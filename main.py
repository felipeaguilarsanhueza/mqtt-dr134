# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import threading
from mqtt_worker import mqtt_worker, MQTT_AVAILABLE as MQTT1_AVAILABLE
from dr154_worker import dr154_worker, MQTT_AVAILABLE as MQTT2_AVAILABLE
from database import Base, engine
from api.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Lanzar los workers MQTT si la dependencia paho-mqtt está disponible
if MQTT1_AVAILABLE:
    mqtt_thread = threading.Thread(target=mqtt_worker, daemon=True)
    mqtt_thread.start()
else:
    logger.warning("MQTT worker disabled due to missing dependency")

if MQTT2_AVAILABLE:
    dr154_thread = threading.Thread(target=dr154_worker, daemon=True)
    dr154_thread.start()
else:
    logger.warning("DR154 worker disabled due to missing dependency")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
