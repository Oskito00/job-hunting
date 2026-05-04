from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cv_agent.config import StaticProfileConfig
from cv_agent.experience_bank import load_experience_file, load_experience_files, search_experience_files


@dataclass(frozen=True)
class ToolRuntime:
    bank_dir: Path
    static_config: StaticProfileConfig


def build_tools(runtime: ToolRuntime) -> list[Any]:
    from agents import function_tool

    @function_tool
    def list_experience_files() -> list[str]:
        """List Markdown files available in the local experience bank."""
        files = load_experience_files(runtime.bank_dir)
        return [file.relative_path for file in files]

    @function_tool
    def search_experience_bank(query: str, limit: int = 12) -> list[dict[str, object]]:
        """Search the local experience bank by role, skill, domain, and content keywords."""
        files = load_experience_files(runtime.bank_dir)
        results = search_experience_files(query=query, files=files, limit=limit)
        return [asdict(result) for result in results]

    @function_tool
    def read_experience_file(path: str) -> dict[str, object]:
        """Read one Markdown file from the experience bank by relative path."""
        file = load_experience_file(path=Path(path), bank_dir=runtime.bank_dir)
        return {
            "path": file.relative_path,
            "metadata": file.metadata,
            "body": file.body,
        }

    @function_tool
    def read_static_profile_config() -> dict[str, object]:
        """Read confirmed contact and education details."""
        return asdict(runtime.static_config)

    return [
        list_experience_files,
        search_experience_bank,
        read_experience_file,
        read_static_profile_config,
    ]
