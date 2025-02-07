"""Validation utilities for reporting and monitoring purposes"""
from typing import Dict, Any, List
from config import (
    ANALYSIS_CATEGORIES,
    RELATIONSHIP_CATEGORIES,
    VALID_TAXA,
    RESEARCH_TASKS,
    METHOD_TYPES
)

__all__ = [
    'validate_research_categories',
    'validate_analysis_categories',
    'validate_taxa',
    'validate_research_tasks',
    'validate_method_detection',
    'validate_method_names'
]

def validate_research_categories(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate research categories and add validation flags
    Returns the results with added validation flags
    """
    validation_flags = {
        "combined_analysis_valid": True,
        "multi_dimensional_valid": True,
        "relationship_evidence_valid": True
    }
    
    try:
        categories = analysis_results['paper_categories']
        
        # Update relationship validation
        if categories['effect_structure_on_biodiversity']['present'] or \
           categories['effect_biodiversity_on_structure']['present']:
            # Check for mechanism testing
            if 'relationship_details' in analysis_results:
                mech_testing = analysis_results['relationship_details']['mechanism_testing']
                validation_flags["relationship_evidence_valid"] = mech_testing['present']
        
        # Add validation flags to results
        analysis_results['validation_flags'] = validation_flags
        return analysis_results
        
    except Exception as e:
        print(f"Validation error: {str(e)}")
        analysis_results['validation_flags'] = {k: False for k in validation_flags}
        return analysis_results

def validate_analysis_categories(categories: Dict[str, Any]) -> bool:
    """
    Validate analysis categories match expected structure.
    For reporting purposes only - does not modify GPT results.
    """
    for category_type, valid_values in ANALYSIS_CATEGORIES.items():
        if category_type not in categories:
            return False
        for value in valid_values:
            if value not in categories[category_type]:
                return False
    return True

def validate_taxa(taxa: List[str]) -> bool:
    """
    Validate taxa are from allowed list.
    For reporting purposes only - does not modify GPT results.
    """
    return all(taxon in VALID_TAXA for taxon in taxa)

def validate_research_tasks(tasks: Dict[str, Any]) -> bool:
    """
    Validate research tasks match expected list.
    For reporting purposes only - does not modify GPT results.
    """
    return all(task in RESEARCH_TASKS for task in tasks)

def validate_method_detection(detection_comparison: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """
    Compare regex and GPT method detection results.
    For reporting purposes only - does not modify results.
    """
    agreement_stats = {}
    for method, details in detection_comparison.items():
        regex = details.get('regex_detected', False)
        gpt = details.get('gpt_detected', False)
        agreement_stats[method] = 1.0 if regex == gpt else 0.0
    
    return agreement_stats

def validate_method_names(methods: Dict[str, Any]) -> bool:
    """
    Validate that all method names match the configured types.
    For reporting purposes only - does not modify results.
    """
    valid_methods = [method_key for _, method_key in METHOD_TYPES]
    return all(method in valid_methods for method in methods)