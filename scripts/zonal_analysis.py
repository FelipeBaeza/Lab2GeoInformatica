import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterstats import zonal_stats
from pathlib import Path

# Configuración
RUTA_ZONAS = Path('data/vector/zonas_analisis.geojson')
RASTER_CAMBIO = Path('data/processed/cambio_clasificado.tif')
DIR_INDICES = Path('data/processed')
DIR_SALIDA_FIGURAS = Path('outputs/figures')
DIR_SALIDA_DATOS = Path('data/processed')
DIR_SALIDA_FIGURAS.mkdir(parents=True, exist_ok=True)
DIR_SALIDA_DATOS.mkdir(parents=True, exist_ok=True)

CATEGORIAS = {
    1: 'urbanizacion',
    2: 'perdida_veg',
    3: 'ganancia_veg'
}

def analizar_cambios_zonales():
    print("Ejecutando Análisis Zonal...")
    
    if not RUTA_ZONAS.exists():
        print(f"Error: No se encuentra el archivo de zonas en {RUTA_ZONAS}")
        return

    # Leer zonas
    zonas = gpd.read_file(RUTA_ZONAS)
    
    # Ejecutar estadísticas zonales
    # Queremos conteos de cada valor categórico
    stats = zonal_stats(
        zonas,
        RASTER_CAMBIO,
        categorical=True,
        category_map={
            1: 'urbanizacion',
            2: 'perdida_veg',
            3: 'ganancia_veg',
            4: 'nuevo_agua',
            5: 'perdida_agua'
        }
    )
    
    # Convertir a DataFrame
    df_stats = pd.DataFrame(stats)
    
    # Añadir ID de Zona si está disponible
    col_nombre = 'id' if 'id' in zonas.columns else zonas.columns[0]
    df_stats['zona'] = zonas[col_nombre]
    
    # Llenar NaNs con 0
    df_stats = df_stats.fillna(0)
    
    # Calcular Áreas (asumiendo 10x10m = 100m2 = 0.01 ha)
    area_pixel_ha = 0.01
    
    cols_interes = ['urbanizacion', 'perdida_veg', 'ganancia_veg']
    for col in cols_interes:
        if col in df_stats.columns:
            df_stats[f'{col}_ha'] = df_stats[col] * area_pixel_ha
            
    # Guardar CSV
    csv_salida = DIR_SALIDA_DATOS / 'estadisticas_cambio.csv'
    df_stats.to_csv(csv_salida, index=False)
    print(f"  Estadísticas guardadas en {csv_salida}")
    
    # Resumen
    print("\nResultados Resumen (Ha):")
    if 'urbanizacion_ha' in df_stats.columns:
        print(f"  Total Urbanización: {df_stats['urbanizacion_ha'].sum():.2f} ha")
    if 'perdida_veg_ha' in df_stats.columns:
        print(f"  Total Pérdida Veg: {df_stats['perdida_veg_ha'].sum():.2f} ha")

    return df_stats

def analizar_evolucion_temporal():
    print("\nAnalizando Evolución Temporal...")
    
    archivos = sorted(list(DIR_INDICES.glob('indices_*.tif')))
    resultados = []
    
    for f in archivos:
        # Extraer fecha del nombre indices_YYYY_YYYYMMDD.tif
        try:
            str_fecha = f.stem.split('_')[2]
            anio = f.stem.split('_')[1]
        except:
             continue
             
        with rasterio.open(f) as src:
            ndvi = src.read(1)
            ndbi = src.read(2)
            
            # Máscara para NaNs
            valido = ~np.isnan(ndvi)
            
            resultados.append({
                'fecha': pd.to_datetime(str_fecha, format='%Y%m%d'),
                'anio': anio,
                'ndvi_mean': np.nanmean(ndvi),
                'ndvi_std': np.nanstd(ndvi),
                'ndbi_mean': np.nanmean(ndbi),
                'ndbi_std': np.nanstd(ndbi),
                'pct_veg': 100 * np.sum((ndvi > 0.3) & valido) / np.sum(valido),
                'pct_urb': 100 * np.sum((ndbi > 0.0) & valido) / np.sum(valido)
            })
            
    if not resultados:
        print("No se encontraron datos temporales.")
        return

    df = pd.DataFrame(resultados)
    df = df.sort_values('fecha')
    
    # Gráficos
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # NDVI
    axes[0,0].errorbar(df['fecha'], df['ndvi_mean'], yerr=df['ndvi_std'], fmt='-o', capsize=5)
    axes[0,0].set_title('Evolución NDVI Medio')
    axes[0,0].grid(True)
    
    # NDBI
    axes[0,1].errorbar(df['fecha'], df['ndbi_mean'], yerr=df['ndbi_std'], fmt='-s', color='orange', capsize=5)
    axes[0,1].set_title('Evolución NDBI Medio')
    axes[0,1].grid(True)
    
    # Cobertura Veg
    axes[1,0].bar(df['fecha'], df['pct_veg'], width=20, color='green', alpha=0.6)
    axes[1,0].set_title('% Cobertura Vegetación (>0.3 NDVI)')
    
    # Cobertura Urbana
    axes[1,1].bar(df['fecha'], df['pct_urb'], width=20, color='grey', alpha=0.6)
    axes[1,1].set_title('% Cobertura Urbana (>0 NDBI)')
    
    plt.tight_layout()
    plot_salida = DIR_SALIDA_FIGURAS / 'evolucion_temporal.png'
    plt.savefig(plot_salida)
    print(f"  Gráfico temporal guardado en {plot_salida}")
    
    # Guardar CSV temporal
    df.to_csv(DIR_SALIDA_DATOS / 'evolucion_temporal.csv', index=False)


def main():
    analizar_cambios_zonales()
    analizar_evolucion_temporal()

if __name__ == "__main__":
    main()
