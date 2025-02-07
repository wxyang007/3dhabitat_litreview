import pandas as pd
import requests
import os
import time
from urllib.parse import quote

def get_paper_url(doi):
    """Get paper URL from Crossref and Unpaywall"""
    try:
        # Try Unpaywall first
        email = "wenxinyang@ucsb.edu"  # Replace with your email
        unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
        response = requests.get(unpaywall_url)
        
        if response.status_code == 200:
            data = response.json()
            # Check for open access PDF
            if data.get('is_oa') and data.get('best_oa_location'):
                return data['best_oa_location'].get('url_for_pdf') or data['best_oa_location'].get('url')
        
        # Try Crossref as backup
        crossref_url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(crossref_url)
        
        if response.status_code == 200:
            data = response.json()
            urls = data.get('message', {}).get('link', [])
            for url in urls:
                if url.get('content-type', '').lower() == 'application/pdf':
                    return url.get('URL')
                
    except Exception as e:
        print(f"Error getting URL for DOI {doi}: {str(e)}")
    
    return None

def download_pdf(url, filename):
    """Download PDF from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200 and ('pdf' in response.headers.get('content-type', '').lower()):
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Download error: {str(e)}")
    return False

def download_papers_with_doi(excel_file, output_dir, start_row=0):
    """Download papers using DOIs until error occurs"""
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    pdf_dir = os.path.join(output_dir, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Read Excel file
    df = pd.read_excel(excel_file)
    df = df.iloc[start_row:]
    print(f"Starting from row {start_row} (total rows remaining: {len(df)})")
    
    # Load existing results
    results_file = os.path.join(output_dir, 'download_results.xlsx')
    if os.path.exists(results_file):
        existing_results = pd.read_excel(results_file)
        processed_dois = set(existing_results['DOI'])
        print(f"Found {len(processed_dois)} previously processed papers")
    else:
        existing_results = pd.DataFrame(columns=['ID', 'Title', 'DOI', 'URL', 'Status', 'PDF_Path'])
        processed_dois = set()
    
    papers_processed = 0
    
    for idx, row in df.iterrows():
        doi = row['DOI']
        title = row['Title']
        paper_id = row['ID']
        
        if not doi or pd.isna(doi) or doi in processed_dois:
            print(f"\nSkipping {paper_id}: No DOI or already processed")
            continue
        
        print(f"\nProcessing {idx} (ID: {paper_id}): {title}")
        print(f"DOI: {doi}")
        
        try:
            # Get paper URL
            url = get_paper_url(doi)
            
            if url:
                # Create filename
                safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
                pdf_filename = os.path.join(pdf_dir, f"{paper_id} {safe_title}.pdf")
                
                # Try to download
                if download_pdf(url, pdf_filename):
                    status = 'PDF Downloaded'
                    print(f"Downloaded PDF: {pdf_filename}")
                else:
                    status = 'Download Failed'
                    pdf_filename = ''
            else:
                status = 'No URL Found'
                pdf_filename = ''
                
            # Record result
            paper_info = {
                'ID': paper_id,
                'Title': title,
                'DOI': doi,
                'URL': url if url else '',
                'Status': status,
                'PDF_Path': pdf_filename
            }
            
            # Add to results
            new_result = pd.DataFrame([paper_info])
            existing_results = pd.concat([existing_results, new_result], ignore_index=True)
            existing_results.to_excel(results_file, index=False)
            
            papers_processed += 1
            print(f"Successfully processed {papers_processed} papers")
            
            # Add delay between requests
            time.sleep(3)
                
        except Exception as e:
            print(f"\nError processing {doi}: {str(e)}")
            print(f"Stopping after processing {papers_processed} papers")
            break  # Stop on any error
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    rootpath = '/Users/wenxinyang/Desktop/GitHub/3dhabitat_litreview/lit/AllJan25'
    excel_file = os.path.join(rootpath, "paper_dois.xlsx")
    output_dir = os.path.join(rootpath, "bulk_papers")
    
    download_papers_with_doi(excel_file, output_dir, start_row=20)