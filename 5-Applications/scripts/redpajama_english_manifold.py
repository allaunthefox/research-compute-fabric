#!/usr/bin/env python3
"""
REDPAJAMA ENGLISH MANIFOLD BUILDER

Ingest the RedPajama dataset (or a representative subset) and build the
mathematical model of English at scale. RedPajama contains:

  - Common Crawl:      ~878B tokens
  - C4:                ~175B tokens  
  - GitHub:            ~59B tokens
  - Books:             ~26B tokens
  - Wikipedia:         ~24B tokens
  - ArXiv:             ~28B tokens
  - StackExchange:     ~20B tokens
  
Total: ~1.2 TRILLION tokens

This script:
  1. Streams RedPajama data (or compatible JSONL/parquet)
  2. Extracts sentences with lightweight filtering
  3. Builds structural invariant fingerprints
  4. Updates the English language manifold incrementally
  5. Computes compression metrics at scale
  6. Outputs a production-ready grammar model

Usage:
  python redpajama_english_manifold.py --input /path/to/redpajama/*.jsonl --limit 1000000
"""

import os
import re
import sys
import json
import math
import gzip
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterator, Optional

# ── Configuration ──────────────────────────────────────────────────────────────

BASE = Path("/home/allaun/Documents/Research Stack")
OUTDIR = BASE / "3-Mathematical-Models/redpajama_english_manifold"
OUTDIR.mkdir(parents=True, exist_ok=True)

# POS tag dictionaries (same as unified model)
CLOSED = {'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','as',
          'is','was','are','were','be','been','being','have','has','had','do','does','did','will',
          'would','could','should','may','might','can','shall','this','that','these','those','it',
          'its','they','them','their','he','she','his','her','him','we','us','our','you','your',
          'my','mine','i','me','who','which','what','when','where','why','how','all','each',
          'every','both','either','neither','some','any','no','none','more','most','many','much',
          'few','little','other','another','such','only','own','same','so','than','too','very',
          'just','now','then','here','there','up','down','out','off','over','under','again',
          'further','once','not','also','always','never','often','sometimes','usually','still'}
PREP = {'in','on','at','by','for','with','about','against','between','into','through','during',
        'before','after','above','below','to','from','up','down','of','off','over','under',
        'again','further','then','once','around','behind','beyond','despite','except','inside',
        'near','past','since','toward','upon','within','without','across','along','among',
        'beside','besides','concerning','considering','following','including','like','minus',
        'plus','regarding','round','save','till','until','via','worth'}
CONJ = {'and','or','but','nor','yet','so','for','although','because','before','if','since',
        'though','unless','until','when','while','whereas','whether','either','neither',
        'both','not','only','than','rather','however','moreover','furthermore','nevertheless',
        'otherwise','therefore','thus','hence','consequently','meanwhile'}
AUX = {'be','am','is','are','was','were','being','been','have','has','had','do','does','did',
       'will','would','shall','should','may','might','can','could','must','ought','need',
       'dare','used','get','gets','got','getting','become','becomes','became','seem','seems',
       'seemed','appear','appears','appeared'}
PRON = {'i','me','my','mine','myself','you','your','yours','yourself','he','him','his',
        'himself','she','her','hers','herself','it','its','itself','we','us','our','ours',
        'ourselves','they','them','their','theirs','themselves','this','that','these','those',
        'who','whom','whose','which','what','whatever','whoever','whomever','anyone','someone',
        'everyone','nobody','nothing','something','anything','everything'}
DET = {'the','a','an','this','that','these','those','my','your','his','her','its','our',
       'their','some','any','no','each','every','either','neither','both','all','half',
       'enough','several','many','much','few','little','other','another','such','what',
       'which','whose','one','two','three','first','last','next','various','certain'}

def tag(word: str) -> str:
    w = word.lower().strip("'\"")
    if w in DET: return "DET"
    if w in PRON: return "PRON"
    if w in PREP: return "PREP"
    if w in CONJ: return "CONJ"
    if w in AUX: return "AUX"
    if w in CLOSED: return "FUNC"
    if w.endswith("ing"): return "VBG"
    if w.endswith("ed"): return "VBN"
    if w.endswith(("ly","ily","ally")): return "ADV"
    if w.endswith(("tion","sion","ment","ness","ity","ance","ence","hood","ship")): return "NOUN"
    if w.endswith(("able","ible","ful","ous","ive","less","ish","al")): return "ADJ"
    if w.endswith(("ize","ise","ify","ate")): return "VERB"
    if len(w) <= 3: return "SHORT"
    return "LEX"

def fingerprint(sentence: str) -> str:
    """Structural invariant fingerprint of a sentence."""
    words = re.findall(r"[a-zA-Z']+", sentence)
    if len(words) < 3 or len(words) > 40:
        return ""
    tags = [tag(w) for w in words]
    collapsed = []
    prev = None
    for t in tags:
        if t != prev:
            collapsed.append(t)
            prev = t
        elif t == "LEX" and (len(collapsed) < 2 or collapsed[-2] != "LEX+"):
            collapsed[-1] = "LEX+"
    return " ".join(collapsed)

def classify_form(fp: str) -> str:
    """Classify invariant form into grammatical category."""
    tags = fp.split()
    if not tags:
        return "OTHER"
    if "DET" in tags and "NOUN" in tags and "VERB" in tags:
        if tags.index("VERB") > tags.index("NOUN"):
            return "SVO"
        else:
            return "VSO"
    elif "DET" in tags and "NOUN" in tags and "PREP" in tags:
        return "NP_PP"
    elif "AUX" in tags and "VERB" in tags:
        return "AUX_V"
    elif "CONJ" in tags:
        return "COMPOUND"
    elif "PRON" in tags and "VERB" in tags:
        return "PRON_V"
    elif tags.count("PREP") >= 2:
        return "PP_CHAIN"
    elif "LEX+" in tags:
        return "DENSE_NP"
    else:
        return "OTHER"

# ── Streaming Data Sources ─────────────────────────────────────────────────────

def stream_jsonl(path: Path, text_field: str = "text") -> Iterator[str]:
    """Stream text from JSONL (potentially gzipped)."""
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get(text_field, '')
                if text:
                    yield text
            except json.JSONDecodeError:
                continue

def stream_enwik9(path: Path) -> Iterator[str]:
    """Stream text from enwik9 XML."""
    raw = path.read_bytes()
    text_blocks = re.findall(rb'<text[^>]*>(.*?)</text>', raw, re.DOTALL)
    for block in text_blocks:
        text = block.decode('utf-8', errors='ignore')
        text = re.sub(r'\{\{.*?\}\}', ' ', text, flags=re.DOTALL)
        text = re.sub(r'\[\[.*?\|', ' ', text)
        text = re.sub(r'\[\[|\]\]', ' ', text)
        text = re.sub(r"'{2,}", ' ', text)
        text = re.sub(r'<.*?>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'&\w+;', ' ', text)
        text = re.sub(r'https?://\S+', ' ', text)
        text = re.sub(r'[#*|=\{\}\[\]\|]', ' ', text)
        yield text

# ── Manifold Builder ──────────────────────────────────────────────────────────

class IncrementalManifold:
    """Build English invariant manifold incrementally from streaming data."""
    
    def __init__(self, max_forms: int = 10_000_000):
        self.forms = Counter()
        self.examples = defaultdict(list)
        self.sentences_processed = 0
        self.bytes_processed = 0
        self.max_forms = max_forms
        
    def ingest_text(self, text: str, max_sentences: Optional[int] = None):
        """Process raw text into sentences and update manifold."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        count = 0
        for sent in sentences:
            sent = sent.strip()
            if 10 < len(sent) < 300 and sent[0].isupper():
                fp = fingerprint(sent)
                if fp and len(fp.split()) >= 3:
                    self.forms[fp] += 1
                    if len(self.examples[fp]) < 3:
                        self.examples[fp].append(sent)
                    self.sentences_processed += 1
                    count += 1
                    if max_sentences and count >= max_sentences:
                        break
        self.bytes_processed += len(text.encode('utf-8'))
        return count
    
    def taxonomy(self) -> dict:
        """Compute grammatical category distribution."""
        cats = Counter()
        for fp, count in self.forms.items():
            cats[classify_form(fp)] += count
        return dict(cats)
    
    def compute_entropy(self) -> float:
        """Shannon entropy of the invariant distribution."""
        total = sum(self.forms.values())
        if total == 0:
            return 0.0
        entropy = 0.0
        for count in self.forms.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def top(self, n: int = 100) -> list:
        return self.forms.most_common(n)
    
    def save(self, path: Path, limit_examples: int = 1000):
        """Save manifold to JSON."""
        top_forms = self.top(limit_examples)
        report = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "sentences_processed": self.sentences_processed,
            "bytes_processed": self.bytes_processed,
            "unique_forms": len(self.forms),
            "shannon_entropy_bits": round(self.compute_entropy(), 4),
            "taxonomy": self.taxonomy(),
            "top_forms": [{"fingerprint": fp, "count": c, "example": self.examples[fp][0][:120] if fp in self.examples else ""} for fp, c in top_forms],
        }
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Saved manifold: {path}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build English manifold from RedPajama-scale data")
    parser.add_argument("--input", type=Path, nargs="+", help="Input file(s) - JSONL or enwik9 XML")
    parser.add_argument("--limit", type=int, default=1_000_000, help="Max sentences to process")
    parser.add_argument("--batch-save", type=int, default=100_000, help="Save checkpoint every N sentences")
    parser.add_argument("--text-field", default="text", help="JSON field containing text")
    args = parser.parse_args()
    
    print("=" * 70)
    print("  REDPAJAMA ENGLISH MANIFOLD BUILDER")
    print("  Target: Scale invariant model to millions/billions of sentences")
    print("=" * 70)
    
    manifold = IncrementalManifold(max_forms=10_000_000)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine source type and stream
    if not args.input:
        # Default: use enwik9_purified.bin
        default_path = BASE / "shared-data/data/hutter_archive/enwik9_purified.bin"
        print(f"\nNo --input specified. Using default: {default_path}")
        args.input = [default_path]
    
    for path in args.input:
        print(f"\nProcessing: {path}")
        
        if path.name == "enwik9_purified.bin" or path.suffix == '.xml':
            stream = stream_enwik9(path)
        else:
            stream = stream_jsonl(path, text_field=args.text_field)
        
        for text in stream:
            count = manifold.ingest_text(text)
            if manifold.sentences_processed >= args.limit:
                print(f"  Reached limit: {args.limit:,} sentences")
                break
            
            # Checkpoint
            if manifold.sentences_processed % args.batch_save == 0:
                print(f"  Checkpoint: {manifold.sentences_processed:,} sentences, {len(manifold.forms):,} forms")
                ckpt = OUTDIR / f"manifold_checkpoint_{manifold.sentences_processed}_{ts}.json"
                manifold.save(ckpt, limit_examples=500)
        
        if manifold.sentences_processed >= args.limit:
            break
    
    # Final report
    print(f"\n{'='*70}")
    print("  MANIFOLD BUILD COMPLETE")
    print(f"{'='*70}")
    print(f"  Sentences processed:    {manifold.sentences_processed:,}")
    print(f"  Bytes processed:        {manifold.bytes_processed:,}")
    print(f"  Unique forms:             {len(manifold.forms):,}")
    print(f"  Shannon entropy:          {manifold.compute_entropy():.2f} bits/form")
    
    print(f"\n  Taxonomy:")
    cats = manifold.taxonomy()
    total = sum(cats.values())
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:12s}: {cnt:>8,} ({cnt/total*100:.1f}%)")
    
    print(f"\n  Top 20 forms:")
    for fp, cnt in manifold.top(20):
        print(f"    {cnt:>6,}  {fp}")
    
    # Save final
    final_path = OUTDIR / f"redpajama_english_manifold_{ts}.json"
    manifold.save(final_path, limit_examples=2000)
    
    print(f"\n{'='*70}")
    print(f"  Final manifold: {final_path}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
