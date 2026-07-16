from pydantic import BaseModel
from typing import List, Tuple, Optional

class EvacuationRequest(BaseModel):
    user_lat: float
    user_lon: float
    radius_meters: float = 2000.0

class ShelterInfo(BaseModel):
    id: int
    name: str
    lat: float
    lon: float

class EvacuationResponse(BaseModel):
    assigned_shelter: ShelterInfo
    route_coordinates: List[Tuple[float, float]]
    distance_meters: float

class RiskZoneCreate(BaseModel):
    name: str
    lat: float
    lon: float
    radius_meters: float = 50.0 # Will generate a square polygon around the point
