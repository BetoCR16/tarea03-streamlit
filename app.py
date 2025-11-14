import streamlit as st
import pandas as pd
# Carga de la clase WebFeatureService del módulo wfs de owslib
# Permite interactuar con servicios web geoespaciales tipo WFS
from owslib.wfs import WebFeatureService
# Carga de geopandas con el alias gdp
import geopandas as gpd
from io import BytesIO

import plotly.express as px

# Fuentes de datos

DATOS_FIRMS = "data/incendios_2020-2024_costa_rica.csv"


# Carga de datos

def cargar_datos_incendios():
    # Carga con pandas
    datos = pd.read_csv(DATOS_FIRMS)
    return datos

datos_incendios = cargar_datos_incendios()


### Organizacion de datos

## Conversion de fechas
datos_incendios['acq_date'] = pd.to_datetime(datos_incendios['acq_date'])
datos_incendios['acq_time'] = datos_incendios['acq_time'].astype(str).str.zfill(4)
datos_incendios['complete_date'] = pd.to_datetime(
    datos_incendios['acq_date'].dt.strftime('%Y-%m-%d') + ' ' +
    datos_incendios['acq_time'].str[:2] + ':' +
    datos_incendios['acq_time'].str[2:]
)

# Columnas relevantes
columnas = [
    'complete_date',
    'latitude', 
    'longitude', 
    'brightness',
    'confidence',
    'frp',
    'daynight'
]
datos_incendios = datos_incendios[columnas]

datos_incendios = datos_incendios.rename(columns={
    'complete_date': 'Fecha',
    'latitude': 'Latitud',
    'longitude': 'Longitud',
    'brightness': 'Brillo',
    'frp': 'FRP',
    'confidence': 'Confianza',
    'daynight': 'Día/Noche'
})

## TABLA
st.subheader('Datos de incendios en Costa Rica 2020 - 2024')
st.dataframe(datos_incendios, hide_index=True)

### GRAFICO

# Creación de columna con solo el año
datos_incendios['Año'] = datos_incendios['Fecha'].dt.year

# Conteo de incendios por cada año
conteo_incendios_por_anyo = (
    datos_incendios.groupby('Año')
    .size()
    .reset_index(name='Frecuencia')
    .rename(columns={'year': 'Año'})
)

fig_incendios_anuales = px.line(
    conteo_incendios_por_anyo,
    x='Año',
    y='Frecuencia',
    title='Focos de calor detectados a lo largo del tiempo',
    labels={'Frecuencia':'Cantidad de focos de calor detectados'}
)
fig_incendios_anuales.update_xaxes(dtick=1)

# Mostrar el gráfico
st.subheader('Tendencia de focos de calor (incendios) en Costa Rica (2020-2024)')
st.plotly_chart(fig_incendios_anuales)

