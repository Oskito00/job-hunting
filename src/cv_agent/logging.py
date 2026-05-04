from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class CliLogger:
    quiet: bool = False

    def step(self, message: str) -> None:
        if not self.quiet:
            print(f"[cv-agent] {message}", file=sys.stderr)

    def success(self, message: str) -> None:
        if not self.quiet:
            print(f"[cv-agent] done: {message}", file=sys.stderr)

    def warn(self, message: str) -> None:
        if not self.quiet:
            print(f"[cv-agent] warning: {message}", file=sys.stderr)


def null_logger() -> CliLogger:
    return CliLogger(quiet=True)
