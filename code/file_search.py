import os
import re
from pathlib import Path
from datetime import datetime

class FileSearch:
    def __init__(self, root_dir="."):
        """
        Initialize FileSearch with a root directory
        
        Args:
            root_dir (str): Root directory to start searches from
        """
        self.root_dir = root_dir

    def search_content(self, search_term, file_extensions=None, ignore_case=True):
        """
        Search for a term in all files within the root directory and its subdirectories.
        
        Args:
            search_term (str): Term to search for
            file_extensions (list): List of file extensions to search (e.g., ['.py', '.txt'])
            ignore_case (bool): Whether to perform case-insensitive search
        """
        results = []
        
        # Convert search term to lowercase if ignore_case is True
        if ignore_case:
            search_term = search_term.lower()
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                # Check file extension if specified
                if file_extensions and not any(file.endswith(ext) for ext in file_extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            search_line = line.lower() if ignore_case else line
                            
                            if search_term in search_line:
                                rel_path = os.path.relpath(file_path, self.root_dir)
                                results.append({
                                    'file': rel_path,
                                    'line_number': line_num,
                                    'line': line.strip(),
                                    'full_path': file_path
                                })
                except UnicodeDecodeError:
                    # Skip binary files
                    continue
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
        
        return results

    def list_by_date(self, file_extensions=None, reverse=True):
        """
        Get all files sorted by last modified date.
        
        Args:
            file_extensions (list): List of file extensions to include
            reverse (bool): If True, sorts newest to oldest
        """
        file_list = []
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file_extensions and not any(file.endswith(ext) for ext in file_extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    mod_time = datetime.fromtimestamp(mtime)
                    rel_path = os.path.relpath(file_path, self.root_dir)
                    
                    file_list.append({
                        'file': rel_path,
                        'modified': mod_time,
                        'full_path': file_path,
                        'size': os.path.getsize(file_path)
                    })
                except Exception as e:
                    print(f"Error accessing {file_path}: {str(e)}")
        
        return sorted(file_list, key=lambda x: x['modified'], reverse=reverse)

    @staticmethod
    def format_size(size):
        """Convert size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

def main():
    # Example usage
    searcher = FileSearch(".")
    
    # Search for content
    print("Content Search Example:")
    results = searcher.search_content("def", ['.py'])
    for result in results[:3]:  # Show first 3 results
        print(f"\nFile: {result['file']}")
        print(f"Line {result['line_number']}: {result['line']}")
        print("-" * 80)
    
    # List files by date
    print("\nFiles by Date Example:")
    files = searcher.list_by_date(['.py', '.txt'])
    for file_info in files[:3]:  # Show first 3 files
        print(f"\nFile: {file_info['file']}")
        print(f"Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Size: {FileSearch.format_size(file_info['size'])}")
        print("-" * 80)

if __name__ == "__main__":
    main() 