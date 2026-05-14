from __future__ import annotations

from pathlib import Path

from app.services.roz_evidence import analyze_roz_file, summarize_for_cli


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROZ = PROJECT_ROOT / "import_samples" / "mmmmmmmmmmm2-2.roz"


def test_roz_evidence_extracts_real_asctt_binary_markers() -> None:
    result = analyze_roz_file(SAMPLE_ROZ, max_records=300)
    summary = summarize_for_cli(result)

    assert summary["parser_stage"] == "asctt_binary_roz_evidence_only"
    assert summary["format"]["family"] == "ASCTT/ROZ"

    assert summary["format"]["flags"]["has_asctt"] is True
    assert summary["format"]["flags"]["has_classtt"] is True
    assert summary["format"]["counts"]["ASCTT"] >= 1
    assert summary["format"]["counts"]["CLASSTT"] >= 1

    assert summary["confidence"]["percent"] >= 90
    assert summary["detected_counts"]["period_labels"] >= 1
    assert summary["detected_counts"]["class_labels"] >= 1
    assert summary["detected_counts"]["subject_candidates"] >= 1
    assert summary["detected_counts"]["arabic_records"] >= 1

    assert summary["safety"]["safe_to_import_entities"] is True
    assert summary["safety"]["safe_to_import_slots"] is False
    assert summary["safety"]["safe_to_confirm"] is False


def test_roz_evidence_summary_is_json_safe_and_read_only() -> None:
    result = analyze_roz_file(SAMPLE_ROZ, max_records=80)
    summary = summarize_for_cli(result)

    assert summary["file"]["name"] == "mmmmmmmmmmm2-2.roz"
    assert summary["file"]["size"] > 0
    assert len(summary["file"]["sha256"]) == 64

    assert isinstance(summary["detected_preview"]["period_labels"], list)
    assert isinstance(summary["detected_preview"]["class_labels"], list)
    assert isinstance(summary["detected_preview"]["subject_candidates"], list)

    notes = summary["safety"]["notes_ar"]
    assert any("Evidence" in note for note in notes)
    assert any("استيراد الحصص" in note for note in notes)


if __name__ == "__main__":
    test_roz_evidence_extracts_real_asctt_binary_markers()
    test_roz_evidence_summary_is_json_safe_and_read_only()
    print("✅ roz_evidence tests passed without pytest")
