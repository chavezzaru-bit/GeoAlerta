from app.database import engine, Base, SessionLocal
from app.models import Shelter, RiskZone

# Ensure tables are created
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# We will wipe existing data for this new seed
db.query(Shelter).delete()
db.query(RiskZone).delete()
db.commit()

print("Sembrando base de datos en Lima, Perú...")

# Shelter 1: Parque Kennedy (Miraflores)
# Capacidad muy pequeña para probar rápido el desbordamiento (solo 3 cupos)
s1 = Shelter(name="Refugio Kennedy (Central)", location_wkt="POINT(-77.029707 -12.121915)", max_capacity=3, current_occupancy=0)

# Shelter 2: Estadio Manuel Bonilla
s2 = Shelter(name="Refugio Estadio Bonilla (Respaldo)", location_wkt="POINT(-77.042718 -12.115856)", max_capacity=50, current_occupancy=0)

# Shelter 3: Parque Reducto No. 2
s3 = Shelter(name="Refugio Parque Reducto", location_wkt="POINT(-77.020473 -12.127811)", max_capacity=100, current_occupancy=0)

# Risk Zone: Derrumbe cerca al óvalo de Miraflores
rz = RiskZone(name="Zona de Derrumbe", area_wkt="POLYGON((-77.031 -12.119, -77.031 -12.120, -77.028 -12.120, -77.028 -12.119, -77.031 -12.119))", risk_level=5)

db.add(s1)
db.add(s2)
db.add(s3)
db.add(rz)
db.commit()

print("¡Semilla completada exitosamente!")
db.close()
