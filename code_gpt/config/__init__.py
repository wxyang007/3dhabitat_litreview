"""Configuration settings"""
import os

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MAX_TOTAL_CHARS = 5000
MAX_ABSTRACT_CHARS = 1000

ANALYSIS_CATEGORIES = {
    'structure_analysis': ['vertical_3d', 'horizontal_2d'],
    'animal_biodiversity': ['vertical_3d', 'horizontal_2d']
}

RELATIONSHIP_CATEGORIES = [
    'structure_animal_correlation',
    'effect_structure_on_animals',
    'effect_animals_on_structure'
]

EVIDENCE_TYPES = [
    'experimental',
    'natural_experiment', 
    'statistical',
    'causal'
]

VALID_TAXA = [
    'birds',
    'bats', 
    'primates',
    'other_mammals',
    'amphibians',
    'reptiles',
    'invertebrates'
]

RESEARCH_TASKS = [
    'species_richness',
    'abundance',
    'occurrence_distribution',
    'community_composition',
    'functional_diversity',
    'beta_diversity',
    'stratification_niche',
    'movement',
    'behavior',
    'habitat_preference',
    'habitat_suitability',
    'survival_mortality',   
    'acoustic_characteristics',
    'trait'
]

METHOD_TYPES = [
    ('Airborne LiDAR', 'airborne_lidar'),
    ('Terrestrial LiDAR', 'terrestrial_lidar'),
    ('Spaceborne LiDAR', 'spaceborne_lidar'),
    ('Structure from Motion', 'structure_from_motion'),
    ('Field Sampling', 'field_sampling'),
    ('Other Remote Sensing', 'other_remote_sensing'),
    ('Other Field', 'other_field')
] 