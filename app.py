import folium
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static
from owslib.wfs import WebFeatureService
from io import BytesIO

# Fuentes de datos

DATOS_FIRMS = "data/incendios_2020-2024_costa_rica.csv"

st.title('Focos de calor (incendios) detectados en Costa Rica utilizando FIRMS (2020–2024)')
st.write("— *Aplicación desarrollada por Roberto Méndez*")


# Carga de datos

def cargar_datos_incendios():
    # Carga con pandas
    datos = pd.read_csv(DATOS_FIRMS)
    return datos

datos_incendios = cargar_datos_incendios()

# Carga de Áreas de conservación de Costa Rica
# Conexión al servicio WFS
wfs_url = 'http://geos1pne.sirefor.go.cr/wfs'
wfs_version = '1.1.0'
wfs = WebFeatureService(url=wfs_url, version=wfs_version)

# Obtener la capa de áreas de conservación
capa = 'PNE:areas_conservacion'
respuesta = wfs.getfeature(typename=capa, outputFormat='application/json')

# Leer la respuesta en un GeoDataFrame y convertir a CRS 4326
areas_conservacion_gdf = gpd.read_file(BytesIO(respuesta.read())).to_crs(epsg=4326)


### Organizacion de datos

## Conversion de fechas
datos_incendios['acq_date'] = pd.to_datetime(datos_incendios['acq_date'])
datos_incendios['acq_time'] = datos_incendios['acq_time'].astype(str).str.zfill(4)
datos_incendios['complete_date'] = pd.to_datetime(
    datos_incendios['acq_date'].dt.strftime('%Y-%m-%d') + ' ' +
    datos_incendios['acq_time'].str[:2] + ':' +
    datos_incendios['acq_time'].str[2:]
)

# Convertir datos de incendios a geodataframe
datos_incendios_gdf = gpd.GeoDataFrame(
    datos_incendios,
    geometry=gpd.points_from_xy(datos_incendios['longitude'], datos_incendios['latitude']),
    crs="EPSG:4326"
)

# Unir incendios a las areas
datos_incendios_por_area = gpd.sjoin(
    datos_incendios_gdf,
    areas_conservacion_gdf,
    how="left",
    predicate="within"
)

# Columnas relevantes
columnas = [
    'complete_date',
    'latitude', 
    'longitude', 
    'brightness',
    'confidence',
    'frp',
    'daynight',
    'nombre_ac'
]
datos_incendios_por_area_tabla = datos_incendios_por_area[columnas]

datos_incendios_por_area_tabla = datos_incendios_por_area_tabla.rename(columns={
    'complete_date': 'Fecha',
    'nombre_ac': 'Área de Conservación',
    'latitude': 'Latitud',
    'longitude': 'Longitud',
    'brightness': 'Brillo',
    'frp': 'FRP',
    'confidence': 'Confianza',
    'daynight': 'Día/Noche'
})

## TABLA
st.subheader('Datos de focos de calor detectados (incendios) por área de conservación en Costa Rica (2020 - 2024)')
st.dataframe(datos_incendios_por_area_tabla, hide_index=True)

### GRAFICO

# Creación de columna para meses
datos_incendios['month_num'] = datos_incendios['complete_date'].dt.month

# Pasar numero de mes a texto
# Se realiza de esta forma dado que month_name presenta un error 
# sobre locale setting
traductor_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Aplicar el mapeo para crear la columna 'Mes'
datos_incendios['month'] = datos_incendios['month_num'].map(traductor_meses)


# Conteo de focos de calor 
frecuencia_mensual = datos_incendios.groupby(['month_num', 'month']).size().reset_index(name='Frecuencia')

# Creacion de gráfico
fig_incendios_mensual = px.line(
    frecuencia_mensual,
    x='month',
    y='Frecuencia',
    labels={'month': 'Mes', 'Frecuencia': 'Cantidad de focos de calor detectados'},
    title='Focos de calor detectados a lo largo del tiempo (meses) (2020-2024)',
    markers=True
)
fig_incendios_mensual.update_xaxes(dtick=1)

# Mostrar el gráfico
st.subheader('Tendencia mensual de focos de calor (incendios) en Costa Rica (2020–2024)')
st.plotly_chart(fig_incendios_mensual)

## MAPA

conteo_por_area = (
    datos_incendios_por_area.groupby("nombre_ac")
    .size()
    .reset_index(name="frecuencia")
)

# Unir los datos de casos con GeoDataFrame
areas_merged = areas_conservacion_gdf.merge(
    conteo_por_area,  
    on='nombre_ac',
    how='left'
)

# Crear una paleta de colores
from branca.colormap import linear
paleta_colores = linear.YlOrRd_09.scale(areas_merged['frecuencia'].min(), areas_merged['frecuencia'].max())

mapa = folium.Map(
    location=[9.7489, -83.7534], #Costa Ricac
    zoom_start=7
    )

# Añadir los polígonos al mapa
folium.GeoJson(
    areas_merged,
    name='Cantidad de focos de calor por área de conservación',
    style_function=lambda feature: {
        'fillColor': paleta_colores(feature['properties']['frecuencia']),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    },
    highlight_function=lambda feature: {
        'weight': 3,
        'color': 'black',
        'fillOpacity': 0.9,
    },
    tooltip=folium.features.GeoJsonTooltip(
        fields=['nombre_ac', 'frecuencia'],
        aliases=['Área de conservación: ', 'Cantidad de focos de calor detectados: '],
        localize=True
        )
).add_to(mapa)

# Agregar el control de capas al mapa
folium.LayerControl().add_to(mapa)

# Mostrar el mapa
st.subheader('Mapa de cantidad de focos de calor en áreas de conservación de Costa Rica')

# Forma antigua
folium_static(mapa)