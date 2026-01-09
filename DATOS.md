# Gestión de Datos Satelitales (Almacenamiento Externo)

Debido al tamaño de las imágenes satelitales (~12 GB en total), los archivos **ZIP** no se almacenan en este repositorio. En su lugar, utilizamos un servicio de almacenamiento externo (Google Drive) para alojar los datos crudos.

Este repositorio contiene:
1. Scripts de descarga y procesamiento (`scripts/`)
2. Metadatos de las imágenes (`data/raw/sentinel_series/*.json`)
3. Archivos vectoriales de la zona de estudio (`data/vector/`)

## Acceso a los Datos

**[https://drive.google.com/drive/u/1/folders/1HvHf0ji-kvhaiA1DFp3KNw1lto0NZduM]**

> **Nota para el usuario:** Debes subir los archivos de tu carpeta local `data/raw/sentinel_series/` a tu nube personal y pegar el enlace arriba para que otros puedan acceder.

### Estructura de carpetas requerida
Si descargas los datos desde el enlace externo, asegúrate de colocarlos en la siguiente estructura local para que los scripts funcionen:

```
PROYECTO/
├── data/
│   └── raw/
│       └── sentinel_series/
│           ├── S2A_MSIL2A_2020...SAFE.zip
│           ├── S2B_MSIL2A_2021...SAFE.zip
│           └── ... (resto de archivos ZIP)
```

## Reproducir la descarga (Alternativa)
Si no tienes acceso al Drive, puedes volver a descargar los datos originales usando el script incluido:

1. **Registrarse** en [Copernicus Data Space](https://dataspace.copernicus.eu/) (Gratis)
2. **Ejecutar**:
   ```powershell
   # Configurar credenciales primero
   $env:COPERNICUS_USER = "tu_email"
   $env:COPERNICUS_PASSWORD = "tu_pw"
   
   python scripts/download_sentinel_series.py
   ```
