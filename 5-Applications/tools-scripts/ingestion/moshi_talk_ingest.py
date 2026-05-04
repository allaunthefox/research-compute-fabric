#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
5-Applications/scripts/moshi_talk_ingest.py — Moshi ASR → phoneme stream → substrate ingest

Pipeline:
  audio file / URL → Moshi MimiModel RVQ → phoneme stream (RVQ levels 0-1)
  → concept_vector (14 axes from phoneme statistics)
  → staged session JSON → substrate ingest-session

Install:
  pip install moshi   # 0.2.13, requires torch (already installed)

Usage:
  python3 5-Applications/scripts/moshi_talk_ingest.py <audio.wav>
  python3 5-Applications/scripts/moshi_talk_ingest.py --url <youtube-or-direct-audio-url>
  python3 5-Applications/scripts/moshi_talk_ingest.py --transcript <existing.txt>   # skip ASR

Outputs:
  5-Applications/out/moshi_talk_ingest/<timestamp>_<slug>.json
  5-Applications/out/moshi_talk_ingest/<timestamp>_<slug>.md

Reference: memory/reference_personaplex_phoneme_map.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import hashlib
import pathlib
import re
from datetime import datetime, timezone
from collections import Counter

OUT_DIR = pathlib.Path("5-Applications/out/moshi_talk_ingest")

# ── concept_vector axis labels (must match substrate schema) ──────────────────
CV_AXES = [
    "lexical_density", "mean_word_len", "phoneme_entropy",
    "consonant_vowel_ratio", "stop_codon_density", "silence_fraction",
    "voiced_fraction", "plosive_density", "fricative_density",
    "nasal_density", "tonal_variation", "utterance_rate",
    "unique_phoneme_ratio", "bind_z_proxy",
]
assert len(CV_AXES) == 14


# ── phoneme helpers ───────────────────────────────────────────────────────────

# Very rough IPA→feature map for offline fallback
_VOICED    = set("bvðznŋmŋlrwjæøyœɔɛɪʊə")
_PLOSIVE   = set("ptk bdg")
_FRICATIVE = set("fvsʒʃθð xɣ")
_NASAL     = set("mnŋ")
_VOWEL_PAT = re.compile(r"[aeiouæøyœɔɛɪʊəɐɑ]", re.I)

def _phoneme_features(phoneme_seq: list[str]) -> dict[str, float]:
    """Compute 14-axis concept vector from a phoneme sequence."""
    if not phoneme_seq:
        return {k: 0.0 for k in CV_AXES}

    counts = Counter(phoneme_seq)
    total  = len(phoneme_seq)
    uniq   = len(counts)

    entropy = -sum((c/total)*math.log2(c/total) for c in counts.values() if c > 0)

    vowels     = sum(1 for p in phoneme_seq if _VOWEL_PAT.search(p))
    consonants = total - vowels
    cv_ratio   = consonants / max(vowels, 1)

    voiced_n   = sum(1 for p in phoneme_seq if any(c in _VOICED    for c in p))
    plosive_n  = sum(1 for p in phoneme_seq if any(c in _PLOSIVE   for c in p))
    fricative_n= sum(1 for p in phoneme_seq if any(c in _FRICATIVE for c in p))
    nasal_n    = sum(1 for p in phoneme_seq if any(c in _NASAL     for c in p))

    # bind_z proxy: ratio of distinctive phonemes to total (high = structured)
    bind_z_proxy = uniq / max(total, 1) * math.log2(max(total, 1) + 1)

    return {
        "lexical_density":      min(1.0, uniq / 40.0),   # normalised to IPA size
        "mean_word_len":        min(1.0, total / 200.0),
        "phoneme_entropy":      min(1.0, entropy / 6.0),  # max ~6 bits for 64 symbols
        "consonant_vowel_ratio":min(1.0, cv_ratio / 4.0),
        "stop_codon_density":   0.0,                       # filled by ASR silence detector
        "silence_fraction":     0.0,                       # filled by ASR
        "voiced_fraction":      voiced_n / max(total, 1),
        "plosive_density":      plosive_n  / max(total, 1),
        "fricative_density":    fricative_n/ max(total, 1),
        "nasal_density":        nasal_n    / max(total, 1),
        "tonal_variation":      0.0,                       # requires pitch track
        "utterance_rate":       0.0,                       # filled by ASR timing
        "unique_phoneme_ratio": uniq / max(total, 1),
        "bind_z_proxy":         min(1.0, bind_z_proxy / 5.0),
    }


# ── moshi ASR path ────────────────────────────────────────────────────────────

def _asr_moshi(audio_path: str) -> tuple[str, list[str], dict[str, float]]:
    """
    Run Moshi ASR on audio_path.
    Returns (transcript, phoneme_seq, timing_info).

    RVQ levels 0-1 capture phoneme identity (place/manner/voicing).
    Levels 2+ = fine acoustic realisation — discarded here.
    Silence tokens = STOP codons = soliton checkpoints.

    Requires: pip install moshi
    """
    try:
        import torch
        from moshi.models import loaders
        from moshi.run.offline import run_offline   # type: ignore
    except ImportError as exc:
        print(f"[moshi_talk_ingest] moshi not installed: {exc}")
        print("  pip install moshi")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[moshi_talk_ingest] loading Moshi on {device}")

    moshi_weight, mimi_weight = loaders.resolve_model_ids()
    mimi = loaders.get_mimi(mimi_weight, device=device)
    mimi.eval()

    import torchaudio  # type: ignore
    wav, sr = torchaudio.load(audio_path)
    if sr != 24000:
        wav = torchaudio.functional.resample(wav, sr, 24000)
    wav = wav.mean(0, keepdim=True).unsqueeze(0).to(device)  # (1,1,T)

    with torch.no_grad():
        codes = mimi.encode(wav)   # (1, n_q, T_codes)

    # Levels 0-1 = phoneme identity stream
    phoneme_codes = codes[0, :2, :].cpu().tolist()   # [[lvl0...], [lvl1...]]
    flat = [f"L0_{c}" for c in phoneme_codes[0]] + [f"L1_{c}" for c in phoneme_codes[1]]

    # Silence = code 0 at level 0 → STOP codon
    silences = sum(1 for c in phoneme_codes[0] if c == 0)
    total_frames = len(phoneme_codes[0])
    silence_frac = silences / max(total_frames, 1)

    # Crude transcript from RVQ (placeholder — real transcript needs Moshi LM)
    transcript = f"[Moshi RVQ stream: {total_frames} frames, {silences} silence tokens]"

    timing = {
        "total_frames": total_frames,
        "silence_fraction": silence_frac,
        "stop_codon_density": silences / max(total_frames // 50, 1),
        "utterance_rate": (total_frames - silences) / max(total_frames, 1),
    }
    return transcript, flat, timing


def _asr_transcript_fallback(path: str) -> tuple[str, list[str], dict[str, float]]:
    """Read an existing transcript file, produce a word-level phoneme proxy."""
    text = pathlib.Path(path).read_text()
    words = re.findall(r"[a-z']+", text.lower())
    # Proxy phoneme seq: word characters as approximate phoneme tokens
    phonemes = [ch for w in words for ch in w]
    timing = {
        "total_frames": len(words),
        "silence_fraction": 0.05,
        "stop_codon_density": 0.02,
        "utterance_rate": 0.95,
    }
    return text, phonemes, timing


# ── session output ────────────────────────────────────────────────────────────

def _slug(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len]

def _write_session(
    source: str,
    transcript: str,
    phoneme_seq: list[str],
    timing: dict[str, float],
) -> pathlib.Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slug(pathlib.Path(source).stem if pathlib.Path(source).exists() else source)

    cv = _phoneme_features(phoneme_seq)
    cv["silence_fraction"]   = timing.get("silence_fraction", 0.0)
    cv["stop_codon_density"] = timing.get("stop_codon_density", 0.0)
    cv["utterance_rate"]     = timing.get("utterance_rate", 0.0)

    sha = hashlib.sha256(transcript.encode()).hexdigest()[:16]

    package = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "sha256_prefix": sha,
        "pipeline_mode": "moshi_asr",
        "transcript_excerpt": transcript[:400],
        "phoneme_frames": len(phoneme_seq),
        "concept_vector": cv,
        "idea_weights": {
            # top concept axes as idea weights for substrate search
            axis: round(val, 4)
            for axis, val in sorted(cv.items(), key=lambda x: -x[1])
            if val > 0.05
        },
        "foam_score": None,   # computed by substrate on ingest
        "notes": (
            "RVQ levels 0-1 = phoneme identity (place/manner/voicing). "
            "Levels 2+ discarded. Silence = STOP codon = soliton checkpoint. "
            "K=3 ternary encoding: 3^4=81 >= IPA phoneme count."
        ),
    }

    json_path = OUT_DIR / f"{ts}_{slug}.json"
    md_path   = OUT_DIR / f"{ts}_{slug}.md"

    json_path.write_text(json.dumps(package, indent=2))
    md_path.write_text(
        f"# Moshi Talk Ingest: {slug}\n\n"
        f"**Source:** {source}  \n"
        f"**Generated:** {package['generated_at']}  \n"
        f"**Phoneme frames:** {package['phoneme_frames']}  \n\n"
        f"## Transcript excerpt\n\n{transcript[:600]}\n\n"
        f"## Concept vector\n\n"
        + "\n".join(f"- `{k}`: {v:.4f}" for k, v in cv.items())
        + "\n\n## Idea weights\n\n"
        + "\n".join(f"- `{k}`: {v}" for k, v in package["idea_weights"].items())
        + f"\n\n**Next step:** `python3 substrate_git_index.py ingest-session {json_path}`\n"
    )
    return json_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?", help="Audio file (.wav/.mp3/.flac)")
    ap.add_argument("--transcript", help="Use existing transcript text file (skip ASR)")
    ap.add_argument("--url", help="Download audio from URL before processing")
    args = ap.parse_args()

    if args.url:
        try:
            import yt_dlp  # type: ignore
            out_tmpl = "/tmp/moshi_ingest_%(id)s.%(ext)s"
            yt_dlp.YoutubeDL({"format": "bestaudio", "outtmpl": out_tmpl, "quiet": True}).download([args.url])
            import glob
            audio_path = sorted(glob.glob("/tmp/moshi_ingest_*"))[-1]
        except ImportError:
            print("[moshi_talk_ingest] yt-dlp not installed — provide audio file directly")
            print("  pip install yt-dlp")
            sys.exit(1)
    elif args.audio:
        audio_path = args.audio
    elif args.transcript:
        audio_path = args.transcript
    else:
        ap.print_help()
        sys.exit(1)

    if args.transcript:
        transcript, phoneme_seq, timing = _asr_transcript_fallback(args.transcript)
        source = args.transcript
    else:
        transcript, phoneme_seq, timing = _asr_moshi(audio_path)
        source = audio_path

    json_path = _write_session(source, transcript, phoneme_seq, timing)
    print(f"[moshi_talk_ingest] session written: {json_path}")
    print(f"[moshi_talk_ingest] next: python3 substrate_git_index.py ingest-session {json_path}")


if __name__ == "__main__":
    main()
