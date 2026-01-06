import numpy as np
import rasterio
from pathlib import Path
import os

def load_indices(tif_path):
    """Carga los indices desde el GeoTIFF procesado."""
    with rasterio.open(tif_path) as src:
        # Asumiendo orden: 1:NDVI, 2:NDBI, 3:NDWI, 4:BSI
        data = {
            'ndvi': src.read(1),
            'ndbi': src.read(2),
            'ndwi': src.read(3),
            'bsi': src.read(4),
            'profile': src.profile
        }
    return data

def detectar_cambio_diferencia(indices_t1, indices_t2, umbral=0.15):
    """
    Detecta cambios usando diferencia de NDVI.
    Retorna 1 (Ganancia), -1 (Perdida), 0 (Sin cambio)
    """
    diferencia = indices_t2['ndvi'] - indices_t1['ndvi']
    
    cambio = np.zeros_like(diferencia, dtype=np.int8)
    # Ignorar nodata
    mask_nodata = (indices_t1['ndvi'] == -9999) | (indices_t2['ndvi'] == -9999)
    
    cambio[diferencia < -umbral] = -1 # Perdida
    cambio[diferencia > umbral] = 1   # Ganancia
    cambio[mask_nodata] = 0
    
    return cambio, diferencia

def clasificar_cambio_urbano(indices_t1, indices_t2, umbrales=None):
    """
    Clasifica tipo de cambio urbano.
    0: Sin cambio
    1: Urbanizacion
    2: Perdida vegetacion
    3: Ganancia vegetacion
    4: Nuevo cuerpo agua
    5: Perdida agua
    """
    if umbrales is None:
        umbrales = {
            'ndvi_veg': 0.3, 
            'ndbi_urbano': 0.0,
            'cambio_min': 0.1
        }
    
    ndvi_t1 = indices_t1['ndvi']
    ndbi_t2 = indices_t2['ndbi']
    ndvi_t2 = indices_t2['ndvi']
    ndwi_t1 = indices_t1['ndwi']
    ndwi_t2 = indices_t2['ndwi']
    
    clase = np.zeros_like(ndvi_t1, dtype=np.uint8)
    
    # Mascara nodata
    valid_mask = (ndvi_t1 != -9999) & (ndvi_t2 != -9999)
    
    # 1. Urbanizacion: era veg y ahora es urbano
    era_veg = ndvi_t1 > umbrales['ndvi_veg']
    es_urbano = ndbi_t2 > umbrales['ndbi_urbano']
    clase[valid_mask & era_veg & es_urbano] = 1
    
    # 2. Perdida veg (general)
    perdio_veg = (ndvi_t1 - ndvi_t2) > umbrales['cambio_min']
    # Solo si no es ya urbanizacion
    clase[valid_mask & perdio_veg & (clase == 0)] = 2
    
    # 3. Ganancia veg
    gano_veg = (ndvi_t2 - ndvi_t1) > umbrales['cambio_min']
    clase[valid_mask & gano_veg & (clase == 0)] = 3
    
    return clase

if __name__ == "__main__":
    processed_dir = Path('data/processed')
    
    files = sorted(processed_dir.glob('indices_*.tif'))
    if len(files) < 2:
        print("Se necesitan al menos 2 imagenes procesadas.")
        exit()
        
    # Comparar primera (T1) con ultima (T2)
    t1_path = files[0]
    t2_path = files[-1]
    
    print(f"Comparando {t1_path.name} con {t2_path.name}...")
    
    indices_t1 = load_indices(t1_path)
    indices_t2 = load_indices(t2_path)
    
    # Metodo 1: Diferencia
    cambio_dif, dif_val = detectar_cambio_diferencia(indices_t1, indices_t2)
    
    # Metodo 2: Clasificacion
    clase_cambio = clasificar_cambio_urbano(indices_t1, indices_t2)
    
    # Guardar resultados
    profile = indices_t1['profile'].copy()
    profile.update(dtype='int8', count=1, nodata=0)
    
    out_diff = processed_dir / 'cambio_diferencia.tif'
    with rasterio.open(out_diff, 'w', **profile) as dst:
        dst.write(cambio_dif, 1)
        
    profile.update(dtype='uint8')
    out_class = processed_dir / 'cambio_clasificado.tif'
    with rasterio.open(out_class, 'w', **profile) as dst:
        dst.write(clase_cambio, 1)
        
    print(f"Resultados guardados: {out_diff}, {out_class}")
