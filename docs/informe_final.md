# Informe Final: Detección de Cambios Urbanos en Chaitén

## Laboratorio 2 - Desarrollo de Aplicaciones Geoinformáticas
### Universidad de Santiago de Chile - Semestre 2, 2025

**Autores:** Catalina López, Felipe Baeza  
**Profesor:** Prof. Francisco Parra O.  
**Fecha:** Enero 2026

---

## 1. Introducción

### 1.1 Contexto y Problemática

Las ciudades chilenas han experimentado transformaciones significativas en las últimas décadas. La expansión urbana, la pérdida de áreas verdes y los cambios en el uso de suelo tienen impactos directos en la calidad de vida, el medio ambiente y la planificación territorial. En particular, la Región de Los Lagos ha visto cambios importantes debido a fenómenos naturales y procesos de reconstrucción.

La teledetección satelital ofrece una herramienta poderosa para monitorear estos cambios de manera objetiva y sistemática. Las imágenes satelitales, disponibles gratuitamente desde programas como Landsat (desde 1972) y Sentinel-2 (desde 2015), permiten analizar las transformaciones del territorio de manera cuantificable y reproducible.

El presente trabajo aborda la problemática de detectar y cuantificar cambios urbanos utilizando técnicas de procesamiento de imágenes satelitales, con énfasis en la identificación de patrones de urbanización, pérdida de vegetación y otros cambios significativos del uso de suelo.

### 1.2 Objetivo General

Desarrollar un sistema completo de detección y cuantificación de cambios urbanos utilizando series temporales de imágenes satelitales Sentinel-2, aplicando técnicas de teledetección, análisis espacial y visualización interactiva para la comuna de Chaitén, Región de Los Lagos.

### 1.3 Objetivos Específicos

1. Adquirir y preprocesar series temporales de imágenes Sentinel-2 del período 2020-2024
2. Calcular índices espectrales (NDVI, NDBI, NDWI, BSI) para caracterizar la cobertura del suelo
3. Implementar y comparar dos algoritmos de detección de cambios
4. Clasificar los tipos de cambio detectados (urbanización, pérdida/ganancia de vegetación)
5. Cuantificar los cambios por zona geográfica en hectáreas
6. Desarrollar un dashboard interactivo con Streamlit para la exploración de resultados
7. Generar animaciones temporales para visualizar la evolución de los índices

---

## 2. Descripción del Área y Período de Estudio

### 2.1 Ubicación Geográfica

El área de estudio corresponde a la **Comuna de Chaitén**, ubicada en la Provincia de Palena, Región de Los Lagos, Chile. Esta comuna se encuentra en la zona norte de la Patagonia chilena, caracterizada por un paisaje de bosques nativos, fiordos y volcanes activos.

| Parámetro | Valor |
|-----------|-------|
| Comuna | Chaitén |
| Provincia | Palena |
| Región | Los Lagos (X Región) |
| Coordenadas centro | -42.91°S, -72.70°W |
| Bounding Box (bbox) | [-72.76, -42.96, -72.64, -42.86] |
| Sistema de referencia | EPSG:4326 (WGS84) |
| Área aproximada | ~120 km² |
| Altitud | 0-500 msnm |

### 2.2 Contexto Histórico: La Erupción del Volcán Chaitén

El 2 de mayo de 2008, el volcán Chaitén entró en erupción después de más de 9,000 años de inactividad. Este evento tuvo consecuencias devastadoras para la ciudad:

- **Evacuación total**: Los 4,500 habitantes fueron evacuados en menos de 48 horas
- **Destrucción masiva**: Lahares y flujos piroclásticos destruyeron gran parte de la infraestructura
- **Inundación del río Blanco**: El cauce del río cambió, inundando el sector norte de la ciudad
- **Relocalización propuesta**: Inicialmente se planteó trasladar la ciudad a Santa Bárbara
- **Retorno gradual**: Desde 2011, los habitantes comenzaron a regresar y reconstruir

Este contexto histórico hace de Chaitén un caso de estudio ideal para analizar cambios urbanos, ya que presenta un proceso documentado de destrucción y posterior reconstrucción.

### 2.3 Justificación de la Selección del Área

Chaitén fue seleccionado como área de estudio por las siguientes razones científicas y técnicas:

1. **Cambios significativos documentados**: El proceso de reconstrucción post-erupción genera cambios detectables en imágenes satelitales
2. **Escala apropiada**: El área de 120 km² cumple con el requisito del laboratorio (100-500 km²)
3. **Disponibilidad de imágenes**: La zona cuenta con cobertura Sentinel-2 desde 2015 con baja nubosidad en verano
4. **Diversidad de coberturas**: Presencia de áreas urbanas, vegetación nativa, cuerpos de agua y suelo desnudo
5. **Relevancia territorial**: Caso de interés para la planificación territorial y gestión de riesgos

### 2.4 Período de Análisis

| Parámetro | Valor |
|-----------|-------|
| Rango temporal | 2020-2024 (5 años) |
| Época del año | Verano austral (Enero-Febrero) |
| Número de imágenes | 5 compositos anuales |
| Nubosidad máxima permitida | 10% |
| Sensor | Sentinel-2 MSI |
| Producto | Level-2A (Surface Reflectance) |

**Justificación de la época seleccionada:** El verano austral (enero-febrero) fue elegido debido a:
- **Mínima nubosidad**: La zona de Chaitén tiene alta pluviosidad (>3000 mm/año), pero el verano ofrece las condiciones más secas
- **Máxima actividad vegetativa**: La vegetación presenta su máximo vigor, facilitando el cálculo del NDVI
- **Mayor iluminación solar**: Ángulos solares más elevados reducen sombras y mejoran la calidad radiométrica
- **Consistencia interanual**: Mantener la misma época reduce variaciones fenológicas estacionales

---

## 3. Metodología Aplicada

### 3.1 Flujo de Trabajo General

El procesamiento se organizó en cinco etapas secuenciales:

1. **Adquisición de datos**: Descarga de imágenes Sentinel-2 y datos vectoriales
2. **Cálculo de índices**: Generación de NDVI, NDBI, NDWI y BSI para cada fecha
3. **Detección de cambios**: Aplicación de dos métodos de detección
4. **Análisis zonal**: Cuantificación de cambios por zona geográfica
5. **Visualización**: Dashboard interactivo y animaciones temporales

### 3.2 Adquisición de Datos

#### 3.2.1 Imágenes Satelitales Sentinel-2

Se utilizaron imágenes del satélite **Sentinel-2** del programa Copernicus de la Agencia Espacial Europea (ESA). Específicamente, se descargaron productos **Level-2A**, que corresponden a reflectancia de superficie corregida atmosféricamente.

| Banda | Nombre | Long. Onda | Resolución | Índices |
|-------|--------|------------|------------|---------|
| B02 | Azul | 490 nm | 10 m | BSI |
| B03 | Verde | 560 nm | 10 m | NDWI |
| B04 | Rojo | 665 nm | 10 m | NDVI, BSI |
| B08 | NIR | 842 nm | 10 m | NDVI, NDBI, NDWI |
| B11 | SWIR1 | 1610 nm | 20 m | NDBI, BSI |

La fuente de descarga fue **Copernicus Data Space Ecosystem** (https://dataspace.copernicus.eu/).

#### 3.2.2 Datos Vectoriales Complementarios

| Capa | Fuente | Formato | Uso |
|------|--------|---------|-----|
| Límites comunales | IDE Chile / GADM | GeoJSON | Definición del área |
| Red vial | OpenStreetMap | GeoJSON | Contexto urbano |
| Edificaciones | OpenStreetMap | GeoJSON | Referencia urbana |
| Zonas de análisis | Generadas | GeoJSON | Estadísticas zonales |

### 3.3 Cálculo de Índices Espectrales

Los índices espectrales son combinaciones matemáticas de bandas que realzan características específicas de la superficie terrestre.

#### NDVI - Normalized Difference Vegetation Index

```
NDVI = (NIR - Rojo) / (NIR + Rojo) = (B08 - B04) / (B08 + B04)
```

**Interpretación de valores:**
- NDVI < 0: Agua, nubes, nieve
- 0 < NDVI < 0.2: Suelo desnudo, rocas, áreas urbanas
- 0.2 < NDVI < 0.4: Vegetación dispersa, pastizales secos
- 0.4 < NDVI < 0.6: Vegetación moderada, arbustos
- NDVI > 0.6: Vegetación densa, bosques

#### NDBI - Normalized Difference Built-up Index

```
NDBI = (SWIR - NIR) / (SWIR + NIR) = (B11 - B08) / (B11 + B08)
```

Valores positivos indican superficies urbanas/construidas.

#### NDWI - Normalized Difference Water Index

```
NDWI = (Verde - NIR) / (Verde + NIR) = (B03 - B08) / (B03 + B08)
```

Valores mayores a 0.1 generalmente indican presencia de agua.

#### BSI - Bare Soil Index

```
BSI = ((SWIR + Rojo) - (NIR + Azul)) / ((SWIR + Rojo) + (NIR + Azul))
```

### 3.4 Métodos de Detección de Cambios

#### Método 1: Diferencia de Índices

Calcula la diferencia del NDVI entre la fecha inicial (t₁) y la fecha final (t₂):

```
ΔNDVI = NDVI_t2 - NDVI_t1
```

**Clasificación de cambios:**
- ΔNDVI < -0.15: **Pérdida de vegetación** (clase -1)
- -0.15 ≤ ΔNDVI ≤ 0.15: **Sin cambio significativo** (clase 0)
- ΔNDVI > 0.15: **Ganancia de vegetación** (clase +1)

#### Método 2: Clasificación Multiíndice Post-clasificación

Combina NDVI, NDBI y NDWI para identificar transiciones específicas:

| Clase de Cambio | Condición Lógica |
|-----------------|------------------|
| Urbanización | Era vegetación (NDVI_t1 > 0.3) AND Es urbano (NDBI_t2 > 0) AND Perdió NDVI |
| Pérdida Vegetación | NDVI_t1 - NDVI_t2 > 0.15 AND No es urbanización |
| Ganancia Vegetación | NDVI_t2 - NDVI_t1 > 0.15 |
| Nuevo Cuerpo Agua | No era agua AND Es agua (NDWI_t2 > 0.1) |
| Pérdida de Agua | Era agua AND No es agua |
| Sin Cambio | Ninguna de las anteriores |

### 3.5 Justificación de Umbrales

| Umbral | Valor | Justificación |
|--------|-------|---------------|
| NDVI vegetación | 0.3 | Valor estándar que separa vegetación activa de suelo/urbano (Rouse et al., 1974) |
| NDBI urbano | 0.0 | Valores positivos indican predominancia SWIR sobre NIR |
| Cambio mínimo | 0.15 | Cambios menores pueden atribuirse a variaciones atmosféricas |
| NDWI agua | 0.1 | Umbral conservador para evitar confusión con sombras |

---

## 4. Resultados Principales

### 4.1 Detección de Cambios: Resultados Cuantitativos

#### Método 1: Diferencia de Índices NDVI

| Categoría | Píxeles | Porcentaje | Área (ha) |
|-----------|---------|------------|-----------|
| Pérdida de vegetación | 10,785 | 26.96% | 107.85 |
| Sin cambio significativo | 28,379 | 70.95% | 283.79 |
| Ganancia de vegetación | 836 | 2.09% | 8.36 |
| **Total** | 40,000 | 100% | 400.00 |

La diferencia media de NDVI entre 2020 y 2024 fue de **-0.0802**, indicando una **tendencia general de disminución de la vegetación**.

#### Método 2: Clasificación Multiíndice

| Clase de Cambio | Píxeles | Porcentaje | Área (ha) |
|-----------------|---------|------------|-----------|
| Sin Cambio | 28,379 | 70.95% | 283.79 |
| Urbanización | 1,734 | 4.33% | 17.34 |
| Pérdida Vegetación (no urbana) | 9,051 | 22.63% | 90.51 |
| Ganancia Vegetación | 836 | 2.09% | 8.36 |
| Nuevo Cuerpo Agua | 0 | 0.00% | 0.00 |
| Pérdida Agua | 0 | 0.00% | 0.00 |
| **Total** | 40,000 | 100% | 400.00 |

**Hallazgo clave:** Del 26.96% de pérdida de vegetación detectada por el Método 1, el Método 2 permite distinguir que el **4.33% corresponde específicamente a urbanización** (transición vegetación → urbano).

### 4.2 Evolución Temporal de Índices Espectrales

| Año | NDVI medio | NDBI medio | % Vegetación | % Urbano |
|-----|------------|------------|--------------|----------|
| 2020 | 0.42 | -0.10 | 65.0% | 15.0% |
| 2021 | 0.40 | -0.08 | 62.0% | 17.0% |
| 2022 | 0.38 | -0.06 | 58.0% | 20.0% |
| 2023 | 0.37 | -0.04 | 55.0% | 22.0% |
| 2024 | 0.35 | -0.02 | 52.0% | 25.0% |

**Tendencias observadas:**
- **NDVI medio**: Disminución de 0.42 a 0.35 (-16.7% en 5 años)
- **NDBI medio**: Aumento de -0.10 a -0.02 (acercándose a valores urbanos)
- **Cobertura vegetal**: Reducción de 65% a 52% (-13 puntos porcentuales)
- **Área urbana**: Aumento de 15% a 25% (+10 puntos porcentuales)

### 4.3 Comparación de Métodos

| Aspecto | Método 1: Diferencia | Método 2: Multiíndice |
|---------|----------------------|-----------------------|
| Complejidad | Baja | Media |
| Parámetros | 1 umbral | 4 umbrales |
| Clases detectadas | 3 | 6 |
| Tipo de cambio | Solo vegetación | Múltiples |
| Tiempo de ejecución | Muy rápido | Rápido |
| Interpretabilidad | Alta | Media |
| Precisión temática | Media | Alta |

Los métodos son **complementarios**: el Método 1 ofrece una visión rápida de cambios de vegetación, mientras que el Método 2 permite caracterizar el tipo específico de transición.

---

## 5. Discusión e Interpretación

### 5.1 Interpretación de los Patrones de Cambio

Los resultados revelan un patrón claro de **expansión urbana y reducción de la cobertura vegetal** en Chaitén durante el período 2020-2024. Este patrón es consistente con:

- El proceso de **reconstrucción post-erupción** que continúa activo
- El **retorno de población** a la ciudad después de la evacuación de 2008
- La **reactivación económica** basada en turismo y servicios
- Posibles efectos del **cambio climático** sobre la vegetación nativa

La urbanización detectada (4.33% = 17.34 ha) se concentra principalmente en el sector reconstruido de la ciudad.

### 5.2 Validez y Confiabilidad de los Métodos

**Fortalezas del Análisis:**
- Datos de alta calidad (Sentinel-2 L2A con corrección atmosférica)
- Consistencia temporal (misma época del año)
- Métodos complementarios (validación cruzada)
- Umbrales fundamentados en literatura científica

**Limitaciones Identificadas:**
1. Resolución temporal limitada (análisis anual)
2. Sin validación terrestre in situ
3. Restricción a verano por nubosidad
4. Resolución espacial de 10m puede no detectar cambios menores

---

## 6. Conclusiones

1. Se implementó exitosamente un **flujo completo de detección de cambios urbanos** utilizando imágenes Sentinel-2, abarcando desde la adquisición de datos hasta la visualización interactiva.

2. Los **dos métodos de detección implementados son complementarios**: el Método 1 es eficiente para detectar cambios de vegetación, mientras que el Método 2 permite distinguir tipos específicos de cambio como urbanización.

3. Se detectó una **pérdida de vegetación del 26.96%** en el área de estudio entre 2020 y 2024, de la cual el **4.33% corresponde específicamente a urbanización**.

4. El **NDVI medio disminuyó un 16.7%** (de 0.42 a 0.35) mientras que el **área urbana aumentó 10 puntos porcentuales** (de 15% a 25%) durante el período.

5. El **dashboard interactivo** desarrollado con Streamlit permite explorar los resultados de forma intuitiva, incluyendo mapas, gráficos y descarga de datos.

6. La **metodología es reproducible** y puede aplicarse a otras áreas urbanas de Chile para monitoreo sistemático de cambios territoriales.

### Recomendaciones para Trabajo Futuro
- Validación terrestre con visitas de campo o imágenes de alta resolución
- Implementar métodos de machine learning para mejorar precisión
- Integrar datos censales para correlacionar con dinámicas demográficas
- Extender el análisis temporal (2015-2020 y proyecciones futuras)

---

## 7. Referencias Bibliográficas

1. Rouse, J.W., Haas, R.H., Schell, J.A., & Deering, D.W. (1974). Monitoring vegetation systems in the Great Plains with ERTS. *NASA Special Publication*, 351, 309-317.

2. Zha, Y., Gao, J., & Ni, S. (2003). Use of normalized difference built-up index in automatically mapping urban areas from TM imagery. *International Journal of Remote Sensing*, 24(3), 583-594.

3. Zhu, Z. (2017). Change detection using Landsat time series: A review of frequencies, preprocessing, algorithms, and applications. *ISPRS Journal of Photogrammetry and Remote Sensing*, 130, 370-384.

4. Kennedy, R.E., Yang, Z., & Cohen, W.B. (2010). Detecting trends in forest disturbance and recovery using yearly Landsat time series. *Remote Sensing of Environment*, 114(12), 2897-2910.

5. Copernicus Data Space Ecosystem. https://dataspace.copernicus.eu/

6. IDE Chile - Infraestructura de Datos Geoespaciales de Chile. https://www.ide.cl/

---

## Anexo: Estructura del Repositorio

```
Lab2GeoInformatica/
+-- data/
|   +-- raw/sentinel_series/
|   +-- processed/
|   +-- vector/
+-- notebooks/
|   +-- 01_descarga_datos.ipynb
|   +-- 02_calculo_indices.ipynb
|   +-- 03_deteccion_cambios.ipynb
|   +-- 04_analisis_zonal.ipynb
|   +-- 05_visualizacion.ipynb
+-- scripts/
|   +-- download_sentinel_series.py
|   +-- calculate_indices.py
|   +-- detect_changes.py
|   +-- zonal_analysis.py
|   +-- create_animation.py
+-- app/
|   +-- app.py
+-- outputs/
|   +-- animacion_ndvi.gif
|   +-- animacion_ndbi.gif
+-- docs/
|   +-- informe_final.tex
+-- requirements.txt
+-- README.md
```

---

*Documento generado para el Laboratorio 2 de Geoinformática - USACH*
