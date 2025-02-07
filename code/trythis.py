from semanticscholar import SemanticScholar
import spacy
import re
from typing import Dict, List, Set

sch = SemanticScholar()


def analyze_text_for_study_info(text: str) -> Dict:
    """
    Analyze text to extract study locations and taxa using natural language understanding.
    """
    # List of location-indicating phrases
    location_indicators = [
        "study site",
        "study area",
        "field site",
        "sampling site",
        "conducted in",
        "located in",
        "carried out in",
        "performed in",
        "collected from",
        "samples from",
        "specimens from"
    ]

    # List of taxa-indicating phrases
    taxa_indicators = [
        "species",
        "genus",
        "family",
        "specimens of",
        "populations of",
        "individuals of",
        "observed",
        "surveyed",
        "sampled",
        "collected"
    ]

    # Extract sentences that likely contain location information
    location_sentences = []
    taxa_sentences = []

    # Split text into sentences (simple approach)
    sentences = [s.strip() for s in text.split('.') if s.strip()]

    for sentence in sentences:
        # Check for location indicators
        if any(indicator.lower() in sentence.lower() for indicator in location_indicators):
            location_sentences.append(sentence)

        # Check for taxa indicators
        if any(indicator.lower() in sentence.lower() for indicator in taxa_indicators):
            taxa_sentences.append(sentence)

    # Find scientific names (improved pattern)
    scientific_pattern = r'([A-Z][a-z]+\s+(?:[a-z]+\s*(?:var\.|subsp\.|sp\.|spp\.|)\s*[a-z]*\b))'
    potential_taxa = set(re.findall(scientific_pattern, text))

    # Find common names (capitalized species names often used in papers)
    common_name_pattern = r'(?<=[^A-Za-z])([A-Z][a-z]+(?:\s+[a-z]+)?(?=\s+(?:population|individual|specimen|species)))'
    common_names = set(re.findall(common_name_pattern, text))

    return {
        'location_context': location_sentences,
        'taxa_context': taxa_sentences,
        'scientific_names': list(potential_taxa),
        'common_names': list(common_names)
    }


def extract_paper_info(paper_id: str) -> Dict:
    """Extract relevant information from a paper."""
    try:
        paper = sch.get_paper(paper_id)
        text = f"{paper.title if hasattr(paper, 'title') else ''} {paper.abstract if hasattr(paper, 'abstract') else ''}"
        study_info = analyze_text_for_study_info(text)

        return {
            'title': paper.title if hasattr(paper, 'title') else '',
            'year': paper.year if hasattr(paper, 'year') else None,
            'authors': [author.name for author in paper.authors] if hasattr(paper, 'authors') else [],
            'locations_context': study_info['location_context'],
            'taxa_context': study_info['taxa_context'],
            'scientific_names': study_info['scientific_names'],
            'common_names': study_info['common_names']
        }
    except Exception as e:
        print(f"Error fetching paper {paper_id}: {e}")
        return None


def process_multiple_papers(paper_ids: List[str]) -> List[Dict]:
    """Process multiple papers and extract relevant information."""
    results = []

    for paper_id in paper_ids:
        paper_info = extract_paper_info(paper_id)
        if paper_info:
            results.append(paper_info)

    return results


# Example usage
if __name__ == "__main__":
    paper_ids = [
        '10.1016/j.rse.2006.11.016',
        '10.1890/09-1670.1'
    ]

    results = process_multiple_papers(paper_ids)

    # Print results in a more detailed format
    for paper in results:
        print("\nPaper:", paper['title'])
        print("Year:", paper['year'])
        print("\nLocation Context:")
        for loc in paper['locations_context']:
            print(f"- {loc.strip()}")
        print("\nTaxa Context:")
        for taxa in paper['taxa_context']:
            print(f"- {taxa.strip()}")
        print("\nScientific Names Found:", ', '.join(paper['scientific_names']))
        print("Common Names Found:", ', '.join(paper['common_names']))
        print("Authors:", ', '.join(paper['authors']))
        print("-" * 80)