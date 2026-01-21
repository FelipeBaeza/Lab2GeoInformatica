"""
==============================================================================
Dashboard Interactivo de Cambios Urbanos - Chaitén
Laboratorio 2: Detección de Cambios Urbanos
Desarrollo de Aplicaciones Geoinformáticas - USACH

Características:
- Mapa interactivo con capas de cambio (Folium)
- Gráficos dinámicos con selección de fechas (Plotly)
- Comparador visual antes/después
- Descarga de resultados (CSV)
- Estadísticas por zona y temporales
==============================================================================
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(
    page_title="Monitor de Cambios Urbanos - Chaitén",
    page_icon=":material/satellite_alt:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rutas de datos
RUTA_VECTOR = Path('data/vector/zonas_analisis.geojson')
RUTA_ESTADISTICAS = Path('data/processed/estadisticas_cambio.csv')
RUTA_TEMPORAL = Path('data/processed/evolucion_temporal.csv')
RUTA_COMPARACION = Path('data/processed/comparacion_metodos.md')

# ==============================================================================
# FUNCIONES DE CARGA
# ==============================================================================
@st.cache_data
def cargar_datos():
    """Carga todos los datos necesarios para el dashboard."""
    try:
        zonas = gpd.read_file(RUTA_VECTOR)
        stats = pd.read_csv(RUTA_ESTADISTICAS)
        stats_temporal = pd.read_csv(RUTA_TEMPORAL)
        stats_temporal['fecha'] = pd.to_datetime(stats_temporal['fecha'])
        return zonas, stats, stats_temporal
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None, None, None


def cargar_comparacion_metodos():
    """Carga el archivo de comparación de métodos si existe."""
    if RUTA_COMPARACION.exists():
        with open(RUTA_COMPARACION, 'r', encoding='utf-8') as f:
            return f.read()
    return None


# ==============================================================================
# COMPONENTES DEL DASHBOARD
# ==============================================================================
def mostrar_sidebar(stats, stats_temporal):
    """Sidebar con controles y opciones de descarga."""
    st.sidebar.header("Configuración")
    
    # Selector de tipo de cambio a visualizar
    tipo_cambio = st.sidebar.multiselect(
        "Tipos de cambio a mostrar",
        ["Urbanización", "Pérdida Vegetación", "Ganancia Vegetación"],
        default=["Urbanización"]
    )
    
    # Selector de fechas para comparación
    if stats_temporal is not None and len(stats_temporal) > 1:
        fechas_disponibles = stats_temporal['fecha'].dt.strftime('%Y-%m-%d').tolist()
        
        st.sidebar.subheader("Comparación Temporal")
        fecha_inicio = st.sidebar.selectbox(
            "Fecha inicial",
            fechas_disponibles,
            index=0
        )
        fecha_fin = st.sidebar.selectbox(
            "Fecha final",
            fechas_disponibles,
            index=len(fechas_disponibles) - 1
        )
    else:
        fecha_inicio, fecha_fin = None, None
    
    # Sección de Descarga
    st.sidebar.markdown("---")
    st.sidebar.subheader("Descargar Datos")
    
    # Botón de descarga de estadísticas zonales
    if stats is not None:
        csv_stats = stats.to_csv(index=False)
        st.sidebar.download_button(
            label="Estadísticas por Zona (CSV)",
            data=csv_stats,
            file_name="estadisticas_cambio_chaiten.csv",
            mime="text/csv",
            help="Descarga las estadísticas de cambio por zona"
        )
    
    # Botón de descarga de evolución temporal
    if stats_temporal is not None:
        csv_temporal = stats_temporal.to_csv(index=False)
        st.sidebar.download_button(
            label="Evolución Temporal (CSV)",
            data=csv_temporal,
            file_name="evolucion_temporal_chaiten.csv",
            mime="text/csv",
            help="Descarga la evolución temporal de índices"
        )
    
    # Información del proyecto
    st.sidebar.markdown("---")
    st.sidebar.caption("**Laboratorio 2** - Geoinformática USACH")
    st.sidebar.caption("Autores: Catalina López, Felipe Baeza")
    
    return tipo_cambio, fecha_inicio, fecha_fin


def mostrar_metricas_globales(stats):
    """Muestra las métricas globales de cambio."""
    st.header("Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_urb = stats['urbanizacion_ha'].sum() if 'urbanizacion_ha' in stats.columns else 0
    total_perd_veg = stats['perdida_veg_ha'].sum() if 'perdida_veg_ha' in stats.columns else 0
    total_gan_veg = stats['ganancia_veg_ha'].sum() if 'ganancia_veg_ha' in stats.columns else 0
    
    # Calcular cambio neto de vegetación
    cambio_neto = total_gan_veg - total_perd_veg
    
    col1.metric(
        "Urbanización Total",
        f"{total_urb:.2f} ha",
        help="Área total convertida a uso urbano"
    )
    col2.metric(
        "Pérdida Vegetación",
        f"{total_perd_veg:.2f} ha",
        delta=f"-{total_perd_veg:.0f}",
        delta_color="inverse"
    )
    col3.metric(
        "Ganancia Vegetación",
        f"{total_gan_veg:.2f} ha",
        delta=f"+{total_gan_veg:.0f}",
        delta_color="normal"
    )
    col4.metric(
        "Cambio Neto Veg.",
        f"{cambio_neto:.2f} ha",
        delta=f"{'+' if cambio_neto > 0 else ''}{cambio_neto:.0f}",
        delta_color="normal" if cambio_neto > 0 else "inverse"
    )


def mostrar_mapa_y_tabla(zonas, stats):
    """Muestra el mapa coroplético y la tabla de zonas."""
    st.header("Mapa de Cambios por Zona")
    
    # Preparar datos
    col_zi = 'id' if 'id' in zonas.columns else zonas.columns[0]
    stats['zona'] = stats['zona'].astype(str)
    zonas[col_zi] = zonas[col_zi].astype(str)
    zonas_stats = zonas.merge(stats, left_on=col_zi, right_on='zona', how='left')
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Mapa Folium
        centroid = [zonas.geometry.centroid.y.mean(), zonas.geometry.centroid.x.mean()]
        m = folium.Map(location=centroid, zoom_start=12, tiles='CartoDB positron')
        
        # Capa Cloropleta: Intensidad de Urbanización
        folium.Choropleth(
            geo_data=zonas_stats,
            name='Urbanización',
            data=stats,
            columns=['zona', 'urbanizacion_ha'],
            key_on=f'feature.properties.{col_zi}',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name='Urbanización (ha)',
            nan_fill_color='lightgray'
        ).add_to(m)
        
        # Capa adicional: Pérdida de Vegetación
        folium.Choropleth(
            geo_data=zonas_stats,
            name='Pérdida Vegetación',
            data=stats,
            columns=['zona', 'perdida_veg_ha'],
            key_on=f'feature.properties.{col_zi}',
            fill_color='OrRd',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name='Pérdida Veg (ha)',
            show=False
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=500, returned_objects=[])
        
    with c2:
        st.subheader("Top 10 Zonas con Mayor Cambio")
        
        tab_urb, tab_perd, tab_gan = st.tabs(["Urbanización", "Pérdida Veg", "Ganancia Veg"])
        
        with tab_urb:
            if 'urbanizacion_ha' in stats.columns:
                top = stats.nlargest(10, 'urbanizacion_ha')[['zona', 'urbanizacion_ha']]
                top.columns = ['Zona', 'Hectáreas']
                st.dataframe(top.set_index('Zona'), use_container_width=True)
        
        with tab_perd:
            if 'perdida_veg_ha' in stats.columns:
                top = stats.nlargest(10, 'perdida_veg_ha')[['zona', 'perdida_veg_ha']]
                top.columns = ['Zona', 'Hectáreas']
                st.dataframe(top.set_index('Zona'), use_container_width=True)
        
        with tab_gan:
            if 'ganancia_veg_ha' in stats.columns:
                top = stats.nlargest(10, 'ganancia_veg_ha')[['zona', 'ganancia_veg_ha']]
                top.columns = ['Zona', 'Hectáreas']
                st.dataframe(top.set_index('Zona'), use_container_width=True)


def mostrar_comparacion_temporal(stats_temporal, fecha_inicio, fecha_fin):
    """Muestra la comparación de índices entre dos fechas."""
    st.header("Comparador Antes/Después")
    
    if stats_temporal is None or len(stats_temporal) < 2:
        st.warning("No hay suficientes datos temporales para comparación.")
        return
    
    # Filtrar fechas
    df = stats_temporal.copy()
    df['fecha_str'] = df['fecha'].dt.strftime('%Y-%m-%d')
    
    t1 = df[df['fecha_str'] == fecha_inicio].iloc[0] if fecha_inicio else df.iloc[0]
    t2 = df[df['fecha_str'] == fecha_fin].iloc[0] if fecha_fin else df.iloc[-1]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Fecha Inicial: {t1['fecha'].strftime('%Y-%m-%d')}")
        
        # Métricas T1
        m1, m2 = st.columns(2)
        m1.metric("NDVI Medio", f"{t1['ndvi_mean']:.4f}")
        m2.metric("NDBI Medio", f"{t1['ndbi_mean']:.4f}")
        
        m3, m4 = st.columns(2)
        m3.metric("% Vegetación", f"{t1['pct_veg']:.1f}%")
        m4.metric("% Urbano", f"{t1['pct_urb']:.1f}%")
    
    with col2:
        st.subheader(f"Fecha Final: {t2['fecha'].strftime('%Y-%m-%d')}")
        
        # Métricas T2 con deltas
        delta_ndvi = t2['ndvi_mean'] - t1['ndvi_mean']
        delta_ndbi = t2['ndbi_mean'] - t1['ndbi_mean']
        delta_veg = t2['pct_veg'] - t1['pct_veg']
        delta_urb = t2['pct_urb'] - t1['pct_urb']
        
        m1, m2 = st.columns(2)
        m1.metric("NDVI Medio", f"{t2['ndvi_mean']:.4f}", delta=f"{delta_ndvi:+.4f}")
        m2.metric("NDBI Medio", f"{t2['ndbi_mean']:.4f}", delta=f"{delta_ndbi:+.4f}")
        
        m3, m4 = st.columns(2)
        m3.metric("% Vegetación", f"{t2['pct_veg']:.1f}%", delta=f"{delta_veg:+.1f}%")
        m4.metric("% Urbano", f"{t2['pct_urb']:.1f}%", delta=f"{delta_urb:+.1f}%")
    
    # Gráfico de radar comparativo
    st.subheader("Comparación Visual")
    
    categorias = ['NDVI', 'Vegetación (%)', 'NDBI (inv)', 'Urbano (%)']
    
    # Normalizar valores para radar (0-1)
    max_vals = {
        'ndvi': max(t1['ndvi_mean'], t2['ndvi_mean'], 0.5),
        'veg': 100,
        'ndbi': max(abs(t1['ndbi_mean']), abs(t2['ndbi_mean']), 0.3),
        'urb': 100
    }
    
    valores_t1 = [
        t1['ndvi_mean'] / max_vals['ndvi'],
        t1['pct_veg'] / max_vals['veg'],
        (t1['ndbi_mean'] + max_vals['ndbi']) / (2 * max_vals['ndbi']),  # Invertir para que menor sea mejor
        t1['pct_urb'] / max_vals['urb']
    ]
    
    valores_t2 = [
        t2['ndvi_mean'] / max_vals['ndvi'],
        t2['pct_veg'] / max_vals['veg'],
        (t2['ndbi_mean'] + max_vals['ndbi']) / (2 * max_vals['ndbi']),
        t2['pct_urb'] / max_vals['urb']
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=valores_t1 + [valores_t1[0]],
        theta=categorias + [categorias[0]],
        fill='toself',
        name=f"T1: {t1['fecha'].strftime('%Y-%m-%d')}",
        line_color='blue',
        opacity=0.6
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=valores_t2 + [valores_t2[0]],
        theta=categorias + [categorias[0]],
        fill='toself',
        name=f"T2: {t2['fecha'].strftime('%Y-%m-%d')}",
        line_color='red',
        opacity=0.6
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Comparación de Indicadores (normalizado)"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def mostrar_evolucion_temporal(stats_temporal):
    """Muestra gráficos de evolución temporal."""
    st.header("Evolución Temporal")
    
    if stats_temporal is None:
        st.warning("No hay datos de evolución temporal disponibles.")
        return
    
    tab1, tab2, tab3 = st.tabs(["Índices Espectrales", "Cobertura de Suelo", "Estadísticas"])
    
    with tab1:
        fig_idx = px.line(
            stats_temporal,
            x='fecha',
            y=['ndvi_mean', 'ndbi_mean'],
            labels={'value': 'Valor Índice', 'fecha': 'Fecha', 'variable': 'Índice'},
            title='Evolución Promedio NDVI vs NDBI',
            markers=True
        )
        fig_idx.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Valor del Índice",
            legend_title="Índice"
        )
        st.plotly_chart(fig_idx, use_container_width=True)
        
    with tab2:
        fig_cob = px.bar(
            stats_temporal,
            x='fecha',
            y=['pct_veg', 'pct_urb'],
            labels={'value': 'Porcentaje (%)', 'fecha': 'Fecha', 'variable': 'Tipo'},
            title='Cobertura Estimada del Suelo',
            barmode='group',
            color_discrete_map={'pct_veg': 'green', 'pct_urb': 'gray'}
        )
        fig_cob.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Porcentaje del Área (%)",
            legend_title="Cobertura"
        )
        st.plotly_chart(fig_cob, use_container_width=True)
    
    with tab3:
        st.subheader("Estadísticas Descriptivas por Fecha")
        
        # Tabla de estadísticas
        df_display = stats_temporal[['fecha', 'ndvi_mean', 'ndvi_std', 'ndbi_mean', 'ndbi_std', 'pct_veg', 'pct_urb']].copy()
        df_display['fecha'] = df_display['fecha'].dt.strftime('%Y-%m-%d')
        df_display.columns = ['Fecha', 'NDVI (μ)', 'NDVI (σ)', 'NDBI (μ)', 'NDBI (σ)', 'Veg (%)', 'Urb (%)']
        
        st.dataframe(
            df_display.style.format({
                'NDVI (μ)': '{:.4f}',
                'NDVI (σ)': '{:.4f}',
                'NDBI (μ)': '{:.4f}',
                'NDBI (σ)': '{:.4f}',
                'Veg (%)': '{:.1f}',
                'Urb (%)': '{:.1f}'
            }),
            use_container_width=True,
            height=400
        )


def mostrar_metodologia():
    """Muestra información sobre la metodología utilizada."""
    st.header("Metodología")
    
    with st.expander("Ver detalles de los métodos de detección de cambios", expanded=False):
        comparacion = cargar_comparacion_metodos()
        if comparacion:
            st.markdown(comparacion)
        else:
            st.markdown("""
            ### Métodos Implementados
            
            **Método 1: Diferencia de Índices (NDVI)**
            - Calcula la diferencia simple de NDVI entre dos fechas
            - Clasifica en: pérdida, sin cambio, ganancia
            
            **Método 2: Clasificación Multiíndice**
            - Combina NDVI, NDBI y NDWI
            - Detecta: Urbanización, Pérdida/Ganancia Vegetación, Cambios de Agua
            
            Ver archivo `data/processed/comparacion_metodos.md` para más detalles.
            """)


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================
def main():
    # Título principal
    st.title("Monitor de Cambios Urbanos: Chaitén")
    st.markdown("""
    **Análisis de cambios territoriales basado en imágenes Sentinel-2 (2020-2024)**
    
    Este dashboard presenta los resultados del análisis de detección de cambios 
    urbanos en la comuna de Chaitén, Chile.
    """)
    
    # Cargar datos
    zonas, stats, stats_temporal = cargar_datos()
    
    if zonas is None:
        st.error("No se pudieron cargar los datos. Verifica que existan los archivos en data/processed/")
        return
    
    # Sidebar con controles y descargas
    tipo_cambio, fecha_inicio, fecha_fin = mostrar_sidebar(stats, stats_temporal)
    
    # Contenido principal
    mostrar_metricas_globales(stats)
    
    st.markdown("---")
    
    mostrar_mapa_y_tabla(zonas, stats)
    
    st.markdown("---")
    
    mostrar_comparacion_temporal(stats_temporal, fecha_inicio, fecha_fin)
    
    st.markdown("---")
    
    mostrar_evolucion_temporal(stats_temporal)
    
    st.markdown("---")
    
    mostrar_metodologia()
    
    # Footer
    st.markdown("---")
    st.caption("Laboratorio 2: Detección de Cambios Urbanos | Geoinformática USACH | 2025")


if __name__ == "__main__":
    main()
