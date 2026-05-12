#!/usr/bin/env python3
"""Targeted ingest for the prehensile-tail / BraidStorm ChatGPT session."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/allaun/Documents/Research Stack")
SOURCE = Path("/home/allaun/Documents/ingest/ChatGPT-Prehensile_Fox_Tail_Possibility.json")
OUT_DIR = ROOT / "data" / "ingested" / "chatgpt"
WIKI_DIR = ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
DB = ROOT / "data" / "substrate_index.db"
RECEIPT = ROOT / "4-Infrastructure" / "shim" / "prehensile_tail_session_ingest_receipt.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def transcript(messages: list[dict]) -> str:
    blocks = []
    for msg in messages:
        role = str(msg.get("role", "unknown")).upper()
        stamp = msg.get("timestamp", "unknown-time")
        content = msg.get("content", "")
        blocks.append(f"[{role}][{stamp}]\n{content}")
    return "\n\n---\n\n".join(blocks)


def count_terms(text: str) -> dict[str, int]:
    terms = [
        "tail",
        "prehensile",
        "embodiment",
        "control",
        "feedback",
        "haptic",
        "proprioception",
        "autopath",
        "bci",
        "braid",
        "braidstorm",
        "famm",
        "sid",
        "c64",
        "retrocomputing",
    ]
    lower = text.lower()
    return {term: lower.count(term) for term in terms if lower.count(term)}


def pkg_name(title: str) -> str:
    return f"aiscroll/{slugify(title)}"


def ensure_package(title: str, body: str, kind: str, tags: list[str], sigma: dict) -> dict:
    pkg = pkg_name(title)
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "select rowid, version from packages where pkg = ? and sha256 = ? order by rowid desc limit 1",
            (pkg, sha),
        ).fetchone()
        if row:
            return {"ok": True, "pkg": pkg, "version": row[1], "rowid": row[0], "reused": True}

        version = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")
        now = datetime.now(timezone.utc).isoformat()
        description = (
            f"[SIGMA: {sigma.get('sigma_codon', 'UNK')}] {sigma.get('classify', 'FORMING')}\n"
            f"OBSERVE: {sigma.get('observe', '')}\n"
            f"PROVE: {sigma.get('prove', '')}\n---\n"
            f"{body[:500]}"
        )
        cur = conn.execute(
            """
            insert into packages (
              pkg, version, tier, domain, archetype, description, tags, source,
              session_id, notion_id, sha256, indexed_utc, model_status, foam_score,
              verification_basis, idea_weights, extension_points, concept_vector,
              analog_map, concept_anchor, audit_rationale
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pkg,
                version,
                "RESEARCH",
                "neural_embodiment",
                kind,
                description,
                json.dumps(tags, sort_keys=True),
                "YourAIScroll",
                "https://chatgpt.com/c/69fcc09f-37dc-83ea-8df8-0a22c5c74a61",
                None,
                sha,
                now,
                "INGESTED",
                0.0,
                sha,
                json.dumps({}),
                json.dumps([]),
                json.dumps(tags, sort_keys=True),
                json.dumps(sigma, sort_keys=True),
                json.dumps({"domain": "neural_embodiment", "concept": title, "resolution": "FORMING"}),
                json.dumps(sigma, sort_keys=True),
            ),
        )
        conn.commit()
        return {"ok": True, "pkg": pkg, "version": version, "rowid": cur.lastrowid, "reused": False}
    finally:
        conn.close()


def update_existing_package(pkg: str, body: str, tags: list[str], sigma: dict) -> dict:
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "select rowid, version from packages where pkg = ? order by rowid desc limit 1",
            (pkg,),
        ).fetchone()
        if not row:
            return {"ok": False, "pkg": pkg, "reason": "missing"}
        description = (
            f"[SIGMA: {sigma.get('sigma_codon', 'UNK')}] {sigma.get('classify', 'FORMING')}\n"
            f"OBSERVE: {sigma.get('observe', '')}\n"
            f"PROVE: {sigma.get('prove', '')}\n---\n"
            f"{body[:500]}"
        )
        conn.execute(
            """
            update packages
            set sha256 = ?,
                verification_basis = ?,
                description = ?,
                tags = ?,
                concept_vector = ?,
                analog_map = ?,
                audit_rationale = ?
            where rowid = ?
            """,
            (
                sha,
                sha,
                description,
                json.dumps(tags, sort_keys=True),
                json.dumps(tags, sort_keys=True),
                json.dumps(sigma, sort_keys=True),
                json.dumps(sigma, sort_keys=True),
                row[0],
            ),
        )
        conn.commit()
        return {"ok": True, "pkg": pkg, "version": row[1], "rowid": row[0], "sha256": sha}
    finally:
        conn.close()


def tiddler(title: str, tags: str, body: str) -> str:
    return (
        "created: 20260507000000000\n"
        "modified: 20260507000000000\n"
        f"tags: {tags}\n"
        f"title: {title}\n"
        "type: text/vnd.tiddlywiki\n\n"
        f"! {title}\n\n"
        f"{body.strip()}\n"
    )


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    messages = data["messages"]
    body = transcript(messages)
    source_hash = sha256_path(SOURCE)
    transcript_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    counts = count_terms(body)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    source_copy = OUT_DIR / "prehensile_fox_tail_possibility_source.json"
    shutil.copyfile(SOURCE, source_copy)

    targeted_brief = OUT_DIR / "prehensile_fox_tail_possibility_targeted_brief.md"
    targeted_text = f"""# Prehensile Fox Tail Possibility - Targeted ENE Brief

Source export: `{SOURCE}`
Chat URL: {data.get("url", "not recorded")}
Timestamp: {data.get("timestamp", "not recorded")}
Messages: {len(messages)}
Source SHA-256: `{source_hash}`
Transcript SHA-256: `{transcript_hash}`

## Core Read

This session should be interpreted as a neural embodiment and control-surface prior, not as a literal biological promise.

The useful concept is:

```text
non-native appendage control
  = body-schema plasticity
  + low-bandwidth intent inference
  + autopath sensing
  + reflex safety
  + haptic/proprioceptive feedback
  + receipt-bounded claim discipline
```

For the Research Stack, the prehensile-tail idea is a concrete test shape for learned appendage control. The operator should not consciously drive each actuator. A better surface is a small set of intent primitives such as brace, counterbalance, reach, wrap, signal, and retract, with a local controller resolving joint-level motion.

## BraidStorm Continuation

The later session turns into a braid-serial / retrocomputing surface:

```text
BraidStorm FAMM
  = massively parallel braid-coded reconstruction
  + FAMM timing scheduler
  + delay-flight RAM buffers
  + retro endpoint projection
```

The durable bridge to current work is [[Virtual Baud Reconstruction Layer]] and `0-Core-Formalism/lean/Semantics/Semantics/BraidSerial.lean`.

## Claim Boundary

Do not claim:

* near-term biological tail feasibility
* surgical safety
* medical efficacy
* verified external article facts from this ingest alone
* working BCI or robotic-tail implementation
* BraidStorm hardware proof

This ingest preserves a concept session. External science and hardware claims still need separate source receipts.

## Term Counts

```json
{json.dumps(counts, indent=2, sort_keys=True)}
```
"""
    targeted_brief.write_text(targeted_text, encoding="utf-8")

    tags = [
        "chatgpt",
        "ene-ingest",
        "neural-embodiment",
        "prehensile-tail",
        "autopath-sensing",
        "bci",
        "haptic-feedback",
        "braidstorm",
        "famm",
        "virtual-baud",
        "retrocomputing",
    ]
    sigma = {
        "sigma_codon": "PREHENSILE-TAIL-AUTOPATH",
        "classify": "FORMING",
        "observe": "Session frames a non-native appendage as learned body-schema control plus autopath sensing, feedback, and reflex safety.",
        "prove": "Next target is a bounded control taxonomy and simulator receipt before any biological, medical, or hardware claim.",
        "tags": tags,
    }
    pkg = ensure_package("Prehensile Fox Tail Possibility Targeted Brief", targeted_text, "research_brief", tags, sigma)
    generic_brief_path = OUT_DIR / "prehensile_fox_tail_possibility_ene_brief.md"
    repaired_generic = targeted_text.replace(
        "# Prehensile Fox Tail Possibility - Targeted ENE Brief",
        "# Prehensile Fox Tail Possibility - ENE Ingest Brief",
    )
    repaired_generic += (
        "\n## Repair Note\n\n"
        "This file was repaired by `4-Infrastructure/shim/ingest_prehensile_tail_session.py` "
        "because the generic ChatGPT ingester initially used an older S3C/PIST fallback brief. "
        "The targeted package is the interpretive authority for this session.\n"
    )
    generic_brief_path.write_text(repaired_generic, encoding="utf-8")
    repaired_generic_pkg = update_existing_package(
        "aiscroll/prehensile_fox_tail_possibility_ene_brief",
        repaired_generic,
        tags + ["brief-repaired"],
        sigma
        | {
            "sigma_codon": "PREHENSILE-TAIL-BRIEF-REPAIRED",
            "observe": "Generated ENE brief repaired to match the prehensile-tail/autopath and BraidStorm content of the source session.",
        },
    )

    tail_body = f"""
This tiddler records the targeted ingest of `/home/allaun/Documents/ingest/ChatGPT-Prehensile_Fox_Tail_Possibility.json`.

Raw source hash:

```
{source_hash}
```

Targeted brief:

```
data/ingested/chatgpt/prehensile_fox_tail_possibility_targeted_brief.md
```

ENE package:

```
{pkg["pkg"]}
rowid: {pkg["rowid"]}
```

!! Core Prior

The session treats a prehensile tail as a control and embodiment problem:

```
intent/posture/micro-motion/neural-ish signals
  -> probabilistic movement predictor
  -> tail action manifold
  -> reflex controller
  -> haptic/proprioceptive feedback
```

The important design rule is that the user should not pilot every joint. The appendage should expose a compact intent surface:

* brace
* counterbalance
* reach
* wrap
* signal
* retract

That makes the concept relevant to ENE/GCCL control surfaces: a dense actuator field can be made usable only when the control grammar is compressed into lawful primitives with feedback.

!! Autopath Sensing

Autopath sensing means the appendage reads whole-body context and chooses a lawful motion path without requiring explicit joint-by-joint commands.

Useful input lanes:

* lower-back, pelvic, gluteal, abdominal, and shoulder micro-motion
* gaze and object fixation
* balance correction and vestibular mismatch
* EMG/body-signature hints
* optional BCI high-level intent lane
* haptic and proprioceptive feedback

!! Claim Boundary

This is a research prior only. It is not a medical, surgical, prosthetic, or safety claim. The ingest preserves the concept session; external article claims need their own source receipts.
"""
    (WIKI_DIR / "Prehensile Tail Embodiment Control Prior.tid").write_text(
        tiddler(
            "Prehensile Tail Embodiment Control Prior",
            "ResearchStack NeuralEmbodiment AutopathSensing BCI Haptics ENEIngest ClaimBoundary",
            tail_body,
        ),
        encoding="utf-8",
    )

    braid_body = f"""
This tiddler records the BraidStorm FAMM continuation inside the same ChatGPT export:

```
{SOURCE}
```

It should be linked to [[Virtual Baud Reconstruction Layer]] and the Lean braid-serial scaffold:

```
0-Core-Formalism/lean/Semantics/Semantics/BraidSerial.lean
```

!! Core Definition

```
BraidStorm FAMM =
  massively parallel braid-coded reconstruction
  + FAMM timing scheduler
  + delay-flight RAM buffers
  + residual repair lanes
  + retro endpoint projection
```

The architecture class is not a single serial stream. It is a storm of braid bundles that synchronize, cross, repair, and close into byte/signal/manifold projections.

!! Retro Target Read

The session explores C64/Famicom/Amiga-style endpoints as constraint fossils. The point is not historical purity. The point is to force a modern braid/modem/decompression architecture to speak through tiny, weird, timing-sensitive surfaces.

Candidate projection surfaces:

* C64 SID as a mixed-signal witness endpoint
* C64 user/serial/expansion surfaces as protocol fossils
* Famicom expansion connector as a bounded peripheral shim
* Amiga blitter/copper/DMA topology as the cleaner literal blitter target

!! Link To Codec Work

This belongs beside:

* [[Virtual Baud Reconstruction Layer]]
* [[Omindirection Compression Concept Ledger]]
* [[Finance Claim LUT Compression Harness]]
* [[Remote Compression Test Ladder]]

The durable codec lesson is:

```
control lanes + braid timing + residual repair + witness checkpoints
  -> byte-exact reconstruction surface
```

!! Claim Boundary

No working hardware is claimed by this ingest. Treat BraidStorm FAMM as a named architecture candidate and demo target until there are fixture streams, FPGA/host receipts, and byte/signal verification.
"""
    (WIKI_DIR / "BraidStorm FAMM.tid").write_text(
        tiddler(
            "BraidStorm FAMM",
            "ResearchStack BraidStorm FAMM Retrocomputing VBRL Compression HardwarePrior ClaimBoundary",
            braid_body,
        ),
        encoding="utf-8",
    )

    receipt = {
        "lawful": True,
        "source": str(SOURCE),
        "source_hash": source_hash,
        "source_copy": str(source_copy.relative_to(ROOT)),
        "source_copy_hash": sha256_path(source_copy),
        "chat_url": data.get("url"),
        "timestamp": data.get("timestamp"),
        "messages": len(messages),
        "transcript_sha256": transcript_hash,
        "targeted_brief": str(targeted_brief.relative_to(ROOT)),
        "targeted_brief_hash": sha256_path(targeted_brief),
        "targeted_package": pkg,
        "repaired_generic_brief": str(generic_brief_path.relative_to(ROOT)),
        "repaired_generic_brief_hash": sha256_path(generic_brief_path),
        "repaired_generic_package": repaired_generic_pkg,
        "wiki_tiddlers": {
            "tail": "6-Documentation/tiddlywiki-local/wiki/tiddlers/Prehensile Tail Embodiment Control Prior.tid",
            "braidstorm": "6-Documentation/tiddlywiki-local/wiki/tiddlers/BraidStorm FAMM.tid",
        },
        "term_counts": counts,
        "claim_boundary": "Concept-session ingest only; no medical, surgical, biological feasibility, hardware proof, or external source verification claim.",
        "generic_ingester_note": "The generic ChatGPT ingester initially wrote an ENE brief tuned to older S3C/PIST defaults; this targeted shim repaired that generated brief and keeps the targeted brief as interpretive authority.",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
