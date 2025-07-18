from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Device, EnergyData
from ..crud import get_device_by_mac

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/data/{mac}")
def get_data(mac: str, limit: int = 10, db: Session = Depends(get_db)):
    device = get_device_by_mac(db, mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    data = db.query(EnergyData).filter(EnergyData.device_id == device.id)\
        .order_by(EnergyData.timestamp.desc()).limit(limit).all()
    return [
        {"timestamp": r.timestamp, "voltage": r.voltage, "current": r.current}
        for r in data
    ]
