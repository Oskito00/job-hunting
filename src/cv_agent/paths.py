from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re


EXPERIENCE_BANK_DIR = "experience-bank"
WORKSPACE_DIR = ".cv-agent"
APPLICATIONS_DIR = "applications"


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    experience_bank: Path
    applications: Path


def resolve_project_paths(root: Path | None = None) -> ProjectPaths:
    project_root = (root or Path.cwd()).resolve()
    return ProjectPaths(
        root=project_root,
        experience_bank=resolve_experience_bank_path(project_root),
        applications=project_root / APPLICATIONS_DIR,
    )


def resolve_experience_bank_path(project_root: Path) -> Path:
    workspace_bank = project_root / WORKSPACE_DIR / EXPERIENCE_BANK_DIR
    legacy_bank = project_root / EXPERIENCE_BANK_DIR
    if workspace_bank.exists() or not legacy_bank.exists():
        return workspace_bank
    return legacy_bank


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-") or "application"


def application_folder_name(company: str, role: str, run_date: date | None = None) -> str:
    current_date = run_date or date.today()
    return f"{slugify(company)}-{slugify(role)}-{current_date.isoformat()}"


def create_application_dir(paths: ProjectPaths, company: str, role: str) -> Path:
    output_dir = paths.applications / application_folder_name(company, role)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def relative_to_root(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_relative_child(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
