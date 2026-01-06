import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import rasterio
import numpy as np
from pathlib import Path
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monitor de Cambio Urbano - Chaitén", layout="wide")

st.title("🛡️ Monitor de Cambio Urbano: Chaitén")
st.markdown("""
Esta aplicación visualiza los cambios urbanos detectados en la comuna de Chaitén utilizando imágenes satelitales Sentinel-2.
""")

# --- Sidebar ---
st.sidebar.header("Configuración")

data_path = Path('data')
processed_path = data_path / 'processed'
vector_path = data_path / 'vector'

# 1. Select Dates
# Dynamically find available years
indices_files = sorted(processed_path.glob('indices_*.tif'))
years = [f.stem.split('_')[1] for f in indices_files]

if not years:
    st.error("No se encontraron datos procesados. Por favor ejecuta los scripts de procesamiento primero.")
    st.stop()

st.sidebar.subheader("Selección Temporal")
fecha_inicio = st.sidebar.selectbox("Fecha Inicial (Base)", years, index=0)
fecha_fin = st.sidebar.selectbox("Fecha Final (Comparación)", years, index=len(years)-1 if years else 0)

if fecha_inicio == fecha_fin:
    st.sidebar.warning("Selecciona fechas diferentes para ver cambios.")

st.sidebar.markdown("---")

# --- Load Data ---
@st.cache_data
def load_stats():
    csv_path = processed_path / 'estadisticas_cambio.csv'
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None

@st.cache_data
def load_zones():
    # Try finding the geojson or shapefile
    # Prioritizing the test grid if created or real file
    possible_files = list(vector_path.glob('*.geojson')) + list(vector_path.glob('*.shp'))
    if possible_files:
        return gpd.read_file(possible_files[0])
    return None

stats_df = load_stats()
zones_gdf = load_zones()

# --- Main Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Mapa de Cambios")
    
    if zones_gdf is not None and stats_df is not None:
        # Join stats to geometry
        # Ensure ID columns match (using 'zona' from stats and 'zona_id' or index from gdf)
        # In script we used 'zona_id' for grid test
        
        # Simple merge attempt
        if 'zona' in stats_df.columns:
             # Check which column in zones_gdf matches
             if 'zona_id' in zones_gdf.columns:
                 zones_mapped = zones_gdf.merge(stats_df, left_on='zona_id', right_on='zona')
             else:
                 # Assume index
                 zones_mapped = zones_gdf.copy()
                 zones_mapped['zona_idx'] = zones_mapped.index
                 # This is fragile without knowing exact column, but works for the generated grid
                 zones_mapped = zones_mapped.merge(stats_df, left_on='zona_idx', right_on='zona', how='left') # Fallback
        else:
            zones_mapped = zones_gdf

        # Reproject to 4326 for Folium
        zones_mapped = zones_mapped.to_crs(epsg=4326)
        
        centro_lat = zones_mapped.geometry.centroid.y.mean()
        centro_lon = zones_mapped.geometry.centroid.x.mean()
        
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14)
        
        # Choropleth or Style function
        folium.GeoJson(
            zones_mapped,
            style_function=lambda x: {
                'fillColor': 'red' if x['properties'].get('urbanizacion_ha', 0) > 0.1 else 'green',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['zona', 'urbanizacion_ha'] if 'urbanizacion_ha' in zones_mapped.columns else ['zona_id'],
                aliases=['Zona:', 'Urb. (ha):'] if 'urbanizacion_ha' in zones_mapped.columns else ['ID:']
            )
        ).add_to(m)
        
        st_folium(m, width=700, height=500)
    else:
        st.info("Mapa no disponible. Faltan datos vectoriales o estadísticas.")

with col2:
    st.subheader("Estadísticas Globales")
    
    if stats_df is not None:
        total_urb = stats_df['urbanizacion_ha'].sum()
        total_lost_veg = stats_df['perdida_veg_ha'].sum()
        
        st.metric("Nueva Urbanización", f"{total_urb:.2f} ha", delta=None)
        st.metric("Pérdida de Vegetación", f"{total_lost_veg:.2f} ha", delta_color="inverse")
        
        st.subheader("Top Zonas con Cambios")
        top_urb = stats_df.nlargest(5, 'urbanizacion_ha')
        st.dataframe(top_urb[['zona', 'urbanizacion_ha', 'perdida_veg_ha']])
        
        fig = px.bar(top_urb, x='zona', y='urbanizacion_ha', title="Top 5 Urbanización por Zona")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No hay estadísticas calculadas.")

st.markdown("---")
st.subheader("Comparación Visual (NDVI)")

c1, c2 = st.columns(2)

def get_ndvi_image(year):
    path = processed_path / f'indices_{year}.tif'
    if path.exists():
        with rasterio.open(path) as src:
            ndvi = src.read(1)
            # Normalize for display 0-255
            # NDVI is -1 to 1. 
            # We want to map -0.2 to 0.8 mostly.
            ndvi_norm = np.clip((ndvi + 0.2) / 1.0, 0, 1) # simple scaling
            # Create colormap? For now just grayscale or basic
            return ndvi_norm
    return None

with c1:
    st.markdown(f"**{fecha_inicio}**")
    img1 = get_ndvi_image(fecha_inicio)
    if img1 is not None:
        st.image(img1, clamp=True, channels='GRAY', caption=f"NDVI {fecha_inicio}")
        
with c2:
    st.markdown(f"**{fecha_fin}**")
    img2 = get_ndvi_image(fecha_fin)
    if img2 is not None:
        st.image(img2, clamp=True, channels='GRAY', caption=f"NDVI {fecha_fin}")

st.markdown("---")
st.info("Nota: Ejecuta los scripts de procesamiento en `scripts/` para actualizar los datos.")
