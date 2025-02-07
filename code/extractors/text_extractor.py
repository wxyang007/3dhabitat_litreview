"""PDF text extraction utilities"""
import os
from typing import List, Dict, Any
import asyncio
from PyPDF2 import PdfReader
from ..config import BATCH_SIZE
from .section_extractor import extract_sections
from ..analyzers.categories import get_detailed_analysis

async def extract_pdf_info_async(pdf_path: str, client) -> Dict[str, Any]:
    """Extract and analyze information from a single PDF"""
    try:
        # Read PDF
        reader = PdfReader(pdf_path)
        full_text = ""
        
        # Extract text from all pages
        for page in reader.pages:
            try:
                full_text += page.extract_text() + "\n"
            except Exception as e:
                print(f"Error extracting text from page in {pdf_path}: {str(e)}")
                continue
        
        # Extract relevant sections and analyze
        relevant_text = extract_sections(full_text)
        analysis_results = await get_detailed_analysis(relevant_text, client)
        
        # Create result dictionary
        return create_info_dict(pdf_path, reader, analysis_results)
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None

async def process_pdf_batch(folder_path: str, client, batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """Process a batch of PDFs in parallel"""
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    results = []
    
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        tasks = [
            asyncio.create_task(extract_pdf_info_async(
                os.path.join(folder_path, pdf_file), 
                client
            ))
            for pdf_file in batch
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend([r for r in batch_results if r is not None])
        await asyncio.sleep(1)  # Rate limiting
    
    return results 