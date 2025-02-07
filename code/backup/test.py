#!/users/wenxinyang/anaconda3/envs/3dhabitat/bin/python

import os
from PyPDF2 import PdfReader
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
from time import sleep
import json
import re
import csv
import asyncio
import aiohttp
from functools import partial
from typing import List, Dict, Any
from utils.data_processing import save_results, print_summaries
from analyzers.categories import get_paper_type, get_detailed_analysis
from utils.ai_client import init_client
from config import ROOT_PATH

def extract_sections(text):
    """
    Extract abstract and methods/study area/data sections from the text
    Returns a concatenated string of these sections
    """
    relevant_text = ""
    
    # Find Abstract
    abstract_patterns = [
        r'(?i)abstract\s*\n(.*?)(?=\n\s*(?:introduction|keywords|background|methods|results))',
        r'(?i)abstract[:\s]+(.*?)(?=\n\s*(?:introduction|keywords|background|methods|results))',
    ]
    
    # Find Methods and everything until Results
    methods_patterns = [
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure)\s*\n(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure).*?\n(.*?)(?=\n\s*(?:results|discussion|conclusion))',
    ]
    
    # Additional patterns for study area and data sections
    study_data_patterns = [
        # Study area/site patterns
        r'(?i)(?:study\s+area|study\s+site|research\s+area|site\s+description)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        r'(?i)(?:study\s+area|study\s+site|research\s+area|site\s+description)\s*\n(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        # Data related patterns
        r'(?i)(?:data\s+collection|data\s+analysis|data\s+processing|data\s+and\s+methods)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        r'(?i)(?:data\s+acquisition|data\s+sources|data\s+sets?|data\s+description)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        # Field methods patterns
        r'(?i)(?:field\s+methods|sampling\s+methods|experimental\s+design)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        r'(?i)(?:field\s+sampling|field\s+measurements|field\s+data)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))'
    ]
    
    # Try to find abstract
    abstract_text = ""
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract_text = match.group(1).strip()
            break
    
    # Try to find methods first
    methods_text = ""
    for pattern in methods_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            methods_text = match.group(1).strip()
            break
    
    # If methods not found or too short, try all study area and data sections
    if not methods_text or len(methods_text) < 500:
        study_data_text = ""
        for pattern in study_data_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                section_text = match.group(1).strip()
                if section_text and len(section_text) > 50:  # Avoid very short matches
                    study_data_text += section_text + "\n\n"
        
        # If we found study/data sections, use them instead of or in addition to methods
        if study_data_text:
            if methods_text:
                methods_text += "\n\n" + study_data_text
            else:
                methods_text = study_data_text
    
    # Combine the sections
    if abstract_text:
        relevant_text += "ABSTRACT:\n" + abstract_text + "\n\n"
    if methods_text:
        relevant_text += "METHODS AND STUDY DETAILS:\n" + methods_text
    
    # If neither section was found, return a larger portion of the original text
    if not relevant_text:
        return text[:4000]  # Increased from 3000 to get more context
    
    return relevant_text

def validate_research_categories(analysis_results):
    """
    Validate that research categories follow the updated rules:
    1. At least one type of analysis present (structure, biodiversity, or relationship)
    2. For structure and biodiversity, validate sub-categories
    3. For relationships, check for valid combinations
    """
    try:
        categories = analysis_results['paper_categories']
        
        # Check if at least one major category is present
        has_structure = any(v['present'] for v in categories['structure_analysis'].values())
        has_biodiversity = any(v['present'] for v in categories['biodiversity_analysis'].values())
        has_relationship = (categories['structure_biodiversity_correlation']['present'] or 
                          categories['structure_to_biodiversity_causal']['present'] or 
                          categories['biodiversity_to_structure_causal']['present'])
        
        if not (has_structure or has_biodiversity or has_relationship):
            print("Warning: No research categories marked as true")
            return False
        
        # Validate structure analysis
        if has_structure:
            structure_cats = categories['structure_analysis']
            if structure_cats['combined_analysis']['present']:
                # If combined analysis is present, check for integration method
                if not structure_cats['combined_analysis']['integration_method'].strip():
                    print("Warning: Combined analysis marked but no integration method specified")
                    return False
        
        # Validate biodiversity analysis
        if has_biodiversity:
            bio_cats = categories['biodiversity_analysis']
            if bio_cats['multi_dimensional']['present']:
                # If multi-dimensional is present, check for integration approach
                if not bio_cats['multi_dimensional']['integration_approach'].strip():
                    print("Warning: Multi-dimensional analysis marked but no integration approach specified")
                    return False
        
        # Validate relationship categories
        if has_relationship:
            # Count number of relationship types present
            relationship_count = sum([
                categories['structure_biodiversity_correlation']['present'],
                categories['structure_to_biodiversity_causal']['present'],
                categories['biodiversity_to_structure_causal']['present']
            ])
            
            # Check confidence scores for relationship claims
            for rel_type in ['structure_biodiversity_correlation', 
                           'structure_to_biodiversity_causal',
                           'biodiversity_to_structure_causal']:
                if categories[rel_type]['present']:
                    if categories[rel_type]['confidence'] < 0.7:  # Threshold for causal claims
                        print(f"Warning: Low confidence ({categories[rel_type]['confidence']}) for {rel_type}")
                        return False
                    
                    # Check for supporting evidence in key_indicators
                    if not categories[rel_type]['key_indicators']:
                        print(f"Warning: No key indicators provided for {rel_type}")
                        return False
        
        return True
        
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return False

def analyze_study_site(text, client):
    """Extract basic study site information"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object with study site information:
{
    "study_site": {
        "location": "country name or 'Not specified'",
        "area_size": "text",
        "spatial_scale": "text"
    }
}

Classification rules:
1. Location: Infer country from any location info:
- US States → United States
- Canadian Provinces → Canada
- German Länder → Germany
- Australian States → Australia
- Cities/regions and their country
- GPS coordinates

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

def analyze_data_collection(text, client):
    """Extract data collection methods and structure metrics"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object with data collection information:
{
    "data_collection": {
        "airborne_lidar": false,
        "spaceborne_lidar": false,
        "terrestrial_lidar": false,
        "structure_from_motion": false,
        "field_data": false,
        "other_remote_sensing": false,
        "other_rs_details": "text"
    },
    "structure_metrics": {
        "cover_density": false,
        "height": false,
        "horizontal_heterogeneity": false,
        "vertical_heterogeneity": false,
        "landscape": false,
        "other": false,
        "other_details": "text"
    }
}

Classification rules:
1. Remote sensing:
- Airborne LiDAR: ALS, LVIS, aerial/helicopter LiDAR
- Spaceborne LiDAR: GEDI, ICESAT(-2)
- Other RS: Landsat, Sentinel-1/2, MODIS, aerial photos, SAR

2. Structure metrics:
- Cover/density: canopy cover, LAI, stem density
- Height: canopy/vegetation height profiles
- Horizontal: spatial variation, gaps
- Vertical: complexity, height diversity, FHD
- Landscape: fragmentation, connectivity

3. field_data should only be marked true when researchers physically measured vegetation/habitat structure in the field.

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

def analyze_taxa(text, client):
    """Extract taxa information"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object with taxa information:
{
    "taxa": {
        "birds": false,
        "bats": false,
        "other_small_mammals": false,
        "reptiles": false,
        "amphibians": false,
        "invertebrates": false,
        "other": false
    }
}

Classification rules:
Taxa (check methods for sampling techniques):
- Birds: avian, point counts, mist nets
- Bats: chiroptera, bat detectors, acoustic monitoring
- Small Mammals: rodents, shrews, small marsupials (<5kg)
- Reptiles: snakes, lizards, turtles
- Amphibians: frogs, salamanders, wetland surveys
- Invertebrates: insects, arthropods, pitfall traps
- Other: large mammals, fish

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

def analyze_research_tasks(text, client):
    """Extract research tasks information"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object with research tasks information:
{
    "research_tasks": {
        "movement": {"present": false, "details": "text"},
        "functional_trait": {"present": false, "details": "text"},
        "distribution_occupancy": {"present": false, "details": "text"},
        "prevalence": {"present": false, "details": "text"},
        "use_of_space": {"present": false, "details": "text"},
        "behaviors": {"present": false, "details": "text"},
        "life_history": {"present": false, "details": "text"},
        "habitat_preference": {"present": false, "details": "text"},
        "abundance_density": {"present": false, "details": "text"},
        "stratification_niche": {"present": false, "details": "text"},
        "species_richness_diversity": {"present": false, "details": "text"},
        "community_composition": {"present": false, "details": "text"},
        "functional_richness_diversity": {"present": false, "details": "text"},
        "community_similarity": {"present": false, "details": "text"},
        "acoustic_characteristics": {"present": false, "details": "text"},
        "habitat_suitability": {"present": false, "details": "text"}
    }
}

Classification rules:
Research tasks:
- Movement: flight heights, animal movement patterns
- Distribution: presence/absence, SDM
- Space use: habitat selection
- Behavior: foraging, activity
- Life history: survival, breeding
- Community: composition, turnover
- Diversity: species/functional richness

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

def analyze_research_categories(text, client):
    """Extract research categories information"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object with research categories information:
{
    "research_categories": {
        "structure_analysis": {
            "vertical_structure": false,
            "vertical_strata": false,
            "acoustic_analysis": false,
            "visibility_analysis": false
        },
        "biodiversity_analysis": {
            "vertical_distribution": false,
            "strata_specific": false,
            "acoustic_sampling": false,
            "visibility_based": false
        },
        "structure_biodiversity_relationship": {
            "correlative": false,
            "causal": false,
            "species_to_structure": false,
            "details": "text"
        },
        "external_factors": {
            "management": false,
            "disturbance": false,
            "details": "text"
        }
    }
}

Classification rules:
1. Each paper must have at least one true value across all categories
2. For structure_biodiversity_relationship, only ONE of these can be true:
   - correlative: Simple correlation/association studies
   - causal: Path analysis, structural equation modeling, experimental studies
   - species_to_structure: Studies of how animals affect vegetation

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

def get_ai_response(prompt, client, max_retries=3):
    """Helper function to get AI response with error handling"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON generator that only outputs valid JSON objects with the exact structure specified. "
                                 "Never include explanatory text. Use double quotes for all strings and true/false for booleans."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            return json.loads(response_text)
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error in AI response: {str(e)}")
                raise
            sleep(1)

async def get_ai_response_async(prompt, client, max_retries=3):
    """Async helper function to get AI response with error handling"""
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.acreate(
                model="gpt-4-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON generator that only outputs valid JSON objects with the exact structure specified. "
                                 "Never include explanatory text. Use double quotes for all strings and true/false for booleans."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            
            return json.loads(response_text)
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error in AI response: {str(e)}")
                raise
            await asyncio.sleep(1)

async def analyze_components(text, client):
    """Run all analysis components in parallel"""
    tasks = [
        analyze_study_site(text, client),
        analyze_data_collection(text, client),
        analyze_taxa(text, client),
        analyze_research_tasks(text, client),
        analyze_research_categories(text, client)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error in component {i}: {str(result)}")
            raise result
    
    return results

def get_paper_type(text, client):
    """First stage: Determine the paper's categories"""
    prompt = """Analyze this scientific paper text and return ONLY a JSON object classifying the paper's categories:
{
    "paper_categories": {
        "structure_analysis": {
            "vertical_3d": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"]
            },
            "horizontal_2d": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"]
            },
            "combined_analysis": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"],
                "integration_method": "text"
            }
        },
        "biodiversity_analysis": {
            "vertical_distribution": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"]
            },
            "horizontal_distribution": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"]
            },
            "multi_dimensional": {
                "present": false,
                "confidence": 0.0,
                "key_indicators": ["text"],
                "integration_approach": "text"
            }
        },
        "structure_biodiversity_correlation": {
            "present": false,
            "confidence": 0.0,
            "key_indicators": ["text"],
            "details": "text"
        },
        "structure_to_biodiversity_causal": {
            "present": false,
            "confidence": 0.0,
            "key_indicators": ["text"],
            "details": "text"
        },
        "biodiversity_to_structure_causal": {
            "present": false,
            "confidence": 0.0,
            "key_indicators": ["text"],
            "details": "text"
        },
        "methodology": {
            "present": false,
            "confidence": 0.0,
            "key_indicators": ["text"]
        }
    }
}

Classification rules:
1. Papers can analyze structure/biodiversity in:
   - Vertical/3D dimension only
   - Horizontal/2D dimension only
   - Both dimensions with integration

2. Structure Analysis:
   - vertical_3d: 3D vegetation structure, vertical layers, height profiles
   - horizontal_2d: Cover, gaps, spatial patterns
   - combined_analysis: Integration of vertical and horizontal metrics

3. Biodiversity Analysis:
   - vertical_distribution: Species in 3D space, vertical stratification
   - horizontal_distribution: Spatial distribution, landscape patterns
   - multi_dimensional: Combined vertical and horizontal distribution

4. Structure-Biodiversity Relationships:
   - correlation: Statistical associations without mechanisms
   - structure_to_biodiversity_causal: Structure affecting biodiversity
   - biodiversity_to_structure_causal: Species affecting structure

5. Look for:
   - Multi-scale analyses
   - Interaction effects
   - Combined metrics
   - Cross-scale relationships
   - Clear evidence of causality vs correlation

Paper text to analyze:
"""
    return get_ai_response(prompt + text, client)

async def get_detailed_analysis(text, paper_categories, client):
    """Second stage: Get detailed analysis based on paper categories"""
    analysis_tasks = []
    
    # Always analyze study site and data collection
    base_tasks = [
        analyze_study_site(text, client),
        analyze_data_collection(text, client)
    ]
    analysis_tasks.extend(base_tasks)
    
    # Structure Analysis
    structure_cats = paper_categories['structure_analysis']
    if any(v['present'] for v in structure_cats.values()):
        structure_prompt = """Analyze structural aspects in detail:
        {
            "structure_details": {
                "vertical_methods": ["text"],
                "horizontal_methods": ["text"],
                "integration_approaches": ["text"],
                "spatial_scales": ["text"],
                "measurement_techniques": ["text"]
            }
        }
        """
        analysis_tasks.append(get_ai_response_async(structure_prompt + text, client))
    
    # Biodiversity Analysis
    bio_cats = paper_categories['biodiversity_analysis']
    if any(v['present'] for v in bio_cats.values()):
        analysis_tasks.extend([
            analyze_taxa(text, client),
            analyze_research_tasks(text, client)
        ])
    
    # Relationship Analysis
    if (paper_categories['structure_biodiversity_correlation']['present'] or
        paper_categories['structure_to_biodiversity_causal']['present'] or
        paper_categories['biodiversity_to_structure_causal']['present']):
        
        relationship_prompt = """Analyze structure-biodiversity relationships in detail:
        {
            "relationship_analysis": {
                "type": "correlation|structure_to_bio|bio_to_structure",
                "evidence_level": "statistical|experimental|observational",
                "structural_variables": ["text"],
                "biodiversity_variables": ["text"],
                "analysis_methods": ["text"],
                "causal_evidence": ["text"],
                "confounding_factors": ["text"],
                "limitations": ["text"]
            }
        }
        """
        analysis_tasks.extend([
            analyze_taxa(text, client),
            analyze_research_tasks(text, client),
            get_ai_response_async(relationship_prompt + text, client)
        ])
    
    # Run selected analyses in parallel
    results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
    
    # Combine results
    combined_results = {}
    for result in results:
        if isinstance(result, dict):
            combined_results.update(result)
    
    # Add paper categories to results
    combined_results['paper_categories'] = paper_categories
    
    return combined_results

async def combined_extraction_with_ai_async(text, client):
    """Modified two-stage analysis"""
    try:
        # Clean and truncate text
        truncated_text = text[:4000] if len(text) > 4000 else text
        clean_text = truncated_text.replace('"', "'").replace('\\', '/').replace('\r', ' ').replace('\n', ' ')
        
        # Stage 1: Determine paper type
        paper_categories = get_paper_type(clean_text, client)
        print(f"Analyzing paper categories: {', '.join([f'{k}: {v["present"]}' for k, v in paper_categories["paper_categories"].items()])}")
        
        # Stage 2: Get detailed analysis based on paper type
        analysis_results = await get_detailed_analysis(clean_text, paper_categories["paper_categories"], client)
        
        # Add paper type to results
        analysis_results['paper_categories'] = paper_categories["paper_categories"]
        
        # Validate results
        if not validate_research_categories(analysis_results):
            print("Retrying analysis due to validation failure...")
            return await combined_extraction_with_ai_async(text, client)
        
        return analysis_results
        
    except Exception as e:
        print(f"Error in AI extraction: {str(e)}")
        # Return error template...

def extract_pdf_info_async(pdf_path, client):
    """Updated to handle multiple categories"""
    try:
        # Open PDF file
        reader = PdfReader(pdf_path)
        
        # Extract text from all pages
        full_text = ""
        for page in reader.pages:
            try:
                full_text += page.extract_text() + "\n"
            except Exception as page_error:
                print(f"Error extracting text from page in {pdf_path}: {str(page_error)}")
                continue
        
        # Extract relevant sections
        relevant_text = extract_sections(full_text)
        
        # Get analysis results using two-stage approach
        analysis_results = await combined_extraction_with_ai_async(relevant_text, client)
        
        # Create base info dict
        info = {
            'filename': os.path.basename(pdf_path),
            'num_pages': len(reader.pages),
            'file_size': os.path.getsize(pdf_path) / 1024,
            # Add category flags
            'includes_structure_analysis': analysis_results['paper_categories']['structure_analysis']['present'],
            'structure_confidence': analysis_results['paper_categories']['structure_analysis']['confidence'],
            'includes_biodiversity_analysis': analysis_results['paper_categories']['biodiversity_analysis']['present'],
            'biodiversity_confidence': analysis_results['paper_categories']['biodiversity_analysis']['confidence'],
            'includes_relationship_analysis': analysis_results['paper_categories']['structure_biodiversity_relationship']['present'],
            'relationship_confidence': analysis_results['paper_categories']['structure_biodiversity_relationship']['confidence'],
            'includes_methodology': analysis_results['paper_categories']['methodology']['present'],
            'methodology_confidence': analysis_results['paper_categories']['methodology']['confidence'],
            'author': reader.metadata.get('/Author', ''),
            'creation_date': reader.metadata.get('/CreationDate', ''),
            'title': reader.metadata.get('/Title', ''),
            # Study site information
            'study_site': analysis_results['study_site']['location'],
            'study_area_size': analysis_results['study_site']['area_size'],
            'spatial_scale': analysis_results['study_site']['spatial_scale'],
            'text': relevant_text,
            # Taxa information
            'birds': analysis_results['taxa']['birds'],
            'bats': analysis_results['taxa']['bats'],
            'other_small_mammals': analysis_results['taxa']['other_small_mammals'],
            'reptiles': analysis_results['taxa']['reptiles'],
            'amphibians': analysis_results['taxa']['amphibians'],
            'invertebrates': analysis_results['taxa']['invertebrates'],
            'other_taxa': analysis_results['taxa']['other'],
            # Data collection information
            'airborne_lidar': analysis_results['data_collection']['airborne_lidar'],
            'spaceborne_lidar': analysis_results['data_collection']['spaceborne_lidar'],
            'terrestrial_lidar': analysis_results['data_collection']['terrestrial_lidar'],
            'structure_from_motion': analysis_results['data_collection']['structure_from_motion'],
            'field_data': analysis_results['data_collection']['field_data'],
            'other_remote_sensing': analysis_results['data_collection']['other_remote_sensing'],
            'other_rs_details': analysis_results['data_collection']['other_rs_details'],
            # Structure metrics
            'metric_cover_density': analysis_results['structure_metrics']['cover_density'],
            'metric_height': analysis_results['structure_metrics']['height'],
            'metric_horizontal_heterogeneity': analysis_results['structure_metrics']['horizontal_heterogeneity'],
            'metric_vertical_heterogeneity': analysis_results['structure_metrics']['vertical_heterogeneity'],
            'metric_landscape': analysis_results['structure_metrics']['landscape'],
            'metric_other': analysis_results['structure_metrics']['other'],
            'metric_other_details': analysis_results['structure_metrics']['other_details'],
            # Vertical stratification
            'uses_vertical_strata': analysis_results['vertical_stratification']['uses_strata'],
            'number_of_strata': analysis_results['vertical_stratification']['number_of_strata'],
            'strata_definition': analysis_results['vertical_stratification']['strata_definition'],
            # Special analyses
            'uses_viewshed': analysis_results['special_analyses']['uses_viewshed'],
            'uses_acoustic': analysis_results['special_analyses']['uses_acoustic'],
            
            # Research tasks with updated names
            'task_movement': analysis_results['research_tasks']['movement']['present'],
            'task_movement_details': analysis_results['research_tasks']['movement']['details'],
            'task_functional_trait': analysis_results['research_tasks']['functional_trait']['present'],
            'task_functional_trait_details': analysis_results['research_tasks']['functional_trait']['details'],
            'task_distribution_occupancy': analysis_results['research_tasks']['distribution_occupancy']['present'],
            'task_distribution_occupancy_details': analysis_results['research_tasks']['distribution_occupancy']['details'],
            'task_prevalence': analysis_results['research_tasks']['prevalence']['present'],
            'task_prevalence_details': analysis_results['research_tasks']['prevalence']['details'],
            'task_use_of_space': analysis_results['research_tasks']['use_of_space']['present'],
            'task_use_of_space_details': analysis_results['research_tasks']['use_of_space']['details'],
            'task_behaviors': analysis_results['research_tasks']['behaviors']['present'],
            'task_behaviors_details': analysis_results['research_tasks']['behaviors']['details'],
            'task_life_history': analysis_results['research_tasks']['life_history']['present'],
            'task_life_history_details': analysis_results['research_tasks']['life_history']['details'],
            'task_habitat_preference': analysis_results['research_tasks']['habitat_preference']['present'],
            'task_habitat_preference_details': analysis_results['research_tasks']['habitat_preference']['details'],
            'task_abundance_density': analysis_results['research_tasks']['abundance_density']['present'],
            'task_abundance_density_details': analysis_results['research_tasks']['abundance_density']['details'],
            'task_stratification_niche': analysis_results['research_tasks']['stratification_niche']['present'],
            'task_stratification_niche_details': analysis_results['research_tasks']['stratification_niche']['details'],
            'task_species_richness_diversity': analysis_results['research_tasks']['species_richness_diversity']['present'],
            'task_species_richness_diversity_details': analysis_results['research_tasks']['species_richness_diversity']['details'],
            'task_community_composition': analysis_results['research_tasks']['community_composition']['present'],
            'task_community_composition_details': analysis_results['research_tasks']['community_composition']['details'],
            'task_functional_richness_diversity': analysis_results['research_tasks']['functional_richness_diversity']['present'],
            'task_functional_richness_diversity_details': analysis_results['research_tasks']['functional_richness_diversity']['details'],
            'task_community_similarity': analysis_results['research_tasks']['community_similarity']['present'],
            'task_community_similarity_details': analysis_results['research_tasks']['community_similarity']['details'],
            'task_acoustic_characteristics': analysis_results['research_tasks']['acoustic_characteristics']['present'],
            'task_acoustic_characteristics_details': analysis_results['research_tasks']['acoustic_characteristics']['details'],
            'task_habitat_suitability': analysis_results['research_tasks']['habitat_suitability']['present'],
            'task_habitat_suitability_details': analysis_results['research_tasks']['habitat_suitability']['details'],
            # Research categories
            'structure_analysis_vertical_structure': analysis_results['research_categories']['structure_analysis']['vertical_structure'],
            'structure_analysis_vertical_strata': analysis_results['research_categories']['structure_analysis']['vertical_strata'],
            'structure_analysis_acoustic_analysis': analysis_results['research_categories']['structure_analysis']['acoustic_analysis'],
            'structure_analysis_visibility_analysis': analysis_results['research_categories']['structure_analysis']['visibility_analysis'],
            'biodiversity_analysis_vertical_distribution': analysis_results['research_categories']['biodiversity_analysis']['vertical_distribution'],
            'biodiversity_analysis_strata_specific': analysis_results['research_categories']['biodiversity_analysis']['strata_specific'],
            'biodiversity_analysis_acoustic_sampling': analysis_results['research_categories']['biodiversity_analysis']['acoustic_sampling'],
            'biodiversity_analysis_visibility_based': analysis_results['research_categories']['biodiversity_analysis']['visibility_based'],
            'structure_biodiversity_relationship_correlative': analysis_results['research_categories']['structure_biodiversity_relationship']['correlative'],
            'structure_biodiversity_relationship_causal': analysis_results['research_categories']['structure_biodiversity_relationship']['causal'],
            'structure_biodiversity_relationship_species_to_structure': analysis_results['research_categories']['structure_biodiversity_relationship']['species_to_structure'],
            'structure_biodiversity_relationship_details': analysis_results['research_categories']['structure_biodiversity_relationship']['details'],
            'external_factors_management': analysis_results['research_categories']['external_factors']['management'],
            'external_factors_disturbance': analysis_results['research_categories']['external_factors']['disturbance'],
            'external_factors_details': analysis_results['research_categories']['external_factors']['details']
        }
        
        # Add category-specific fields
        if analysis_results['paper_categories']['structure_biodiversity_relationship']['present']:
            if 'relationship_analysis' in analysis_results:
                info.update({
                    'structural_predictors': ', '.join(analysis_results['relationship_analysis']['structural_predictors']),
                    'biodiversity_responses': ', '.join(analysis_results['relationship_analysis']['biodiversity_responses']),
                    'statistical_methods': ', '.join(analysis_results['relationship_analysis']['statistical_methods'])
                })
        
        if analysis_results['paper_categories']['methodology']['present']:
            if 'methodology_details' in analysis_results:
                info.update({
                    'novel_methods': ', '.join(analysis_results['methodology_details']['novel_methods']),
                    'technical_improvements': ', '.join(analysis_results['methodology_details']['technical_improvements'])
                })
        
        return info
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None

async def process_pdf_batch(pdf_files, folder_path, client, batch_size=5):
    """Process a batch of PDFs in parallel"""
    tasks = []
    results = []
    
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        batch_tasks = []
        
        for pdf_file in batch:
            pdf_path = os.path.join(folder_path, pdf_file)
            task = asyncio.create_task(extract_pdf_info_async(pdf_path, client))
            batch_tasks.append(task)
        
        # Wait for batch to complete
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"Error processing PDF: {str(result)}")
            elif result is not None:
                results.append(result)
        
        # Small delay between batches
        await asyncio.sleep(1)
    
    return results

async def process_all_pdfs_async(folder_path, client):
    """Async version of process_all_pdfs"""
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Process PDFs in parallel batches
    results = await process_pdf_batch(pdf_files, folder_path, client)
    
    # Convert to DataFrame
    df = pd.DataFrame([r for r in results if r is not None])
    
    # Save results to CSV with additional safety measures
    output_file = os.path.join(root_path, 'pdf_information.csv')
    try:
        # First attempt with standard settings
        df.to_csv(output_file, 
                 index=False,
                 escapechar='\\',
                 encoding='utf-8',
                 quoting=csv.QUOTE_ALL)
    except Exception as e:
        print(f"First save attempt failed: {str(e)}")
        try:
            # Second attempt with more aggressive character handling
            df.to_csv(output_file,
                     index=False,
                     escapechar='\\',
                     encoding='utf-8-sig',  # Try with BOM
                     quoting=csv.QUOTE_ALL,
                     errors='replace')       # Replace problematic characters
        except Exception as e2:
            print(f"Second save attempt failed: {str(e2)}")
            # Last resort: try to clean the data first
            for column in df.columns:
                df[column] = df[column].astype(str).str.replace('\r\n', ' ').str.replace('\n', ' ')
            df.to_csv(output_file,
                     index=False,
                     encoding='utf-8',
                     quoting=csv.QUOTE_ALL)
    
    print(f"\nResults saved to {output_file}")
    
    # Update the research tasks summary printing
    print("\nResearch Tasks Summary:")
    task_mapping = {
        'task_movement': 'Movement',
        'task_functional_trait': 'Functional Traits',
        'task_distribution_occupancy': 'Distribution/Occupancy',
        'task_prevalence': 'Prevalence',
        'task_use_of_space': 'Use of Space',
        'task_behaviors': 'Behaviors',
        'task_life_history': 'Life History',
        'task_habitat_preference': 'Habitat Preference',
        'task_abundance_density': 'Abundance/Density',
        'task_stratification_niche': 'Stratification/Niche',
        'task_species_richness_diversity': 'Species Richness/Diversity',
        'task_community_composition': 'Community Composition',
        'task_functional_richness_diversity': 'Functional Richness/Diversity',
        'task_community_similarity': 'Community Similarity',
        'task_acoustic_characteristics': 'Acoustic Characteristics',
        'task_habitat_suitability': 'Habitat Suitability'
    }
    
    for task_col, task_name in task_mapping.items():
        if task_col in df.columns:
            count = df[task_col].sum()
            print(f"{task_name}: {count} papers")
            
            # Print details for papers that performed this task
            if count > 0:
                details_col = f"{task_col}_details"
                if details_col in df.columns:
                    task_details = df[df[task_col]][details_col]
                    if not task_details.empty:
                        print("Details:")
                        for detail in task_details.unique():
                            if detail != 'none' and detail != 'error in extraction':
                                print(f"  - {detail}")
                        print()

    # Print research categories summary
    print("\nResearch Categories Summary:")
    
    print("\n1. Structure Analysis:")
    structure_columns = ['structure_analysis_vertical_structure', 'structure_analysis_vertical_strata',
                        'structure_analysis_acoustic_analysis', 'structure_analysis_visibility_analysis']
    for col in structure_columns:
        count = df[col].sum()
        print(f"{col.replace('structure_analysis_', '').replace('_', ' ').title()}: {count} papers")
    
    print("\n2. Biodiversity Analysis:")
    biodiversity_columns = ['biodiversity_analysis_vertical_distribution', 'biodiversity_analysis_strata_specific',
                          'biodiversity_analysis_acoustic_sampling', 'biodiversity_analysis_visibility_based']
    for col in biodiversity_columns:
        count = df[col].sum()
        print(f"{col.replace('biodiversity_analysis_', '').replace('_', ' ').title()}: {count} papers")
    
    print("\n3. Structure-Biodiversity Relationship:")
    relationship_columns = ['structure_biodiversity_relationship_correlative',
                          'structure_biodiversity_relationship_causal',
                          'structure_biodiversity_relationship_species_to_structure']
    for col in relationship_columns:
        count = df[col].sum()
        print(f"{col.replace('structure_biodiversity_relationship_', '').replace('_', ' ').title()}: {count} papers")
        if count > 0:
            details = df[df[col]]['structure_biodiversity_relationship_details']
            if not details.empty:
                print("Details:")
                for detail in details.unique():
                    if detail != 'error' and detail != 'none':
                        print(f"  - {detail}")
    
    print("\n4. External Factors:")
    external_columns = ['external_factors_management', 'external_factors_disturbance']
    for col in external_columns:
        count = df[col].sum()
        print(f"{col.replace('external_factors_', '').replace('_', ' ').title()}: {count} papers")
        if count > 0:
            details = df[df[col]]['external_factors_details']
            if not details.empty:
                print("Details:")
                for detail in details.unique():
                    if detail != 'error' and detail != 'none':
                        print(f"  - {detail}")

    return df

def process_all_pdfs(folder_path, client):
    """Synchronous wrapper for async processing"""
    return asyncio.run(process_all_pdfs_async(folder_path, client))

async def analyze_paper(pdf_text: str, client) -> Dict[str, Any]:
    """Analyze a single paper"""
    # Get paper type
    paper_categories = await get_paper_type(pdf_text, client)
    
    # Get detailed analysis
    detailed_results = await get_detailed_analysis(pdf_text, paper_categories['paper_categories'], client)
    
    # Combine results
    results = {**paper_categories, **detailed_results}
    return results

async def process_papers(pdf_files: List[str]) -> List[Dict[str, Any]]:
    """Process multiple papers"""
    client = init_client()
    results = []
    
    for pdf_file in pdf_files:
        try:
            # Read PDF text
            with open(pdf_file, 'r', encoding='utf-8') as f:
                pdf_text = f.read()
            
            print(f"\nProcessing: {pdf_file}")
            paper_results = await analyze_paper(pdf_text, client)
            results.append(paper_results)
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
    
    return results

async def main():
    """Main execution function"""
    # Directory containing PDF files
    pdf_dir = os.path.join(ROOT_PATH, "data/pdfs")
    
    # Get list of PDF files
    pdf_files = [
        os.path.join(pdf_dir, f) 
        for f in os.listdir(pdf_dir) 
        if f.endswith('.txt')  # Using .txt for now
    ]
    
    # Process papers
    results = await process_papers(pdf_files)
    
    # Save results
    save_results(results, "output/analysis_results.csv")
    
    # Print summaries
    print_summaries(results)

if __name__ == "__main__":
    asyncio.run(main())
