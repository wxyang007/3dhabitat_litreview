import requests
import re
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from slugify import slugify
import pandas as pd
from datetime import datetime

class SciHubDownloader:
    def __init__(self, download_dir="papers", excel_path="scihub_dlwd_info.xlsx", log_path="download_log.xlsx"):
        # Sci-Hub mirrors can change, so it's good to have multiple options
        self.scihub_urls = [
            "https://sci-hub.ru/",
            "https://sci-hub.se/",
            "https://sci-hub.st/",
            "https://sci-hub.ee/",
            "https://sci-hub.ren/",
            "https://sci-hub.wf/",
            # Add more mirrors as needed
        ]
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.df = pd.read_excel(excel_path)
        self.log_path = log_path
        self.download_results = []
        
    def get_working_url(self):
        """Test mirrors and return the first working one."""
        for url in self.scihub_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return url
            except:
                continue
        raise Exception("No working Sci-Hub mirror found")

    def clean_title(self, title):
        """Clean and format the title for filename."""
        return slugify(title)[:100]  # Limit length to avoid too long filenames

    def save_download_log(self):
        """Save download results to Excel file."""
        log_df = pd.DataFrame(self.download_results, columns=[
            'ID', 'DOI', 'Title', 'Status', 'File Path', 'Error Message', 'Timestamp'
        ])
        log_df.to_excel(self.log_path, index=False)

    def download_paper(self, doi, title, paper_id):
        """Download paper from Sci-Hub using DOI."""
        base_url = self.get_working_url()
        result = {
            'ID': paper_id,
            'DOI': doi,
            'Title': title,
            'Status': 'Failed',
            'File Path': '',
            'Error Message': '',
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Create the full URL
            paper_url = urljoin(base_url, doi)
            
            # Get the Sci-Hub page
            response = requests.get(paper_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the PDF link
            pdf_iframe = soup.find('iframe', id='pdf')
            if not pdf_iframe:
                raise Exception(f"Could not find PDF for DOI: {doi}")
                
            pdf_url = pdf_iframe.get('src')
            if pdf_url.startswith('//'):
                pdf_url = 'https:' + pdf_url
            
            # Download the PDF
            pdf_response = requests.get(pdf_url)
            
            # Create filename with new format
            safe_title = self.clean_title(title)
            filename = f"{paper_id} {safe_title}.pdf"
            filepath = os.path.join(self.download_dir, filename)
            
            # Save the PDF
            with open(filepath, 'wb') as f:
                f.write(pdf_response.content)
            
            # Update result with success
            result.update({
                'Status': 'Success',
                'File Path': filepath,
            })
            return filepath
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading {doi}: {error_msg}")
            # Update result with error
            result.update({
                'Error Message': error_msg
            })
            return None
        finally:
            self.download_results.append(result)

def main():
    # Create an instance of SciHubDownloader
    downloader = SciHubDownloader()
    
    # Use this instance to download papers
    for _, row in downloader.df.iterrows():
        print(f"Downloading: {row['Title']}")
        filepath = downloader.download_paper(
            doi=row['DOI'],
            title=row['Title'],
            paper_id=row['ID']
        )
        if filepath:
            print(f"Successfully downloaded to: {filepath}")
        else:
            print(f"Failed to download paper with DOI: {row['DOI']}")
    
    # Save download results
    downloader.save_download_log()
    print(f"\nDownload log saved to: {downloader.log_path}")

if __name__ == "__main__":
    main() 