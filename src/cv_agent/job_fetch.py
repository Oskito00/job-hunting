from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "cv-agent/0.1 (+https://www.oscaralberigo.co.uk/)"


class JobFetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    url: str
    html: str


def validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise JobFetchError(f"Expected an http(s) URL, got: {url}")


def build_request(url: str) -> Request:
    return Request(url, headers={"User-Agent": USER_AGENT})


def decode_response(body: bytes, charset: str | None) -> str:
    encoding = charset or "utf-8"
    return body.decode(encoding, errors="replace")


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> FetchResult:
    validate_http_url(url)
    request = build_request(url)
    try:
        with urlopen(request, timeout=timeout) as response:
            html = decode_response(response.read(), response.headers.get_content_charset())
    except HTTPError as exc:
        raise JobFetchError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise JobFetchError(f"Could not fetch {url}: {exc.reason}") from exc
    return FetchResult(url=url, html=html)
