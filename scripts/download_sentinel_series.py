"""
==============================================================================
Script de Descarga de Series Temporales Sentinel-2 para Chaitén, Chile
Usando Copernicus Data Space Ecosystem
==============================================================================

Descripción:
    Este script descarga imágenes satelitales Sentinel-2 Level 2A (Surface 
    Reflectance) para la comuna de Chaitén, Región de Los Lagos, Chile.
    
    Se descargan imágenes del período 2020-2025, con mínimo 1 y máximo 3 
    imágenes por año durante la temporada de verano (enero-febrero) para
    minimizar la cobertura de nubes.

Área de Estudio:
    Comuna de Chaitén, Chile
    Coordenadas aproximadas: [-72.76, -42.96, -72.64, -42.86] (EPSG:4326)
    
Sensor:
    Sentinel-2 MSI (MultiSpectral Instrument)
    Producto: S2MSI2A (Level-2A Surface Reflectance)
    Resolución espacial: 10m (bandas visibles y NIR)

Justificación de fechas seleccionadas:
    - Período: Verano austral (enero-febrero)
    - Razón: Menor probabilidad de nubosidad y mejor iluminación solar
    - La zona de Chaitén tiene alta pluviosidad, por lo que el verano
      ofrece las mejores condiciones atmosféricas para imágenes ópticas
    - Se priorizan imágenes con <10% de nubosidad

Requisitos:
    - Cuenta GRATUITA en Copernicus Data Space
    - Registro en: https://dataspace.copernicus.eu/
    - Biblioteca: requests (incluida con Python)
    
    IMPORTANTE: Copernicus Data Space es 100% GRATUITO.
    Solo necesitas registrarte con un email.

Autor: Script generado para Lab2 Geoinformática
Fecha: Enero 2026
==============================================================================
"""

import os
import sys
import json
import time
import requests
import zipfile
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Credenciales de Copernicus Data Space
# Opción 1: Variables de entorno (recomendado)
# Opción 2: Editar directamente aquí
COPERNICUS_USER = os.environ.get('COPERNICUS_USER', '')
COPERNICUS_PASSWORD = os.environ.get('COPERNICUS_PASSWORD', '')

# Área de estudio: Comuna de Chaitén, Región de Los Lagos, Chile
# Bounding box: [Oeste, Sur, Este, Norte] en coordenadas WGS84
CHAITEN_BBOX = [-72.76, -42.96, -72.64, -42.86]

# Años a analizar (rango de 5 años: 2020-2025)
YEARS = [2020, 2021, 2022, 2023, 2024]

# Período de cada año (verano austral - menor nubosidad)
# Justificación: Enero-Febrero son los meses más secos en la zona
START_MONTH_DAY = '01-01'  # 1 de enero
END_MONTH_DAY = '02-28'    # 28 de febrero

# Umbral máximo de nubosidad (%)
MAX_CLOUD_COVER = 10

# Máximo de imágenes por año
MAX_IMAGES_PER_YEAR = 3

# Directorio de salida
OUTPUT_DIR = Path('data/raw/sentinel_series')

# ==============================================================================
# ENDPOINTS DE LA API
# ==============================================================================

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"

# ==============================================================================
# FUNCIONES
# ==============================================================================

def print_registration_instructions():
    """
    Muestra instrucciones para registrarse en Copernicus Data Space.
    """
    print("\n" + "="*70)
    print("INSTRUCCIONES PARA REGISTRARSE EN COPERNICUS DATA SPACE")
    print("="*70)
    print("""
1. Ve a: https://dataspace.copernicus.eu/

2. Haz clic en "REGISTER" (esquina superior derecha)

3. Completa el formulario con:
   - Email
   - Contraseña
   - Nombre y apellido

4. Confirma tu email (revisa bandeja de spam)

5. Una vez registrado, configura las credenciales:

   OPCIÓN A - Variables de entorno (Windows PowerShell):
   
   $env:COPERNICUS_USER = "tu_email@ejemplo.com"
   $env:COPERNICUS_PASSWORD = "tu_contraseña"
   python scripts/download_sentinel_series.py

   OPCIÓN B - Editar el script directamente:
   
   Abre scripts/download_sentinel_series.py y modifica:
   COPERNICUS_USER = 'tu_email@ejemplo.com'
   COPERNICUS_PASSWORD = 'tu_contraseña'

IMPORTANTE: El registro es 100% GRATUITO.
    No se requiere tarjeta de crédito ni pago alguno.
""")
    print("="*70 + "\n")


def get_access_token(username, password):
    """
    Obtiene token de acceso OAuth2 desde Copernicus.
    
    Args:
        username: Email de usuario
        password: Contraseña
        
    Returns:
        str: Token de acceso
    """
    print("Obteniendo token de acceso...")
    
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    
    try:
        response = requests.post(TOKEN_URL, data=data, timeout=30)
        response.raise_for_status()
        token = response.json()["access_token"]
        print("Token obtenido correctamente")
        return token
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("Error de autenticación: Email o contraseña incorrectos")
        else:
            print(f"Error HTTP: {e}")
        return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None


def search_products(bbox, start_date, end_date, cloud_cover=10):
    """
    Busca productos Sentinel-2 L2A en el catálogo de Copernicus.
    
    Args:
        bbox: Lista [west, south, east, north]
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        cloud_cover: Máximo porcentaje de nubosidad
        
    Returns:
        list: Lista de productos encontrados
    """
    west, south, east, north = bbox
    footprint = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
    
    # Query OData para Sentinel-2 Level 2A
    filter_query = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and "
        f"ContentDate/Start ge {start_date}T00:00:00.000Z and "
        f"ContentDate/Start le {end_date}T23:59:59.999Z and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {cloud_cover})"
    )
    
    params = {
        "$filter": filter_query,
        "$orderby": "ContentDate/Start asc",
        "$top": 10,
    }
    
    try:
        response = requests.get(CATALOGUE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("value", [])
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return []


def extract_metadata(product, year, image_num):
    """
    Extrae metadatos de un producto Sentinel-2.
    
    Args:
        product: Diccionario con información del producto
        year: Año de la imagen
        image_num: Número de imagen en el año
        
    Returns:
        dict: Metadatos estructurados
    """
    # Extraer atributos del producto
    attributes = {}
    for attr in product.get('Attributes', []):
        if 'Name' in attr:
            name = attr['Name']
            # El valor puede estar en diferentes campos según el tipo
            value = attr.get('Value', attr.get('OData.CSC.StringAttribute', {}).get('Value', 'N/A'))
            attributes[name] = value
    
    # Extraer fecha de adquisición
    content_date = product.get('ContentDate', {})
    acquisition_date = content_date.get('Start', 'N/A')
    
    return {
        'id': product.get('Id', 'N/A'),
        'nombre_producto': product.get('Name', 'N/A'),
        'año': year,
        'numero_imagen': image_num,
        'fecha_adquisicion': acquisition_date[:19] if acquisition_date != 'N/A' else 'N/A',
        'nubosidad_porcentaje': attributes.get('cloudCover', 'N/A'),
        'sensor': 'Sentinel-2 MSI',
        'producto': 'S2MSI2A (Level-2A Surface Reflectance)',
        'plataforma': attributes.get('platformSerialIdentifier', 'Sentinel-2'),
        'tile_mgrs': attributes.get('tileId', 'N/A'),
        'orbita': attributes.get('orbitNumber', 'N/A'),
        'sistema_referencia': 'EPSG:4326 (WGS84)',
        'resolucion_m': 10,
        'tamaño_mb': round(product.get('ContentLength', 0) / (1024*1024), 2)
    }


def create_session_with_retries():
    """
    Crea una sesión de requests con política de reintentos.
    
    Returns:
        requests.Session: Sesión configurada con reintentos automáticos
    """
    session = requests.Session()
    
    # Configurar política de reintentos
    retry_strategy = Retry(
        total=5,  # Número máximo de reintentos
        backoff_factor=2,  # Factor de backoff exponencial (2, 4, 8, 16 segundos)
        status_forcelist=[429, 500, 502, 503, 504],  # Códigos HTTP para reintentar
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # Métodos permitidos para reintento
        raise_on_status=False
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session


def verify_zip_integrity(filepath, expected_size=None):
    """
    Verifica que un archivo ZIP sea válido y esté completo.
    
    Args:
        filepath: Ruta al archivo ZIP
        expected_size: Tamaño esperado en bytes (opcional)
        
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    try:
        # Verificar que el archivo existe y tiene contenido
        if not filepath.exists():
            return False, "Archivo no existe"
        
        actual_size = filepath.stat().st_size
        if actual_size == 0:
            return False, "Archivo vacío"
        
        # Verificar tamaño si se proporciona
        if expected_size and actual_size < expected_size * 0.95:  # 5% tolerancia
            return False, f"Tamaño incompleto: {actual_size} vs {expected_size} esperado"
        
        # Verificar que es un ZIP válido
        if not zipfile.is_zipfile(filepath):
            return False, "No es un archivo ZIP válido"
        
        # Verificar integridad del contenido
        with zipfile.ZipFile(filepath, 'r') as z:
            bad_file = z.testzip()
            if bad_file:
                return False, f"Archivo corrupto dentro del ZIP: {bad_file}"
        
        return True, "ZIP válido y completo"
        
    except zipfile.BadZipFile:
        return False, "Archivo ZIP dañado (BadZipFile)"
    except Exception as e:
        return False, f"Error verificando ZIP: {e}"


def download_product(product_id, product_name, access_token, output_dir, max_retries=5):
    """
    Descarga un producto Sentinel-2 con reintentos y manejo robusto de errores.
    
    Args:
        product_id: ID del producto
        product_name: Nombre del producto
        access_token: Token de acceso OAuth2
        output_dir: Directorio de salida
        max_retries: Número máximo de reintentos (default: 5)
        
    Returns:
        Path: Ruta del archivo descargado o None si falla
    """
    url = f"{DOWNLOAD_URL}({product_id})/$value"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Nombre simplificado para el archivo
    output_path = output_dir / f"{product_name}.zip"
    temp_path = output_dir / f"{product_name}.zip.partial"
    
    if output_path.exists():
        print(f"  Ya existe: {output_path.name}")
        return output_path
    
    print(f"Descargando {product_name[:50]}...")
    
    # Crear sesión con reintentos
    session = create_session_with_retries()
    
    for attempt in range(1, max_retries + 1):
        try:
            # Verificar si hay descarga parcial para continuar
            downloaded = 0
            if temp_path.exists():
                downloaded = temp_path.stat().st_size
                headers["Range"] = f"bytes={downloaded}-"
                print(f"  Continuando descarga parcial desde byte {downloaded}...")
            
            response = session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=(30, 300)  # (connect timeout, read timeout)
            )
            
            # Si el servidor no soporta rangos, empezar de nuevo
            if response.status_code == 200 and downloaded > 0:
                downloaded = 0
                if temp_path.exists():
                    temp_path.unlink()
            
            response.raise_for_status()
            
            # Obtener tamaño total
            if response.status_code == 206:  # Partial Content
                content_range = response.headers.get('content-range', '')
                if '/' in content_range:
                    total_size = int(content_range.split('/')[-1])
                else:
                    total_size = downloaded + int(response.headers.get('content-length', 0))
            else:
                total_size = int(response.headers.get('content-length', 0))
            
            # Descargar con progreso
            mode = 'ab' if downloaded > 0 else 'wb'
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=32768):  # Chunk más grande
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgreso: {progress:.1f}% ({downloaded/(1024*1024):.1f} MB)", end='', flush=True)
            
            # Verificar integridad del ZIP antes de renombrar
            print(f"\n  Verificando integridad del archivo...")
            is_valid, message = verify_zip_integrity(temp_path, total_size)
            
            if is_valid:
                # Renombrar archivo temporal al final
                temp_path.rename(output_path)
                print(f"  {message}")
                print(f"Guardado: {output_path.name}")
                
                # Pausa después de descarga exitosa para no saturar el servidor
                print("  Esperando 3 segundos antes de la siguiente descarga...")
                time.sleep(3)
                
                return output_path
            else:
                print(f"  ERROR: {message}")
                print(f"  Eliminando archivo corrupto y reintentando...")
                temp_path.unlink()
                # Continuar al siguiente intento
                continue
            
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.Timeout,
                ConnectionResetError) as e:
            
            wait_time = min(5 * (2 ** (attempt - 1)), 60)  # Backoff: 5, 10, 20, 40, 60 segundos
            print(f"\n  Error de conexión (intento {attempt}/{max_retries}): {type(e).__name__}")
            
            if attempt < max_retries:
                print(f"  Esperando {wait_time} segundos antes de reintentar...")
                time.sleep(wait_time)
            else:
                print(f"  Máximo de reintentos alcanzado.")
                if temp_path.exists():
                    print(f"  Archivo parcial guardado: {temp_path.name}")
                    print(f"  Puedes reiniciar el script para continuar la descarga.")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"\nError HTTP: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return None
            
        except Exception as e:
            print(f"\nError inesperado: {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait_time = min(5 * (2 ** (attempt - 1)), 60)
                print(f"  Esperando {wait_time} segundos antes de reintentar...")
                time.sleep(wait_time)
            else:
                if temp_path.exists():
                    temp_path.unlink()
                return None
    
    return None


def save_metadata(metadata_list, output_path):
    """
    Guarda los metadatos en un archivo JSON.
    
    Args:
        metadata_list: Lista de diccionarios con metadatos
        output_path: Ruta del archivo de salida
    """
    output_data = {
        'descripcion': 'Metadatos de imágenes Sentinel-2 para Chaitén, Chile',
        'area_estudio': {
            'nombre': 'Comuna de Chaitén',
            'region': 'Región de Los Lagos',
            'pais': 'Chile',
            'bbox': CHAITEN_BBOX,
            'sistema_coordenadas': 'EPSG:4326 (WGS84)'
        },
        'parametros_descarga': {
            'periodo': f'{YEARS[0]}-{YEARS[-1]}',
            'meses': 'Enero-Febrero (verano austral)',
            'max_nubosidad': f'{MAX_CLOUD_COVER}%',
            'max_imagenes_por_año': MAX_IMAGES_PER_YEAR,
            'fuente': 'Copernicus Data Space Ecosystem'
        },
        'justificacion_fechas': (
            'Se seleccionó el período de verano austral (enero-febrero) porque: '
            '1) Menor probabilidad de cobertura nubosa en la zona de Chaitén, '
            '2) Mayor cantidad de horas de luz solar disponibles, '
            '3) Mejor ángulo de elevación solar para imágenes ópticas, '
            '4) Condiciones atmosféricas más estables en la Patagonia norte.'
        ),
        'fecha_generacion': datetime.now().isoformat(),
        'imagenes': metadata_list
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nMetadatos guardados en: {output_path}")


def search_available_images():
    """
    Busca imágenes disponibles sin necesidad de autenticación.
    Útil para ver qué hay disponible antes de registrarse.
    """
    print("\n" + "="*70)
    print("BÚSQUEDA DE IMÁGENES DISPONIBLES (sin autenticación)")
    print("="*70)
    
    all_products = []
    
    for year in YEARS:
        start_date = f'{year}-{START_MONTH_DAY}'
        end_date = f'{year}-{END_MONTH_DAY}'
        
        print(f"\nAño {year} ({start_date} a {end_date}):")
        
        products = search_products(CHAITEN_BBOX, start_date, end_date, MAX_CLOUD_COVER)
        
        if not products:
            # Intentar con umbral más alto
            products = search_products(CHAITEN_BBOX, start_date, end_date, 15)
            if products:
                print(f"   (usando nubosidad <15% por falta de imágenes más limpias)")
        
        if products:
            print(f"   Encontradas: {len(products)} imágenes")
            for i, p in enumerate(products[:MAX_IMAGES_PER_YEAR]):
                name = p.get('Name', 'N/A')
                date = p.get('ContentDate', {}).get('Start', 'N/A')[:10]
                
                # Buscar nubosidad en atributos
                cloud = 'N/A'
                for attr in p.get('Attributes', []):
                    if attr.get('Name') == 'cloudCover':
                        cloud = attr.get('Value', 'N/A')
                        break
                
                print(f"   {i+1}. Fecha: {date}, Nubosidad: {cloud}%")
                print(f"      ID: {p.get('Id', 'N/A')[:20]}...")
                
                all_products.append({
                    'year': year,
                    'name': name,
                    'date': date,
                    'cloud_cover': cloud,
                    'id': p.get('Id')
                })
        else:
            print(f"No se encontraron imágenes")
    
    # Guardar resumen de productos disponibles
    if all_products:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        summary_path = OUTPUT_DIR / 'productos_disponibles.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"\nResumen guardado en: {summary_path}")
    
    return all_products


def main():
    """
    Función principal del script.
    """
    print("="*70)
    print("DESCARGA DE SERIES TEMPORALES SENTINEL-2 - CHAITÉN, CHILE")
    print("    Usando Copernicus Data Space Ecosystem (GRATUITO)")
    print("="*70)
    print(f"\nÁrea de estudio: {CHAITEN_BBOX}")
    print(f"Período: {YEARS[0]} - {YEARS[-1]}")
    print(f"Máxima nubosidad: {MAX_CLOUD_COVER}%")
    print(f"Imágenes por año: 1-{MAX_IMAGES_PER_YEAR}")
    
    # Verificar credenciales
    if not COPERNICUS_USER or not COPERNICUS_PASSWORD:
        print_registration_instructions()
        
        # Aún así, buscar productos disponibles
        print("\nBuscando imágenes disponibles (sin descargar)...")
        search_available_images()
        
        print("\n" + "="*70)
        print("PRÓXIMOS PASOS:")
        print("="*70)
        print("1. Regístrate en https://dataspace.copernicus.eu/ (GRATIS)")
        print("2. Configura tus credenciales como se indica arriba")
        print("3. Vuelve a ejecutar este script para descargar las imágenes")
        print("="*70 + "\n")
        return
    
    # Obtener token de acceso
    token = get_access_token(COPERNICUS_USER, COPERNICUS_PASSWORD)
    if not token:
        print("\nNo se pudo obtener token de acceso. Verifica tus credenciales.")
        return
    
    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Lista para almacenar metadatos
    metadata_list = []
    downloaded_files = []
    
    print("\n" + "-"*70)
    print("DESCARGANDO IMÁGENES")
    print("-"*70)
    
    for year in YEARS:
        start_date = f'{year}-{START_MONTH_DAY}'
        end_date = f'{year}-{END_MONTH_DAY}'
        
        print(f"\n{'='*50}")
        print(f"Procesando año {year}")
        print(f"   Período: {start_date} a {end_date}")
        print(f"{'='*50}")
        
        # Buscar productos
        products = search_products(CHAITEN_BBOX, start_date, end_date, MAX_CLOUD_COVER)
        
        if not products:
            # Intentar con umbral más alto
            print(f"   Buscando con nubosidad <15%...")
            products = search_products(CHAITEN_BBOX, start_date, end_date, 15)
        
        if not products:
            print(f"No se encontraron imágenes para {year}")
            continue
        
        print(f"   Encontradas: {len(products)} imágenes")
        
        # Descargar hasta MAX_IMAGES_PER_YEAR
        for i, product in enumerate(products[:MAX_IMAGES_PER_YEAR]):
            product_id = product['Id']
            product_name = product['Name']
            
            # Extraer metadatos
            meta = extract_metadata(product, year, i+1)
            metadata_list.append(meta)
            
            print(f"\n   Imagen {i+1}/{min(len(products), MAX_IMAGES_PER_YEAR)}:")
            print(f"   Fecha: {meta['fecha_adquisicion']}")
            print(f"   Nubosidad: {meta['nubosidad_porcentaje']}%")
            print(f"   Tamaño: {meta['tamaño_mb']} MB")
            
            # Descargar
            output_file = download_product(product_id, product_name, token, OUTPUT_DIR)
            if output_file:
                downloaded_files.append(output_file)
    
    # Guardar metadatos
    if metadata_list:
        save_metadata(metadata_list, OUTPUT_DIR / 'metadata_imagenes.json')
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN DE DESCARGA")
    print("="*70)
    print(f"\nImágenes descargadas: {len(downloaded_files)}")
    print(f"Años cubiertos: {len(set(m['año'] for m in metadata_list))}")
    print(f"Directorio: {OUTPUT_DIR.absolute()}")
    
    if downloaded_files:
        print("\nArchivos descargados:")
        for f in downloaded_files:
            print(f"   - {f.name}")
    
    print("\n" + "="*70)
    print("DESCARGA COMPLETADA")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
