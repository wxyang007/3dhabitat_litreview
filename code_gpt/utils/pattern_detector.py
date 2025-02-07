"""Pattern detection utilities for metrics and research tasks"""
import re
from typing import Dict, Tuple

METRIC_PATTERNS = {
    "cover_density": r'\b(basal\s+area|canopy[\s\n]*cover|tree\s+density|stem\s+density|stand\s+density|crown\s+cover|' + 
                    r'vegetation\s+volume|crown\s+diameter|gap[s]?\b|openness|' +
                    r'shrub\s+(?:density|cover)|understor[ey]\s+cover)',
    "height": r'\b(canopy\s+height|tree\s+height|vegetation\s+height|height\s+profile|height\s+distribution)',
    "horizontal_heterogeneity": r'\b(gap\s+distribution|spatial\s+pattern|horizontal\s+structure|canopy\s+gaps|spatial\s+heterogeneity)',
    "vertical_heterogeneity": r'\b(vertical\s+stratification|layering|vertical\s+profile|vertical\s+distribution|foliage\s+height\s+diversity)', # add foliage height diversity
    "landscape": r'\b(patch\s+size|fragmentation|connectivity|landscape\s+heterogeneity|landscape\s+pattern|landscape\s+metric)'
}

# not that for certain tasks, as long as its words get detected, it definitely exists for animal species
# for others like abundance, it might be for vegetation
TASK_PATTERNS = {
    # "species_richness": r'\b(species\s+richness|species\s+diversity|biodiversity|species\s+number)',
    # "abundance": r'\b(abundance|density|population\s+size|number\s+of\s+individuals)',
    # "occurrence_distribution": r'\b(occurrence|distribution|presence|absence|habitat\s+use)',
    # "community_composition": r'\b(community\s+composition|species\s+composition|assemblage|community\s+structure)',
    # "functional_diversity": r'\b(functional\s+diversity|trait|functional\s+group|guild)',
    # "beta_diversity": r'\b(beta\s+diversity|species\s+turnover|community\s+similarity)',
    # "stratification_niche": r'\b(stratification|vertical\s+niche|height\s+preference|vertical\s+partitioning)',
    # "movement": r'\b(movement|dispersal|migration|home\s+range|territory)',
    # "behavior": r'\b(behavior|foraging|social\s+interaction|predation)',
    # "habitat_preference": r'\b(habitat\s+preference|site\s+selection|habitat\s+choice|habitat\s+selection)',
    # "habitat_suitability": r'\b(habitat\s+suitability|habitat\s+quality|habitat\s+model)',
    # "survival_mortality": r'\b(survival|mortality|death\s+rate|survival\s+rate)',
    # "acoustic_characteristics": r'\b(acoustic|vocal|song|call)'
    "major_tasks": r'\b(major\s+tasks|major\s+research\s+tasks|major\s+research\s+questions|major\s+research\s+objectives)',
    "acoustic_monitoring": r'\b(acoustic\s+monitoring|acoustic\s+data|acoustic\s+data\s+collection|acoustic\s+data\s+analysis)',
    "vertical_movement": r'\b(vertical\s+movement|vertical\s+movement\s+studies|vertical\s+movement\s+analysis|vertical\s+movement\s+patterns)' 
}

def detect_metrics(text: str) -> Tuple[Dict[str, bool], Dict[str, str]]:
    """
    Detect structure metrics using regex patterns
    Returns: (detection_results, evidence_snippets)
    """
    
    results = {}
    evidence = {}
    
    for metric, pattern in METRIC_PATTERNS.items():
        match = re.search(pattern, text, re.I)
        results[metric] = bool(match)
        if match:
            # Just use the entire methods section as evidence
            evidence[metric] = text.strip()[:50]
    
    return results, evidence

def detect_research_tasks(text: str) -> Tuple[Dict[str, bool], Dict[str, str]]:
    """
    Detect animal research tasks using regex patterns
    Returns: (detection_results, evidence_snippets)
    """
    results = {}
    evidence = {}
    
    for task, pattern in TASK_PATTERNS.items():
        match = re.search(pattern, text, re.I)
        results[task] = bool(match)
        if match:
            start = max(0, match.start() - 4000)
            end = min(len(text), match.end() + 4000)
            evidence[task] = text[start:end].strip()
    
    return results, evidence 