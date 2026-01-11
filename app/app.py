import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from pathlib import Path

# Configuración de página
st.set_page_config(page_title="Monitor de Cambios Urbanos - Chaitén", layout="wide")

# Rutas de datos
RUTA_VECTOR = Path('data/vector/zonas_analisis.geojson')
RUTA_ESTADISTICAS = Path('data/processed/estadisticas_cambio.csv')
RUTA_TEMPORAL = Path('data/processed/evolucion_temporal.csv')

def cargar_datos():
    try:
        zonas = gpd.read_file(RUTA_VECTOR)
        stats = pd.read_csv(RUTA_ESTADISTICAS)
        stats_temporal = pd.read_csv(RUTA_TEMPORAL)
        return zonas, stats, stats_temporal
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None, None, None

def main():
    st.title("Monitor de Cambios Urbanos: Chaitén")
    st.markdown("Análisis de cambios territoriales basado en imágenes Sentinel-2 (2020-2024).")
    
    zonas, stats, stats_temporal = cargar_datos()
    
    if zonas is None:
        return

    # Unir geometrías con estadísticas para el mapa
    # Asumimos que 'zona' en stats corresponde a una columna en zonas
    # Si zonas tiene 'id', usamos ese.
    col_zi = 'id' if 'id' in zonas.columns else zonas.columns[0]
    stats['zona'] = stats['zona'].astype(str)
    zonas[col_zi] = zonas[col_zi].astype(str)
    
    zonas_stats = zonas.merge(stats, left_on=col_zi, right_on='zona', how='left')

    # Métricas Globales
    st.header("Resumen General")
    col1, col2, col3 = st.columns(3)
    
    total_urb = stats['urbanizacion_ha'].sum() if 'urbanizacion_ha' in stats.columns else 0
    total_perd_veg = stats['perdida_veg_ha'].sum() if 'perdida_veg_ha' in stats.columns else 0
    total_gan_veg = stats['ganancia_veg_ha'].sum() if 'ganancia_veg_ha' in stats.columns else 0
    
    col1.metric("Urbanización Total (ha)", f"{total_urb:.2f}")
    col2.metric("Pérdida Vegetación (ha)", f"{total_perd_veg:.2f}")
    col3.metric("Ganancia Vegetación (ha)", f"{total_gan_veg:.2f}")

    # Visualización Principal
    st.header("Mapa de Cambios por Zona")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Mapa Folium
        centroid = [zonas.geometry.centroid.y.mean(), zonas.geometry.centroid.x.mean()]
        m = folium.Map(location=centroid, zoom_start=14)
        
        # Capa Cloropleta: Intensidad de Urbanización
        folium.Choropleth(
            geo_data=zonas_stats,
            name='Urbanización',
            data=stats,
            columns=['zona', 'urbanizacion_ha'],
            key_on=f'feature.properties.{col_zi}',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Urbanización (ha)'
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=500)
        
    with c2:
        st.subheader("Top Zonas con Urbanización")
        if 'urbanizacion_ha' in stats.columns:
            top_urb = stats.nlargest(10, 'urbanizacion_ha')
            st.dataframe(top_urb[['zona', 'urbanizacion_ha']].set_index('zona'))
        else:
            st.write("No hay datos de urbanización disponibles.")

    # Evolución Temporal
    st.header("Evolución Temporal")
    
    if stats_temporal is not None:
        tab1, tab2 = st.tabs(["Índices Espectrales", "Cobertura de Suelo"])
        
        with tab1:
            fig_idx = px.line(stats_temporal, x='fecha', y=['ndvi_mean', 'ndbi_mean'],
                              labels={'value': 'Valor Índice', 'fecha': 'Fecha', 'variable': 'Índice'},
                              title='Evolución Promedio NDVI vs NDBI')
            st.plotly_chart(fig_idx, use_container_width=True)
            
        with tab2:
            fig_cob = px.bar(stats_temporal, x='fecha', y=['pct_veg', 'pct_urb'],
                             labels={'value': 'Porcentaje (%)', 'fecha': 'Fecha', 'variable': 'Tipo'},
                             title='Cobertura Estimada del Suelo',
                             barmode='group')
            st.plotly_chart(fig_cob, use_container_width=True)
            
    st.markdown("---")
    st.caption("Laboratorio de Geoinformática - Detección de Cambios Urbanos")

if __name__ == "__main__":
    main()
