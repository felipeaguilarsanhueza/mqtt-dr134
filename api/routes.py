from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
import os
import logging
from database import SessionLocal
from models import EnergyData
from crud import get_device_by_identifier
from api.schemas import EnergyDataBase, CurrentData

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "secret")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter()

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/data/{identifier}", response_model=list[EnergyDataBase])
def get_data(
    identifier: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    logger.info("Fetching data for identifier %s", identifier)
    device = get_device_by_identifier(db, identifier)
    if not device:
        logger.warning("Device %s not found", identifier)
        raise HTTPException(status_code=404, detail="Device not found")
    data = (
        db.query(EnergyData)
        .filter(EnergyData.device_id == device.id)
        .order_by(EnergyData.timestamp.desc())
        .limit(limit)
        .all()
    )
    logger.info("Returning %d readings for device %s", len(data), identifier)
    return data


@router.get("/current/{identifier}", response_model=CurrentData)
def get_current(
    identifier: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    logger.info("Fetching latest current for %s", identifier)
    device = get_device_by_identifier(db, identifier)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    data = (
        db.query(EnergyData)
        .filter(EnergyData.device_id == device.id)
        .order_by(EnergyData.timestamp.desc())
        .first()
    )
    if not data:
        raise HTTPException(status_code=404, detail="No readings for device")
    return data
