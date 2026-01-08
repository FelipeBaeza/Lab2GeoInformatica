# Laboratorio 2: Detección de Cambios Urbanos - Chaitén

Este proyecto implementa un flujo de trabajo para detectar, cuantificar y visualizar cambios urbanos en la comuna de Chaitén utilizando imágenes satelitales Sentinel-2.

## Estructura del Proyecto

```
/
├── data/
│   ├── raw/            # Imágenes Sentinel-2 descargadas (TIF)
│   ├── processed/      # Índices espectrales y cambios clasificados
│   └── vector/         # Shapefiles/GeoJSON de zonas (manzanas, etc.)
├── scripts/
│   ├── download_sentinel.py  # Descarga de GEE
│   ├── calculate_indices.py  # Cálculo de NDVI, NDBI, etc.
│   ├── detect_changes.py     # Detección de cambios (Diferencia y Clasificación)
│   └── zonal_analysis.py     # Estadísticas por zona
├── app/
│   └── app.py                # Dashboard Streamlit
├── requirements.txt
└── README.md
```

## Instrucciones de Instalación

1.  Crear entorno virtual (opcional pero recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Flujo de Ejecución

Debes ejecutar los scripts en el siguiente orden:

1.  **Adquisición de Datos**:
    Descarga las imágenes de Sentinel-2 para los veranos de 2018, 2020, 2022 y 2024.
    ```bash
    python scripts/download_sentinel.py
    ```
    *Nota: Requiere autenticación de Google Earth Engine. Sigue las instrucciones en consola si se solicita.*

2.  **Procesamiento de Índices**:
    Calcula NDVI, NDBI, NDWI y BSI para cada imagen descargada.
    ```bash
    python scripts/calculate_indices.py
    ```

3.  **Detección de Cambios**:
    Genera mapas de cambio entre la primera y última fecha.
    ```bash
    python scripts/detect_changes.py
    ```

4.  **Análisis Zonal**:
    Calcula estadísticas de cambio por zona (a falta de shapefile real, genera uno de prueba).
    ```bash
    python scripts/zonal_analysis.py
    ```

5.  **Visualización (Dashboard)**:
    Inicia la aplicación web para explorar los resultados.
    ```bash
    streamlit run app/app.py
    ```

## Metodología

-   **Área de Estudio**: Chaitén urbano (bbox aproximado).
-   **Métodos**:
    -   Diferencia de NDVI para cambios de vegetación.
    -   Clasificación multispectral para urbanización (NDVI + NDBI).
-   **Validación**: Visual a través del dashboard comparando imágenes RGB/NDVI.

## Autores
Catalina López
Felipe Baeza
