from sqlalchemy import Column, Integer, String
from .database import Base

class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location_wkt = Column(String)  # Storing as Well-Known Text (POINT)
    max_capacity = Column(Integer, default=100)
    current_occupancy = Column(Integer, default=0)

class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    area_wkt = Column(String)  # Storing as Well-Known Text (POLYGON)
    risk_level = Column(Integer, default=1)
