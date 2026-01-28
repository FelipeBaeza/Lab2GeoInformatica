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
│   │   ├── estadisticas_cambio.csv     # Estadísticas por zona
│   │   └── evolucion_temporal.csv      # Series temporales de índices
│   └── vector/         # GeoJSON de zonas de análisis
├── scripts/
│   ├── download_sentinel_series.py # Descarga de Copernicus
│   ├── calculate_indices.py        # Cálculo de NDVI, NDBI, NDWI, BSI
│   ├── detect_changes.py           # Detección de cambios (2 métodos)
│   └── zonal_analysis.py           # Estadísticas zonales y temporales
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

4.  **Análisis Zonal y Temporal**:
    Calcula estadísticas de cambio por zona y genera series de tiempo de la evolución de índices.
    ```bash
    python scripts/zonal_analysis.py
    ```
    Esto genera `estadisticas_cambio.csv` y `evolucion_temporal.csv`.

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

## Notebooks

El directorio `notebooks/` contiene documentación interactiva del flujo de trabajo:

1. `01_descarga_datos.ipynb` - Adquisición de imágenes
2. `02_calculo_indices.ipynb` - Cálculo de índices espectrales
3. `03_deteccion_cambios.ipynb` - Métodos de detección
4. `04_analisis_zonal.ipynb` - Estadísticas por zona
5. `05_visualizacion.ipynb` - Dashboard y visualización

## Animación Temporal (GIF)

Para generar una animación GIF de la evolución temporal:

```bash
python scripts/create_animation.py
```

Esto genera `outputs/animacion_ndvi.gif` y `outputs/animacion_ndbi.gif`.

## Deploy en la Nube (Streamlit Cloud)

Para desplegar el dashboard en Streamlit Cloud:

1. Subir el repositorio a GitHub
2. Ir a [share.streamlit.io](https://share.streamlit.io/)
3. Conectar con GitHub y seleccionar este repositorio
4. Configurar:
   - **Main file path**: `app/app.py`
   - **Python version**: 3.10

El archivo `.streamlit/config.toml` ya está configurado para el deploy.

## Documentación

- `docs/informe_final.md` - Informe final del proyecto
- `outputs/interpretacion_resultados.md` - Interpretación detallada de resultados
- `data/processed/comparacion_metodos.md` - Comparación de métodos de detección

## Autores
Catalina López
Felipe Baeza

