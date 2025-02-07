from pyzotero import zotero
import os
from datetime import datetime
import pandas as pd

class ZoteroExporter:
    def __init__(self, library_id, api_key, library_type='user'):
        """
        Initialize Zotero connection
        
        Args:
            library_id (str): Your Zotero library ID
            api_key (str): Your Zotero API key
            library_type (str): 'user' or 'group'
        """
        self.zot = zotero.Zotero(library_id, library_type, api_key)
    
    def export_collection(self, collection_key, output_file):
        """
        Export items from a specific collection to an Excel file
        
        Args:
            collection_key (str): The collection key to export
            output_file (str): Path to output Excel file
        """
        # Get all items in collection
        items = self.zot.collection_items(collection_key)
        
        # Prepare data for DataFrame
        data = []
        for item in items:
            # Access the data dictionary
            item_data = item.get('data', {})
            
            if item_data.get('itemType') == 'attachment':
                continue  # Skip standalone attachments
            
            # Get basic information
            title = item_data.get('title', 'No Title')
            authors = '; '.join([author.get('firstName', '') + ' ' + author.get('lastName', '') 
                               for author in item_data.get('creators', [])])
            year = item_data.get('date', '')[:4] if item_data.get('date') else 'No Year'
            doi = item_data.get('DOI', 'No DOI')
            
            # Get attachment information
            attachments = self.zot.children(item_data.get('key', ''))
            has_pdf = any(att.get('data', {}).get('contentType') == 'application/pdf' 
                         for att in attachments)
            
            pdf_files = ', '.join([att.get('data', {}).get('filename', '') 
                                 for att in attachments 
                                 if att.get('data', {}).get('contentType') == 'application/pdf'])
            
            # Add to data list
            data.append({
                'Title': title,
                'Authors': authors,
                'Year': year,
                'DOI': doi,
                'Has PDF': 'Yes' if has_pdf else 'No',
                'PDF Files': pdf_files if has_pdf else ''
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel writer with datetime in filename
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Papers', index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Papers']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Items', 'Items with PDF', 'Items without PDF'],
                'Count': [
                    len(data),
                    df['Has PDF'].value_counts().get('Yes', 0),
                    df['Has PDF'].value_counts().get('No', 0)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Auto-adjust summary columns
            worksheet = writer.sheets['Summary']
            for idx, col in enumerate(summary_df.columns):
                max_length = max(
                    summary_df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length

def main():
    # Your Zotero credentials
    LIBRARY_ID = '8436705'
    API_KEY = 'HWRNx1XyaHme2clCfDxYtZb2'
    COLLECTION_KEY = '8EMHKYBB'  # Replace with your actual collection key from the URL
    
    # Create exporter
    exporter = ZoteroExporter(LIBRARY_ID, API_KEY)
    
    # Export to Excel file
    output_file = f"zotero_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    exporter.export_collection(COLLECTION_KEY, output_file)
    print(f"Export completed. Check {output_file}")

if __name__ == "__main__":
    main() 