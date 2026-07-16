from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, database
from .services import routing
import os

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="GeoAlert MVP API", description="Tactical Evacuation Routing System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend estático
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to GeoAlert API"}

@app.get("/api/shelters")
def get_shelters(db: Session = Depends(database.get_db)):
    shelters = db.query(models.Shelter).all()
    # Serialize manually for quick MVP
    result = []
    for s in shelters:
        pt = __import__('shapely.wkt').wkt.loads(s.location_wkt)
        result.append({
            "id": s.id,
            "name": s.name,
            "lat": pt.y,
            "lon": pt.x,
            "max_capacity": s.max_capacity,
            "current_occupancy": s.current_occupancy
        })
    return result

@app.get("/api/risk-zones")
def get_risk_zones(db: Session = Depends(database.get_db)):
    zones = db.query(models.RiskZone).all()
    result = []
    for z in zones:
        poly = __import__('shapely.wkt').wkt.loads(z.area_wkt)
        # Extract coordinates for Leaflet
        coords = list(poly.exterior.coords)
        result.append({
            "id": z.id,
            "name": z.name,
            "coordinates": [{"lat": c[1], "lon": c[0]} for c in coords],
            "risk_level": z.risk_level
        })
    return result

@app.post("/api/risk-zones")
def create_risk_zone(request: schemas.RiskZoneCreate, db: Session = Depends(database.get_db)):
    # Generate a simple square bounding box around the point
    # Rough approximation: 1 degree latitude = ~111km
    offset = request.radius_meters / 111000.0
    
    # Polygon points: bottom-left, top-left, top-right, bottom-right, bottom-left
    min_lat = request.lat - offset
    max_lat = request.lat + offset
    min_lon = request.lon - offset
    max_lon = request.lon + offset

    wkt_poly = f"POLYGON(({min_lon} {min_lat}, {min_lon} {max_lat}, {max_lon} {max_lat}, {max_lon} {min_lat}, {min_lon} {min_lat}))"
    
    new_zone = models.RiskZone(
        name=request.name,
        area_wkt=wkt_poly,
        risk_level=5
    )
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    return {"message": "Zona de riesgo registrada con éxito"}

@app.get("/api/stats")
def get_stats(db: Session = Depends(database.get_db)):
    shelters = db.query(models.Shelter).all()
    total_capacity = sum(s.max_capacity for s in shelters)
    total_occupancy = sum(s.current_occupancy for s in shelters)
    risk_zones_count = db.query(models.RiskZone).count()
    
    shelter_stats = [{"name": s.name, "occupancy": s.current_occupancy, "free": s.max_capacity - s.current_occupancy} for s in shelters]
    
    return {
        "global": {
            "total_capacity": total_capacity,
            "total_occupancy": total_occupancy,
            "risk_zones_active": risk_zones_count
        },
        "shelters": shelter_stats
    }

@app.post("/evacuation-route", response_model=schemas.EvacuationResponse)
def get_route(request: schemas.EvacuationRequest, db: Session = Depends(database.get_db)):
    try:
        response = routing.get_evacuation_route(db, request)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
