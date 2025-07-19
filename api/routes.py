from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from database import SessionLocal
from models import Device, EnergyData
from crud import get_device_by_mac

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/data/{mac}")
def get_data(mac: str, limit: int = 10, db: Session = Depends(get_db)):
    logger.info("Fetching data for MAC %s", mac)
    device = get_device_by_mac(db, mac)
    if not device:
        logger.warning("Device with MAC %s not found", mac)
        raise HTTPException(status_code=404, detail="Device not found")
    data = db.query(EnergyData).filter(EnergyData.device_id == device.id)\
        .order_by(EnergyData.timestamp.desc()).limit(limit).all()
    logger.info("Returning %d readings for device %s", len(data), mac)
    return [
        {"timestamp": r.timestamp, "voltage": r.voltage, "current": r.current}
        for r in data
    ]
