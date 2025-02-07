"""Main script for analyzing research papers"""
import asyncio
import os
import re
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from utils.data_processing import save_results, print_summaries
from analyzers.categories import get_combined_analysis
from utils.ai_client import init_client
from utils.logger import setup_logger
from config import ROOT_PATH
from utils.pattern_detector import detect_metrics

logger = setup_logger()

def extract_sections(text: str) -> str:
    """Extract abstract and methods/study area/data sections"""
    # Find Abstract first with original text
    abstract_patterns = [
        # Pattern for abstracts after keywords
        r'(?i)(?:keywords?|key\s*words)[:\s]*.*?\n(.*?)(?=\n\s*(?:introduction|methods|results|\d\.|$))',
        # Pattern for abstracts after article info
        r'(?i)article\s+(?:info|history).*?(?:keywords?|key\s*words)[:\s]*.*?\n(.*?)(?=\n\s*(?:introduction|methods|results|\d\.|$))',
        # Original patterns as fallback
        r'(?i)abstract[:\s.]*\n+(.*?)(?=\n\s*(?:introduction|keywords?|key\s*words|background|methods|results))',
        # Summary as final fallback
        r'(?i)summary[:\s.]*\n+(.*?)(?=\n\s*(?:introduction|keywords?|key\s*words|background|methods|results))'
    ]
    
    # Try to find abstract
    abstract_text = ""
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Get the full text before the match to check keywords position
            pre_match_text = text[:match.start()]
            keywords_pos = max(
                pre_match_text.lower().rfind('keywords'),
                pre_match_text.lower().rfind('key words')
            )
            
            if keywords_pos >= 0 and keywords_pos < 500:
                # Keywords appear early - use text after keywords
                abstract_text = match.group(1).strip()
            else:
                # Keywords appear late or not found - try to get text before keywords
                abstract_pattern = r'(?i)(?:abstract|summary)[:\s.]*\n+(.*?)(?=\n\s*(?:keywords?|key\s*words))'
                pre_keywords_match = re.search(abstract_pattern, text, re.DOTALL)
                if pre_keywords_match and len(pre_keywords_match.group(1).strip()) > 200:
                    abstract_text = pre_keywords_match.group(1).strip()
                else:
                    # Fallback to original match if pre-keywords abstract is too short
                    abstract_text = match.group(1).strip()
            
            # Clean up newlines in abstract text
            abstract_text = re.sub(r'(?<=\w)\n(?=\w)', ' ', abstract_text)
            
            # Verify we got enough text
            if len(abstract_text.strip()) > 200:
                break
    
    # Now clean the text for further processing
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between merged words
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.replace('\r', ' ')  # Replace carriage returns
    text = re.sub(r'(?<=\w)\s+(?=\w)', ' ', text)  # Ensure single space between words
    
    relevant_text = ""
    
    # Find Methods and everything until Results
    methods_patterns = [
        # Capture everything between methods and results/discussion/conclusion/summary
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|experimental\s+procedure|study\s+area|data\s+collection)[:\s]*\n*(.*?)(?=\n\s*(?:results|discussion|conclusion|summary))',
        
        # Fallback pattern - less strict section markers
        r'(?i)(?:materials\s+and\s+methods|methods|methodology|study\s+area|data)[:\s]*\n*(.*?)(?=\n\s*(?:\d+\.|[A-Z][a-z]+\s*\n|results|discussion|conclusion|summary))',
        
        # Very loose pattern as last resort
        r'(?i)(?:methods|methodology|study\s+area)[:\s]*\n*(.*?)(?=\n\s*(?:results|discussion|conclusion|summary))'
    ]
    
    # Additional patterns for study area and data sections
    study_data_patterns = [
        # Study area/site patterns
        r'(?i)(?:study\s+area|study\s+site|research\s+area|site\s+description)[:\s]*(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        r'(?i)(?:study\s+area|study\s+site|research\s+area|site\s+description)\s*\n(.*?)(?=\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][a-z]+\s*\n|results|discussion|conclusion))',
        
        # Data related patterns
        r'(?i)(?:data\s+collection|data\s+analysis|data\s+processing|data\s+and\s+methods)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:data\s+acquisition|data\s+sources|data\s+sets?|data\s+description)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        
        # Field methods patterns
        r'(?i)(?:field\s+methods|sampling\s+methods|experimental\s+design)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:field\s+sampling|field\s+measurements|field\s+data)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        
        # Data processing/analysis patterns
        r'(?i)(?:data\s+processing|analysis\s+methods|statistical\s+analysis)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))',
        r'(?i)(?:data\s+analysis|analytical\s+methods|processing\s+steps)[:\s]*(.*?)(?=\n\s*(?:results|discussion|conclusion))'
    ]
    
    # Try to find methods first
    methods_text = ""
    for pattern in methods_patterns:
        match = re.search(pattern, text, re.DOTALL | re.I)  # Added re.I for case insensitive
        if match:
            methods_text = match.group(1).strip()
            if len(methods_text) > 100:  # Only accept if we got substantial text
                break
    
    # Always try to find study area and data sections
    study_data_text = ""
    for pattern in study_data_patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            section_text = match.group(1).strip()
            if section_text and len(section_text) > 50:  # Avoid very short matches
                # Check if this section is not already included in methods_text
                if methods_text and section_text in methods_text:
                    continue  # Skip if already in methods
                study_data_text += section_text + "\n\n"
    
    # Combine methods and study/data sections if both exist
    if methods_text and study_data_text:
        # Split into sentences for more granular deduplication
        methods_sentences = set(s.strip() for s in methods_text.split('.'))
        data_sentences = [s.strip() for s in study_data_text.split('.')]
        
        # Only add non-duplicate sentences from data section
        unique_data = []
        for sentence in data_sentences:
            if sentence and sentence not in methods_sentences:
                unique_data.append(sentence)
        
        if unique_data:
            methods_text += "\n\n" + '. '.join(unique_data)
    elif study_data_text:  # Use only study/data if no methods
        methods_text = study_data_text
    
    # Adjust method length limit based on whether we found an abstract
    method_length_limit = 4000 if not abstract_text else 2500
    
    # Reduce maximum text length
    if abstract_text:
        abstract_text = abstract_text[:1500]  # Limit abstract
    if methods_text:
        methods_text = methods_text[:method_length_limit]  # Use adjusted limit
    
    # Combine the sections
    if abstract_text:
        relevant_text += "ABSTRACT:\n" + abstract_text + "\n\n"
    if methods_text:
        relevant_text += "METHODS AND STUDY DETAILS:\n" + methods_text
    
    return relevant_text

async def analyze_paper(pdf_path: str, client) -> Dict[str, Any]:
    """Analyze a single paper"""
    try:
        logger.info(f"Starting analysis of: {os.path.basename(pdf_path)}")
        
        # Read PDF
        reader = PdfReader(pdf_path)
        logger.info(f"Successfully opened PDF with {len(reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for page in reader.pages:
            try:
                full_text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error extracting text from page: {str(e)}")
                continue
        
        
        if not full_text.strip():
            logger.error("No text extracted from PDF")
            return None
            
        # Extract relevant sections
        relevant_text = extract_sections(full_text)
        logger.info("Successfully extracted relevant sections")
        
        
        # Clean text
        clean_text = relevant_text.replace('"', "'").replace('\\', '/').replace('\r', ' ')
        clean_text_full = full_text.replace('"', "'").replace('\\', '/').replace('\r', ' ')
        
        try:
            # Use 4000 character context for GPT
            analysis_text = clean_text[:4000]
            
            # Extract methods section for regex (everything between methods and results)
            methods_match = re.search(
                r'(?i)(?:materials?\s+and\s+methods|methods\s+and\s+study\s+details|methods?):\s*(.*?)(?=\n\s*(?:results|discussion|conclusion|summary))',
                clean_text_full,
                re.DOTALL
            )
            regex_text = methods_match.group(1) if methods_match else clean_text_full
            
            # Debug prints for regex
            print("\n=== Regex Detection Tracking ===")
            print("1. Methods Section:")
            print(f"   Found: {bool(methods_match)}")
            
            print("\n2. Canopy Height Check:")
            print(f"   Present in text: {'canopy height' in regex_text.lower()}")
            if "canopy height" in regex_text.lower():
                pos = regex_text.lower().find("canopy height")
                context = regex_text[max(0, pos-50):min(len(regex_text), pos+50)]
                print(f"   Context: ...{context}...")
            
            # Run regex detection
            metric_results, metric_evidence = detect_metrics(regex_text)
            print("\n3. Regex Results:")
            print(f"   Height metric detected: {metric_results.get('height', False)}")
            if metric_results.get('height'):
                print(f"   Evidence: {metric_evidence.get('height', '')[:200]}...")
            print("=" * 30)
            
            results = await get_combined_analysis(analysis_text, regex_text, client)
            logger.info("Successfully completed main analysis")
            
            # Add metadata
            results['filename'] = os.path.basename(pdf_path)
            results['num_pages'] = len(reader.pages)
            results['file_size'] = os.path.getsize(pdf_path) / 1024
            
            logger.info(f"Successfully analyzed {os.path.basename(pdf_path)}")
            return results
            
        except Exception as e:
            logger.error(f"Error in API analysis: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {str(e)}")
        return None

async def process_papers(pdf_files: List[str]) -> List[Dict[str, Any]]:
    """Process multiple papers in parallel"""
    client = init_client()
    results = []
    
    # Use ROOT_PATH for absolute path
    output_file = os.path.join(ROOT_PATH, "output", "analysis_results.csv")
    
    # Process papers in parallel with a limit
    chunk_size = 3  # Process 3 papers at a time
    total = len(pdf_files)
    
    logger.info(f"Starting analysis of {total} papers in chunks of {chunk_size}")
    
    for i in range(0, total, chunk_size):
        chunk = pdf_files[i:i + chunk_size]
        logger.info(f"\nProcessing papers {i+1}-{min(i+chunk_size, total)} of {total}")
        
        # Process chunk in parallel
        try:
            chunk_results = await asyncio.gather(
                *[analyze_paper(pdf, client) for pdf in chunk],
                return_exceptions=True
            )
            
            # Filter out errors and None results
            valid_results = [
                r for r in chunk_results 
                if r is not None and not isinstance(r, Exception)
            ]
            results.extend(valid_results)
            
            # Save results after each chunk
            logger.info(f"Saving results for chunk {i+1}-{min(i+chunk_size, total)}")
            save_results(results, output_file)  # This will overwrite/update the file
            
            logger.info(f"Successfully processed {len(valid_results)}/{len(chunk)} papers in current chunk")
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
    
    logger.info(f"Completed analysis of {len(results)}/{total} papers")
    return results

async def main(test_mode: bool = False):
    """Main execution function"""
    try:
        logger.info("Starting analysis pipeline")
        
        # Create required directories with absolute paths
        os.makedirs(os.path.join(ROOT_PATH, "data/pdfs"), exist_ok=True)
        os.makedirs(os.path.join(ROOT_PATH, "output"), exist_ok=True)
        os.makedirs(os.path.join(ROOT_PATH, "logs"), exist_ok=True)
        
        # Directory containing PDF files
        pdf_dir = os.path.join(ROOT_PATH, "data/pdfs")
        
        # Get list of PDF files
        pdf_files = [
            os.path.join(pdf_dir, f) 
            for f in os.listdir(pdf_dir) 
            if f.endswith('.pdf')
        ]
        
        if test_mode:
            if pdf_files:
                logger.info("TEST MODE: Processing only the first PDF")
                pdf_files = [pdf_files[0]]
                output_file = os.path.join(ROOT_PATH, "output", "test_results.csv")
            else:
                logger.error("No PDF files found in data/pdfs/")
                return
        
        # Process papers
        results = await process_papers(pdf_files)
        
        # Print summaries
        logger.info("\nAnalysis Summary:")
        print_summaries(results)
        
        logger.info("Analysis pipeline completed")
    finally:
        # Clean up cache
        from utils.ai_client import cache_manager
        # Always clear all cache files
        cache_manager.clear_cache()
        logger.info("Cache files cleared")

if __name__ == "__main__":
    # Get mode from command line argument or environment variable
    import sys
    test_mode = len(sys.argv) > 1 and sys.argv[1] == '--test'
    
    # Log which mode we're running in
    if test_mode:
        logger.info("Running in TEST mode")
    else:
        logger.info("Running in NORMAL mode")
        
    asyncio.run(main(test_mode)) 