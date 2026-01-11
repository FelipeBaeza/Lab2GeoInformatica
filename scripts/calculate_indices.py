import os
import zipfile
import rasterio
import numpy as np
import warnings
from pathlib import Path
from rasterio.enums import Resampling

# Suprimir advertencias
warnings.filterwarnings('ignore')

# Configuración
INPUT_DIR = Path('data/raw/sentinel_series')
OUTPUT_DIR = Path('data/processed')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def buscar_banda_en_zip(zip_path, sufijo_banda):
    """
    Encuentra la ruta completa de una banda dentro del archivo zip.
    ejemplos de sufijo_banda: '_B02_10m.jp2', '_B02.jp2' (dependiendo de la estructura L2A)
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for filename in z.namelist():
                # Buscar fecha de imagen en carpeta GRANULE típicamente
                # Patrón a menudo: .../IMG_DATA/R10m/..._B02_10m.jp2 o similar
                if filename.endswith('.jp2') and 'IMG_DATA' in filename:
                    if sufijo_banda in filename:
                         return f"/vsizip/{zip_path}/{filename}"
    except Exception as e:
        print(f"Error leyendo zip {zip_path}: {e}")
    return None

def leer_banda(ruta, forma_objetivo=None):
    """Lee una banda y la remuestrea si es necesario para coincidir con la forma objetivo."""
    with rasterio.open(ruta) as src:
        if forma_objetivo is None:
            datos = src.read(1)
            perfil = src.profile
            return datos.astype('float32'), perfil
        else:
            datos = src.read(
                1,
                out_shape=forma_objetivo,
                resampling=Resampling.bilinear
            )
            return datos.astype('float32')

def calcular_indices(zip_path):
    print(f"Procesando {zip_path.name}...")
    
    # Identificar bandas
    # La nomenclatura L2A puede variar. Usualmente termina con _BXX_10m.jp2 o _BXX_20m.jp2
    # Necesitamos:
    # Azul: B02 (10m)
    # Verde: B03 (10m)
    # Rojo: B04 (10m)
    # NIR: B08 (10m)
    # SWIR1: B11 (20m)
    # SWIR2: B12 (20m) - opcional, se usa B11 usualmente para NDBI en este contexto
    
    # Intentar sufijos de 10m primero
    ruta_b02 = buscar_banda_en_zip(zip_path, '_B02_10m.jp2') or buscar_banda_en_zip(zip_path, '_B02.jp2')
    ruta_b03 = buscar_banda_en_zip(zip_path, '_B03_10m.jp2') or buscar_banda_en_zip(zip_path, '_B03.jp2')
    ruta_b04 = buscar_banda_en_zip(zip_path, '_B04_10m.jp2') or buscar_banda_en_zip(zip_path, '_B04.jp2')
    ruta_b08 = buscar_banda_en_zip(zip_path, '_B08_10m.jp2') or buscar_banda_en_zip(zip_path, '_B08.jp2')
    
    # Bandas de 20m
    ruta_b11 = buscar_banda_en_zip(zip_path, '_B11_20m.jp2') or buscar_banda_en_zip(zip_path, '_B11.jp2')
    
    if not all([ruta_b02, ruta_b03, ruta_b04, ruta_b08, ruta_b11]):
        print(f"  ERROR: Faltan bandas en {zip_path.name}")
        return

    # Leer bandas de 10m primero para establecer forma de referencia
    azul, perfil = leer_banda(ruta_b02)
    verde, _ = leer_banda(ruta_b03)
    rojo, _ = leer_banda(ruta_b04)
    nir, _ = leer_banda(ruta_b08)
    
    forma_objetivo = azul.shape
    
    # Leer y remuestrear banda de 20m
    swir1 = leer_banda(ruta_b11, forma_objetivo=forma_objetivo)
    
    # Escalar a reflectancia (0-1)
    # Los valores Sentinel-2 son típicamente 0-10000.
    azul /= 10000.0
    verde /= 10000.0
    rojo /= 10000.0
    nir /= 10000.0
    swir1 /= 10000.0
    
    eps = 1e-10

    # 1. NDVI (Vegetación)
    ndvi = (nir - rojo) / (nir + rojo + eps)
    
    # 2. NDBI (Zonas Construidas)
    # Formula variation: (SWIR - NIR) / (SWIR + NIR)
    ndbi = (swir1 - nir) / (swir1 + nir + eps)
    
    # 3. NDWI (Agua)
    # (Green - NIR) / (Green + NIR)
    ndwi = (verde - nir) / (verde + nir + eps)
    
    # 4. BSI (Suelo Desnudo)
    # ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))
    numerador = (swir1 + rojo) - (nir + azul)
    denominador = (swir1 + rojo) + (nir + azul) + eps
    bsi = numerador / denominador

    # Preparar perfil de salida
    perfil.update(
        driver='GTiff',
        count=4,
        dtype='float32'
    )
    
    # Extraer año/fecha para el nombre del archivo
    # Formato nombre: S2A_MSIL2A_YYYYMMDD...
    try:
        str_fecha = zip_path.name.split('_')[2][:8] # YYYYMMDD
        anio = str_fecha[:4]
    except:
        str_fecha = "desconocida"
        anio = "desconocido"

    nombre_salida = f"indices_{anio}_{str_fecha}.tif"
    ruta_salida = OUTPUT_DIR / nombre_salida
    
    print(f"  Guardando {nombre_salida}...")
    
    with rasterio.open(ruta_salida, 'w', **perfil) as dst:
        dst.write(ndvi, 1)
        dst.write(ndbi, 2)
        dst.write(ndwi, 3)
        dst.write(bsi, 4)
        dst.descriptions = ('NDVI', 'NDBI', 'NDWI', 'BSI')

    print(f"  Listo. NDVI medio: {np.nanmean(ndvi):.3f}")

def main():
    print("Iniciando Cálculo de Índices...")
    archivos_zip = sorted(INPUT_DIR.glob('*.zip'))
    
    if not archivos_zip:
        print("No se encontraron archivos zip en data/raw/sentinel_series")
        return

    for archivo_zip in archivos_zip:
        try:
            calcular_indices(archivo_zip)
        except Exception as e:
            print(f"Falló el procesamiento de {archivo_zip.name}: {e}")

if __name__ == "__main__":
    main()
