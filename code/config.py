"""Configuration settings and constants"""

# API Configuration
OPENAI_MODEL = "gpt-4-mini"
MAX_TEXT_LENGTH = 4000
MAX_RETRIES = 3
BATCH_SIZE = 5

# Confidence thresholds
CAUSAL_CONFIDENCE_THRESHOLD = 0.7

# File paths
ROOT_PATH = '/users/wenxinyang/desktop/github/3dhabitat_litreview'
PDF_FOLDER = "lit/selected_files"
OUTPUT_FILE = "pdf_information.csv"

# Analysis categories
STRUCTURE_CATEGORIES = ["vertical_3d", "horizontal_2d", "combined_analysis"]
BIODIVERSITY_CATEGORIES = ["vertical_distribution", "horizontal_distribution", "multi_dimensional"]
RELATIONSHIP_CATEGORIES = [
    "structure_biodiversity_correlation",
    "structure_to_biodiversity_causal",
    "biodiversity_to_structure_causal"
] 