import folium
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st
from streamlit_folium import folium_static
from streamlit_folium import st_folium
from owslib.wfs import WebFeatureService
from io import BytesIO
from folium.plugins import MarkerCluster

# Fuentes de datos

DATOS_FIRMS = "data/incendios_2020-2024_costa_rica.csv"
DATOS_COBERTURA_2023 = "data/datos_completos_preprocesados.gpkg"

st.title('Focos de calor (incendios) detectados en Costa Rica utilizando FIRMS (2020–2024)')
st.write("— *Aplicación desarrollada por Roberto Méndez*")


# -------- Carga de datos
@st.cache_data
def cargar_datos_incendios():
    # Carga con pandas
    datos = pd.read_csv(DATOS_FIRMS)
    return datos

@st.cache_data
def cargar_datos_cobertura_forestal():
    datos_preprocesados = gpd.read_file(
    DATOS_COBERTURA_2023
    ).to_crs(epsg=4326)
    return datos_preprocesados

@st.cache_data
def cargar_wfs(url, capa, version="1.1.0", epsg=4326):
    """
    Descarga una capa WFS y la retorna como GeoDataFrame con sistema de coords especificado.
    url (str): URL WFS
    capa (str): Nombre de la capa (typename)
    version (str): Versión WFS (default 1.1.0)
    epsg (int): Código EPSG (default 4326)
    """
    wfs = WebFeatureService(url=url, version=version)
    respuesta = wfs.getfeature(typename=capa, outputFormat='application/json')
    gdf = gpd.read_file(BytesIO(respuesta.read())).to_crs(epsg=epsg)
    return gdf


with st.spinner("*⏳ Carga de datos...*"):
    datos_incendios = cargar_datos_incendios()
    #cobertura_forestal_2023 = carga_cobertura_forestal()

    # Áreas de conservación
    areas_conservacion_gdf = cargar_wfs(
        url='http://geos1pne.sirefor.go.cr/wfs',
        capa='PNE:areas_conservacion'
    )

    # Cantones
    cantones_gdf = cargar_wfs(
        url='https://geos.snitcr.go.cr/be/IGN_5_CO/wfs',
        capa='IGN_5_CO:limitecantonal_5k'
    )

    datos_preprocesados = cargar_datos_cobertura_forestal()

st.write("*Datos cargados ✅*")

### Organizacion de datos
def sjoin_clean(left, right, how="left", predicate="intersects"):
    out = gpd.sjoin(left, right, how=how, predicate=predicate)
    return out.drop(columns=["index_right"], errors="ignore")

with st.spinner("*⏳ Preparación de datos...*"):
    # @st.cache_data
    # def data_preparation():
    #     ## Conversion de fechas
    #     datos_incendios['acq_date'] = pd.to_datetime(datos_incendios['acq_date'])
    #     datos_incendios['acq_time'] = datos_incendios['acq_time'].astype(str).str.zfill(4)
    #     datos_incendios['complete_date'] = pd.to_datetime(
    #         datos_incendios['acq_date'].dt.strftime('%Y-%m-%d') + ' ' +
    #         datos_incendios['acq_time'].str[:2] + ':' +
    #         datos_incendios['acq_time'].str[2:]
    #     )

    #     # Conversión a GeoDataFrame
    #     datos_incendios_gdf = gpd.GeoDataFrame(
    #         datos_incendios,
    #         geometry = gpd.points_from_xy(
    #             datos_incendios["longitude"],
    #             datos_incendios["latitude"]
    #         ),
    #         crs="EPSG:4326"
    #     )

    #     # Uniones
    #     datos_incendios_por_area = sjoin_clean(datos_incendios_gdf, areas_conservacion_gdf)
    #     return sjoin_clean(datos_incendios_por_area, cantones_gdf).dropna(subset=["nombre_ac"])

    datos_incendios_completo = datos_preprocesados.copy()

st.write("*Datos listos ✅*")

## LATERAL
# Obtener lista de áreas de conservación
lista_areas_conservacion = datos_incendios_completo['nombre_ac'].unique().tolist()
lista_cantones = datos_incendios_completo['CANTÓN'].unique().tolist()

# Añadir la opción "Todos" al inicio de la lista
opciones_areas = ['Todos'] + lista_areas_conservacion
opciones_cantones = ['Todos'] + lista_cantones

# Crear el selectbox en la barra lateral
area_seleccionada = st.sidebar.selectbox(
    'Selecciona un área de conservación',
    opciones_areas
)

# --- FILTROS DEPENDIENTES ---
df_temp = datos_incendios_completo.copy()

# Si eligen área, restringimos cantones
if area_seleccionada != "Todos":
    df_temp = datos_incendios_completo[datos_incendios_completo["nombre_ac"] == area_seleccionada]
    cantones_filtrados = sorted(df_temp["CANTÓN"].dropna().unique())
else:
    cantones_filtrados = lista_cantones

opciones_cantones = ["Todos"] + cantones_filtrados

# Crear el selectbox en la barra lateral
canton_seleccionado = st.sidebar.selectbox(
    'Selecciona un cantón',
    opciones_cantones
)

# Si eligen cantón, restringimos áreas
if canton_seleccionado != "Todos":
    df_temp = datos_incendios_completo[datos_incendios_completo["CANTÓN"] == canton_seleccionado]
    areas_filtradas = sorted(df_temp["nombre_ac"].dropna().unique())
else:
    areas_filtradas = lista_areas_conservacion

# --- VOLVER A MOSTRAR LOS SELECTBOX DE FORMA DEPENDIENTE ---
opciones_areas = ["Todos"] + areas_filtradas


datos_filtrados = datos_incendios_completo.copy()

if area_seleccionada != 'Todos':
    #Filtrar
    datos_filtrados = datos_incendios_completo[datos_incendios_completo['nombre_ac'] == area_seleccionada]

if canton_seleccionado != 'Todos':
    #Filtrar
    datos_filtrados = datos_incendios_completo[datos_incendios_completo['CANTÓN'] == canton_seleccionado]

# ## TABLA
# Columnas relevantes
columnas = [
    'complete_date',
    'latitude', 
    'longitude', 
    'brightness',
    'confidence',
    'frp',
    'daynight',
    'nombre_ac',
    'CANTÓN'
]
datos_incendios_tabla = datos_filtrados[columnas]

datos_incendios_tabla = datos_incendios_tabla.rename(columns={
    'complete_date': 'Fecha',
    'nombre_ac': 'Área de Conservación',
    'latitude': 'Latitud',
    'longitude': 'Longitud',
    'brightness': 'Brillo',
    'frp': 'FRP',
    'confidence': 'Confianza',
    'daynight': 'Día/Noche',
    'CANTÓN': 'Cantón'
})
st.subheader('Datos de focos de calor detectados (incendios) en Costa Rica (2020 - 2024)')
st.dataframe(datos_incendios_tabla, hide_index=True)

### GRAFICO

# Creación de columna para meses
datos_filtrados['month_num'] = datos_filtrados['complete_date'].dt.month

# Pasar numero de mes a texto
# Se realiza de esta forma dado que month_name presenta un error 
# sobre locale setting
traductor_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Aplicar el mapeo para crear la columna 'Mes'
datos_filtrados['month'] = datos_filtrados['month_num'].map(traductor_meses)


# Conteo de focos de calor 
frecuencia_mensual = datos_filtrados.groupby(['month_num', 'month']).size().reset_index(name='Frecuencia')

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


# --- GRAFICO DE BARRA CANTONES 2024 ---
datos_filtrados['year'] = datos_filtrados['complete_date'].dt.year
datos_2024 = datos_filtrados[datos_filtrados['year'] == 2024]

frecuencia_por_canton = datos_2024.groupby('CANTÓN').size().reset_index(name='Frecuencia')

fig_canton_2024 = px.bar(
    frecuencia_por_canton, 
    x='CANTÓN',               # El Cantón en el eje X
    y='Frecuencia',               # El Conteo (frecuencia) en el eje Y
    orientation='v',          # Barras verticales
    title='Focos de calor detectados por cantón en Costa Rica durante 2024',
    labels={'CANTÓN': 'Cantón', 'Frecuencia': 'Cantidad de focos de calor'},
    color='Frecuencia',           # Coloreamos las barras según la frecuencia
    color_continuous_scale=px.colors.sequential.Viridis # Escala de color
)
fig_canton_2024.update_layout(
    xaxis={'categoryorder': 'total descending'} 
)
st.subheader('Cantidad de focos de calor detectados por cantón en Costa Rica durante 2024')
st.plotly_chart(fig_canton_2024)

## --- GRAFICO COBERTURA ---

frecuencia_por_bosque = datos_preprocesados.groupby('Clase').size().reset_index(name='Frecuencia')

fig_cobertura = px.bar(
    frecuencia_por_bosque, 
    x='Clase',               # El Cantón en el eje X
    y='Frecuencia',               # El Conteo (frecuencia) en el eje Y
    orientation='v',          # Barras verticales
    title='Focos de calor detectados por tipo de bosque en Costa Rica (2020-2024)',
    labels={'Clase': 'Tipo de bosque', 'Frecuencia': 'Cantidad de focos de calor'},
    color='Frecuencia',           # Coloreamos las barras según la frecuencia
    color_continuous_scale=px.colors.sequential.Viridis # Escala de color
)
fig_cobertura.update_layout(
    xaxis={'categoryorder': 'total descending'} 
)
st.subheader('Cantidad de focos de calor detectados por tipo de bosque en Costa Rica (2020 - 2024)')
st.plotly_chart(fig_cobertura)

## MAPA
st.subheader('Mapa de cantidad de focos de calor en áreas de conservación de Costa Rica (2020 - 2024)')

with st.spinner("Cargando mapa, por favor espere..."):
    conteo_por_area = (
        datos_filtrados.groupby("nombre_ac")
        .size()
        .reset_index(name="frecuencia")
    )

    conteo_por_canton = (
        datos_filtrados.groupby("CANTÓN")
        .size()
        .reset_index(name="frecuencia")
    )

    # Unir los datos de casos con GeoDataFrame
    areas_merged = areas_conservacion_gdf.merge(
        conteo_por_area,  
        on='nombre_ac',
        how='left'
    ).fillna(0)

    canton_merged = cantones_gdf.merge(
        conteo_por_canton,  
        on='CANTÓN',
        how='left'
    ).fillna(0)

    canton_map = canton_merged[["geometry", "CANTÓN", "frecuencia"]].copy()

    # Crear una paleta de colores
    from branca.colormap import linear
    paleta_colores_areas = linear.YlOrRd_09.scale(areas_merged['frecuencia'].min(), areas_merged['frecuencia'].max())
    paleta_colores_cantones = linear.YlOrRd_09.scale(canton_map['frecuencia'].min(), canton_map['frecuencia'].max())
    
    def generar_mapas_base():
        return folium.Map(
            location=[9.7489, -83.7534], #Costa Rica
            zoom_start=7
        )
        
    mapa = generar_mapas_base()
    mapa_cantones = generar_mapas_base()

    # Crear columna para tooltip
    areas_merged["frecuencia_tooltip"] = areas_merged["frecuencia"].apply(
        lambda x: str(int(x)) if x > 0 else ""
    )
    # Añadir los polígonos al mapa
    folium.GeoJson(
        areas_merged,
        name='Cantidad de focos de calor por área de conservación',
        style_function=lambda feature: {
            'fillColor': paleta_colores_areas(feature['properties']['frecuencia']),
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
            fields=['nombre_ac', 'frecuencia_tooltip'],
            aliases=['Área de conservación: ', 'Cantidad de focos de calor detectados: '],
            localize=True
            )
    ).add_to(mapa)

    folium.GeoJson(
        canton_map,
        name='Cantidad de focos de calor por cantón',
        style_function=lambda feature: {
            'fillColor': paleta_colores_cantones(feature['properties']['frecuencia']),
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
            fields=['CANTÓN', 'frecuencia'],
            aliases=['Cantón: ', 'Cantidad de focos de calor detectados: '],
            localize=True
            )
    ).add_to(mapa_cantones)

    # Añadir la leyenda al mapa
    paleta_colores_areas.caption = 'Cantidad de focos de calor detectados'
    paleta_colores_areas.add_to(mapa)

    # Añadir la leyenda al mapa
    paleta_colores_cantones.caption = 'Cantidad de focos de calor detectados'
    paleta_colores_cantones.add_to(mapa_cantones)

    # Agregar el control de capas al mapa
    folium.LayerControl().add_to(mapa)
    folium.LayerControl().add_to(mapa_cantones)

    # Mostrar mapa forma antigua
    folium_static(mapa)

    st.subheader('Mapa de cantidad de focos de calor en cantones de Costa Rica')

    folium_static(mapa_cantones)

# --- MAPA DE PUNTOS FORESTAL ---
@st.cache_data
def create_forest_map(_datos):
    if 'map' not in st.session_state or st.session_state.map is None:
        mapa_forestal = folium.Map(
            location=[9.9328,-84.0795],
            zoom_start=7,
            control_scale=True
        )
        marker_cluster = MarkerCluster().add_to(mapa_forestal)
        for index, row in _datos.iterrows():
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
        
        st.session_state.map = mapa_forestal  # Save the map in the session state
    return st.session_state.map

st.subheader('Mapa de puntos de focos de calor detectados en Costa Rica (2020-2024)')
mapa_forestal = create_forest_map(datos_preprocesados)
folium_static(mapa_forestal)


