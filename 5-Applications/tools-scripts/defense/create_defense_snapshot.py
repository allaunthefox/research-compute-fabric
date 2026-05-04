#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_REPORT_RECIPIENT = "PassInbox Abuse Intake <2s3sa2.monthly496@passinbox.com>"
DEFAULT_REPORT_CHANNEL = "passinbox abuse intake"

from scripts.generate_trace_attestation import build_attestation, sha256_file
from scripts.zero_metadata_loopback import build_payload, pack_loopback, unpack_loopback, verify_payload_files


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def summarize_findings(attestation: Dict[str, Any]) -> List[str]:
    snapshot = attestation.get("database_snapshot", {})
    counts = snapshot.get("counts", {})
    events = snapshot.get("events", [])
    observables = snapshot.get("observables", [])
    relationships = snapshot.get("relationships", [])

    lines = [
        (
            "Observed "
            f"{counts.get('events', 0)} event(s), "
            f"{counts.get('observables', 0)} observable(s), and "
            f"{counts.get('relationships', 0)} relationship(s)."
        )
    ]

    grouped: Dict[str, List[str]] = {}
    for item in observables:
        grouped.setdefault(str(item.get("observable_type", "unknown")), []).append(str(item.get("value", "")))

    for observable_type in sorted(grouped):
        values = grouped[observable_type]
        preview = ", ".join(values[:3])
        if len(values) > 3:
            preview += ", ..."
        lines.append(f"Observed {observable_type}: {preview}")

    for event in events[:3]:
        source = event.get("source", "unknown")
        observed_at = event.get("observed_at", "unknown")
        notes = str(event.get("notes", "")).strip()
        detail = f"Event {event.get('event_id', '?')} from {source} at {observed_at}"
        if notes:
            detail += f" with note: {notes}"
        lines.append(detail)

    if relationships:
        relation_names = sorted({str(item.get("relation_type", "unknown")) for item in relationships})
        lines.append("Relationship types present: " + ", ".join(relation_names))

    return lines


def render_finding_line(item: str) -> str:
    prefix = "Observed url: "
    if item.startswith(prefix):
        return prefix + f"<{item[len(prefix):]}>"
    return item


def foam_statement(passes: int) -> str:
    if passes < 1:
        passes = 1
    blends = {
        "preserve": ["preserves", "keeps", "retains", "safeguards"],
        "evidence": ["technical evidence", "forensic records", "verifiable traces"],
        "attribution": ["avoids attribution", "refrains from blame assignment", "does not label actors"],
        "handoff": ["safe handoff", "clean transfer", "neutral transfer"],
        "restore": ["service restoration", "connectivity recovery", "normal operation recovery"],
    }

    def pick(values: List[str], offset: int) -> str:
        return values[(passes + offset) % len(values)]

    return (
        f"After {passes} smoothing passes, this brief {pick(blends['preserve'], 0)} "
        f"{pick(blends['evidence'], 1)}, {pick(blends['attribution'], 2)}, and supports "
        f"{pick(blends['handoff'], 0)} for {pick(blends['restore'], 1)}. "
        "The intent is stability, the language is neutral, and the objective is safe closure."
    )


def write_handoff_brief(path: Path, snapshot: Dict[str, Any], passes: int = 1) -> None:
    lines: List[str] = []
    lines.append("# Defense Handoff Brief")
    lines.append("")
    lines.append(f"Created: {snapshot['created_utc']}")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("This package preserves passive technical evidence for transfer and review.")
    lines.append("It is written to be neutral, factual, and easy to read.")
    lines.append("No person, group, or country attribution is asserted in this document.")
    lines.append(f"Language smoothing passes applied: {passes}")
    lines.append("")
    lines.append("## Integrity")
    lines.append("")
    lines.append(f"- Loopback verified: {snapshot['loopback']['verified']}")
    lines.append(f"- Loopback file: {snapshot['loopback']['path']}")
    lines.append(f"- Loopback SHA-256: {snapshot['loopback']['sha256']}")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- Attestation: {snapshot['attestation']['path']}")
    lines.append(f"- Attestation SHA-256: {snapshot['attestation']['sha256']}")
    for item in snapshot["evidence_files"]:
        lines.append(f"- Evidence: {item['path']} ({item['sha256']})")
    lines.append("")
    lines.append("## Plain-Language Summary")
    lines.append("")
    lines.append("The goal is service restoration and safe handoff, not private investigation.")
    lines.append("This package is structured so another team can verify integrity without relying on file metadata.")
    lines.append(foam_statement(passes))
    lines.append("")
    lines.append("## Minimal Action Path")
    lines.append("")
    lines.append("1. Hand this package to platform abuse or CERT channels.")
    lines.append("2. Keep a local copy unchanged.")
    lines.append("3. Avoid active investigation or interaction with suspected actors.")
    lines.append("4. Focus only on connectivity and service recovery on your side.")
    lines.append("")
    lines.append("## Short Neutral Statement (Multilingual)")
    lines.append("")
    lines.append("English: This report preserves technical evidence only and makes no attribution claims.")
    lines.append("Español: Este informe conserva solo evidencia técnica y no hace atribuciones.")
    lines.append("Français: Ce rapport conserve uniquement des preuves techniques et ne fait aucune attribution.")
    lines.append("Deutsch: Dieser Bericht bewahrt nur technische Belege und enthält keine Zuschreibungen.")
    lines.append("Português: Este relatório preserva apenas evidências técnicas e não faz atribuições.")
    lines.append("Italiano: Questo rapporto conserva solo prove tecniche e non formula attribuzioni.")
    lines.append("Polski: Ten raport zachowuje wyłącznie dowody techniczne i nie przypisuje odpowiedzialności.")
    lines.append("Nederlands: Dit rapport bewaart alleen technische bewijzen en doet geen toeschrijvingen.")
    lines.append("Türkçe: Bu rapor yalnızca teknik kanıtları korur ve atıf iddiasında bulunmaz.")
    lines.append("Svenska: Denna rapport bevarar endast tekniska bevis och gör inga tillskrivningar.")
    lines.append("Norsk: Denne rapporten bevarer kun tekniske bevis og gjør ingen attribusjoner.")
    lines.append("Dansk: Denne rapport bevarer kun tekniske beviser og fremsætter ingen attributioner.")
    lines.append("Suomi: Tämä raportti säilyttää vain tekniset todisteet eikä tee attribuutioväitteitä.")
    lines.append("Čeština: Tato zpráva uchovává pouze technické důkazy a neobsahuje žádná přičtení.")
    lines.append("Slovenčina: Táto správa uchováva iba technické dôkazy a neobsahuje žiadne pripisovanie.")
    lines.append("Magyar: Ez a jelentés csak technikai bizonyítékokat őriz meg, és nem tesz attribúciós állításokat.")
    lines.append("Română: Acest raport păstrează doar dovezi tehnice și nu face atribuiri.")
    lines.append("Български: Този доклад съхранява само технически доказателства и не прави приписвания.")
    lines.append("Українська: Цей звіт зберігає лише технічні докази і не містить атрибуції.")
    lines.append("Русский: Этот отчет сохраняет только технические доказательства и не содержит атрибуции.")
    lines.append("العربية: يحفظ هذا التقرير أدلة تقنية فقط ولا يتضمن أي إسناد.")
    lines.append("עברית: דוח זה שומר ראיות טכניות בלבד ואינו כולל ייחוס.")
    lines.append("فارسی: این گزارش فقط شواهد فنی را حفظ می‌کند و هیچ انتسابی ارائه نمی‌دهد.")
    lines.append("हिन्दी: यह रिपोर्ट केवल तकनीकी साक्ष्य सुरक्षित रखती है और कोई आरोपित पहचान नहीं करती।")
    lines.append("বাংলা: এই প্রতিবেদনে শুধু প্রযুক্তিগত প্রমাণ সংরক্ষণ করা হয়েছে, কোনো দায় আরোপ করা হয়নি।")
    lines.append("தமிழ்: இந்த அறிக்கை தொழில்நுட்ப ஆதாரங்களை மட்டும் பாதுகாக்கிறது; குற்றச்சாட்டு ஒதுக்கீடு செய்யாது.")
    lines.append("తెలుగు: ఈ నివేదిక సాంకేతిక ఆధారాలను మాత్రమే భద్రపరుస్తుంది; ఎటువంటి ఆపాదింపు చేయదు.")
    lines.append("اردو: یہ رپورٹ صرف تکنیکی شواہد محفوظ کرتی ہے اور کوئی انتساب نہیں کرتی۔")
    lines.append("中文: 本报告仅保存技术证据，不作归因结论。")
    lines.append("日本語: この報告は技術的証拠のみを保全し、帰属判断は行いません。")
    lines.append("한국어: 이 보고서는 기술적 증거만 보존하며 귀속 판단을 하지 않습니다.")
    lines.append("Bahasa Indonesia: Laporan ini hanya menyimpan bukti teknis dan tidak membuat atribusi.")
    lines.append("Tiếng Việt: Báo cáo này chỉ lưu giữ bằng chứng kỹ thuật và không đưa ra quy kết.")
    lines.append("ไทย: รายงานนี้เก็บรักษาหลักฐานทางเทคนิคเท่านั้น และไม่ระบุการชี้ตัวผู้กระทำ")
    lines.append("Kiswahili: Ripoti hii huhifadhi ushahidi wa kiufundi pekee na haitoi uhusisho.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_trigger_report(
    path: Path,
    snapshot: Dict[str, Any],
    attestation: Dict[str, Any],
    recipient: str,
    channel: str,
) -> None:
    findings = summarize_findings(attestation)
    lines: List[str] = []
    lines.append("# Trigger Report")
    lines.append("")
    lines.append(f"Created: {snapshot['created_utc']}")
    lines.append(f"Recipient: {recipient}")
    lines.append(f"Channel: {channel}")
    lines.append("")
    lines.append("## What I Found")
    lines.append("")
    for item in findings:
        lines.append(f"- {render_finding_line(item)}")
    lines.append("")
    lines.append("## What Is Attached")
    lines.append("")
    lines.append(f"- Verified loopback container: {snapshot['loopback']['path']}")
    lines.append(f"- Loopback SHA-256: {snapshot['loopback']['sha256']}")
    lines.append(f"- Attestation JSON: {snapshot['attestation']['path']}")
    lines.append(f"- Attestation SHA-256: {snapshot['attestation']['sha256']}")
    lines.append("")
    lines.append("## Plain Handoff Statement")
    lines.append("")
    lines.append(
        "I found the technical indicators listed above and preserved them in a verifiable package. "
        "I am not making attribution claims. I am handing this to your team for review and disposition; "
        "any further action is up to you."
    )
    lines.append("")
    lines.append("## Copy-Paste Message")
    lines.append("")
    lines.append(f"Subject: Passive technical evidence package for {channel}")
    lines.append("")
    lines.append(f"To: {recipient}")
    lines.append("")
    lines.append("Hello,")
    lines.append("")
    lines.append("I am sending a passive technical evidence package for your review.")
    lines.append("The package contains a verified loopback container and an attestation file with hashes.")
    lines.append("Summary of findings:")
    lines.append("")
    for item in findings:
        lines.append(f"- {render_finding_line(item)}")
    lines.append("")
    lines.append(
        "I am not making attribution claims and I am not asking for an interactive investigation on my side. "
        "Please review the package and decide any further action that your process requires."
    )
    lines.append("")
    lines.append("Regards,")
    lines.append("Operator")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_snapshot(
    db_path: Path,
    clusters_csv: Path,
    timeline_json: Path,
    template_csv: Path,
    out_dir: Path,
    passes: int = 1,
    report_recipient: str = DEFAULT_REPORT_RECIPIENT,
    report_channel: str = DEFAULT_REPORT_CHANNEL,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    attestation_path = out_dir / "trace_attestation.json"
    loopback_path = out_dir / "defense_loopback.zmlb"
    snapshot_path = out_dir / "defense_snapshot.json"
    handoff_path = out_dir / "defense_handoff_brief.md"
    trigger_report_path = out_dir / "defense_trigger_report.md"

    attestation = build_attestation(db_path, clusters_csv, timeline_json, template_csv)
    write_json(attestation_path, attestation)

    evidence_paths = [db_path, clusters_csv, timeline_json]
    payload = build_payload(attestation_path, evidence_paths)
    loopback_metrics = pack_loopback(payload, loopback_path)
    unpacked_payload, _ = unpack_loopback(loopback_path)
    file_findings = verify_payload_files(unpacked_payload)
    verified = all(item["status"] == "ok" for item in file_findings)

    snapshot: Dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "language_smoothing_passes": int(passes),
        "attestation": {
            "path": str(attestation_path),
            "sha256": sha256_file(attestation_path),
        },
        "loopback": {
            "path": str(loopback_path),
            "sha256": loopback_metrics["container_sha256"],
            "canonical_sha256": loopback_metrics["canonical_sha256"],
            "verified": verified,
        },
        "evidence_files": [
            {"path": str(path), "sha256": sha256_file(path)} for path in evidence_paths
        ],
        "loopback_file_checks": file_findings,
    }

    write_json(snapshot_path, snapshot)
    write_handoff_brief(handoff_path, snapshot, passes=passes)
    write_trigger_report(
        trigger_report_path,
        snapshot,
        attestation,
        recipient=report_recipient,
        channel=report_channel,
    )
    return {
        "snapshot": str(snapshot_path),
        "handoff_brief": str(handoff_path),
        "trigger_report": str(trigger_report_path),
        "attestation": str(attestation_path),
        "loopback": str(loopback_path),
        "verified": verified,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a passive defense snapshot package for quick handoff.")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "out" / "demo_trace.sqlite3"), help="Trace database path.")
    parser.add_argument("--clusters", default=str(PROJECT_ROOT / "out" / "clusters.csv"), help="Cluster CSV path.")
    parser.add_argument("--timeline", default=str(PROJECT_ROOT / "out" / "timeline.json"), help="Timeline JSON path.")
    parser.add_argument("--template", default=str(PROJECT_ROOT / "data_baselines" / "suspicious_repo_list_template.csv"), help="Repo list template path.")
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / "out"), help="Output directory.")
    parser.add_argument("--passes", type=int, default=1, help="Number of language smoothing passes for handoff text.")
    parser.add_argument("--report-recipient", default=DEFAULT_REPORT_RECIPIENT, help="Recipient label for the trigger report.")
    parser.add_argument("--report-channel", default=DEFAULT_REPORT_CHANNEL, help="Channel label for the trigger report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = [Path(args.db), Path(args.clusters), Path(args.timeline), Path(args.template)]
    missing = [str(path) for path in inputs if not path.exists()]
    if missing:
        print(json.dumps({"error": "missing_input_files", "paths": missing}, indent=2))
        return 2

    result = create_snapshot(
        db_path=Path(args.db),
        clusters_csv=Path(args.clusters),
        timeline_json=Path(args.timeline),
        template_csv=Path(args.template),
        out_dir=Path(args.out_dir),
        passes=int(args.passes),
        report_recipient=args.report_recipient,
        report_channel=args.report_channel,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
