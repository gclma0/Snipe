from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field


class PortfolioPage(BaseModel):
    url: str
    final_url: str
    title: str | None = None
    description: str | None = None
    text: str
    links: list[str] = Field(default_factory=list)


class PortfolioFetchError(RuntimeError):
    pass


class PortfolioClient:
    def fetch_url(self, url: str) -> PortfolioPage:
        normalized_url = normalize_portfolio_url(url)
        try:
            with httpx.Client(
                timeout=20,
                follow_redirects=True,
                trust_env=False,
                headers={"User-Agent": "snipe-career-intelligence"},
            ) as client:
                response = client.get(normalized_url)
        except httpx.HTTPError as exc:
            raise PortfolioFetchError("Portfolio URL could not be reached.") from exc

        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400:
            raise PortfolioFetchError(f"Portfolio fetch failed with status {response.status_code}.")
        if "html" not in content_type.lower():
            raise PortfolioFetchError("Portfolio URL must return an HTML page.")

        parser = _PortfolioHtmlParser()
        parser.feed(response.text)
        text = _compact_text(" ".join(parser.text_chunks))
        if not text:
            raise PortfolioFetchError("Portfolio page did not contain readable text.")

        return PortfolioPage(
            url=normalized_url,
            final_url=str(response.url),
            title=_compact_text(parser.title) or None,
            description=_compact_text(parser.description) or None,
            text=text[:30000],
            links=sorted(set(parser.links))[:50],
        )


def normalize_portfolio_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise PortfolioFetchError("Portfolio URL is required.")
    parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PortfolioFetchError("Enter a valid http or https portfolio URL.")
    return parsed.geturl()


class _PortfolioHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attributes.get("name", "").lower() == "description":
            self.description = attributes.get("content") or ""
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self.title += data
            return
        cleaned = _compact_text(data)
        if cleaned:
            self.text_chunks.append(cleaned)


def _compact_text(value: str) -> str:
    return " ".join(value.split())
