import numpy as np
import rasterio
from pathlib import Path
from rasterio.plot import show

# Configuración
INPUT_DIR = Path('data/processed')
OUTPUT_DIR = Path('data/processed')
# Configuración Método 2: Umbrales
UMBRALES = {
    'ndvi_veg': 0.3,
    'ndbi_urbano': 0.0,
    'cambio_min': 0.15 # Sensibilidad
}

def detectar_cambios(ruta_t1, ruta_t2, ruta_salida):
    print(f"Detectando cambios entre {ruta_t1.name} y {ruta_t2.name}...")
    
    with rasterio.open(ruta_t1) as src1:
        # Banda 1=NDVI, 2=NDBI, 3=NDWI
        ndvi_t1 = src1.read(1)
        ndbi_t1 = src1.read(2)
        ndwi_t1 = src1.read(3)
        perfil = src1.profile
        
    with rasterio.open(ruta_t2) as src2:
        ndvi_t2 = src2.read(1)
        ndbi_t2 = src2.read(2)
        ndwi_t2 = src2.read(3)

    # Inicializar raster de clasificación
    # 0: Sin Cambio
    # 1: Urbanización (Vegetación/Suelo -> Construido)
    # 2: Pérdida de Vegetación (no urbanización)
    # 3: Ganancia de Vegetación
    # 4: Nuevo Cuerpo de Agua
    # 5: Pérdida de Agua
    
    clase = np.zeros_like(ndvi_t1, dtype=np.uint8)
    
    # Máscaras para datos válidos
    mascara_valida = ~np.isnan(ndvi_t1) & ~np.isnan(ndvi_t2)
    
    # 1. Urbanización: Era veg/suelo, Es ahora Urbano Y aumento drástico de NDBI o caída de NDVI
    # Simplificación: Era Vegetación -> Es Urbano
    era_vegetacion = ndvi_t1 > UMBRALES['ndvi_veg']
    es_urbano = ndbi_t2 > UMBRALES['ndbi_urbano']
    # Verificar si el cambio es real (caída de NDVI)
    caida_ndvi = (ndvi_t1 - ndvi_t2) > UMBRALES['cambio_min']
    
    # Regla: Vegetación a Urbano
    mascara_urb = era_vegetacion & es_urbano & caida_ndvi
    clase[mascara_urb & mascara_valida] = 1
    
    # 2. Pérdida de Vegetación (Otro)
    # Solo caída de NDVI, pero no clasificado como urbanización aún
    perdio_veg = caida_ndvi
    clase[perdio_veg & (clase == 0) & mascara_valida] = 2
    
    # 3. Ganancia de Vegetación
    gano_veg = (ndvi_t2 - ndvi_t1) > UMBRALES['cambio_min']
    clase[gano_veg & (clase == 0) & mascara_valida] = 3
    
    # 4. Nuevo Cuerpo de Agua
    era_no_agua = ndwi_t1 < 0
    es_agua = ndwi_t2 > 0.1
    clase[era_no_agua & es_agua & (clase == 0) & mascara_valida] = 4
    
    # 5. Pérdida de Agua
    era_agua = ndwi_t1 > 0.1
    no_es_agua = ndwi_t2 < 0
    clase[era_agua & no_es_agua & (clase == 0) & mascara_valida] = 5
    
    # Guardar resultado
    perfil.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )
    
    print(f"  Guardando clasificación en {ruta_salida}...")
    with rasterio.open(ruta_salida, 'w', **perfil) as dst:
        dst.write(clase, 1)
        # Añadir mapa de colores
        dst.write_colormap(1, {
            0: (0, 0, 0, 0),       # Transparente
            1: (255, 0, 0, 255),   # Urbanización (Rojo)
            2: (255, 165, 0, 255), # Pérdida Veg (Naranja)
            3: (0, 255, 0, 255),   # Ganancia Veg (Verde)
            4: (0, 0, 255, 255),   # Nuevo Agua (Azul)
            5: (0, 255, 255, 255)  # Pérdida Agua (Cian)
        })

    # Imprimir estadísticas
    total_pixeles = np.sum(mascara_valida)
    if total_pixeles > 0:
        print(f"  Urbanización: {np.sum(clase==1)} pixeles ({100*np.sum(clase==1)/total_pixeles:.2f}%)")
        print(f"  Pérdida Veg: {np.sum(clase==2)} pixeles ({100*np.sum(clase==2)/total_pixeles:.2f}%)")
        print(f"  Ganancia Veg: {np.sum(clase==3)} pixeles ({100*np.sum(clase==3)/total_pixeles:.2f}%)")

def main():
    print("Iniciando Detección de Cambios...")
    
    # Encontrar archivos procesados
    # Ordenar por año
    archivos = sorted(list(INPUT_DIR.glob('indices_*.tif')))
    
    if len(archivos) < 2:
        print("No hay suficientes imágenes procesadas para la detección de cambios (se necesitan al menos 2).")
        return
        
    t1 = archivos[0]  # Más antigua
    t2 = archivos[-1] # Más reciente
    
    print(f"Comparando T1: {t1.name} -> T2: {t2.name}")
    
    archivo_salida = OUTPUT_DIR / 'cambio_clasificado.tif'
    
    detectar_cambios(t1, t2, archivo_salida)

if __name__ == "__main__":
    main()
