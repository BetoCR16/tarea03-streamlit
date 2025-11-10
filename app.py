import streamlit as st
import pandas as pd

# Fuentes de datos

DATOS_FIRMS = "data/incendios_2020-2024_costa_rica.csv"


# Carga de datos

def cargar_datos_incendios():
    # Carga con pandas
    datos = pd.read_csv(DATOS_FIRMS)
    return datos

datos_incendios = cargar_datos_incendios()

datos_incendios['acq_date'] = pd.to_datetime(datos_incendios['acq_date']).dt.date

st.subheader('Datos de incendios en Costa Rica 2020 - 2024')
st.dataframe(datos_incendios, hide_index=True)