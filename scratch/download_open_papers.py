#!/usr/bin/env python3
import os
import sys
import time
import urllib.request
import json
import urllib.parse
import ssl

# Bypass SSL verification if needed (common in local environments/proxies)
ssl_context = ssl._create_unverified_context()

def openalex_search(query, polite_email="allaunthefox@gmail.com"):
    """
    Search OpenAlex works for a given query and return a list of matching papers with PDF links.
    """
    headers = {
        "User-Agent": f"OpenAlexDownloader/1.0 (mailto:{polite_email})"
    }
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={encoded_query}&per-page=5"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            data = json.loads(response.read().decode())
            results = data.get("results", [])
            return results
    except Exception as e:
        print(f"Error querying OpenAlex for '{query}': {e}", file=sys.stderr)
        return []

def download_pdf(pdf_url, output_path, polite_email="allaunthefox@gmail.com"):
    """
    Download a PDF file from a given URL to the output path.
    """
    headers = {
        "User-Agent": f"OpenAlexDownloader/1.0 (mailto:{polite_email})"
    }
    req = urllib.request.Request(pdf_url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Failed to download from {pdf_url}: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 download_open_papers.py <query_or_arxiv_id> [output_directory]")
        print("Example: python3 download_open_papers.py \"inverse matrices Gauss-Jordan\" ./papers")
        sys.exit(1)
        
    query = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./downloaded_papers"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Searching OpenAlex for: '{query}'...")
    works = openalex_search(query)
    
    if not works:
        print("No works found.")
        return
        
    downloaded_count = 0
    for idx, work in enumerate(works):
        title = work.get("display_name", "untitled")
        doi = work.get("doi")
        
        # Clean title for filename
        safe_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in title])[:60].strip()
        work_id = work.get("id", "").split("/")[-1]
        filename = f"{safe_title}_{work_id}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        # Try to find a PDF link
        pdf_url = None
        best_location = work.get("best_oa_location")
        if best_location and best_location.get("pdf_url"):
            pdf_url = best_location.get("pdf_url")
        else:
            # Check alternative locations
            for loc in work.get("locations", []):
                if loc.get("pdf_url"):
                    pdf_url = loc.get("pdf_url")
                    break
                    
        if pdf_url:
            print(f"\nFound Open Access PDF for: \"{title}\"")
            print(f"URL: {pdf_url}")
            print(f"Downloading to: {output_path}...")
            
            success = download_pdf(pdf_url, output_path)
            if success:
                print("Download complete!")
                downloaded_count += 1
            
            # Safe sequential delay to respect rate limits
            time.sleep(3)
        else:
            print(f"\nWork found but no Open Access PDF link available: \"{title}\" (DOI: {doi})")
            
    print(f"\nDone. Successfully downloaded {downloaded_count} paper(s) to '{output_dir}'.")

if __name__ == "__main__":
    main()
