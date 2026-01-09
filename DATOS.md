# Datos Satelitales Sentinel-2

Los archivos de imágenes Sentinel-2 (~12 GB) **no están incluidos en este repositorio** debido a su tamaño.

## Cómo obtener los datos

### Opción 1: Descargar automáticamente (recomendado)

1. **Regístrate gratis** en [Copernicus Data Space](https://dataspace.copernicus.eu/)

2. **Configura credenciales** en PowerShell:
   ```powershell
   $env:COPERNICUS_USER = "tu_email@ejemplo.com"
   $env:COPERNICUS_PASSWORD = "tu_contraseña"
   ```

3. **Ejecuta el script**:
   ```powershell
   python scripts/download_sentinel_series.py
   ```

Los archivos se guardarán en `data/raw/sentinel_series/`.

### Opción 2: Descargar manualmente

Visita [Copernicus Browser](https://browser.dataspace.copernicus.eu/) y busca imágenes Sentinel-2 L2A para:
- **Ubicación**: Chaitén, Chile (-72.76, -42.96, -72.64, -42.86)
- **Fechas**: Enero-Febrero de 2020-2024
- **Nubosidad**: < 15%

## Archivos incluidos

Aunque los ZIPs no están versionados, sí se incluyen:
- `data/raw/sentinel_series/metadata_imagenes.json` - Metadatos de las imágenes
- `data/raw/sentinel_series/productos_disponibles.json` - Lista de productos disponibles

## Estructura esperada

Después de ejecutar el script, tendrás ~15 archivos ZIP (~800 MB cada uno):
```
data/raw/sentinel_series/
├── S2A_MSIL2A_20200121...SAFE.zip
├── S2B_MSIL2A_20200116...SAFE.zip
├── ...
├── metadata_imagenes.json
└── productos_disponibles.json
```
