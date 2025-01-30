"""Data processing utilities"""
import pandas as pd
import os
from typing import List, Dict, Any
import csv
import logging
from config import METHOD_TYPES, RESEARCH_TASKS

logger = logging.getLogger(__name__)

__all__ = ['save_results', 'print_summaries']

def save_results(results: List[Dict[str, Any]], output_file: str) -> None:
    """Save analysis results to CSV with flattened structure"""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if not results:
        logger.warning("No results to save")
        return
    
    # Flatten nested dictionaries
    flattened_results = []
    for result in results:
        flat_dict = {}
        
        # Add metadata with clearer names
        flat_dict['File_Name'] = result.get('filename', '')
        flat_dict['Number_of_Pages'] = result.get('num_pages', 0)
        flat_dict['File_Size_KB'] = result.get('file_size', 0)
        
        # Paper categories with clearer names
        cats = result.get('paper_categories', {})
        for analysis_type, prefix in [
            ('structure_analysis', 'Structure_'),
            ('animal_biodiversity', 'Animal_')
        ]:
            if analysis_type in cats:
                for key, value in cats[analysis_type].items():
                    flat_dict[f'{prefix}{key}'] = value.get('present', False)
                    flat_dict[f'{prefix}{key}_Confidence'] = value.get('confidence', 0.0)
        
        # Relationship categories with clearer names
        for rel_type in ['structure_animal_correlation',
                        'effect_structure_on_animals',
                        'effect_animals_on_structure']:
            if rel_type in cats:
                clean_name = rel_type.replace('_', ' ').title()
                flat_dict[f'Relationship_{clean_name}'] = cats[rel_type].get('present', False)
                flat_dict[f'Relationship_{clean_name}_Confidence'] = cats[rel_type].get('confidence', 0.0)
        
        # Study site with clearer names
        site = result.get('study_site', {})
        flat_dict['Study_Country'] = site.get('location', {}).get('country', '')
        flat_dict['Habitat_Types'] = ', '.join(site.get('location', {}).get('habitat_type', []))
        flat_dict['Spatial_Scale'] = site.get('spatial_scale', {}).get('scale_category', '')
        
        # Structure methods with both detections
        struct = result.get('structure_details', {})
        methods = struct.get('data_collection', {}).get('methods', {})
        detection_comparison = methods.get('detection_comparison', {})
        
        for _, method_key in METHOD_TYPES:
            details = detection_comparison.get(method_key, {})
            clean_name = method_key.replace('_', ' ').title()
            flat_dict[f'Method_{clean_name}_Regex'] = details.get('regex_detected', False)
            flat_dict[f'Method_{clean_name}_GPT'] = details.get('gpt_detected', False)
            if details.get('evidence'):
                flat_dict[f'Method_{clean_name}_Evidence'] = details['evidence']
        
        # Structure metrics with clearer names
        metrics = struct.get('metrics', {})
        for metric in ["cover_density", "height", "horizontal_heterogeneity", "vertical_heterogeneity", "landscape"]:
            clean_name = metric.replace('_', ' ').title()
            details = metrics.get(metric, {})
            
            # Ensure all fields exist with default values
            flat_dict[f'Metric_{clean_name}_Present'] = details.get('present', False)
            flat_dict[f'Metric_{clean_name}_Regex'] = details.get('regex_detected', False)
            
            # Clean up evidence field
            evidence = details.get('evidence', '')
            if evidence:
                # Remove newlines and limit length
                evidence = evidence.replace('\n', ' ').strip()
                evidence = evidence[:100]  # Limit length to avoid CSV issues
            flat_dict[f'Metric_{clean_name}_Evidence'] = evidence
            
            # Handle metrics_used field
            metrics_used = details.get('metrics_used', [])
            if isinstance(metrics_used, list):
                flat_dict[f'Metric_{clean_name}_Used'] = ', '.join(metrics_used)
            else:
                flat_dict[f'Metric_{clean_name}_Used'] = str(metrics_used)
        
        # Animal details
        animal = result.get('animal_details', {})
        flat_dict['Animal_Taxa_Studied'] = ', '.join(animal.get('taxa_studied', []))
        flat_dict['Animal_Sampling_Methods'] = ', '.join(animal.get('sampling_methods', []))
        
        # Animal research tasks
        tasks = animal.get('research_tasks', {})
        for task, details in tasks.items():
            # Ensure consistent naming for habitat preference
            if task == 'habitat_preference':
                clean_name = 'Habitat Preference'  # Force exact naming
            else:
                clean_name = task.replace('_', ' ').title()
            
            # Ensure all fields exist with default values
            flat_dict[f'Animal_{clean_name}_Present'] = details.get('present', False)
            flat_dict[f'Animal_{clean_name}_Regex'] = details.get('regex_detected', False)
            
            # Clean up evidence field
            evidence = details.get('evidence', '')
            if evidence:
                evidence = evidence.replace('\n', ' ').strip()
                evidence = evidence[:100]
            flat_dict[f'Animal_{clean_name}_Evidence'] = evidence
            
            # Handle metrics field
            metrics = details.get('metrics_used', [])
            if isinstance(metrics, list):
                flat_dict[f'Animal_{clean_name}_Metrics'] = ', '.join(metrics)
            else:
                flat_dict[f'Animal_{clean_name}_Metrics'] = str(metrics)
        
        # Add relationship details
        rel_details = result.get('relationship_details', {})
        if 'mechanism_testing' in rel_details:
            mech = rel_details['mechanism_testing']
            flat_dict['Mechanism_Testing_Present'] = mech.get('present', False)
            flat_dict['Mechanism_Testing_Methods'] = ', '.join(mech.get('methods', []))
            flat_dict['Mechanisms_Tested'] = ', '.join(mech.get('mechanisms_tested', []))
            
            # Evidence types (removed process_based)
            evidence = mech.get('evidence_type', {})
            for ev_type in ['experimental', 'natural_experiment', 'statistical']:
                flat_dict[f'Evidence_{ev_type.replace("_", " ").title()}'] = evidence.get(ev_type, False)
        
        flattened_results.append(flat_dict)
    
    # Before saving to CSV
    print("\nFinal data to be saved:")
    for result in flattened_results:
        for key, value in result.items():
            if 'Cover_Density' in key:
                print(f"{key}: {value}")
    
    # Convert to DataFrame and ensure all columns exist
    df = pd.DataFrame(flattened_results)
    
    # Define column order
    column_order = [
        # Metadata
        'File_Name', 'Number_of_Pages', 'File_Size_KB',
        
        # Study site
        'Study_Country', 'Habitat_Types', 'Spatial_Scale',
        
        # Structure analysis
        'Structure_vertical_3d', 'Structure_vertical_3d_Confidence',
        'Structure_horizontal_2d', 'Structure_horizontal_2d_Confidence',
        
        # Animal biodiversity
        'Animal_vertical_3d', 'Animal_vertical_3d_Confidence',
        'Animal_horizontal_2d', 'Animal_horizontal_2d_Confidence',
        
        # Relationships
        'Relationship_Structure Animal Correlation', 'Relationship_Structure Animal Correlation_Confidence',
        'Relationship_Effect Structure On Animals', 'Relationship_Effect Structure On Animals_Confidence',
        'Relationship_Effect Animals On Structure', 'Relationship_Effect Animals On Structure_Confidence',
    ]
    
    # Add method columns
    for display_name, method_key in METHOD_TYPES:
        clean_name = method_key.replace('_', ' ').title()
        method_cols = [
            f'Method_{clean_name}_Regex',
            f'Method_{clean_name}_GPT',
            f'Method_{clean_name}_Evidence'
        ]
        column_order.extend(method_cols)
        # Ensure columns exist
        for col in method_cols:
            if col not in df.columns:
                df[col] = None
    
    # Add metric columns
    metric_cols = []
    for metric in ["cover_density", "height", "horizontal_heterogeneity", "vertical_heterogeneity", "landscape"]:
        clean_name = metric.replace('_', ' ').title()
        metric_cols.extend([
            f'Metric_{clean_name}_Present',
            f'Metric_{clean_name}_Regex',
            f'Metric_{clean_name}_Evidence',
            f'Metric_{clean_name}_Used'
        ])
    column_order.extend(metric_cols)
    # Ensure columns exist
    for col in metric_cols:
        if col not in df.columns:
            df[col] = False if col.endswith('_Present') or col.endswith('_Regex') else ''
    
    # Add animal details
    animal_cols = [
        'Animal_Taxa_Studied', 'Animal_Sampling_Methods'
    ]
    column_order.extend(animal_cols)
    for col in animal_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Add research task columns
    for task in RESEARCH_TASKS:
        clean_name = task.replace('_', ' ').title()
        task_cols = [
            f'Animal_{clean_name}_Present',
            f'Animal_{clean_name}_Regex',
            f'Animal_{clean_name}_Evidence',
            f'Animal_{clean_name}_Metrics'
        ]
        column_order.extend(task_cols)
        # Ensure columns exist
        for col in task_cols:
            if col not in df.columns:
                df[col] = False if col.endswith('_Present') or col.endswith('_Regex') else ''
    
    # Add relationship details
    relationship_cols = [
        'Mechanism_Testing_Present', 'Mechanism_Testing_Methods', 'Mechanisms_Tested',
        'Evidence_Experimental', 'Evidence_Natural_Experiment', 'Evidence_Statistical'
    ]
    column_order.extend(relationship_cols)
    # Ensure columns exist
    for col in relationship_cols:
        if col not in df.columns:
            df[col] = False if col.endswith('_Present') or col.startswith('Evidence_') else ''
    
    # Ensure all columns exist before reordering
    for col in column_order:
        if col not in df.columns:
            logger.warning(f"Missing column {col}, adding with default value")
            df[col] = None
    
    # Reorder columns
    df = df[column_order]
    
    try:
        df.to_csv(output_file, 
                 index=False,
                 escapechar='\\',
                 encoding='utf-8',
                 quoting=csv.QUOTE_ALL)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        # Try saving with simpler encoding if original fails
        df.to_csv(output_file,
                 index=False,
                 encoding='utf-8',
                 errors='replace')

def print_summaries(results: List[Dict[str, Any]]) -> None:
    """Print detailed analysis summaries"""
    if not results:
        logger.warning("No results to summarize")
        return
        
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    
    print(f"\nProcessed {len(results)} papers")
    
    # Spatial Scale Summary
    print("\nSpatial Scale Distribution:")
    print("-------------------------")
    if 'Spatial_Scale' in df.columns:
        scale_counts = df['Spatial_Scale'].value_counts()
        print(scale_counts)
    
    # Location Summary
    print("\nStudy Locations:")
    print("---------------")
    if 'Study_Country' in df.columns:
        country_counts = df['Study_Country'].value_counts()
        print("\nTop Study Countries:")
        print(country_counts.head())
    
    # Structure Analysis Summary
    print("\nStructure Analysis:")
    print("-------------------")
    structure_counts = {
        "Vertical/3D": df['Structure_vertical_3d'].sum() if 'Structure_vertical_3d' in df.columns else 0,
        "Horizontal/2D": df['Structure_horizontal_2d'].sum() if 'Structure_horizontal_2d' in df.columns else 0
    }
    for category, count in structure_counts.items():
        print(f"{category}: {count} papers")
    
    # Structure Metrics Summary
    print("\nStructure Metrics Used:")
    print("---------------------")
    for result in results:
        if 'structure_details' in result and 'metrics' in result['structure_details']:
            metrics = result['structure_details']['metrics']
            for metric_name, details in metrics.items():
                print(f"\n{metric_name}:")
                print(f"- Present: {details.get('present', False)}")
                print(f"- Regex detected: {details.get('regex_detected', False)}")
                if details.get('metrics_used'):
                    print(f"- Metrics used: {', '.join(details['metrics_used'])}")
    
    # Animal Taxa Summary
    print("\nAnimal Taxa Studied:")
    print("------------------")
    if 'Animal_Taxa_Studied' in df.columns:
        # Split comma-separated taxa and count
        all_taxa = []
        for taxa in df['Animal_Taxa_Studied']:
            if isinstance(taxa, str):
                all_taxa.extend([t.strip() for t in taxa.split(',')])
        
        if all_taxa:
            taxa_counts = pd.Series(all_taxa).value_counts()
            total_papers = len(df)
            
            # Print counts and percentages
            for taxa, count in taxa_counts.items():
                percentage = (count / total_papers) * 100
                print(f"{taxa}: {count} papers ({percentage:.1f}%)")
            
            # Print papers with multiple taxa
            multi_taxa_papers = df[df['Animal_Taxa_Studied'].str.contains(',', na=False)]
            if not multi_taxa_papers.empty:
                print(f"\nPapers studying multiple taxa: {len(multi_taxa_papers)} ({(len(multi_taxa_papers)/total_papers)*100:.1f}%)")
    
    # Animal Biodiversity Analysis Summary
    print("\nAnimal Biodiversity Analysis:")
    print("---------------------------")
    biodiversity_counts = {
        "Vertical/3D": df['Animal_vertical_3d'].sum() if 'Animal_vertical_3d' in df.columns else 0,
        "Horizontal/2D": df['Animal_horizontal_2d'].sum() if 'Animal_horizontal_2d' in df.columns else 0
    }
    for category, count in biodiversity_counts.items():
        print(f"{category}: {count} papers")
    
    # Relationship Analysis Summary
    print("\nStructure-Animal Relationships:")
    print("-----------------------------")
    relationship_counts = {
        "Correlation": df['Relationship_Structure Animal Correlation'].sum() if 'Relationship_Structure Animal Correlation' in df.columns else 0,
        "Structure → Animals": df['Relationship_Effect Structure On Animals'].sum() if 'Relationship_Effect Structure On Animals' in df.columns else 0,
        "Animals → Structure": df['Relationship_Effect Animals On Structure'].sum() if 'Relationship_Effect Animals On Structure' in df.columns else 0
    }
    for category, count in relationship_counts.items():
        print(f"{category}: {count} papers")

    # Mechanism Testing Summary
    print("\nMechanism Testing:")
    print("----------------")
    if 'Mechanism_Testing_Present' in df.columns:
        mech_count = df['Mechanism_Testing_Present'].sum()
        print(f"Papers with mechanism testing: {mech_count}")
        
        if mech_count > 0:
            # Show methods used
            if 'Mechanism_Testing_Methods' in df.columns:
                methods = df[df['Mechanism_Testing_Present']]['Mechanism_Testing_Methods']
                all_methods = []
                for m in methods:
                    if isinstance(m, str):
                        all_methods.extend([x.strip() for x in m.split(',')])
                if all_methods:
                    method_counts = pd.Series(all_methods).value_counts()
                    print("\nMethods used:")
                    print("\n".join(f"- {m}: {c} papers" for m, c in method_counts.head().items()))
            
            # Show evidence types
            print("\nEvidence types:")
            evidence_types = {
                "Experimental": df['Evidence_Experimental'].sum() if 'Evidence_Experimental' in df.columns else 0,
                "Natural Experiment": df['Evidence_Natural_Experiment'].sum() if 'Evidence_Natural_Experiment' in df.columns else 0,
                "Statistical": df['Evidence_Statistical'].sum() if 'Evidence_Statistical' in df.columns else 0
            }
            for ev_type, count in evidence_types.items():
                print(f"- {ev_type}: {count} papers")

    # Method Detection Comparison Summary
    print("\nMethod Detection Comparison:")
    print("-------------------------")
    print("\nMethod                  | Regex | GPT | Agreement")
    print("-" * 55)
    
    for display_name, method_key in METHOD_TYPES:
        regex_key = f'Method_{method_key.replace("_", " ").title()}_Regex'
        gpt_key = f'Method_{method_key.replace("_", " ").title()}_GPT'
        
        if regex_key in df.columns and gpt_key in df.columns:
            regex_count = df[regex_key].sum()
            gpt_count = df[gpt_key].sum()
            agreement = (df[regex_key] == df[gpt_key]).sum()
            total = len(df)
            agreement_pct = (agreement/total)*100
            
            print(f"{display_name:<22} | {regex_count:^5} | {gpt_count:^3} | {agreement}/{total} ({agreement_pct:.1f}%)")
            
            # Show evidence for disagreements if requested
            disagreements = df[df[regex_key] != df[gpt_key]]
            if not disagreements.empty:
                evidence_key = f'Method_{method_key.replace("_", " ").title()}_Evidence'
                if evidence_key in disagreements.columns:
                    print("\nDisagreement evidence:")
                    for _, row in disagreements.iterrows():
                        if row[evidence_key]:
                            print(f"  - {row['File_Name']}: {row[evidence_key][:100]}...")
                print()

    # Biodiversity Tasks Summary
    print("\nAnimal Research Tasks:")
    print("------------------")
    task_types = [
        'Species_Richness', 'Abundance', 'Occurrence_Distribution',
        'Community_Composition', 'Functional_Diversity', 'Beta_Diversity',
        'Stratification_Niche', 'Movement', 'Behavior', 'Habitat_Preference',
        'Habitat_Suitability', 'Survival_Mortality', 'Acoustic_Characteristics'
    ]
    
    for task in task_types:
        present_col = f'Animal_{task}_Present'
        metrics_col = f'Animal_{task}_Metrics'
        regex_col = f'Animal_{task}_Regex'
        
        if present_col in df.columns:
            gpt_count = df[present_col].sum()
            regex_count = df[regex_col].sum() if regex_col in df.columns else 0
            agreement = (df[present_col] == df[regex_col]).sum() if regex_col in df.columns else 0
            total = len(df)
            
            print(f"\n{task.replace('_', ' ')}:")
            print(f"- GPT detection: {gpt_count} papers")
            print(f"- Regex detection: {regex_count} papers")
            print(f"- Agreement: {agreement}/{total} papers ({(agreement/total)*100:.1f}%)")
            
            if metrics_col in df.columns and gpt_count > 0:
                metrics = df[df[present_col]][metrics_col]
                if not metrics.empty:
                    # Split comma-separated metrics and count
                    all_metrics = []
                    for m in metrics:
                        if isinstance(m, str):
                            all_metrics.extend([x.strip() for x in m.split(',')])
                    if all_metrics:
                        metric_counts = pd.Series(all_metrics).value_counts()
                        print("  Top metrics:")
                        print("  " + "\n  ".join(f"- {m}: {c} papers" for m, c in metric_counts.head().items())) 