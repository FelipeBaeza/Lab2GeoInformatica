import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
from pathlib import Path
import os
import matplotlib.pyplot as plt

def analisis_zonal_cambios(ruta_cambios, ruta_zonas, columna_zona='id'):
    """
    Calcula estadisticas de cambio por zona.
    Ruta cambios: TIF clasificado.
    Ruta zonas: Shapefile/GeoJSON de zonas (ej. manzanas).
    """
    print(f"Calculando estadisticas zonales para {ruta_zonas}...")
    zonas = gpd.read_file(ruta_zonas)
    
    # Asegurar CRS coincidente si fuera necesario, pero rasterstats usa coordenadas de la imagen
    # Es importante que el vector este en el mismo CRS que la imagen si se usa rasterio mask,
    # pero rasterstats hace transformacion si se provee affine.
    # Por simplicidad asumiremos que estan proyectados o que rasterstats maneja la interseccion espacial basicos
    
    # Categorias esperadas:
    # 0: Sin cambio, 1: Urbanizacion, 2: Perdida veg, 3: Ganancia veg
    categorical_map = {0: 'sin_cambio', 1: 'urbanizacion', 2: 'perdida_veg', 3: 'ganancia_veg'}
    
    stats = zonal_stats(
        zonas,
        ruta_cambios,
        stats=['count', 'majority'],
        categorical=True,
        category_map=categorical_map
    )
    
    df_stats = pd.DataFrame(stats)
    # Llenar nulos con 0 para categorias que no aparezcan
    for cat in categorical_map.values():
        if cat not in df_stats.columns:
            df_stats[cat] = 0
    df_stats = df_stats.fillna(0)
            
    # Agregar ID de zona
    if columna_zona in zonas.columns:
        df_stats['zona'] = zonas[columna_zona]
    else:
        df_stats['zona'] = df_stats.index
        
    # Calcular areas (asumiendo pixel 10x10 = 100m2 = 0.01 ha)
    pixel_area_ha = 0.01
    
    for col in categorical_map.values():
        if col in df_stats.columns:
            df_stats[f'{col}_ha'] = df_stats[col] * pixel_area_ha
            
    return df_stats

if __name__ == "__main__":
    processed_dir = Path('data/processed')
    vector_dir = Path('data/vector')
    
    cambio_tif = processed_dir / 'cambio_clasificado.tif'
    zonas_shp = vector_dir / 'manzanas_chaiten.geojson' # Nombre ejemplo
    
    if not cambio_tif.exists():
        print("No se encontró cambio_clasificado.tif. Ejecuta detect_changes.py primero.")
        exit()
        
    if not zonas_shp.exists():
        print(f"No se encontró {zonas_shp}. Asegurate de poner el archivo vectorial de zonas.")
        # Crear un dummy grid para probar si no existe
        print("Creando grid de prueba...")
        import rasterio
        from shapely.geometry import box
        with rasterio.open(cambio_tif) as src:
            bounds = src.bounds
            crs = src.crs
            
        # Crear grid 4x4
        minx, miny, maxx, maxy = bounds
        dx = (maxx - minx) / 4
        dy = (maxy - miny) / 4
        
        polys = []
        ids = []
        for i in range(4):
            for j in range(4):
                b = box(minx + i*dx, miny + j*dy, minx + (i+1)*dx, miny + (j+1)*dy)
                polys.append(b)
                ids.append(f"Z{i}{j}")
                
        gdf = gpd.GeoDataFrame({'zona_id': ids, 'geometry': polys}, crs=crs)
        zonas_shp = vector_dir / 'grid_test.geojson'
        gdf.to_file(zonas_shp, driver='GeoJSON')
        print(f"Grid de prueba creado en {zonas_shp}")

    # Ejecutar analisis
    resultados = analisis_zonal_cambios(str(cambio_tif), str(zonas_shp), columna_zona='zona_id')
    
    # Guardar CSV
    csv_out = processed_dir / 'estadisticas_cambio.csv'
    resultados.to_csv(csv_out, index=False)
    print(f"Estadisticas guardadas en {csv_out}")
    
    # Print resumen
    print("Resumen Urbanización (ha):", resultados['urbanizacion_ha'].sum())
