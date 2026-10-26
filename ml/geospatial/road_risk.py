import geopandas as gpd
import pyogrio
import sys
import os

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/risk'))
from environmental_risk import calculate_environmental_risk
from logistics_risk import calculate_logistics_risk

def build_road_risk():
    road_path = "c:/NER-Smart-Logistics/data/geospatial/processed/ner_roads.gpkg"
    env_path = "c:/NER-Smart-Logistics/data/geospatial/raw/India_dataset.gpkg"
    out_path = "c:/NER-Smart-Logistics/data/geospatial/processed/ner_road_risk.gpkg"
    
    print("Loading networks...")
    gdf_roads = pyogrio.read_dataframe(road_path)
    
    # Efficient loading of only necessary env columns
    env_cols = ['geometry', 'Elev_mean', 'Slope_mean', 'NDVI_mean']
    gdf_env = pyogrio.read_dataframe(env_path, layer='SUcovariate3857lr_final', columns=env_cols)
    
    print(f"Aligning CRS: roads={gdf_roads.crs}, env={gdf_env.crs}")
    # Convert roads to match env which is EPSG:3857
    gdf_roads_3857 = gdf_roads.to_crs(gdf_env.crs)
    
    print("Spatial R-Tree Indexing and joining...")
    # sjoin uses R-tree implicitly in geopandas
    joined = gpd.sjoin(gdf_roads_3857, gdf_env, how='left', predicate='intersects')
    
    # Handle duplicates due to multiple polygon intersections by keeping the first hit
    joined = joined[~joined.index.duplicated(keep='first')].copy()
    
    print("Calculating Risk Scores...")
    # Defaulting fake rainfall anomaly since we don't have real live radar in this batch
    env_risks = []
    log_risks = []
    
    for idx, row in joined.iterrows():
        # Example rainfall inputs since we aren't joining real time meteorological radars here
        r_risk, r_cat, r_factors = calculate_environmental_risk(
            rainfall_anomaly=40, extreme_indicator=0, 
            slope=row.get('Slope_mean', 5), 
            elev=row.get('Elev_mean', 500), 
            ndvi=row.get('NDVI_mean', 0.5)
        )
        
        l_risk, l_cat, l_factors = calculate_logistics_risk(r_risk, row['length_m'], row.get('highway', 'unknown'))
        
        env_risks.append(r_risk)
        log_risks.append(l_risk)
        
    joined['environmental_risk'] = env_risks
    joined['logistics_risk'] = log_risks
    
    print(f"Writing {len(joined)} features to {out_path}...")
    joined.to_file(out_path, driver='GPKG', engine='pyogrio')
    print("Completed Spatial Integration.")

if __name__ == '__main__':
    build_road_risk()
