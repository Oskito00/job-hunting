from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


WORKSPACE_DIR = ".cv-agent"
SOURCE_DIR = "source"
PROFILE_DIR = "profile"
EXPERIENCE_BANK_DIR = "experience-bank"
APPLICATIONS_DIR = "applications"
TEMPLATE_FILENAME = "template.html"
PROFILE_FILENAME = "profile.json"
IMPORT_REPORT_FILENAME = "import-report.md"


@dataclass(frozen=True)
class CvWorkspace:
    root: Path
    workspace: Path
    source: Path
    profile: Path
    experience_bank: Path
    applications: Path
    template: Path
    profile_json: Path
    import_report: Path


def resolve_workspace(root: Path | None = None) -> CvWorkspace:
    project_root = (root or Path.cwd()).resolve()
    workspace = project_root / WORKSPACE_DIR
    return CvWorkspace(
        root=project_root,
        workspace=workspace,
        source=workspace / SOURCE_DIR,
        profile=workspace / PROFILE_DIR,
        experience_bank=workspace / EXPERIENCE_BANK_DIR,
        applications=project_root / APPLICATIONS_DIR,
        template=workspace / TEMPLATE_FILENAME,
        profile_json=workspace / PROFILE_DIR / PROFILE_FILENAME,
        import_report=workspace / IMPORT_REPORT_FILENAME,
    )


def ensure_workspace(workspace: CvWorkspace) -> None:
    for path in [workspace.workspace, workspace.source, workspace.profile, workspace.experience_bank, workspace.applications]:
        path.mkdir(parents=True, exist_ok=True)


def workspace_exists(root: Path | None = None) -> bool:
    return resolve_workspace(root).workspace.exists()
