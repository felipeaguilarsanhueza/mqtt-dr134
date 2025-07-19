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

def get_devices_by_type(db: Session, device_type: str):
    return db.query(Device).filter(Device.device_type == device_type).all()

def save_reading(db: Session, reading_data: dict, device_id: int):
    """Save a set of measurements for a device."""
    reading = EnergyData(device_id=device_id, **reading_data)
    db.add(reading)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return reading
