#!/usr/bin/env python3
import os
import re
import sys
import time
import urllib.request
import ssl

ssl_context = ssl._create_unverified_context()

def get_arxiv_links(url):
    """
    Fetch the arXiv page and extract all PDF links.
    """
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            html = response.read().decode('utf-8')
            # Look for /pdf/YYMM.NNNNN or similar patterns
            links = re.findall(r'/pdf/[0-9]{4}\.[0-9]{4,5}', html)
            # De-duplicate while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            return unique_links
    except Exception as e:
        print(f"Error fetching arXiv page: {e}", file=sys.stderr)
        return []

def main():
    arxiv_list_url = "https://arxiv.org/list/math/recent?skip=0&show=2000"
    output_dir = "./arxiv_papers"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Fetching recent math papers list from arXiv...")
    pdf_paths = get_arxiv_links(arxiv_list_url)
    total_papers = len(pdf_paths)
    
    if total_papers == 0:
        print("No papers found. Exiting.")
        return
        
    print(f"Found {total_papers} papers to download.")
    print(f"Starting sequential download with a 4-second delay to avoid rate limits...")
    print(f"Target directory: {output_dir}\n")
    
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    for idx, path in enumerate(pdf_paths):
        paper_id = path.split('/')[-1]
        filename = f"{paper_id}.pdf"
        dest_path = os.path.join(output_dir, filename)
        pdf_url = f"https://arxiv.org{path}"
        
        # Resume capability: check if file already exists and is non-empty
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            print(f"[{idx+1}/{total_papers}] Skipping {paper_id} (already downloaded)")
            skipped_count += 1
            continue
            
        print(f"[{idx+1}/{total_papers}] Downloading {paper_id} from {pdf_url}...")
        
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"}
        req = urllib.request.Request(pdf_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                with open(dest_path, 'wb') as f:
                    f.write(response.read())
            print(f"[{idx+1}/{total_papers}] Successfully saved {paper_id}")
            downloaded_count += 1
            # Sleep to prevent IP block
            time.sleep(4)
        except Exception as e:
            print(f"[{idx+1}/{total_papers}] Failed to download {paper_id}: {e}", file=sys.stderr)
            failed_count += 1
            # Sleep a bit longer on failure
            time.sleep(10)
            
    print("\n=== Download Session Finished ===")
    print(f"Total Papers: {total_papers}")
    print(f"Downloaded:   {downloaded_count}")
    print(f"Skipped:      {skipped_count}")
    print(f"Failed:       {failed_count}")

if __name__ == "__main__":
    main()
