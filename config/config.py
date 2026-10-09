import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATABASE_DIR = os.path.join(BASE_DIR, "database")

# Ensure required directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, DATABASE_DIR]:
    os.makedirs(directory, exist_ok=True)

# File paths
DEFAULT_DATASET_NAME = "flood_risk_dataset_india.csv"
LOCAL_DATASET_PATH = os.path.join(BASE_DIR, DEFAULT_DATASET_NAME)
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, "preprocessor.pkl")
MODEL_PATH = os.path.join(MODELS_DIR, "risk_model.pkl")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
DB_PATH = os.path.join(DATABASE_DIR, "field_reports_v2.db")

# Target and feature column detection candidates
TARGET_COLUMN_CANDIDATES = ["Flood Occurred", "Flood_Occurred", "FloodOccurred", "Flood_Risk"]
LATITUDE_CANDIDATES = ["Latitude", "latitude", "lat", "LAT"]
LONGITUDE_CANDIDATES = ["Longitude", "longitude", "lon", "long", "lng", "LON"]

# Configurable prototype risk thresholds
RISK_THRESHOLD_LOW = 0.35
RISK_THRESHOLD_HIGH = 0.70

# Logistics Risk Score weights
LOGISTICS_WEIGHT_ENV = 0.60
LOGISTICS_WEIGHT_ROAD = 0.25
LOGISTICS_WEIGHT_REPORT = 0.15

# Prototype Demonstration Network Hubs (North Eastern Region Coordinates)
NER_HUBS = {
    "Guwahati": {"lat": 26.1445, "lon": 91.7362, "state": "Assam", "district": "Kamrup Metropolitan"},
    "Shillong": {"lat": 25.5788, "lon": 91.8933, "state": "Meghalaya", "district": "East Khasi Hills"},
    "Tezpur": {"lat": 26.6528, "lon": 92.7926, "state": "Assam", "district": "Sonitpur"},
    "Silchar": {"lat": 24.8333, "lon": 92.7789, "state": "Assam", "district": "Cachar"},
    "Itanagar": {"lat": 27.0844, "lon": 93.6053, "state": "Arunachal Pradesh", "district": "Papum Pare"},
    "Imphal": {"lat": 24.8170, "lon": 93.9368, "state": "Manipur", "district": "Imphal East"},
    "Kohima": {"lat": 25.6751, "lon": 94.1086, "state": "Nagaland", "district": "Kohima"},
    "Aizawl": {"lat": 23.7271, "lon": 92.7176, "state": "Mizoram", "district": "Aizawl"},
    "Agartala": {"lat": 23.8315, "lon": 91.2868, "state": "Tripura", "district": "West Tripura"},
    "Gangtok": {"lat": 27.3389, "lon": 88.6065, "state": "Sikkim", "district": "East Sikkim"},
    "Dibrugarh": {"lat": 27.4728, "lon": 94.9120, "state": "Assam", "district": "Dibrugarh"},
    "Dimapur": {"lat": 25.9060, "lon": 93.7271, "state": "Nagaland", "district": "Dimapur"},
    "Jorhat": {"lat": 26.7509, "lon": 94.2037, "state": "Assam", "district": "Jorhat"},
    "Tura": {"lat": 25.5141, "lon": 90.2032, "state": "Meghalaya", "district": "West Garo Hills"},
}

# Prototype Demonstration Network Routes
NER_ROUTES = [
    ("Guwahati", "Shillong", 100, 150, "NH 6"),
    ("Guwahati", "Tezpur", 175, 210, "NH 27"),
    ("Shillong", "Silchar", 210, 330, "NH 6"),
    ("Tezpur", "Itanagar", 155, 240, "NH 15"),
    ("Tezpur", "Jorhat", 160, 220, "NH 715"),
    ("Jorhat", "Dibrugarh", 135, 180, "NH 27"),
    ("Jorhat", "Dimapur", 130, 190, "NH 29"),
    ("Dimapur", "Kohima", 70, 130, "NH 29"),
    ("Kohima", "Imphal", 135, 240, "NH 2"),
    ("Silchar", "Imphal", 255, 420, "NH 37"),
    ("Silchar", "Aizawl", 175, 300, "NH 306"),
    ("Guwahati", "Agartala", 550, 720, "NH 8"),
    ("Shillong", "Tura", 300, 420, "NH 217"),
    ("Guwahati", "Gangtok", 530, 680, "NH 10 / NH 27"),
    ("Silchar", "Agartala", 290, 480, "NH 8"),
    ("Itanagar", "Dibrugarh", 195, 270, "NH 415"),
]

NER_STATES = [
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura"
]
