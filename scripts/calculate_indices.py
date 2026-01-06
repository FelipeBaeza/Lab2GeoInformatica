import rasterio
import numpy as np
from pathlib import Path
import os

def calcular_indices(ruta_imagen, ruta_salida):
    """
    Calcula indices espectrales para una imagen Sentinel-2.
    Bandas esperadas (del script de descarga):
    0: B2 (Blue)
    1: B3 (Green)
    2: B4 (Red)
    3: B8 (NIR)
    4: B11 (SWIR1)
    5: B12 (SWIR2)
    """
    print(f"Procesando {ruta_imagen}...")
    with rasterio.open(ruta_imagen) as src:
        # Leer bandas
        # Escalar a reflectancia (geemap exporta como valores originales, usualmente 0-10000 o float 0-1 si calibrado)
        # Vamos a asumir que vienen en 0-10000 si son enteros, o 0-1 si son float.
        # Check dtype
        dtype = src.profile['dtype']
        scale = 10000.0 if 'int' in dtype else 1.0

        blue = src.read(1).astype(float) / scale
        green = src.read(2).astype(float) / scale
        red = src.read(3).astype(float) / scale
        nir = src.read(4).astype(float) / scale
        swir1 = src.read(5).astype(float) / scale
        swir2 = src.read(6).astype(float) / scale

        profile = src.profile

    # Evitar division por cero
    eps = 1e-10

    # NDVI: Vegetacion (NIR - Red) / (NIR + Red)
    ndvi = (nir - red) / (nir + red + eps)

    # NDBI: Areas construidas (SWIR1 - NIR) / (SWIR1 + NIR)
    # Algunos usan SWIR1 (B11), otros SWIR2. El lab dice SWIR - NIR. Usualmente B11.
    ndbi = (swir1 - nir) / (swir1 + nir + eps)

    # NDWI: Agua (Green - NIR) / (Green + NIR) (McFeeters)
    # O (Green - SWIR) (Gao). El lab dice (Green - NIR) / (Green + NIR)
    ndwi = (green - nir) / (green + nir + eps)

    # BSI: Suelo desnudo 
    # ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
    # Usando SWIR1 (B11)
    numerator = (swir1 + red) - (nir + blue)
    denominator = (swir1 + red) + (nir + blue) + eps
    bsi = numerator / denominator

    # Guardar indices
    profile.update(count=4, dtype='float32', nodata=-9999)
    # Also update transform if needed, but it should be same

    # Mask nans
    ndvi = np.nan_to_num(ndvi, nan=-9999)
    ndbi = np.nan_to_num(ndbi, nan=-9999)
    ndwi = np.nan_to_num(ndwi, nan=-9999)
    bsi = np.nan_to_num(bsi, nan=-9999)

    with rasterio.open(ruta_salida, 'w', **profile) as dst:
        dst.write(ndvi.astype('float32'), 1)
        dst.write(ndbi.astype('float32'), 2)
        dst.write(ndwi.astype('float32'), 3)
        dst.write(bsi.astype('float32'), 4)
        dst.descriptions = ('NDVI', 'NDBI', 'NDWI', 'BSI')

    print(f"Indices guardados en {ruta_salida}")
    return {'ndvi': ndvi, 'ndbi': ndbi, 'ndwi': ndwi, 'bsi': bsi}

if __name__ == "__main__":
    input_dir = Path('data/raw')
    output_dir = Path('data/processed')
    output_dir.mkdir(parents=True, exist_ok=True)

    imagenes = sorted(input_dir.glob('sentinel2_*.tif'))
    
    if not imagenes:
        print("No se encontraron imagenes en data/raw. Ejecuta primero download_sentinel.py")
    
    for img in imagenes:
        year = img.stem.split('_')[1]
        salida = output_dir / f'indices_{year}.tif'
        try:
            calcular_indices(img, salida)
        except Exception as e:
            print(f"Error procesando {img.name}: {e}")
