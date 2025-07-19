from sqlalchemy.orm import Session
from models import Device, EnergyData

def get_device_by_mac(db: Session, mac: str):
    return db.query(Device).filter(Device.mac == mac).first()

def create_device(db: Session, device_data):
    db_device = Device(**device_data)
    db.add(db_device)
    try:
        db.commit()
        db.refresh(db_device)
    except Exception:
        db.rollback()
        raise
    return db_device

def save_reading(db: Session, voltage, current, device_id):
    reading = EnergyData(voltage=voltage, current=current, device_id=device_id)
    db.add(reading)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return reading
