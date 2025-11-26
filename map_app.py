import streamlit as st
from streamlit_folium import st_folium
import folium
import geopandas as gpd
from folium.plugins import MarkerCluster

st.title("Mapa de focos de calor y cobertura forestal de Costa Rica")
st.write("— *Desarrollado por Roberto Méndez*")

# ----- Datos -----
datos_preprocesados = gpd.read_file(
    "data/datos_completos_preprocesados.gpkg"
    ).to_crs(epsg=4326)

COLUMNAS_MAPA = [
    'frp',
    'complete_date', 
    'confidence', 
    'latitude', 
    'longitude'
]

datos_simplificados = datos_preprocesados[COLUMNAS_MAPA]

# ----- Mapa de cobertura forestal -----
lat, lon = 9.9328, -84.0795 # Costa Rica
tiles_url = "https://tiles-cobertura-2023.s3.amazonaws.com/TILES/{z}/{x}/{y}.png"

# Crear el mapa
mapa_forestal = folium.Map(
    location=[lat,lon],
    zoom_start=7
)

folium.TileLayer(
    tiles=tiles_url,
    control=True,
    attr="Cobertura forestal 2023 SINAC"
).add_to(mapa_forestal)

# ----- Cluster de marcadores -----
@st.cache_data
def crear_cluster():
    marker_cluster = MarkerCluster()
    for row in datos_simplificados.itertuples():
        # Creamos el texto del Popup usando las variables que sí tenemos
        popup_text = f"""
        Foco de Incendio<br>
        FRP (Poder Radiativo): {row.frp:.1f} MW<br>
        Fecha de Detección: {row.complete_date.strftime('%Y-%m-%d')}<br>
        Confianza: {row.confidence}<br>
        Coordenadas: {row.latitude:.2f}, {row.longitude:.2f}
        """
        
        # Asignamos color del ícono basado en la confianza (ejemplo)
        if row.confidence == 'h':
            color = 'red'
        elif row.confidence == 'n':
            color = 'orange'
        else:
            color = 'darkblue'

        folium.Marker(
            location=[row.latitude, row.longitude],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"FRP: {row.frp:.1f} MW",
            icon=folium.Icon(color=color, icon='fire', prefix='fa')
        ).add_to(marker_cluster)

    return marker_cluster
with st.spinner("⏳ Generando mapa...", show_time=True):
    markers = crear_cluster()
    markers.add_to(mapa_forestal)

    # Mostrar el mapa en Streamlit
    st_folium(mapa_forestal, height=600, width=800, key="mapa_forestal_2023",returned_objects=[])
st.image("data/forest_map_legend.png")