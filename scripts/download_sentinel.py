import ee
import geemap
import os

# Initialize Earth Engine with geemap (handles auth and project better)
try:
    geemap.ee_initialize()
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    print("Trying to authenticate...")
    #ee.Authenticate() # geemap.ee_initialize usually handles this or asks
    # If fails, we might need manual project input
    try:
        ee.Authenticate(auth_mode='notebook')
        geemap.ee_initialize()
    except Exception as e2:
         print(f"Failed to auth: {e2}")
         exit(1)

# Define Chaitén study area (approximate urban and peri-urban area)
# [West, South, East, North]
chaiten_bbox = [-72.76, -42.96, -72.64, -42.86]
area = ee.Geometry.Rectangle(chaiten_bbox)

# Function to mask clouds
def mask_clouds_s2(image):
    qa = image.select('QA60')
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(
        qa.bitwiseAnd(1 << 11).eq(0))
    return image.updateMask(cloud_mask)

# Years to analyze (Summer: Jan-Feb)
years = [2018, 2020, 2022, 2024]

output_dir = 'data/raw'
os.makedirs(output_dir, exist_ok=True)

print(f"Downloading Sentinel-2 images for Chaitén area: {chaiten_bbox}")

for year in years:
    start_date = f'{year}-01-01'
    end_date = f'{year}-02-28'
    
    # Filter collection
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(area)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) # Increased slightly to ensure coverage
                  .map(mask_clouds_s2))
    
    # Create median composite
    composite = collection.median().clip(area)
    
    # Select bands (Blue, Green, Red, NIR, SWIR1, SWIR2)
    # B2, B3, B4, B8, B11, B12
    bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
    composite_export = composite.select(bands)
    
    output_path = os.path.join(output_dir, f'sentinel2_{year}.tif')
    
    if os.path.exists(output_path):
        print(f"File {output_path} already exists. Skipping.")
        continue

    print(f"Exporting {year} composite to {output_path}...")
    
    # Download directly using geemap (easier than Export.toDrive for local)
    try:
        geemap.ee_export_image(
            composite_export,
            filename=output_path,
            scale=10,
            region=area,
            file_per_band=False
        )
        print(f"Successfully downloaded {year}")
    except Exception as e:
        print(f"Error downloading {year}: {e}")

print("Data acquisition complete.")
