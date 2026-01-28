"""
==============================================================================
Script de Generación de Animación Temporal GIF
Laboratorio 2: Detección de Cambios Urbanos - Chaitén

Este script genera una animación GIF mostrando la evolución temporal
de los índices espectrales o cambios clasificados.

Criterio para Nota 7.0: "Animación temporal (GIF/video de cambios)"
==============================================================================
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless rendering

import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Intentar importar imageio, si no está disponible usar PIL
try:
    import imageio
    USE_IMAGEIO = True
except ImportError:
    from PIL import Image
    USE_IMAGEIO = False
    print("imageio no disponible, usando PIL como alternativa")

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
INPUT_DIR = Path('data/processed')
OUTPUT_DIR = Path('outputs')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de la animación
INDICE = 'NDVI'  # Opciones: 'NDVI', 'NDBI', 'NDWI', 'BSI'
BANDA_INDICE = {'NDVI': 1, 'NDBI': 2, 'NDWI': 3, 'BSI': 4}
CMAP_INDICE = {'NDVI': 'RdYlGn', 'NDBI': 'RdBu_r', 'NDWI': 'Blues', 'BSI': 'YlOrBr'}
VMIN_INDICE = {'NDVI': -0.2, 'NDBI': -0.3, 'NDWI': -0.5, 'BSI': -0.3}
VMAX_INDICE = {'NDVI': 0.8, 'NDBI': 0.3, 'NDWI': 0.5, 'BSI': 0.3}

DURATION = 1.0  # Segundos por frame

# ==============================================================================
# FUNCIONES
# ==============================================================================
def crear_frame(ruta_raster, indice='NDVI', titulo=None):
    """
    Crea una imagen (frame) para el GIF a partir de un raster de índices.
    
    Args:
        ruta_raster: Path al archivo de índices
        indice: Nombre del índice a visualizar
        titulo: Título para el frame (usualmente la fecha)
        
    Returns:
        numpy array: Imagen en formato RGB
    """
    from io import BytesIO
    from PIL import Image
    
    banda = BANDA_INDICE.get(indice, 1)
    cmap = CMAP_INDICE.get(indice, 'viridis')
    vmin = VMIN_INDICE.get(indice, -1)
    vmax = VMAX_INDICE.get(indice, 1)
    
    with rasterio.open(ruta_raster) as src:
        data = src.read(banda)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
    
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(titulo or ruta_raster.stem, fontsize=14, fontweight='bold')
    ax.axis('off')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(indice, fontsize=12)
    
    # Añadir texto de crédito
    fig.text(0.5, 0.02, 'Lab2 Geoinformática - USACH', ha='center', fontsize=10, alpha=0.7)
    
    plt.tight_layout()
    
    # Convertir figura a imagen numpy usando BytesIO (compatible con nuevas versiones)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    image = np.array(Image.open(buf).convert('RGB'))
    buf.close()
    
    plt.close(fig)
    
    return image


def extraer_fecha_de_nombre(nombre):
    """
    Extrae la fecha del nombre del archivo.
    Formato esperado: indices_YYYY_YYYYMMDD.tif
    """
    try:
        partes = nombre.replace('.tif', '').split('_')
        if len(partes) >= 3:
            fecha_str = partes[2]  # YYYYMMDD
            return f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}"
        elif len(partes) >= 2:
            return partes[1]
    except:
        pass
    return nombre


def generar_gif(archivos, indice='NDVI', output_path=None, duration=1.0):
    """
    Genera un GIF animado a partir de una lista de archivos de índices.
    
    Args:
        archivos: Lista de Path a archivos de índices
        indice: Índice a animar
        output_path: Ruta de salida para el GIF
        duration: Duración de cada frame en segundos
    """
    if not archivos:
        print("No hay archivos para animar")
        return
    
    if output_path is None:
        output_path = OUTPUT_DIR / f'animacion_{indice.lower()}.gif'
    
    print(f"Generando animación de {indice}...")
    print(f"  Archivos: {len(archivos)}")
    
    frames = []
    
    for i, archivo in enumerate(archivos):
        fecha = extraer_fecha_de_nombre(archivo.name)
        titulo = f"{indice} - {fecha}"
        
        print(f"  Procesando frame {i+1}/{len(archivos)}: {fecha}")
        
        frame = crear_frame(archivo, indice=indice, titulo=titulo)
        frames.append(frame)
    
    # Guardar GIF
    print(f"  Guardando GIF en {output_path}...")
    
    if USE_IMAGEIO:
        imageio.mimsave(
            str(output_path), 
            frames, 
            duration=duration,
            loop=0  # Loop infinito
        )
    else:
        # Alternativa con PIL
        pil_frames = [Image.fromarray(f) for f in frames]
        pil_frames[0].save(
            str(output_path),
            save_all=True,
            append_images=pil_frames[1:],
            duration=int(duration * 1000),
            loop=0
        )
    
    print(f"  ¡GIF creado exitosamente!")
    print(f"  Tamaño: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path


def main():
    print("=" * 60)
    print("GENERADOR DE ANIMACIÓN TEMPORAL")
    print("Laboratorio 2: Detección de Cambios Urbanos")
    print("=" * 60)
    
    # Buscar archivos de índices
    archivos = sorted(list(INPUT_DIR.glob('indices_*.tif')))
    
    if not archivos:
        print("\nNo se encontraron archivos de índices en data/processed/")
        print("Ejecuta primero: python scripts/calculate_indices.py")
        return
    
    print(f"\nArchivos encontrados: {len(archivos)}")
    for f in archivos:
        print(f"  - {f.name}")
    
    # Generar GIF para cada índice
    indices_a_animar = ['NDVI', 'NDBI']
    
    for indice in indices_a_animar:
        print(f"\n{'='*40}")
        output_path = OUTPUT_DIR / f'animacion_{indice.lower()}.gif'
        generar_gif(archivos, indice=indice, output_path=output_path, duration=DURATION)
    
    print("\n" + "=" * 60)
    print("ANIMACIONES GENERADAS")
    print("=" * 60)
    
    for indice in indices_a_animar:
        gif_path = OUTPUT_DIR / f'animacion_{indice.lower()}.gif'
        if gif_path.exists():
            print(f"  ✓ {gif_path}")
    
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    main()
