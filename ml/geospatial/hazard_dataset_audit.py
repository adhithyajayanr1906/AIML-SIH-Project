import pyogrio
import os
import json

def audit_dataset():
    gpkg_path = "c:/NER-Smart-Logistics/data/geospatial/raw/India_dataset.gpkg"
    if not os.path.exists(gpkg_path):
        return
        
    file_size = os.path.getsize(gpkg_path) / (1024*1024*1024)
    print(f"File Size: {file_size:.2f} GB")
    
    layers = pyogrio.list_layers(gpkg_path)
    output = []
    
    for layer_name, geometry_type in layers:
        try:
            info = pyogrio.read_info(gpkg_path, layer=layer_name)
            output.append({
                "layer": layer_name,
                "geometry": geometry_type,
                "features": info["features"],
                "crs": str(info["crs"]),
                "fields": list(info["fields"])
            })
        except:
            pass
            
    print(f"Total Layers: {len(output)}")
    
if __name__ == "__main__":
    audit_dataset()
