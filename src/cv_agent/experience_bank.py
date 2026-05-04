from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from cv_agent.paths import is_relative_child


FRONTMATTER_DELIMITER = "---"
MARKDOWN_PATTERN = "*.md"


@dataclass(frozen=True)
class ExperienceFile:
    path: Path
    relative_path: str
    metadata: dict[str, object]
    body: str

    @property
    def searchable_text(self) -> str:
        return "\n".join([self.relative_path, stringify_metadata(self.metadata), self.body])


@dataclass(frozen=True)
class SearchResult:
    path: str
    score: int
    title: str
    summary: str


def load_experience_files(bank_dir: Path) -> list[ExperienceFile]:
    files = sorted(bank_dir.rglob(MARKDOWN_PATTERN))
    return [load_experience_file(path, bank_dir) for path in files]


def load_experience_file(path: Path, bank_dir: Path) -> ExperienceFile:
    safe_path = resolve_bank_path(path, bank_dir)
    raw = safe_path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(raw)
    relative_path = safe_path.relative_to(bank_dir.resolve()).as_posix()
    return ExperienceFile(path=safe_path, relative_path=relative_path, metadata=metadata, body=body)


def resolve_bank_path(path: Path | str, bank_dir: Path) -> Path:
    bank_root = bank_dir.resolve()
    candidate = Path(path)
    resolved = resolve_candidate_path(candidate, bank_root)
    if not is_relative_child(resolved, bank_root):
        raise ValueError(f"Path is outside experience bank: {path}")
    if resolved.suffix != ".md":
        raise ValueError(f"Experience files must be Markdown: {path}")
    return resolved


def resolve_candidate_path(candidate: Path, bank_root: Path) -> Path:
    if candidate.is_absolute():
        return candidate.resolve()
    direct = candidate.resolve()
    if is_relative_child(direct, bank_root):
        return direct
    return (bank_root / candidate).resolve()


def split_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, raw.strip()
    end_index = find_frontmatter_end(lines)
    if end_index is None:
        return {}, raw.strip()
    metadata = parse_simple_yaml(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def find_frontmatter_end(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return index
    return None


def parse_simple_yaml(lines: list[str]) -> dict[str, object]:
    metadata: dict[str, object] = {}
    current_key: str | None = None
    for line in lines:
        current_key = parse_yaml_line(line, metadata, current_key)
    return metadata


def parse_yaml_line(line: str, metadata: dict[str, object], current_key: str | None) -> str | None:
    stripped = line.strip()
    if not stripped:
        return current_key
    if stripped.startswith("- ") and current_key:
        append_yaml_list_item(metadata, current_key, stripped[2:])
        return current_key
    if ":" in stripped and not line.startswith(" "):
        key, value = stripped.split(":", 1)
        metadata[key] = parse_yaml_value(value.strip())
        return key
    return current_key


def append_yaml_list_item(metadata: dict[str, object], key: str, value: str) -> None:
    existing = metadata.get(key)
    if not isinstance(existing, list):
        existing = []
        metadata[key] = existing
    existing.append(parse_scalar(value))


def parse_yaml_value(value: str) -> object:
    if value == "":
        return []
    if value.startswith("[") and value.endswith("]"):
        return [parse_scalar(item.strip()) for item in value[1:-1].split(",") if item.strip()]
    return parse_scalar(value)


def parse_scalar(value: str) -> str:
    return value.strip("\"'")


def stringify_metadata(metadata: dict[str, object]) -> str:
    parts: list[str] = []
    for key, value in metadata.items():
        parts.append(key)
        parts.append(stringify_value(value))
    return " ".join(parts)


def stringify_value(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def search_experience_files(query: str, files: list[ExperienceFile], limit: int = 12) -> list[SearchResult]:
    scored = [build_search_result(file, query) for file in files]
    relevant = [result for result in scored if result.score > 0]
    return sorted(relevant, key=lambda result: (-result.score, result.path))[:limit]


def build_search_result(file: ExperienceFile, query: str) -> SearchResult:
    score = score_experience_file(file, query)
    return SearchResult(
        path=file.relative_path,
        score=score,
        title=metadata_title(file),
        summary=first_body_sentence(file.body),
    )


def score_experience_file(file: ExperienceFile, query: str) -> int:
    terms = tokenize(query)
    if not terms:
        return 0
    searchable = file.searchable_text.lower()
    metadata_text = stringify_metadata(file.metadata).lower()
    return sum(score_term(term, searchable, metadata_text) for term in terms)


def score_term(term: str, searchable: str, metadata_text: str) -> int:
    metadata_hits = metadata_text.count(term) * 3
    body_hits = searchable.count(term)
    return metadata_hits + body_hits


def tokenize(text: str) -> list[str]:
    terms = re.findall(r"[a-z0-9][a-z0-9+-]*", text.lower())
    return [term for term in terms if len(term) > 2]


def metadata_title(file: ExperienceFile) -> str:
    title = file.metadata.get("title") or file.metadata.get("company") or file.metadata.get("id")
    return str(title or file.relative_path)


def first_body_sentence(body: str, max_chars: int = 240) -> str:
    cleaned = re.sub(r"\s+", " ", body).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[:max_chars].rstrip()}..."
