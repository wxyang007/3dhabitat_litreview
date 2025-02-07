"""Configuration settings"""
import os

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MAX_TOTAL_CHARS = 10000
MAX_ABSTRACT_CHARS = 2000

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
    'major_tasks',
    'acoustic_monitoring',
    'vertical_movement'
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