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
from config import ROOT_PATH, MAX_TOTAL_CHARS, MAX_ABSTRACT_CHARS

logger = setup_logger()

def extract_sections(text: str) -> str:
    """Extract abstract and methods/study area/data sections"""
    # Set maximum sizes
    # max_total_chars = 5000
    # max_abstract_chars = 1000
    
   # Find all possible variations for section headers
    keyword_patterns = [
        r'key\s*-?\s*words?',  # matches: keywords, key words, key-words
        r'key\s*-?\s*word\s+list',
        r'index\s+terms?'
    ]
    
    abstract_patterns = [
        r'abstract',
        r'summary'
    ]
    
    intro_patterns = [
        r'(?:1\.?\s*)?introduction\s*:?\s*\n',  # matches: Introduction\n, 1. Introduction:\n
        r'(?:1\.?\s*)?background\s*:?\s*\n',
        r'general\s+introduction\s*:?\s*\n',
        r'research\s+background\s*:?\s*\n',
        r'overview\s*:?\s*\n'
    ]

    methods_patterns = [
        r'(?:\d\.?\s*)?materials?\s+and\s+methods?\s*:?\s*\n',  # matches: Materials and Methods:\n
        r'(?:\d\.?\s*)?methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?methodology\s*:?\s*\n',
        r'(?:\d\.?\s*)?experimental\s+methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?study\s+methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?data\s+collection\s*:?\s*\n',
        r'(?:\d\.?\s*)?data\s+and\s+methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?study\s+area\s*:?\s*\n',
        r'(?:\d\.?\s*)?study\s+sites?\s*:?\s*\n',
        r'(?:\d\.?\s*)?study\s+regions?\s*:?\s*\n',
        r'(?:\d\.?\s*)?field\s+methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?sampling\s+methods?\s*:?\s*\n',
        r'(?:\d\.?\s*)?data\s+analysis\s*:?\s*\n'
    ]

    later_patterns = [
        r'(?:\d\.?\s*)?results?\s*:?\s*\n',  # matches: Results:\n
        r'(?:\d\.?\s*)?discussions?\s*:?\s*\n',
        r'(?:\d\.?\s*)?results?\s+and\s+discussions?\s*:?\s*\n',
        r'(?:\d\.?\s*)?conclusions?\s*:?\s*\n',
        r'(?:\d\.?\s*)?concluding\s+remarks?\s*:?\s*\n',
        r'(?:\d\.?\s*)?references?\s*:?\s*\n',
        r'(?:\d\.?\s*)?literature\s+cited\s*:?\s*\n',
        r'(?:\d\.?\s*)?bibliography\s*:?\s*\n',
        r'(?:\d\.?\s*)?acknowledgements?\s*:?\s*\n',
        r'(?:\d\.?\s*)?supporting\s+information\s*:?\s*\n',
        r'(?:\d\.?\s*)?appendix\s*:?\s*\n',
        r'(?:\d\.?\s*)?supplementary\s+materials?\s*:?\s*\n'
    ]
    
    # in case we need to revert to the original text
    raw_text = text

    # 1. Find methods section
    methods_start = 999999
    methods_text = ""
    for pattern in methods_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            methods_start = min(methods_start, match.start())
            break

    # Keep text after methods section
    if methods_start < 999999:
        methods_text = text[methods_start:]

    # 2. Find start of later sections & remove them
    later_start = 999999
    for pattern in later_patterns:
        match = re.search(pattern, methods_text, re.IGNORECASE)
        if match:
            later_start = min(later_start, match.start())
            break

    # Remove later sections from text
    if (later_start < 999999) & (later_start > 0):
        methods_text = methods_text[:later_start]
        logger.info(f"Removed later sections from text of length {later_start} chars")
    else:
        methods_text = methods_text[:MAX_TOTAL_CHARS]

    # 3. Find intro section & remove it
    intro_start = -1
    for pattern in intro_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            intro_start = match.start()
            break
    # Remove intro section from text
    if intro_start >= 0:
        text = text[:intro_start]
        logger.info(f"Removed intro section from text of length {len(text)} chars")
    
    # 4. Find positions of abstract and keywords and keep them
    abstract_start = -1
    keywords_pos = -1
        
    # Find start of abstract
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            abstract_start = match.start()        
            if abstract_start >= 0:
                if abstract_start < MAX_ABSTRACT_CHARS:  # Only consider matches near start of text
                    abstract_start = match.end()
                    break
    
        # Find position of keywords
    for pattern in keyword_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keywords_pos = match.start()
            break
    
    # Extract abstract based on relative positions
    abstract_text = ""
    if abstract_start >= 0:
        # Abstract found
        abstract_text = text[abstract_start:abstract_start+MAX_ABSTRACT_CHARS].strip()
    else:
        # No abstract found
        if keywords_pos >= 1500:
            # Keywords found, keep abstract max chars before keywords
            abstract_text = text[max(0, keywords_pos - MAX_ABSTRACT_CHARS):keywords_pos].strip()
        elif keywords_pos >= 0:
            # Keywords found, keep abstract max chars after keywords
            abstract_text = text[keywords_pos:keywords_pos + MAX_ABSTRACT_CHARS].strip()
        else:
            # No keywords found, keep the first 2000 chars
            logger.warning("No keywords or abstract found - keeping the first 2000 chars")
            abstract_text = text[:MAX_ABSTRACT_CHARS].strip()

    # Clean up abstract text while preserving paragraphs
    if abstract_text:
        # Replace single newlines within paragraphs with spaces
        abstract_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', abstract_text)
        # Replace multiple newlines with double newline
        abstract_text = re.sub(r'\n{2,}', '\n\n', abstract_text)
        # Clean up extra whitespace while preserving paragraph breaks
        abstract_text = '\n\n'.join(p.strip() for p in abstract_text.split('\n\n'))

    # Handle abstract
    if abstract_text:
        if len(abstract_text) > MAX_ABSTRACT_CHARS:
            # logger.info(f"Truncating abstract from {len(abstract_text)} to {MAX_ABSTRACT_CHARS} chars")
            abstract_text = abstract_text[:MAX_ABSTRACT_CHARS] + "..."
        abstract_text = "ABSTRACT SECTION:\n" + abstract_text


    if len(methods_text) > 0:
        # combine methods_text and abstract_text
        full_text = abstract_text + "\n\n" + methods_text
    else:
        logger.warning("No methods section found")
        # get position of end of abstract_text in text
        end_of_abstract = text.find(abstract_text)
        full_text = abstract_text + "\n\n" + text[end_of_abstract:end_of_abstract + MAX_TOTAL_CHARS]

    # Now clean the text for further processing
    full_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', full_text)  # Add space between merged words
    full_text = re.sub(r'\s+', ' ', full_text)  # Normalize whitespace
    full_text = full_text.replace('\r', ' ')  # Replace carriage returns
    full_text = re.sub(r'(?<=\w)\s+(?=\w)', ' ', full_text)  # Ensure single space between words
    

    # Calculate remaining space for full text
    used_chars = len(full_text)
    remaining_chars = MAX_TOTAL_CHARS - used_chars
    
    logger.info(f"Space used by abstract and markers: {used_chars} chars")
    logger.info(f"Remaining space for full text: {remaining_chars} chars")
    
    # Truncate full text if needed
    if len(full_text) > MAX_TOTAL_CHARS:
        logger.info(f"Truncating full text from {len(full_text)} to {MAX_TOTAL_CHARS} chars")
        truncated_text = full_text[:MAX_TOTAL_CHARS] + "..."
    else:
        truncated_text = full_text
    
    full_text = "FULL TEXT:\n" + truncated_text
    
    final_length = len(full_text)
    logger.info(f"Final text length: {final_length} chars (limit: {MAX_TOTAL_CHARS})")
    
    if final_length > MAX_TOTAL_CHARS:
        logger.warning(f"Warning: Final text exceeds limit by {final_length - MAX_TOTAL_CHARS} chars")
    
    return full_text

async def analyze_paper(pdf_path: str, client) -> Dict[str, Any]:
    """Analyze a single paper"""
    try:
        logger.info(f"Starting analysis of: {os.path.basename(pdf_path)}")
        
        # Read PDF
        reader = PdfReader(pdf_path)
        logger.info(f"Successfully opened PDF with {len(reader.pages)} pages")
        
        # Check first page for ResearchGate or JSTOR or BioOne
        first_page_text = reader.pages[0].extract_text().lower()
        # Clean up text for detection
        first_page_text = re.sub(r'\s+', '', first_page_text)  # Remove all whitespace
        skip_first_page = False
        
        # Define patterns to match
        researchgate_patterns = ['researchgate.net', 'researchgatenet', 'researchgate']
        jstor_patterns = ['jstor.org', 'jstororg', 'jstor', 'bioone.org', 'biooneorg', 'ePublications', 'e-publications']
        
        # Check for any pattern match
        if any(pattern in first_page_text for pattern in researchgate_patterns) or \
           any(pattern in first_page_text for pattern in jstor_patterns):
            logger.info("Detected ResearchGate/JSTOR cover page - skipping first page")
            skip_first_page = True
        
        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(reader.pages):
            try:
                # Skip first page if it's a cover page
                if i == 0 and skip_first_page:
                    continue
                page_text = page.extract_text() + "\n"
                full_text += page_text
                # logger.info(f"Page {i+1} text length: {len(page_text)} chars")    
            except Exception as e:
                logger.error(f"Error extracting text from page: {str(e)}")
                continue
        
        logger.info(f"Full text length before cleaning: {len(full_text)} chars")
        
        if not full_text.strip():
            logger.error("No text extracted from PDF")
            return None
            
        # Extract relevant sections
        relevant_text = extract_sections(full_text)
        logger.info("Successfully extracted relevant sections")
        
        # Clea n text
        clean_text = relevant_text.replace('"', "'").replace('\\', '/').replace('\r', ' ')
        clean_text_full = full_text.replace('"', "'").replace('\\', '/').replace('\r', ' ')
        
        logger.info(f"Clean text length: {len(clean_text)} chars")
        logger.info(f"Clean full text length: {len(clean_text_full)} chars")

        try:
            # Get analysis results
            results = await get_combined_analysis(clean_text, clean_text_full, client)
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
    output_file = os.path.join(ROOT_PATH, "output", "gpt_analysis_results.csv")
    
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
        os.makedirs(os.path.join(ROOT_PATH, "code_gpt", "logs"), exist_ok=True)
        
        # Directory containing PDF files
        pdf_dir = os.path.join(ROOT_PATH, "data/pdfs")
        
        # Get list of PDF files
        pdf_files = [
            os.path.join(pdf_dir, f) 
            for f in os.listdir(pdf_dir) 
            if f.endswith('.pdf')
        ]
        
        if test_mode:
            if len(pdf_files) >= 3:
                logger.info("TEST MODE: Processing first 3 PDFs")
                pdf_files = pdf_files[:3]  # Take first 3 files
            elif pdf_files:
                logger.info(f"TEST MODE: Processing all {len(pdf_files)} available PDFs")
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
    # test_mode = True
    
    # Log which mode we're running in
    if test_mode:
        logger.info("Running in TEST mode")
    else:
        logger.info("Running in NORMAL mode")
        print(ROOT_PATH)
        
    asyncio.run(main(test_mode)) 