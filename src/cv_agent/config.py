from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cv_agent.experience_bank import load_experience_file


CONTACT_FILE = "contact.md"
EDUCATION_FILE = "education.md"


@dataclass(frozen=True)
class StaticProfileConfig:
    contact: dict[str, str]
    education: list[dict[str, str]]


def load_static_profile_config(bank_dir: Path) -> StaticProfileConfig:
    contact = load_contact(bank_dir)
    education = load_education(bank_dir)
    return StaticProfileConfig(contact=contact, education=education)


def load_contact(bank_dir: Path) -> dict[str, str]:
    path = bank_dir / CONTACT_FILE
    if not path.exists():
        return {}
    file = load_experience_file(path, bank_dir)
    return parse_bullet_key_values(file.body)


def load_education(bank_dir: Path) -> list[dict[str, str]]:
    path = bank_dir / EDUCATION_FILE
    if not path.exists():
        return []
    file = load_experience_file(path, bank_dir)
    return parse_education_entries(file.body)


def parse_bullet_key_values(markdown: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in markdown.splitlines():
        key, value = parse_bullet_key_value(line)
        if key:
            pairs[key] = value
    return pairs


def parse_bullet_key_value(line: str) -> tuple[str, str]:
    stripped = line.strip()
    if not stripped.startswith("- ") or ":" not in stripped:
        return "", ""
    key, value = stripped[2:].split(":", 1)
    return normalize_key(key), value.strip()


def parse_education_entries(markdown: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in markdown.splitlines():
        current = parse_education_line(line, entries, current)
    return entries


def parse_education_line(line: str, entries: list[dict[str, str]], current: dict[str, str] | None) -> dict[str, str] | None:
    stripped = line.strip()
    if stripped.startswith("## "):
        current = {"institution": stripped[3:].strip()}
        entries.append(current)
        return current
    if current is not None:
        key, value = parse_bullet_key_value(stripped)
        if key:
            current[key] = value
    return current


def normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")
