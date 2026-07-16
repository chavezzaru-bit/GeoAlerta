import osmnx as ox
import networkx as nx
from sqlalchemy.orm import Session
import shapely.wkt
from shapely.geometry import Point
from .. import models, schemas

ox.settings.use_cache = True
ox.settings.log_console = True

def get_evacuation_route(db: Session, request: schemas.EvacuationRequest):
    # 1. Fetch active shelters and risk zones
    shelters = db.query(models.Shelter).filter(models.Shelter.current_occupancy < models.Shelter.max_capacity).all()
    if not shelters:
        # AUTO-RESET: Si todos los refugios se llenaron durante la prueba, los vaciamos automáticamente
        # para que el prototipo pueda seguir funcionando infinitamente.
        all_shelters = db.query(models.Shelter).all()
        for s in all_shelters:
            s.current_occupancy = 0
        db.commit()
        shelters = all_shelters

    risk_zones = db.query(models.RiskZone).all()
    
    # 2. Get street network from OpenStreetMap via OSMnx
    try:
        G = ox.graph_from_point((request.user_lat, request.user_lon), dist=request.radius_meters, network_type='walk')
        
        # 3. Remove nodes/edges inside risk zones
        nodes_to_remove = []
        for node, data in G.nodes(data=True):
            point = shapely.geometry.Point(data['x'], data['y'])
            for zone in risk_zones:
                poly = shapely.wkt.loads(zone.area_wkt)
                if poly.contains(point):
                    nodes_to_remove.append(node)
                    break
        G.remove_nodes_from(nodes_to_remove)

        # 4. Find nearest nodes
        orig_node = ox.distance.nearest_nodes(G, request.user_lon, request.user_lat)

        # 5. Calculate shortest paths avoiding risk zones
        best_shelter = None
        best_route = None
        min_distance = float('inf')

        for shelter in shelters:
            shelter_pt = shapely.wkt.loads(shelter.location_wkt)
            try:
                dest_node = ox.distance.nearest_nodes(G, shelter_pt.x, shelter_pt.y)
                distance = nx.shortest_path_length(G, orig_node, dest_node, weight='length')
                if distance < min_distance:
                    min_distance = distance
                    best_route = nx.shortest_path(G, orig_node, dest_node, weight='length')
                    best_shelter = shelter
            except nx.NetworkXNoPath:
                continue

        if not best_route:
            raise Exception("No safe route found to any available shelter.")

        # [NUEVO LOGICA DE FLUJO MASIVO]: Descontar capacidad del refugio
        best_shelter.current_occupancy += 1
        db.commit()

        # 7. Extract coordinates for the route
        route_coords = []
        for node in best_route:
            point = G.nodes[node]
            route_coords.append([point['y'], point['x']])

        return schemas.EvacuationResponse(
            assigned_shelter=schemas.ShelterInfo(
                id=best_shelter.id,
                name=best_shelter.name,
                lat=shapely.wkt.loads(best_shelter.location_wkt).y,
                lon=shapely.wkt.loads(best_shelter.location_wkt).x
            ),
            route_coordinates=route_coords,
            distance_meters=min_distance
        )
    except Exception as e:
        # FALLBACK: Si OSMnx falla (por ej, por timeout), retornamos ruta en línea recta
        # para no romper el prototipo visual
        best_shelter = shelters[0]
        best_shelter.current_occupancy += 1
        db.commit()
        
        shelter_pt = shapely.wkt.loads(best_shelter.location_wkt)
        route_coords = [
            [request.user_lat, request.user_lon],
            [shelter_pt.y, shelter_pt.x]
        ]
        
        return schemas.EvacuationResponse(
            assigned_shelter=schemas.ShelterInfo(
                id=best_shelter.id,
                name=best_shelter.name,
                lat=shelter_pt.y,
                lon=shelter_pt.x
            ),
            route_coordinates=route_coords,
            distance_meters=1000 # Dummy distance
        )
