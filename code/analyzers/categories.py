"""Paper category analysis"""
from typing import Dict, Any
from utils.ai_client import get_ai_response_async
from config import METHOD_TYPES, ANALYSIS_CATEGORIES, RELATIONSHIP_CATEGORIES, VALID_TAXA, RESEARCH_TASKS
from utils.method_detector import detect_methods
from utils.pattern_detector import detect_metrics, detect_research_tasks
import logging

__all__ = ['get_combined_analysis']

logger = logging.getLogger(__name__)

async def get_paper_type(text: str, client) -> Dict[str, Any]:
    """Determine paper categories"""
    prompt = """Classify paper into these categories:
1. Structure: vertical_3d, horizontal_2d, or combined_analysis
2. Animal biodiversity: vertical_3d, horizontal_2d, or combined_analysis
3. Structure-animal relationships: 
   - correlation: statistical associations
   - effect_structure_on_animals: how structure affects animal distribution/behavior
   - effect_animals_on_structure: how animals affect structure

Return JSON:
{
    "paper_categories": {
        "structure_analysis": {
            "vertical_3d": {"present": false, "confidence": 0.0},
            "horizontal_2d": {"present": false, "confidence": 0.0}
        },
        "animal_biodiversity": {
            "vertical_3d": {"present": false, "confidence": 0.0},
            "horizontal_2d": {"present": false, "confidence": 0.0}
        },
        "structure_animal_correlation": {"present": false, "confidence": 0.0},
        "effect_structure_on_animals": {"present": false, "confidence": 0.0},
        "effect_animals_on_structure": {"present": false, "confidence": 0.0}
    }
}"""
    return await get_ai_response_async(prompt + text, client)

async def get_detailed_analysis(text: str, paper_categories: Dict[str, Any], client) -> Dict[str, Any]:
    """Get detailed analysis based on paper categories"""
    # Get regex results but don't add to prompt
    regex_results, evidence = detect_methods(text)
    
    analysis_prompt = """Analyze paper for:
1. Study site: 
   - Country: Infer from any location information (city, region, protected area, etc.)
   - Habitat type
   - Scale category (plot|stand|landscape|regional|national|global)

2. Methods used

3. Structure metrics: cover_density, height, horizontal_heterogeneity, vertical_heterogeneity, landscape

4. Animal Analysis:
   - Taxa studied (must be one or more of: birds, bats, primates, other_mammals, amphibians, reptiles, invertebrates)
   - Animal sampling methods
   - Animal research tasks:
      * Species richness/diversity
      * Abundance/Density
      * Occurrence/Distribution: presence/absence, occupancy, prevalence, spatial distribution
      * Community composition: species composition, assemblage structure
      * Functional diversity: trait diversity, guilds
      * Beta diversity: species turnover, community similarity
      * Stratification/Niche: vertical stratification, niche segregation
      * Movement: animal movement patterns, home range, dispersal
      * Behavior: foraging behavior, social interactions, predation rate
      * Habitat preference: site selection, height preferences, cover preferences
      * Habitat suitability: habitat quality, suitability modeling, connectivity
      * Survival/Mortality: survival rates, mortality factors
      * Acoustic characteristics: acoustic activity, vocal behavior

Return JSON:
{
    "study_site": {
        "location": {
            "country": "text",          # Inferred from any location information
            "habitat_type": ["text"]
        },
        "spatial_scale": {"scale_category": "text"}
    },
    "structure_details": {
        "data_collection": {
            "methods": {
                "airborne_lidar": {"present": false},
                "terrestrial_lidar": {"present": false},
                "spaceborne_lidar": {"present": false},
                "structure_from_motion": {"present": false},
                "field_sampling": {"present": false},
                "other_remote_sensing": {"present": false},
                "other_field": {"present": false}
            }
        },
        "metrics": {
            "cover_density": {"present": false, "metrics_used": ["text"]},
            "height": {"present": false, "metrics_used": ["text"]},
            "horizontal_heterogeneity": {"present": false, "metrics_used": ["text"]},
            "vertical_heterogeneity": {"present": false, "metrics_used": ["text"]},
            "landscape": {"present": false, "metrics_used": ["text"]}
        }
    },
    "animal_details": {
        "taxa_studied": ["text"],  # Array of taxa from: birds, bats, primates, other_mammals, amphibians, reptiles, invertebrates
        "sampling_methods": ["text"],
        "research_tasks": {
            "species_richness": {"present": false, "metrics_used": ["text"]},
            "abundance": {"present": false, "metrics_used": ["text"]},
            "occurrence_distribution": {"present": false, "metrics_used": ["text"]},
            "community_composition": {"present": false, "metrics_used": ["text"]},
            "functional_diversity": {"present": false, "metrics_used": ["text"]},
            "beta_diversity": {"present": false, "metrics_used": ["text"]},
            "stratification_niche": {"present": false, "metrics_used": ["text"]},
            "movement": {"present": false, "metrics_used": ["text"]},
            "behavior": {"present": false, "metrics_used": ["text"]},
            "habitat_preference": {"present": false, "metrics_used": ["text"]},
            "habitat_suitability": {"present": false, "metrics_used": ["text"]},
            "survival_mortality": {"present": false, "metrics_used": ["text"]},
            "acoustic_characteristics": {"present": false, "metrics_used": ["text"]}
        }
    }
}"""

    detailed_results = await get_ai_response_async(analysis_prompt + text, client)
    
    # Add detection comparison section without influencing GPT analysis
    methods_section = detailed_results["structure_details"]["data_collection"]["methods"]
    methods_section["detection_comparison"] = {
        method_key: {
            "regex_detected": regex_results.get(method_key, False),
            "gpt_detected": methods_section.get(method_key, {}).get("present", False) if method_key in methods_section else False,
            "evidence": evidence.get(method_key, "") if regex_results.get(method_key, False) else ""
        }
        for _, method_key in METHOD_TYPES
    }
    
    # Add relationship analysis if relationships present
    if any(paper_categories[rel_type]['present'] for rel_type in RELATIONSHIP_CATEGORIES):
        relationship_prompt = """Analyze structure-animal relationships in detail.

Look for these types of mechanism testing/causal methods:
1. Experimental:
   - Manipulative experiments
   - Before-after studies
   - Control-impact designs
   
2. Natural experiments:
   - Disturbance events
   - Gradients
   - Chronosequences

3. Statistical/Modeling:
   - Path analysis
   - Structural equation modeling
   - Causal inference methods

Return JSON:
{
    "relationship_details": {
        "mechanism_testing": {
            "present": false,
            "methods": ["text"],           # experimental/observational methods used
            "mechanisms_tested": ["text"],  # specific mechanisms investigated
            "evidence_type": {             # Types of evidence provided
                "experimental": false,      # e.g., experimental manipulation of structure
                "natural_experiment": false, # e.g., comparing different structural conditions
                "statistical": false       # e.g., correlation, regression, path analysis
            }
        }
    }
}"""
        relationship_results = await get_ai_response_async(relationship_prompt + text, client)
        detailed_results.update(relationship_results)
    
    return detailed_results

async def get_combined_analysis(text: str, regex_text: str, client) -> Dict[str, Any]:
    """Combined paper analysis in a single call"""
    # Get regex results first
    regex_results, evidence = detect_methods(text)
    metric_results, metric_evidence = detect_metrics(regex_text)
    task_results, task_evidence = detect_research_tasks(text)
    
    prompt = """Analyze this research paper comprehensively, focusing on structure and animal biodiversity. For each category, assign a confidence score (0.0-1.0) based on how clearly the paper fits that category.

1. Paper Categories (with confidence scores):
    - Structure analysis - assign confidence to ONE of:
      * vertical_3d: Analysis focuses on vertical/3D structure
      * horizontal_2d: Analysis focuses on horizontal/2D structure
    
    - Animal biodiversity analysis - assign confidence to ONE of:
      * vertical_3d: Study examines vertical distribution/movement of animals
      * horizontal_2d: Study examines horizontal distribution/movement
    
    - Structure-animal relationships:
      * correlation
      * effect_structure_on_animals
      * effect_animals_on_structure

2. Study Details:
   - Location (country, habitat_type)
   - Spatial scale (plot|stand|landscape|regional|national|global)

3. Structure Analysis:
   - Data collection methods
   - Structure metrics: 
      * cover_density: basal area, canopy cover, tree density, etc.
      * height
      * horizontal_heterogeneity
      * vertical_heterogeneity
      * landscape
   - Integration approaches

4. Animal Analysis:
   - Taxa studied (must be one or more of: birds, bats, primates, other_mammals, amphibians, reptiles, invertebrates)
   - Animal sampling methods
   - Animal research tasks:
      * Species richness/diversity
      * Abundance/Density
      * Occurrence/Distribution: presence/absence, occupancy, prevalence, spatial distribution
      * Community composition: species composition, assemblage structure
      * Functional diversity: trait diversity, guilds
      * Beta diversity: species turnover, community similarity
      * Stratification/Niche: vertical stratification, niche segregation
      * Movement: animal movement patterns, home range, dispersal
      * Behavior: foraging behavior, social interactions, predation rate
      * Habitat preference: site selection, height preferences, cover preferences
      * Habitat suitability: habitat quality, suitability modeling, connectivity, habitat suitab
      * Survival/Mortality: survival rates, mortality factors
      * Acoustic characteristics: acoustic activity, vocal behavior

Note: Only include analysis of animal biodiversity. Exclude any plant biodiversity analysis.

Return JSON:
{
    "paper_categories": {
        "structure_analysis": {
            "vertical_3d": {"present": false, "confidence": 0.0},
            "horizontal_2d": {"present": false, "confidence": 0.0}
        },
        "animal_biodiversity": {
            "vertical_3d": {"present": false, "confidence": 0.0},
            "horizontal_2d": {"present": false, "confidence": 0.0}
        },
        "structure_animal_correlation": {"present": false, "confidence": 0.0},
        "effect_structure_on_animals": {"present": false, "confidence": 0.0},
        "effect_animals_on_structure": {"present": false, "confidence": 0.0}
    },
    "study_site": {
        "location": {
            "country": "text",          # Inferred from any location information
            "habitat_type": ["text"]
        },
        "spatial_scale": {"scale_category": "text"}
    },
    "structure_details": {
        "data_collection": {
            "methods": {
                "airborne_lidar": {"present": false},
                "terrestrial_lidar": {"present": false},
                "spaceborne_lidar": {"present": false},
                "structure_from_motion": {"present": false},
                "field_sampling": {"present": false},
                "other_remote_sensing": {"present": false},
                "other_field": {"present": false}
            }
        },
        "metrics": {
            "cover_density": {"present": false, "metrics_used": ["text"]},
            "height": {"present": false, "metrics_used": ["text"]},
            "horizontal_heterogeneity": {"present": false, "metrics_used": ["text"]},
            "vertical_heterogeneity": {"present": false, "metrics_used": ["text"]},
            "landscape": {"present": false, "metrics_used": ["text"]}
        }
    },
    "animal_details": {
        "taxa_studied": ["text"],  # Array of taxa from: birds, bats, primates, other_mammals, amphibians, reptiles, invertebrates
        "sampling_methods": ["text"],
        "research_tasks": {
            "species_richness": {"present": false, "metrics_used": ["text"]},
            "abundance": {"present": false, "metrics_used": ["text"]},
            "occurrence_distribution": {"present": false, "metrics_used": ["text"]},
            "community_composition": {"present": false, "metrics_used": ["text"]},
            "functional_diversity": {"present": false, "metrics_used": ["text"]},
            "beta_diversity": {"present": false, "metrics_used": ["text"]},
            "stratification_niche": {"present": false, "metrics_used": ["text"]},
            "movement": {"present": false, "metrics_used": ["text"]},
            "behavior": {"present": false, "metrics_used": ["text"]},
            "habitat_preference": {"present": false, "metrics_used": ["text"]},
            "habitat_suitability": {"present": false, "metrics_used": ["text"]},
            "survival_mortality": {"present": false, "metrics_used": ["text"]},
            "acoustic_characteristics": {"present": false, "metrics_used": ["text"]}
        }
    },
    "relationship_details": {
        "mechanism_testing": {
            "present": false,
            "methods": ["text"],           # experimental/observational methods used
            "mechanisms_tested": ["text"],  # specific mechanisms investigated
            "evidence_type": {             # Types of evidence provided
                "experimental": false,      # e.g., experimental manipulation of structure
                "natural_experiment": false, # e.g., comparing different structural conditions
                "statistical": false       # e.g., correlation, regression, path analysis
            }
        }
    }
}

Notes:
- For relationships, assign confidence independently for each type
- Base confidence scores on explicit evidence in the text
"""

    # Get GPT analysis
    gpt_results = await get_ai_response_async(prompt + text, client)
    
    # Ensure methods section exists
    if "structure_details" not in gpt_results:
        gpt_results["structure_details"] = {}
    if "data_collection" not in gpt_results["structure_details"]:
        gpt_results["structure_details"]["data_collection"] = {}
    if "methods" not in gpt_results["structure_details"]["data_collection"]:
        gpt_results["structure_details"]["data_collection"]["methods"] = {}
    
    methods_section = gpt_results["structure_details"]["data_collection"]["methods"]
    
    # Add detection comparison using consistent method names
    methods_section["detection_comparison"] = {
        method_key: {
            "regex_detected": regex_results.get(method_key, False),
            "gpt_detected": methods_section.get(method_key, {}).get("present", False) if method_key in methods_section else False,
            "evidence": evidence.get(method_key, "") if regex_results.get(method_key, False) else ""
        }
        for _, method_key in METHOD_TYPES
    }
    
    # Add metric detection with consistent structure
    if "metrics" not in gpt_results["structure_details"]:
        gpt_results["structure_details"]["metrics"] = {}
        
    metrics_section = gpt_results["structure_details"]["metrics"]
    for metric in metric_results:
        if metric not in metrics_section:
            metrics_section[metric] = {
                "present": False,
                "regex_detected": False,
                "evidence": "",
                "metrics_used": []
            }
        # Update values from regex detection
        metrics_section[metric]["present"] = metric_results[metric]
        metrics_section[metric]["regex_detected"] = metric_results[metric]
        if metric_evidence.get(metric):
            metrics_section[metric]["evidence"] = metric_evidence[metric]
    
    # Add task detection
    if "animal_details" not in gpt_results:
        gpt_results["animal_details"] = {}
    if "research_tasks" not in gpt_results["animal_details"]:
        gpt_results["animal_details"]["research_tasks"] = {}
        
    tasks_section = gpt_results["animal_details"]["research_tasks"]
    for task in task_results:
        if task not in tasks_section:
            tasks_section[task] = {
                "present": False,
                "regex_detected": False,
                "evidence": "",
                "metrics_used": []
            }
        tasks_section[task]["present"] = task_results[task]
        tasks_section[task]["regex_detected"] = task_results[task]
        if task_evidence.get(task):
            tasks_section[task]["evidence"] = task_evidence[task]
    
    return gpt_results 