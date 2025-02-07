from scholarly import scholarly
import pandas as pd
import requests
import os
import time
from urllib.parse import urljoin

def is_pdf_url(url):
    """Check if URL likely points to a PDF"""
    if not url:
        return False
    return (
        url.lower().endswith('.pdf') or 
        'pdf' in url.lower() or
        'download' in url.lower()
    )

def download_pdf(url, filename):
    """Attempt to download PDF from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check if response is likely a PDF
        content_type = response.headers.get('content-type', '').lower()
        if response.status_code == 200 and ('pdf' in content_type or len(response.content) > 1000):
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"Download error: {str(e)}")
        return False

def paper_exists(pdf_dir, paper_id):
    """Check if a paper with given ID already exists in the directory"""
    if not os.path.exists(pdf_dir):
        return False
    
    # List all files in pdf directory
    files = os.listdir(pdf_dir)
    # Check if any filename starts with this ID
    return any(f.startswith(str(paper_id) + " ") for f in files)

def download_papers(excel_file, output_dir, start_row=708, batch_size=20):
    """
    Download papers using Google Scholar
    """
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    pdf_dir = os.path.join(output_dir, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Read Excel file
    df = pd.read_excel(excel_file)
    
    # Filter to start from specified row
    df = df.iloc[start_row:]
    print(f"Starting from row {start_row} (total rows remaining: {len(df)})")
    
    # Load existing results if any
    results_file = os.path.join(output_dir, 'download_results.xlsx')
    if os.path.exists(results_file):
        existing_results = pd.read_excel(results_file)
        processed_titles = set(existing_results['Title'])
        print(f"Found {len(processed_titles)} previously processed papers")
    else:
        existing_results = pd.DataFrame(columns=['ID', 'Title', 'URL', 'Status', 'PDF_Path'])
        processed_titles = set()
    
    # Process papers in batches
    papers_processed = 0
    
    for idx, row in df.iterrows():
        title = row['Title']
        paper_id = row['ID']
        
        # Skip if already processed or PDF exists
        if title in processed_titles or paper_exists(pdf_dir, paper_id):
            print(f"\nSkipping {paper_id}: Already processed")
            continue
            
        print(f"\nProcessing {idx} (ID: {paper_id}): {title}")
        
        try:
            # Search with exact title
            search_query = scholarly.search_pubs(f'allintitle: "{title}"')
            paper = next(search_query, None)
            
            if paper:
                # Get paper details
                url = paper.get('eprint_url', '') or paper.get('pub_url', '')
                status = 'Found'
                
                # Try to download PDF if URL available
                if url:
                    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
                    pdf_filename = os.path.join(pdf_dir, f"{paper_id} {safe_title}.pdf")
                    
                    if download_pdf(url, pdf_filename):
                        status = 'PDF Downloaded'
                        print(f"Downloaded PDF: {pdf_filename}")
                    else:
                        status = 'Download Failed'
                        pdf_filename = ''
                else:
                    status = 'No URL Found'
                    pdf_filename = ''
            else:
                status = 'Not Found'
                url = ''
                pdf_filename = ''
            
            # Record result
            paper_info = {
                'ID': paper_id,
                'Title': title,
                'URL': url,
                'Status': status,
                'PDF_Path': pdf_filename
            }
            
            # Add to results
            new_result = pd.DataFrame([paper_info])
            existing_results = pd.concat([existing_results, new_result], ignore_index=True)
            
            # Save progress
            existing_results.to_excel(results_file, index=False)
            
            papers_processed += 1
            
            # Add delay between requests
            time.sleep(5)  # 5 second delay to avoid rate limits
            
            # Pause after batch_size papers
            if papers_processed >= batch_size:
                print(f"\nProcessed {batch_size} papers. Pausing...")
                print("Run the script again to continue with next batch")
                break
                
        except Exception as e:
            print(f"Error processing {title}: {str(e)}")
            
            # Record error
            error_info = {
                'ID': paper_id,
                'Title': title,
                'URL': '',
                'Status': f'Error: {str(e)}',
                'PDF_Path': ''
            }
            new_result = pd.DataFrame([error_info])
            existing_results = pd.concat([existing_results, new_result], ignore_index=True)
            existing_results.to_excel(results_file, index=False)
            
            # Add longer delay after errors
            time.sleep(10)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    rootpath = '/Users/wenxinyang/Desktop/GitHub/3dhabitat_litreview/lit/AllJan25'
    excel_file = os.path.join(rootpath, "merged_lit_2501.xlsx")
    output_dir = os.path.join(rootpath, "bulk_papers")
    
    download_papers(excel_file, output_dir, start_row=708, batch_size=20)