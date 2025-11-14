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

datos_incendios['acq_date'] = pd.to_datetime(datos_incendios['acq_date'])

st.subheader('Datos de incendios en Costa Rica 2020 - 2024')
st.dataframe(datos_incendios, hide_index=True)


### Grafico

# Creación de columna con solo el año
datos_incendios['year'] = datos_incendios['acq_date'].dt.year

# Conteo de incendios por cada año
conteo_incendios_por_anyo = (
    datos_incendios.groupby('year')
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