# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from .mqtt_worker import mqtt_worker
from .database import Base, engine
from .api.routes import router as api_router

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

# Lanzar el worker MQTT
mqtt_thread = threading.Thread(target=mqtt_worker, daemon=True)
mqtt_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
