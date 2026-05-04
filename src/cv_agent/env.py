from __future__ import annotations

import os
from pathlib import Path


ENV_FILENAME = ".env"


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or Path.cwd() / ENV_FILENAME
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        load_env_line(line)


def load_env_line(line: str) -> None:
    stripped = line.strip()
    if should_skip_line(stripped):
        return
    key, value = split_env_line(stripped)
    if key and key not in os.environ:
        os.environ[key] = value


def should_skip_line(line: str) -> bool:
    return not line or line.startswith("#") or "=" not in line


def split_env_line(line: str) -> tuple[str, str]:
    key, value = line.split("=", 1)
    return key.strip(), clean_env_value(value)


def clean_env_value(value: str) -> str:
    stripped = value.strip()
    if is_quoted(stripped):
        return stripped[1:-1]
    return stripped


def is_quoted(value: str) -> bool:
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
