"""Main script for paper analysis"""
import asyncio
from openai import OpenAI
from config import ROOT_PATH, PDF_FOLDER, OUTPUT_FILE
from extractors.text_extractor import process_pdf_batch
from utils.data_processing import save_results, print_summaries

async def main():
    # OpenAI configuration
    client = OpenAI(
        api_key="your-actual-api-key-here"  # Replace with your API key
    )
    
    # Process PDFs
    results = await process_pdf_batch(PDF_FOLDER, client)
    
    # Save and summarize results
    save_results(results, OUTPUT_FILE)
    print_summaries(results)

if __name__ == "__main__":
    asyncio.run(main()) 