"""
Hazard Data Loader designed for structured Slope Unit (SU) susceptibility features.
"""
import pyogrio
import os

EXPECTED_LAYERS = ["SUcovariate3857lr_final", "SUcovariate3857woe_final"]

def load_environmental_covariates(file_path="c:/NER-Smart-Logistics/data/geospatial/raw/India_dataset.gpkg"):
    """
    Loads predictor covariates (slope, elevation, ndvi, etc).
    Does NOT load a historical hazard inventory because none exists in this dataset.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing {file_path}")
        
    # Read the core covariate layer lazily
    gdf = pyogrio.read_dataframe(file_path, layer="SUcovariate3857lr_final")
    
    # Selecting available real environmental fields
    useful_cols = ['geometry', 'Elev_mean', 'Slope_mean', 'Asp_mean', 'RnSum_mean', 'NDVI_mean', 'pga_mean', 'litho_0', 'lcover_11']
    existing = [col for col in useful_cols if col in gdf.columns]
    
    return gdf[existing].copy()
    
def get_hazard_events():
    """
    Blocked. The current dataset provides mapping units and susceptibility outputs, but NO EVENT LOGS.
    """
    raise NotImplementedError("Historical landslide events (date, exact lat/lon, severity) are not present in this dataset.")
