from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    mac = Column(String, unique=True, index=True)
    description = Column(String)
    device_type = Column(String, default="dr134")

    readings = relationship("EnergyData", back_populates="device")

class EnergyData(Base):
    __tablename__ = "energy_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    # Voltajes y Corrientes (RMS)
    voltage_phase_a = Column(Float, nullable=True)
    voltage_phase_b = Column(Float, nullable=True)
    voltage_phase_c = Column(Float, nullable=True)
    voltage_line_ab = Column(Float, nullable=True)
    voltage_line_bc = Column(Float, nullable=True)
    voltage_line_ca = Column(Float, nullable=True)
    current_phase_a = Column(Float, nullable=True)
    current_phase_b = Column(Float, nullable=True)
    current_phase_c = Column(Float, nullable=True)
    neutral_current = Column(Float, nullable=True)

    # Potencias
    active_power_phase_a = Column(Float, nullable=True)
    active_power_phase_b = Column(Float, nullable=True)
    active_power_phase_c = Column(Float, nullable=True)
    reactive_power_phase_a = Column(Float, nullable=True)
    reactive_power_phase_b = Column(Float, nullable=True)
    reactive_power_phase_c = Column(Float, nullable=True)
    apparent_power_phase_a = Column(Float, nullable=True)
    apparent_power_phase_b = Column(Float, nullable=True)
    apparent_power_phase_c = Column(Float, nullable=True)
    power_factor_phase_a = Column(Float, nullable=True)
    power_factor_phase_b = Column(Float, nullable=True)
    power_factor_phase_c = Column(Float, nullable=True)
    total_active_power = Column(Float, nullable=True)
    total_reactive_power = Column(Float, nullable=True)
    total_apparent_power = Column(Float, nullable=True)
    total_power_factor = Column(Float, nullable=True)

    # Energía acumulada
    energy_active_import = Column(Float, nullable=True)
    energy_active_export = Column(Float, nullable=True)
    energy_reactive_import = Column(Float, nullable=True)
    energy_reactive_export = Column(Float, nullable=True)

    # Calidad de la energía
    frequency = Column(Float, nullable=True)
    thd_voltage_phase_a = Column(Float, nullable=True)
    thd_voltage_phase_b = Column(Float, nullable=True)
    thd_voltage_phase_c = Column(Float, nullable=True)
    thd_current_phase_a = Column(Float, nullable=True)
    thd_current_phase_b = Column(Float, nullable=True)
    thd_current_phase_c = Column(Float, nullable=True)
    voltage_unbalance = Column(Float, nullable=True)
    current_unbalance = Column(Float, nullable=True)

    device_id = Column(Integer, ForeignKey("devices.id"))

    device = relationship("Device", back_populates="readings")
