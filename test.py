import geopandas as gpd
import pyogrio

osm_path = "c:/NER-Smart-Logistics/data/geospatial/raw/north-eastern-zone-latest.osm.pbf"
try:
    gdf = pyogrio.read_dataframe(osm_path, layer="lines")
    print(f"SUCCESS: {len(gdf)} lines loaded.")
except Exception as e:
    print(f"FAILED: {e}")
