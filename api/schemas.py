from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class EnergyDataBase(BaseModel):
    timestamp: datetime
    voltage_phase_a: Optional[float] = None
    voltage_phase_b: Optional[float] = None
    voltage_phase_c: Optional[float] = None
    voltage_line_ab: Optional[float] = None
    voltage_line_bc: Optional[float] = None
    voltage_line_ca: Optional[float] = None
    current_phase_a: Optional[float] = None
    current_phase_b: Optional[float] = None
    current_phase_c: Optional[float] = None
    neutral_current: Optional[float] = None
    active_power_phase_a: Optional[float] = None
    active_power_phase_b: Optional[float] = None
    active_power_phase_c: Optional[float] = None
    reactive_power_phase_a: Optional[float] = None
    reactive_power_phase_b: Optional[float] = None
    reactive_power_phase_c: Optional[float] = None
    apparent_power_phase_a: Optional[float] = None
    apparent_power_phase_b: Optional[float] = None
    apparent_power_phase_c: Optional[float] = None
    power_factor_phase_a: Optional[float] = None
    power_factor_phase_b: Optional[float] = None
    power_factor_phase_c: Optional[float] = None
    total_active_power: Optional[float] = None
    total_reactive_power: Optional[float] = None
    total_apparent_power: Optional[float] = None
    total_power_factor: Optional[float] = None
    energy_active_import: Optional[float] = None
    energy_active_export: Optional[float] = None
    energy_reactive_import: Optional[float] = None
    energy_reactive_export: Optional[float] = None
    frequency: Optional[float] = None
    thd_voltage_phase_a: Optional[float] = None
    thd_voltage_phase_b: Optional[float] = None
    thd_voltage_phase_c: Optional[float] = None
    thd_current_phase_a: Optional[float] = None
    thd_current_phase_b: Optional[float] = None
    thd_current_phase_c: Optional[float] = None
    voltage_unbalance: Optional[float] = None
    current_unbalance: Optional[float] = None

    class Config:
        orm_mode = True

class CurrentData(BaseModel):
    timestamp: datetime
    current_phase_a: Optional[float] = None
    current_phase_b: Optional[float] = None
    current_phase_c: Optional[float] = None
    neutral_current: Optional[float] = None

    class Config:
        orm_mode = True
