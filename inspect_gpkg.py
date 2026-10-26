import pyogrio
import os
import json

gpkg_path = "c:/NER-Smart-Logistics/data/geospatial/raw/India_dataset.gpkg"
file_size = os.path.getsize(gpkg_path)

layers = pyogrio.list_layers(gpkg_path)

output = {
    "file_size": file_size,
    "layers": []
}

for layer_name, geometry_type in layers:
    try:
        info = pyogrio.read_info(gpkg_path, layer=layer_name)
        layer_info = {
            "name": layer_name,
            "geometry": geometry_type,
            "features": info["features"],
            "crs": str(info["crs"]),
            "fields": list(info["fields"]),
            "dtypes": [str(d) for d in info["dtypes"]]
        }
        output["layers"].append(layer_info)
    except Exception as e:
        output["layers"].append({
            "name": layer_name,
            "error": str(e)
        })

with open('c:/NER-Smart-Logistics/gpkg_info.json', 'w') as f:
    json.dump(output, f, indent=2)
