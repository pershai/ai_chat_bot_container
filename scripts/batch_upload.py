import os
import argparse
import requests

def batch_upload(directory: str, api_url: str):
    """
    Uploads all PDF files in the specified directory to the API.
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in '{directory}'.")
        return

    print(f"Found {len(pdf_files)} PDF files. Starting upload...")

    for filename in pdf_files:
        file_path = os.path.join(directory, filename)
        print(f"Uploading '{filename}'...", end=" ")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = requests.post(api_url, files=files)
                
            if response.status_code == 200:
                print("Success")
            else:
                print(f"Failed (Status: {response.status_code})")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch upload PDFs to the AI Chat Bot.")
    parser.add_argument("directory", help="Path to the directory containing PDF files.")
    parser.add_argument("--url", default="http://localhost:8000/upload", help="API upload endpoint URL.")
    
    args = parser.parse_args()
    
    batch_upload(args.directory, args.url)
