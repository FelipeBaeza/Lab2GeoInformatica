import osmnx as ox
import geopandas as gpd
from pathlib import Path
import os

def download_vector_data():
    """Descarga datos vectoriales de OpenStreetMap para Chaitén."""
    place_name = "Chaitén, Chile"
    vector_dir = Path('data/vector')
    vector_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Descargando datos vectoriales para: {place_name}")
    
    # 1. Limite Comunal (o area urbana)
    try:
        # Intentar obtener el limite administrativo
        gdf_boundary = ox.geocode_to_gdf(place_name)
        boundary_path = vector_dir / 'limite_chaiten.geojson'
        gdf_boundary.to_file(boundary_path, driver='GeoJSON')
        print(f"Límite guardado en {boundary_path}")
        
        # Guardar bbox para referencia
        bbox = gdf_boundary.total_bounds
        print(f"BBox: {bbox}")
        
    except Exception as e:
        print(f"Error descargando límite: {e}")
        gdf_boundary = None

    # Usar grafos desde punto central de Chaiten para asegurar cobertura urbana sin errores de bbox
    point = (-42.91, -72.70)
    
    # 2. Red Vial (Calles)
    try:
        print("Descargando red vial (Urban Area)...")
        # 3km de radio cubre bien Chaiten urbano
        graph = ox.graph_from_point(point, dist=3000, network_type='drive')
            
        # Convertir a GeoDataFrame
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)
        
        edges_path = vector_dir / 'red_vial_chaiten.geojson'
        gdf_edges.to_file(edges_path, driver='GeoJSON')
        print(f"Red vial guardada en {edges_path}")
        
    except Exception as e:
        print(f"Error descargando red vial: {e}")
        
    # 3. Manzanas (Aproximación usando edificios o bloques si fuera posible, 
    # pero OSM no siempre tiene manzanas claras. Usaremos barrios o similar si hay, 
    # si no, crearemos una grilla sobre el area urbana)
    
    # Intentar descargar Buildings como proxy de zona urbana densa
    try:
        print("Descargando huellas de edificios...")
        tags = {'building': True}
        gdf_buildings = ox.features_from_point(point, tags=tags, dist=3000)
             
        buildings_path = vector_dir / 'edificios_chaiten.geojson'
        gdf_buildings.to_file(buildings_path, driver='GeoJSON')
        print(f"Edificios guardados en {buildings_path}")
        
        # Crear 'zonas' agrupando edificios o simplemente una grilla hexagonal sobre el extent de edificios
        # Para el lab, generaremos una grilla hexagonal simple sobre el area poblada
        print("Generando zonas de análisis (grilla)...")
        # Usar total bounds de edificios o del network
        if not gdf_buildings.empty:
            bounds = gdf_buildings.total_bounds
        else:
            bounds = gdf_boundary.total_bounds
            
        # Crear grilla
        # ... logic for grid ...
        # (Simplificado: usar el limite comunal para dividirlo)
        
    except Exception as e:
        print(f"Error descargando edificios: {e}")

if __name__ == "__main__":
    download_vector_data()
