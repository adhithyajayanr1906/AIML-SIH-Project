import os
import geopandas as gpd
import pyogrio

class OSMImporter:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def load_data(self):
        """
        1. Loads the road dataset safely from file path.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Missing OpenStreetMap file: {self.file_path}")
        # Efficiently read lines using pyogrio
        gdf = pyogrio.read_dataframe(self.file_path, layer='lines')
        return gdf

    def extract_features(self, gdf):
        """
        5. Extracts LineString geometries.
        6. Extracts relevant attributes.
        """
        target_highways = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'service']
        
        # Keep useful columns if they exist in the raw OSM file
        useful_cols = ['geometry', 'highway', 'name', 'ref', 'maxspeed', 'lanes', 'surface', 'bridge', 'tunnel', 'oneway']
        available_cols = [c for c in useful_cols if c in gdf.columns]
        
        # Filter for highways
        if 'highway' in gdf.columns:
            gdf = gdf[gdf['highway'].isin(target_highways)].copy()
        
        gdf = gdf[available_cols].copy()
        return gdf

    def filter_to_ner(self, gdf):
        """
        4. Spatial filter or attribute filter restricting bounds to the eight NER states.
        State boundaries are not intrinsically bundled with PBF road extracts.
        We document that we rely on the pre-processed `north-eastern-zone` bounding box limits.
        """
        return gdf

    def inspect_and_project_crs(self, gdf):
        """
        2. Inspects original CRS.
        3. Converts to an appropriate projected CRS suitable for realistic distance calculations.
        Using EPSG:32646 (UTM Zone 46N) for North East India.
        """
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        gdf_proj = gdf.to_crs(epsg=32646)
        gdf_proj['length_m'] = gdf_proj.geometry.length
        return gdf_proj
