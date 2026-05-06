#!/usr/bin/env python3
"""
Download multilingual corpora for PIST framework testing.
Uses HuggingFace datasets for reliable access to large multilingual text.
"""

import os
import sys

def ensure_datasets():
    try:
        from datasets import load_dataset
        return load_dataset
    except ImportError:
        print("Installing datasets library...")
        os.system("pip install -q datasets")
        from datasets import load_dataset
        return load_dataset

def download_c4_multilingual():
    """Download multilingual C4 corpus (mC4) for various languages."""
    load_dataset = ensure_datasets()

    output_dir = "/home/allaun/Documents/Research Stack/data/corpora/mc4"
    os.makedirs(output_dir, exist_ok=True)

    # Languages to download (prioritizing non-Latin scripts + high-resource)
    languages = [
        # Latin scripts
        ("en", "English"),
        ("de", "German"),
        ("fr", "French"),
        ("es", "Spanish"),
        ("pt", "Portuguese"),
        ("it", "Italian"),
        ("nl", "Dutch"),
        ("pl", "Polish"),
        ("ru", "Russian"),  # Cyrillic
        # Non-Latin scripts
        ("zh", "Chinese"),   # CJK
        ("ja", "Japanese"),  # CJK
        ("ko", "Korean"),    # CJK
        ("ar", "Arabic"),    # Arabic script
        ("hi", "Hindi"),     # Devanagari
        ("tr", "Turkish"),   # Latin with diacritics
        ("vi", "Vietnamese"), # Latin with tone marks
    ]

    for lang_code, lang_name in languages:
        try:
            print(f"Downloading {lang_name} ({lang_code})...")
            ds = load_dataset("mc4", lang_code, split="train", streaming=True, trust_remote_code=True)

            # Save first 100K examples (~100MB text)
            output_file = os.path.join(output_dir, f"{lang_code}_sample.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                count = 0
                for example in ds:
                    text = example.get("text", "")
                    if text:
                        f.write(text + "\n")
                        count += 1
                        if count >= 100000:
                            break

            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"  Saved {count} examples, {size_mb:.1f}MB -> {output_file}")

        except Exception as e:
            print(f"  ERROR downloading {lang_name}: {e}")
            continue

def download_opus_parallel():
    """Download OPUS parallel corpus for cross-lingual testing."""
    load_dataset = ensure_datasets()

    output_dir = "/home/allaun/Documents/Research Stack/data/corpora/opus"
    os.makedirs(output_dir, exist_ok=True)

    # Wikipedia parallel text
    try:
        print("Downloading OPUS Wikipedia (English-Spanish parallel)...")
        ds = load_dataset("opus_wikipedia", "en-es", split="train")

        with open(os.path.join(output_dir, "opus_wikipedia_en.txt"), "w", encoding="utf-8") as f:
            for i, example in enumerate(ds):
                f.write(example["translation"]["en"] + "\n")
                if i >= 50000:
                    break

        with open(os.path.join(output_dir, "opus_wikipedia_es.txt"), "w", encoding="utf-8") as f:
            for i, example in enumerate(ds):
                f.write(example["translation"]["es"] + "\n")
                if i >= 50000:
                    break

        print("  Saved OPUS Wikipedia EN-ES parallel corpus")
    except Exception as e:
        print(f"  ERROR: {e}")

def download_wikipedia_dumps():
    """Download raw Wikipedia dumps for specific languages."""
    import urllib.request

    output_dir = "/home/allaun/Documents/Research Stack/data/corpora/wikipedia"
    os.makedirs(output_dir, exist_ok=True)

    # Wikipedia dump URLs for specific languages (latest)
    wikis = [
        ("en", "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2"),
        ("de", "https://dumps.wikimedia.org/dewiki/latest/dewiki-latest-pages-articles.xml.bz2"),
        ("zh", "https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles.xml.bz2"),
        ("ja", "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles.xml.bz2"),
        ("ar", "https://dumps.wikimedia.org/arwiki/latest/arwiki-latest-pages-articles.xml.bz2"),
    ]

    for lang, url in wikis:
        output_path = os.path.join(output_dir, f"{lang}wiki-latest-pages-articles.xml.bz2")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000000:
            print(f"Skipping {lang}wiki (already downloaded)")
            continue

        print(f"Downloading {lang}wiki dump...")
        try:
            urllib.request.urlretrieve(url, output_path)
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  Saved {size_mb:.0f}MB")
        except Exception as e:
            print(f"  ERROR: {e}")

def main():
    print("=" * 60)
    print("Multilingual Corpus Download for PIST Framework")
    print("=" * 60)

    # Priority: mC4 for non-Latin scripts + diverse languages
    print("\n--- mC4 Multilingual Corpus ---")
    download_c4_multilingual()

    print("\n--- OPUS Parallel Corpus ---")
    download_opus_parallel()

    print("\n--- Wikipedia Dumps ---")
    print("Note: Wikipedia dumps are very large (1-50GB each).")
    print("Skipping by default. Uncomment to enable.")
    # download_wikipedia_dumps()

    print("\n" + "=" * 60)
    print("Downloads complete. Check data/corpora/ for results.")
    print("=" * 60)

if __name__ == "__main__":
    main()
