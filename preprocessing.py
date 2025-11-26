import pandas as pd
import geopandas as gpd
from owslib.wfs import WebFeatureService
from io import BytesIO

DATOS_FIRMS = "data/incendios_2020-2024_costa_rica.csv"

def cargar_datos_incendios():
    # Carga con pandas
    datos = pd.read_csv(DATOS_FIRMS)
    return datos

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

print("CARGANDO DATOS")
datos_incendios = cargar_datos_incendios()

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

print("DATOS CARGADOS! UNIENDO DATOS....")
### UNION DE DATOS

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

# Unir incendios a area y cantones
datos_incendios_por_area = gpd.sjoin(
    datos_incendios_gdf,
    areas_conservacion_gdf,
    how="left",
    predicate="intersects"
)

# Dropear index para segundo join
datos_incendios_por_area = datos_incendios_por_area.drop(columns=["index_right"]) 

datos_incendios_completo = gpd.sjoin(
    datos_incendios_por_area,
    cantones_gdf,
    how="left", 
    predicate="intersects"
)

# Drop de datos nulos
datos_incendios_completo = datos_incendios_completo.dropna(subset=["nombre_ac"])
datos_incendios_completo = datos_incendios_completo.drop(columns=["OBJECTID"])


print("LISTO! GUARDANDO EN GEOPACKAGE")
datos_incendios_completo.to_file("datos_completos_preprocesados.gpkg", layer="datos_incendios_completo", driver="GPKG")
print("LISTO!")
