import streamlit as st
import folium
import pandas as pd
from streamlit_folium import folium_static
import geopandas as gpd
from folium.plugins import MarkerCluster


datos_preprocesados = gpd.read_file(
    "data/datos_completos_preprocesados.gpkg"
    ).to_crs(epsg=4326)

#datos_preprocesados = datos_preprocesados.drop(columns=["complete_date", "FECHA_EDICION","acq_date"])

mapa_forestal = folium.Map(
    location=[9.9328,-84.0795],
    zoom_start=7,
    control_scale=True
)

marker_cluster = MarkerCluster().add_to(mapa_forestal)

for index, row in datos_preprocesados.iterrows():
    # Creamos el texto del Popup usando las variables que sí tenemos
    popup_text = f"""
    Foco de Incendio<br>
    FRP (Poder Radiativo): {row['frp']:.1f} MW<br>
    Fecha de Detección: {row['acq_date'].strftime('%Y-%m-%d')}<br>
    Confianza: {row['confidence']}<br>
    Coordenadas: {row['latitude']:.2f}, {row['longitude']:.2f}
    """
    
    # Asignamos color del ícono basado en la confianza (ejemplo)
    if row['confidence'] == 'h':
        color = 'red'
    elif row['confidence'] == 'n':
        color = 'orange'
    else:
        color = 'darkblue'

    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"FRP: {row['frp']:.1f} MW",
        icon=folium.Icon(color=color, icon='fire', prefix='fa')
    ).add_to(marker_cluster)

folium_static(mapa_forestal)