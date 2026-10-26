"""
Mapping of the eight North-Eastern Region (NER) states.

Coordinates are currently NOT hardcoded as per instructions.
Geographic definitions will purely depend on OSM boundaries or verified sources.
"""

NER_STATES = {
    "Arunachal Pradesh": {"abbreviation": "AR"},
    "Assam": {"abbreviation": "AS"},
    "Manipur": {"abbreviation": "MN"},
    "Meghalaya": {"abbreviation": "ML"},
    "Mizoram": {"abbreviation": "MZ"},
    "Nagaland": {"abbreviation": "NL"},
    "Sikkim": {"abbreviation": "SK"},
    "Tripura": {"abbreviation": "TR"}
}

NER_STATE_LIST = list(NER_STATES.keys())

def is_ner_state(state_name):
    return state_name in NER_STATES
