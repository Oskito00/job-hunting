from __future__ import annotations

from html.parser import HTMLParser
import re


MIN_JOB_TEXT_CHARS = 500
IGNORED_TAGS = {"script", "style", "noscript", "svg", "canvas", "header", "footer", "nav"}
BLOCK_TAGS = {"p", "div", "li", "br", "section", "article", "h1", "h2", "h3", "h4"}


class JobExtractionError(RuntimeError):
    pass


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in IGNORED_TAGS:
            self._ignored_depth += 1
        if tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
        if tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def text(self) -> str:
        return clean_text(" ".join(self._parts))


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_visible_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    return parser.text()


def has_job_keywords(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ("responsibilities", "requirements", "skills", "about the role", "job description"))


def extract_job_text(html: str, url: str | None = None) -> str:
    text = extract_visible_text(html)
    if len(text) >= MIN_JOB_TEXT_CHARS and has_job_keywords(text):
        return text
    location = f" from {url}" if url else ""
    raise JobExtractionError(f"Could not confidently extract a job description{location}.")
