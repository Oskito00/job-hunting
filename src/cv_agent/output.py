from __future__ import annotations

import json
from pathlib import Path
from typing import Any


JD_FILENAME = "jd.md"
CV_JSON_FILENAME = "cv-content.json"
COVERAGE_REPORT_FILENAME = "coverage-report.md"


def write_application_files(output_dir: Path, job_text: str, cv_content: dict[str, Any], source_url: str) -> None:
    write_text(output_dir / JD_FILENAME, format_job_description(job_text, source_url))
    write_json(output_dir / CV_JSON_FILENAME, cv_content)
    write_text(output_dir / COVERAGE_REPORT_FILENAME, build_coverage_report(cv_content, source_url))


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def format_job_description(job_text: str, source_url: str) -> str:
    return f"# Job Description\n\nSource: {source_url}\n\n{job_text.strip()}\n"


def build_coverage_report(cv_content: dict[str, Any], source_url: str) -> str:
    evidence = sorted(collect_evidence_paths(cv_content))
    lines = ["# Coverage Report", "", f"Source: {source_url}", "", "## Evidence Files"]
    lines.extend(format_evidence_lines(evidence))
    return "\n".join(lines).strip() + "\n"


def collect_evidence_paths(value: object) -> set[str]:
    paths: set[str] = set()
    collect_evidence(value, paths)
    return paths


def collect_evidence(value: object, paths: set[str]) -> None:
    if isinstance(value, dict):
        add_evidence(value, paths)
        for child in value.values():
            collect_evidence(child, paths)
    elif isinstance(value, list):
        for child in value:
            collect_evidence(child, paths)


def add_evidence(item: dict[object, object], paths: set[str]) -> None:
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        paths.update(str(path) for path in evidence)


def format_evidence_lines(evidence: list[str]) -> list[str]:
    if not evidence:
        return ["", "No evidence paths were included."]
    return ["", *[f"- {path}" for path in evidence]]
