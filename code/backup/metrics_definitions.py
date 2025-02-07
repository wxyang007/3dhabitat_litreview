"""Definitions and validation rules for metrics and methods"""

# Structure Metrics Definitions and Keywords
STRUCTURE_METRICS = {
    "cover_density": {
        "definition": "Metrics that quantify the amount or density of vegetation",
        "keywords": [
            "canopy cover", "LAI", "leaf area index", "vegetation density",
            "crown cover", "basal area", "stem density", "gap fraction",
            "plant area index", "PAI", "vegetation cover"
        ],
        "validation_rules": [
            "Must be quantitative measurement",
            "Must specify measurement unit",
            "Should indicate measurement method"
        ]
    },
    "height": {
        "definition": "Metrics related to vegetation height measurements",
        "keywords": [
            "canopy height", "tree height", "height percentile", "mean height",
            "maximum height", "minimum height", "height distribution",
            "CHM", "canopy height model", "height profile"
        ],
        "validation_rules": [
            "Must specify height unit",
            "Should indicate measurement method",
            "Should specify if single or multiple height measurements"
        ]
    },
    "vertical_heterogeneity": {
        "definition": "Metrics that describe vertical structure variation",
        "keywords": [
            "foliage height diversity", "FHD", "vertical complexity",
            "vertical distribution", "height diversity", "vertical profile",
            "layer diversity", "stratification", "vertical structure index",
            "vegetation density profile"
        ],
        "validation_rules": [
            "Must quantify vertical variation",
            "Should specify number of layers if using stratification",
            "Should indicate calculation method"
        ]
    },
    "horizontal_heterogeneity": {
        "definition": "Metrics that describe horizontal structure variation",
        "keywords": [
            "gap size", "patch size", "fragmentation", "aggregation index",
            "spatial heterogeneity", "spatial distribution", "clustering",
            "spatial pattern", "horizontal structure index"
        ],
        "validation_rules": [
            "Must quantify horizontal variation",
            "Should specify spatial scale",
            "Should indicate calculation method"
        ]
    }
}

# Data Collection Methods Definitions
DATA_METHODS = {
    "lidar": {
        "definition": "Light Detection and Ranging remote sensing",
        "types": {
            "airborne": [
                "ALS", "aerial lidar", "airborne laser scanning",
                "airborne lidar", "aerial laser scanning"
            ],
            "terrestrial": [
                "TLS", "terrestrial laser scanning", "ground-based lidar",
                "terrestrial lidar", "ground lidar"
            ],
            "spaceborne": [
                "satellite lidar", "GEDI", "ICESat", "spaceborne lidar"
            ]
        },
        "validation_rules": [
            "Must specify lidar type (airborne/terrestrial/spaceborne)",
            "Should include point density if applicable",
            "Should specify sensor model if available"
        ]
    },
    "field_measurements": {
        "definition": "Direct measurements taken in the field",
        "keywords": [
            "field survey", "ground measurement", "field sampling",
            "field plot", "inventory", "field data", "ground truth"
        ],
        "validation_rules": [
            "Must specify measurement method",
            "Should include plot size/design",
            "Should indicate sampling intensity"
        ]
    },
    "photogrammetry": {
        "definition": "Structure from Motion and other image-based 3D reconstruction",
        "keywords": [
            "SfM", "structure from motion", "photogrammetry",
            "aerial photography", "drone imagery", "UAV", "aerial images"
        ],
        "validation_rules": [
            "Must specify image acquisition platform",
            "Should include image overlap percentage",
            "Should indicate processing software"
        ]
    }
}

def validate_metric(metric_name: str, metric_details: dict) -> bool:
    """Validate a metric against its rules"""
    if metric_name not in STRUCTURE_METRICS:
        return False
        
    rules = STRUCTURE_METRICS[metric_name]["validation_rules"]
    keywords = STRUCTURE_METRICS[metric_name]["keywords"]
    
    # Check if metric uses recognized keywords
    if not any(keyword.lower() in str(metric_details).lower() for keyword in keywords):
        return False
        
    # Additional validation could be added here
    return True

def validate_method(method_name: str, method_details: dict) -> bool:
    """Validate a data collection method against its rules"""
    if method_name not in DATA_METHODS:
        return False
        
    rules = DATA_METHODS[method_name]["validation_rules"]
    
    # Method-specific validation
    if method_name == "lidar":
        if not any(type_keyword in str(method_details).lower() 
                  for types in DATA_METHODS["lidar"]["types"].values() 
                  for type_keyword in types):
            return False
    
    # Additional validation could be added here
    return True 