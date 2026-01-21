"""
==============================================================================
Script de Detección de Cambios - Laboratorio 2 Geoinformática
Implementa DOS métodos de detección de cambios según la guía del laboratorio:

  MÉTODO 1: Diferencia de Índices (Sección 3.3.1)
    - Resta simple de NDVI entre dos fechas
    - Clasifica en: pérdida (-1), sin cambio (0), ganancia (+1)
    - Ventajas: Simple, rápido, fácil de interpretar
    - Desventajas: Solo detecta cambios de vegetación, sensible a umbrales

  MÉTODO 2: Clasificación Multiíndice de Cambio Urbano (Sección 3.3.2)
    - Combina NDVI, NDBI y NDWI para clasificar tipos de cambio
    - Clases: Urbanización, Pérdida/Ganancia Vegetación, Cambios de Agua
    - Ventajas: Distingue tipos de cambio, más información
    - Desventajas: Más parámetros, requiere calibración

JUSTIFICACIÓN DE UMBRALES:
    - ndvi_veg = 0.3: Valor típico para vegetación moderada/densa
    - ndbi_urbano = 0.0: Valores positivos indican superficies construidas
    - cambio_min = 0.15: Umbral para cambios significativos (±15% de cambio)
    - umbral_ndwi = 0.1: Valores > 0.1 indican presencia de agua

==============================================================================
"""

import numpy as np
import rasterio
import pandas as pd
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
INPUT_DIR = Path('data/processed')
OUTPUT_DIR = Path('data/processed')
OUTPUT_FIGURES = Path('outputs/figures')
OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

# Umbrales para detección de cambios
# JUSTIFICACIÓN:
# - ndvi_veg (0.3): Umbral estándar para separar vegetación de suelo desnudo
#   Valores NDVI > 0.3 generalmente indican vegetación activa
# - ndbi_urbano (0.0): NDBI positivo indica superficies impermeables/construidas
# - cambio_min (0.15): Cambios menores al 15% pueden ser ruido atmosférico/estacional
UMBRALES = {
    'ndvi_veg': 0.3,
    'ndbi_urbano': 0.0,
    'cambio_min': 0.15,
    'umbral_ndwi': 0.1
}

# ==============================================================================
# MÉTODO 1: DIFERENCIA DE ÍNDICES (Guía 3.3.1)
# ==============================================================================
def metodo_diferencia_indices(ruta_t1, ruta_t2, umbral=0.15):
    """
    Detecta cambios usando diferencia de NDVI.
    
    Este método es el más simple y directo. Calcula la diferencia
    NDVI_t2 - NDVI_t1 y clasifica según umbrales.
    
    Args:
        ruta_t1: Ruta al archivo de índices fecha inicial
        ruta_t2: Ruta al archivo de índices fecha final
        umbral: Umbral de cambio significativo (default: 0.15)
        
    Returns:
        cambio: array con valores -1 (pérdida), 0 (sin cambio), 1 (ganancia)
        diferencia: array con valores continuos de diferencia
        estadisticas: diccionario con estadísticas del análisis
    """
    print("\n" + "="*60)
    print("MÉTODO 1: Diferencia de Índices (NDVI)")
    print("="*60)
    
    with rasterio.open(ruta_t1) as src1:
        ndvi_t1 = src1.read(1)  # Banda 1 = NDVI
        perfil = src1.profile
        
    with rasterio.open(ruta_t2) as src2:
        ndvi_t2 = src2.read(1)
    
    # Calcular diferencia
    diferencia = ndvi_t2 - ndvi_t1
    
    # Máscara de datos válidos
    valido = ~np.isnan(diferencia)
    
    # Clasificar cambios
    cambio = np.zeros_like(diferencia, dtype=np.int8)
    cambio[diferencia < -umbral] = -1  # Pérdida de vegetación
    cambio[diferencia > umbral] = 1    # Ganancia de vegetación
    
    # Aplicar máscara
    cambio[~valido] = 0
    
    # Estadísticas
    total_pixeles = np.sum(valido)
    perdida = np.sum(cambio == -1)
    ganancia = np.sum(cambio == 1)
    sin_cambio = np.sum(cambio == 0) - np.sum(~valido)
    
    estadisticas = {
        'metodo': 'Diferencia de Índices',
        'total_pixeles': int(total_pixeles),
        'perdida_pixeles': int(perdida),
        'ganancia_pixeles': int(ganancia),
        'sin_cambio_pixeles': int(sin_cambio),
        'perdida_pct': 100 * perdida / total_pixeles if total_pixeles > 0 else 0,
        'ganancia_pct': 100 * ganancia / total_pixeles if total_pixeles > 0 else 0,
        'diferencia_media': float(np.nanmean(diferencia)),
        'diferencia_std': float(np.nanstd(diferencia))
    }
    
    print(f"  Umbral utilizado: ±{umbral}")
    print(f"  Píxeles con pérdida: {perdida:,} ({estadisticas['perdida_pct']:.2f}%)")
    print(f"  Píxeles con ganancia: {ganancia:,} ({estadisticas['ganancia_pct']:.2f}%)")
    print(f"  Sin cambio significativo: {sin_cambio:,}")
    print(f"  Diferencia media NDVI: {estadisticas['diferencia_media']:.4f}")
    
    return cambio, diferencia, estadisticas, perfil


# ==============================================================================
# MÉTODO 2: CLASIFICACIÓN MULTIÍNDICE DE CAMBIO URBANO (Guía 3.3.2)
# ==============================================================================
def metodo_clasificacion_urbano(ruta_t1, ruta_t2, umbrales=None):
    """
    Clasifica el tipo de cambio urbano usando múltiples índices.
    
    Combina NDVI, NDBI y NDWI para identificar diferentes tipos de cambio:
    - Urbanización (vegetación -> construido)
    - Pérdida de vegetación (otro tipo)
    - Ganancia de vegetación
    - Cambios en cuerpos de agua
    
    Args:
        ruta_t1: Ruta al archivo de índices fecha inicial
        ruta_t2: Ruta al archivo de índices fecha final
        umbrales: Diccionario con umbrales (usa defaults si None)
        
    Returns:
        clase: array con clasificación (0-5)
        estadisticas: diccionario con estadísticas del análisis
    """
    print("\n" + "="*60)
    print("MÉTODO 2: Clasificación Multiíndice de Cambio Urbano")
    print("="*60)
    
    if umbrales is None:
        umbrales = UMBRALES
    
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

    # Inicializar clasificación
    # 0: Sin Cambio
    # 1: Urbanización (Vegetación/Suelo -> Construido)
    # 2: Pérdida de Vegetación (no urbanización)
    # 3: Ganancia de Vegetación
    # 4: Nuevo Cuerpo de Agua
    # 5: Pérdida de Agua
    
    clase = np.zeros_like(ndvi_t1, dtype=np.uint8)
    
    # Máscara para datos válidos
    mascara_valida = ~np.isnan(ndvi_t1) & ~np.isnan(ndvi_t2)
    
    # 1. URBANIZACIÓN: Era vegetación -> Es urbano con caída de NDVI
    era_vegetacion = ndvi_t1 > umbrales['ndvi_veg']
    es_urbano = ndbi_t2 > umbrales['ndbi_urbano']
    caida_ndvi = (ndvi_t1 - ndvi_t2) > umbrales['cambio_min']
    mascara_urb = era_vegetacion & es_urbano & caida_ndvi
    clase[mascara_urb & mascara_valida] = 1
    
    # 2. PÉRDIDA DE VEGETACIÓN (otro)
    perdio_veg = caida_ndvi
    clase[perdio_veg & (clase == 0) & mascara_valida] = 2
    
    # 3. GANANCIA DE VEGETACIÓN
    gano_veg = (ndvi_t2 - ndvi_t1) > umbrales['cambio_min']
    clase[gano_veg & (clase == 0) & mascara_valida] = 3
    
    # 4. NUEVO CUERPO DE AGUA
    era_no_agua = ndwi_t1 < 0
    es_agua = ndwi_t2 > umbrales['umbral_ndwi']
    clase[era_no_agua & es_agua & (clase == 0) & mascara_valida] = 4
    
    # 5. PÉRDIDA DE AGUA
    era_agua = ndwi_t1 > umbrales['umbral_ndwi']
    no_es_agua = ndwi_t2 < 0
    clase[era_agua & no_es_agua & (clase == 0) & mascara_valida] = 5
    
    # Estadísticas
    total_pixeles = np.sum(mascara_valida)
    
    nombres_clase = {
        0: 'Sin Cambio',
        1: 'Urbanización',
        2: 'Pérdida Vegetación',
        3: 'Ganancia Vegetación',
        4: 'Nuevo Cuerpo Agua',
        5: 'Pérdida Agua'
    }
    
    estadisticas = {
        'metodo': 'Clasificación Multiíndice',
        'total_pixeles': int(total_pixeles),
        'clases': {}
    }
    
    print(f"  Umbrales utilizados:")
    print(f"    - NDVI vegetación: {umbrales['ndvi_veg']}")
    print(f"    - NDBI urbano: {umbrales['ndbi_urbano']}")
    print(f"    - Cambio mínimo: {umbrales['cambio_min']}")
    print(f"\n  Resultados por clase:")
    
    for i, nombre in nombres_clase.items():
        count = np.sum(clase == i)
        pct = 100 * count / total_pixeles if total_pixeles > 0 else 0
        estadisticas['clases'][nombre] = {
            'pixeles': int(count),
            'porcentaje': pct
        }
        if i > 0:  # No mostrar "sin cambio" como clase principal
            print(f"    - {nombre}: {count:,} píxeles ({pct:.2f}%)")
    
    return clase, estadisticas, perfil


# ==============================================================================
# GUARDAR RESULTADOS
# ==============================================================================
def guardar_raster_cambio_diferencia(cambio, perfil, ruta_salida):
    """Guarda el resultado del método de diferencia."""
    perfil.update(
        dtype=rasterio.int8,
        count=1,
        nodata=0
    )
    
    with rasterio.open(ruta_salida, 'w', **perfil) as dst:
        dst.write(cambio, 1)
        dst.write_colormap(1, {
            -1: (255, 100, 100, 255),  # Pérdida (Rojo claro)
            0: (200, 200, 200, 128),   # Sin cambio (Gris transparente)
            1: (100, 255, 100, 255)    # Ganancia (Verde claro)
        })
    print(f"  Guardado: {ruta_salida}")


def guardar_raster_cambio_clasificado(clase, perfil, ruta_salida):
    """Guarda el resultado del método de clasificación."""
    perfil.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )
    
    with rasterio.open(ruta_salida, 'w', **perfil) as dst:
        dst.write(clase, 1)
        dst.write_colormap(1, {
            0: (0, 0, 0, 0),         # Transparente
            1: (255, 0, 0, 255),     # Urbanización (Rojo)
            2: (255, 165, 0, 255),   # Pérdida Veg (Naranja)
            3: (0, 255, 0, 255),     # Ganancia Veg (Verde)
            4: (0, 0, 255, 255),     # Nuevo Agua (Azul)
            5: (0, 255, 255, 255)    # Pérdida Agua (Cian)
        })
    print(f"  Guardado: {ruta_salida}")


def guardar_comparacion_metodos(stats_m1, stats_m2, ruta_salida):
    """Genera un archivo de comparación de métodos."""
    
    contenido = """# Comparación de Métodos de Detección de Cambios
## Laboratorio 2: Detección de Cambios Urbanos - Chaitén

---

## Método 1: Diferencia de Índices (NDVI)

### Descripción
Calcula la diferencia simple de NDVI entre dos fechas y clasifica los píxeles según umbrales.

### Fórmula
```
Diferencia = NDVI_t2 - NDVI_t1

Si Diferencia < -umbral → Pérdida de vegetación
Si Diferencia > +umbral → Ganancia de vegetación
Si |Diferencia| ≤ umbral → Sin cambio significativo
```

### Resultados
- Píxeles con pérdida: {m1_perdida:,} ({m1_perdida_pct:.2f}%)
- Píxeles con ganancia: {m1_ganancia:,} ({m1_ganancia_pct:.2f}%)
- Diferencia media NDVI: {m1_diff_media:.4f} ± {m1_diff_std:.4f}

### Ventajas
- ✅ Simple y rápido de implementar
- ✅ Fácil de interpretar
- ✅ Pocos parámetros a calibrar
- ✅ Robusto para detectar cambios de vegetación

### Desventajas
- ❌ Solo detecta cambios en vegetación
- ❌ No distingue tipos de cambio (urbanización vs otros)
- ❌ Sensible a variaciones estacionales
- ❌ No utiliza información de otros índices

---

## Método 2: Clasificación Multiíndice de Cambio Urbano

### Descripción
Combina NDVI, NDBI y NDWI para clasificar diferentes tipos de cambio usando reglas basadas en umbrales múltiples.

### Reglas de Clasificación
```
1. Urbanización: 
   Era vegetación (NDVI_t1 > 0.3) Y Es urbano (NDBI_t2 > 0) Y Cayó NDVI
   
2. Pérdida de vegetación: 
   NDVI_t1 - NDVI_t2 > umbral (no clasificado como urbanización)
   
3. Ganancia de vegetación: 
   NDVI_t2 - NDVI_t1 > umbral
   
4. Nuevo cuerpo de agua: 
   No era agua (NDWI_t1 < 0) Y Es agua (NDWI_t2 > 0.1)
   
5. Pérdida de agua: 
   Era agua (NDWI_t1 > 0.1) Y No es agua (NDWI_t2 < 0)
```

### Resultados
{m2_resultados}

### Ventajas
- ✅ Distingue múltiples tipos de cambio
- ✅ Identifica específicamente urbanización
- ✅ Utiliza información espectral complementaria
- ✅ Mejor caracterización del tipo de transición

### Desventajas
- ❌ Más complejo de implementar
- ❌ Requiere calibración de múltiples umbrales
- ❌ Orden de reglas afecta clasificación
- ❌ Puede haber confusión entre clases

---

## Comparación Cuantitativa

| Aspecto | Método 1 (Diferencia) | Método 2 (Multiíndice) |
|---------|----------------------|------------------------|
| Complejidad | Baja | Media |
| Parámetros | 1 (umbral) | 4 (umbrales) |
| Clases detectadas | 3 | 6 |
| Tipo de cambio | Solo vegetación | Múltiples |
| Velocidad | Muy rápida | Rápida |
| Interpretabilidad | Alta | Media |

---

## Justificación de Umbrales

### Umbral de cambio mínimo (0.15)
- Cambios de NDVI menores a 0.15 pueden deberse a:
  - Variaciones atmosféricas entre fechas
  - Diferencias fenológicas estacionales menores
  - Ruido del sensor
- El valor 0.15 (~15% de cambio) es un umbral conservador que reduce falsos positivos

### Umbral de vegetación NDVI (0.3)
- Valores típicos de NDVI:
  - Agua/Superficies construidas: -0.1 a 0.1
  - Suelo desnudo: 0.1 a 0.2
  - Vegetación dispersa: 0.2 a 0.4
  - Vegetación densa: 0.4 a 0.9
- El umbral 0.3 separa vegetación activa de suelo/urbano

### Umbral de área urbana NDBI (0.0)
- NDBI positivo indica mayor reflectancia SWIR que NIR
- Típico de superficies impermeables (techos, asfalto, hormigón)
- Valores negativos indican vegetación o agua

### Umbral de agua NDWI (0.1)
- NDWI > 0.1 indica alta probabilidad de presencia de agua
- Valores más conservadores reducen confusión con sombras

---

## Recomendaciones

1. **Para análisis rápido**: Usar Método 1 (Diferencia de Índices)
2. **Para caracterización detallada**: Usar Método 2 (Clasificación Multiíndice)
3. **Para validación**: Comparar resultados de ambos métodos
4. **Para zonas urbanas específicas**: El Método 2 es preferible

---

## Archivos Generados

- `cambio_diferencia_ndvi.tif`: Resultado Método 1 (-1, 0, +1)
- `cambio_clasificado.tif`: Resultado Método 2 (0-5 clases)
- `comparacion_metodos.md`: Este archivo

---

*Generado automáticamente por detect_changes.py*
"""
    
    # Formatear resultados método 2
    m2_resultados = ""
    for nombre, datos in stats_m2['clases'].items():
        if nombre != 'Sin Cambio':
            m2_resultados += f"- {nombre}: {datos['pixeles']:,} ({datos['porcentaje']:.2f}%)\n"
    
    contenido_formateado = contenido.format(
        m1_perdida=stats_m1['perdida_pixeles'],
        m1_perdida_pct=stats_m1['perdida_pct'],
        m1_ganancia=stats_m1['ganancia_pixeles'],
        m1_ganancia_pct=stats_m1['ganancia_pct'],
        m1_diff_media=stats_m1['diferencia_media'],
        m1_diff_std=stats_m1['diferencia_std'],
        m2_resultados=m2_resultados
    )
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(contenido_formateado)
    
    print(f"  Comparación guardada: {ruta_salida}")


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================
def main():
    print("\n" + "="*70)
    print("DETECCIÓN DE CAMBIOS - LABORATORIO 2 GEOINFORMÁTICA")
    print("Implementación de 2 métodos según guía del laboratorio")
    print("="*70)
    
    # Encontrar archivos procesados
    archivos = sorted(list(INPUT_DIR.glob('indices_*.tif')))
    
    if len(archivos) < 2:
        print("ERROR: Se necesitan al menos 2 imágenes procesadas.")
        return
    
    t1 = archivos[0]   # Más antigua
    t2 = archivos[-1]  # Más reciente
    
    print(f"\nFecha inicial (T1): {t1.name}")
    print(f"Fecha final (T2): {t2.name}")
    
    # ==== MÉTODO 1: Diferencia de Índices ====
    cambio_m1, diferencia, stats_m1, perfil1 = metodo_diferencia_indices(
        t1, t2, umbral=UMBRALES['cambio_min']
    )
    
    ruta_salida_m1 = OUTPUT_DIR / 'cambio_diferencia_ndvi.tif'
    guardar_raster_cambio_diferencia(cambio_m1, perfil1, ruta_salida_m1)
    
    # ==== MÉTODO 2: Clasificación Multiíndice ====
    clase_m2, stats_m2, perfil2 = metodo_clasificacion_urbano(
        t1, t2, umbrales=UMBRALES
    )
    
    ruta_salida_m2 = OUTPUT_DIR / 'cambio_clasificado.tif'
    guardar_raster_cambio_clasificado(clase_m2, perfil2, ruta_salida_m2)
    
    # ==== GUARDAR COMPARACIÓN ====
    print("\n" + "="*60)
    print("GENERANDO DOCUMENTACIÓN DE COMPARACIÓN")
    print("="*60)
    
    ruta_comparacion = OUTPUT_DIR / 'comparacion_metodos.md'
    guardar_comparacion_metodos(stats_m1, stats_m2, ruta_comparacion)
    
    # ==== RESUMEN FINAL ====
    print("\n" + "="*70)
    print("RESUMEN DE ARCHIVOS GENERADOS")
    print("="*70)
    print(f"  1. {ruta_salida_m1} (Método 1: Diferencia NDVI)")
    print(f"  2. {ruta_salida_m2} (Método 2: Clasificación Multiíndice)")
    print(f"  3. {ruta_comparacion} (Comparación de métodos)")
    print("\n¡Detección de cambios completada!")


if __name__ == "__main__":
    main()
