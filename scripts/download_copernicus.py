"""
Script para descargar imágenes Sentinel-2 desde Copernicus Data Space Ecosystem.
Opción B del laboratorio - Descarga directa.

Requiere cuenta en: https://dataspace.copernicus.eu/
"""
import os
import requests
import json
from datetime import datetime
from pathlib import Path

# --- CONFIGURACIÓN ---
# Credenciales de Copernicus Data Space (el usuario debe registrarse)
# Puedes setear estas variables de entorno o editarlas aquí
COPERNICUS_USER = os.environ.get('COPERNICUS_USER', '')
COPERNICUS_PASSWORD = os.environ.get('COPERNICUS_PASSWORD', '')

# Área de estudio: Chaitén urbano
# [West, South, East, North]
CHAITEN_BBOX = [-72.76, -42.96, -72.64, -42.86]

# Fechas de interés (verano de cada año)
DATES = [
    ('2018-01-01', '2018-02-28'),
    ('2020-01-01', '2020-02-28'),
    ('2022-01-01', '2022-02-28'),
    ('2024-01-01', '2024-02-28'),
]

OUTPUT_DIR = Path('data/raw')

# --- API Endpoints ---
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"


def get_access_token(username, password):
    """Obtiene token de acceso OAuth2."""
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def search_products(bbox, start_date, end_date, cloud_cover=20):
    """Busca productos Sentinel-2 L2A en el catálogo."""
    # Formato WKT para el bbox
    west, south, east, north = bbox
    footprint = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
    
    # Query OData
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
    
    response = requests.get(CATALOGUE_URL, params=params)
    response.raise_for_status()
    return response.json().get("value", [])


def download_product(product_id, product_name, access_token, output_dir):
    """Descarga un producto."""
    url = f"{DOWNLOAD_URL}({product_id})/$value"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    output_path = output_dir / f"{product_name}.zip"
    if output_path.exists():
        print(f"  Ya existe: {output_path}")
        return output_path
    
    print(f"  Descargando {product_name}...")
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"  Guardado: {output_path}")
    return output_path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not COPERNICUS_USER or not COPERNICUS_PASSWORD:
        print("=" * 60)
        print("INSTRUCCIONES PARA DESCARGAR IMÁGENES SENTINEL-2:")
        print("=" * 60)
        print()
        print("1. Regístrate en: https://dataspace.copernicus.eu/")
        print("2. Configura tus credenciales como variables de entorno:")
        print()
        print("   export COPERNICUS_USER='tu_email'")
        print("   export COPERNICUS_PASSWORD='tu_password'")
        print()
        print("3. Vuelve a ejecutar este script.")
        print()
        print("ALTERNATIVA MANUAL:")
        print("-" * 40)
        print("1. Ve a: https://browser.dataspace.copernicus.eu/")
        print("2. Dibuja un rectángulo sobre Chaitén")
        print(f"   Coordenadas: {CHAITEN_BBOX}")
        print("3. Filtra por:")
        print("   - Sentinel-2 MSI")
        print("   - Producto: S2MSI2A (L2A)")
        print("   - Nubosidad: < 20%")
        print("4. Descarga imágenes de: 2018, 2020, 2022, 2024 (verano)")
        print("5. Coloca los .zip en: data/raw/")
        print()
        
        # Generar archivo de metadatos con las búsquedas
        print("Buscando productos disponibles (sin autenticación)...")
        metadata = []
        for start, end in DATES:
            year = start[:4]
            print(f"\nBuscando imágenes para {year}...")
            try:
                products = search_products(CHAITEN_BBOX, start, end)
                print(f"  Encontrados: {len(products)} productos")
                for p in products[:3]:  # Mostrar top 3
                    print(f"    - {p['Name']}")
                    print(f"      Fecha: {p['ContentDate']['Start']}")
                    print(f"      ID: {p['Id']}")
                    metadata.append({
                        'year': year,
                        'id': p['Id'],
                        'name': p['Name'],
                        'date': p['ContentDate']['Start'],
                    })
            except Exception as e:
                print(f"  Error: {e}")
        
        # Guardar metadatos
        if metadata:
            meta_path = OUTPUT_DIR / 'sentinel2_metadata.json'
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"\nMetadatos guardados en: {meta_path}")
        
        return
    
    # Con credenciales: descargar automáticamente
    print("Obteniendo token de acceso...")
    token = get_access_token(COPERNICUS_USER, COPERNICUS_PASSWORD)
    
    for start, end in DATES:
        year = start[:4]
        print(f"\n=== Procesando {year} ===")
        
        products = search_products(CHAITEN_BBOX, start, end)
        if not products:
            print(f"  No se encontraron imágenes para {year}")
            continue
        
        # Descargar el primer producto (menor nubosidad)
        product = products[0]
        print(f"  Seleccionado: {product['Name']}")
        
        download_product(product['Id'], product['Name'], token, OUTPUT_DIR)
    
    print("\n¡Descarga completada!")


if __name__ == "__main__":
    main()
