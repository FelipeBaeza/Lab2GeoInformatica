"""
Script para descargar datos vectoriales de IDE Chile y otras fuentes oficiales.
Descarga límites comunales y otros datos requeridos por el laboratorio.
"""
import geopandas as gpd
import requests
from pathlib import Path
import os

VECTOR_DIR = Path('data/vector')
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

def download_comunas_chile():
    """
    Descarga límites comunales de Chile desde IDE Chile (simplificado).
    Fuente alternativa: GADM o Natural Earth si IDE Chile no está disponible.
    """
    print("Descargando límites comunales de Chile...")
    
    # Opción 1: Intentar desde GADM (más confiable programáticamente)
    # GADM nivel 3 = Comunas para Chile
    gadm_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_CHL_3.json.zip"
    
    try:
        print("  Intentando desde GADM...")
        gdf = gpd.read_file(gadm_url)
        
        # Filtrar solo Chaitén
        chaiten = gdf[gdf['NAME_3'].str.contains('Chait', case=False, na=False)]
        
        if not chaiten.empty:
            output_path = VECTOR_DIR / 'comuna_chaiten_gadm.geojson'
            chaiten.to_file(output_path, driver='GeoJSON')
            print(f"  Guardado: {output_path}")
            return chaiten
        else:
            print("  No se encontró Chaitén en los datos GADM")
            
    except Exception as e:
        print(f"  Error con GADM: {e}")
    
    # Opción 2: Usar el límite ya descargado de OSM si existe
    osm_limit = VECTOR_DIR / 'limite_chaiten.geojson'
    if osm_limit.exists():
        print(f"  Usando límite existente de OSM: {osm_limit}")
        return gpd.read_file(osm_limit)
    
    print("  No se pudo descargar límite comunal automáticamente.")
    print("  Por favor descarga manualmente desde: https://www.ide.cl/")
    return None


def create_analysis_zones(gdf_boundary, n_zones=16):
    """
    Crea zonas de análisis (grilla) sobre el área de estudio.
    Útil si no hay manzanas censales disponibles.
    """
    print("Creando zonas de análisis...")
    
    from shapely.geometry import box
    import numpy as np
    
    if gdf_boundary is None or gdf_boundary.empty:
        print("  No hay límite disponible para crear zonas")
        return None
    
    # Usar el bbox del límite
    bounds = gdf_boundary.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds
    
    # Crear grilla
    n_cols = int(np.sqrt(n_zones))
    n_rows = n_zones // n_cols
    
    dx = (maxx - minx) / n_cols
    dy = (maxy - miny) / n_rows
    
    polygons = []
    zone_ids = []
    
    for i in range(n_cols):
        for j in range(n_rows):
            cell = box(
                minx + i * dx,
                miny + j * dy,
                minx + (i + 1) * dx,
                miny + (j + 1) * dy
            )
            polygons.append(cell)
            zone_ids.append(f"Z{i:02d}{j:02d}")
    
    gdf_zones = gpd.GeoDataFrame({
        'zona_id': zone_ids,
        'geometry': polygons
    }, crs=gdf_boundary.crs)
    
    # Recortar al límite del área de estudio
    gdf_zones = gpd.overlay(gdf_zones, gdf_boundary, how='intersection')
    
    output_path = VECTOR_DIR / 'zonas_analisis.geojson'
    gdf_zones.to_file(output_path, driver='GeoJSON')
    print(f"  Guardado: {output_path} ({len(gdf_zones)} zonas)")
    
    return gdf_zones


def main():
    print("=" * 60)
    print("DESCARGA DE DATOS VECTORIALES PARA CHAITÉN")
    print("=" * 60)
    
    # 1. Descargar/verificar límite comunal
    gdf_boundary = download_comunas_chile()
    
    # 2. Crear zonas de análisis
    if gdf_boundary is not None:
        create_analysis_zones(gdf_boundary)
    
    # 3. Listar archivos disponibles
    print("\n" + "=" * 60)
    print("ARCHIVOS VECTORIALES DISPONIBLES:")
    print("=" * 60)
    for f in VECTOR_DIR.glob('*'):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.1f} KB)")
    
    print("\nDatos vectoriales listos.")


if __name__ == "__main__":
    main()
