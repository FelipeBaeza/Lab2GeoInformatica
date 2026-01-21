# Laboratorio 2: Detección de Cambios Urbanos - Chaitén

Este proyecto implementa un flujo de trabajo para detectar, cuantificar y visualizar cambios urbanos en la comuna de Chaitén utilizando imágenes satelitales Sentinel-2.

## Estructura del Proyecto

```
/
├── data/
│   ├── raw/            # Imágenes Sentinel-2 (Ver DATOS.md)
│   ├── processed/      # Índices espectrales y cambios clasificados
│   │   ├── cambio_clasificado.tif      # Método 2: Clasificación Multiíndice
│   │   ├── cambio_diferencia_ndvi.tif  # Método 1: Diferencia de Índices
│   │   ├── comparacion_metodos.md      # Documentación de métodos
│   │   └── estadisticas_cambio.csv     # Estadísticas por zona
│   └── vector/         # GeoJSON de zonas de análisis
├── scripts/
│   ├── download_sentinel_series.py # Descarga de Copernicus
│   ├── calculate_indices.py        # Cálculo de NDVI, NDBI, NDWI, BSI
│   ├── detect_changes.py           # Detección de cambios (2 métodos)
│   └── zonal_analysis.py           # Estadísticas por zona
├── app/
│   └── app.py                      # Dashboard Streamlit interactivo
├── outputs/
│   ├── figures/                    # Gráficos generados
│   └── interpretacion_resultados.md # Análisis e interpretación
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
    > **IMPORTANTE**: Los archivos de imágenes (~12 GB) no se incluyen en el repositorio. Ver instrucciones en [DATOS.md](DATOS.md).
    
    Para descargar nuevas imágenes (requiere cuenta Copernicus):
    ```bash
    python scripts/download_sentinel_series.py
    ```

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
    python -m streamlit run app/app.py
    ```
    El dashboard se abrirá en http://localhost:8501

## Metodología

-   **Área de Estudio**: Chaitén urbano (bbox: -72.76, -42.96, -72.64, -42.86).
-   **Período**: 2020-2024 (14 imágenes Sentinel-2, verano austral).
-   **Métodos de Detección de Cambios** (ver [comparacion_metodos.md](data/processed/comparacion_metodos.md)):
    1.  **Diferencia de Índices (NDVI)**: Resta simple entre fechas, clasifica pérdida/ganancia de vegetación.
    2.  **Clasificación Multiíndice**: Combina NDVI, NDBI y NDWI para distinguir urbanización, cambios de vegetación y agua.
-   **Umbrales**: NDVI vegetación=0.3, NDBI urbano=0.0, cambio mínimo=0.15.
-   **Validación**: Visual a través del dashboard comparando mapas de cambio.

## Autores
Catalina López
Felipe Baeza
