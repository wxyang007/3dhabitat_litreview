"""Method detection utilities"""
import re
from typing import Dict, Tuple
import logging
from config import METHOD_TYPES

logger = logging.getLogger(__name__)

__all__ = ['detect_methods']

def detect_methods(text: str) -> Tuple[Dict[str, bool], Dict[str, str]]:
    """
    Detect data collection methods using regex patterns
    Returns: (detection_results, evidence_snippets)
    """
    # Store both detection results and text evidence
    results = {}
    evidence = {}
    
    patterns = {
        # Use method keys from config
        "airborne_lidar": r'\b(ALS|aerial\s+li?dar|airborne\s+laser|airborne\s+scanning|aerial\s+laser\s+scan)',
        "terrestrial_lidar": r'\b(TLS|terrestrial\s+li?dar|ground.based\s+laser|ground.based\s+scan)',
        "spaceborne_lidar": r'\b(GEDI|ICESat-?\d*|satellite\s+li?dar|space.borne\s+laser)',
        "structure_from_motion": r'\b(SfM|structure.from.motion|photogrammetr\w+|drone\s+imagery|UAV\s+imag|UAS)',
        "field_sampling": r'\b(field\s+plot|transect|field\s+measurement|ground\s+measurement|field\s+survey)',
        "other_remote_sensing": r'\b(radar|optical\s+satellite|multispectral|hyperspectral|Landsat|Sentinel)',
        "other_field": r'\b(visual\s+assessment|hemispherical|clinometer|dendrometer|field\s+observation)'
    }
    
    # Only detect configured methods
    valid_methods = [method_key for _, method_key in METHOD_TYPES]
    for method in valid_methods:
        if method in patterns:
            match = re.search(patterns[method], text, re.I)
            results[method] = bool(match)
            if match:
                # Use 4000 character context for regex evidence
                start = max(0, match.start() - 4000)
                end = min(len(text), match.end() + 4000)
                evidence[method] = text[start:end].strip()
        else:
            logger.warning(f"No pattern defined for method: {method}")
            results[method] = False
    
    return results, evidence 