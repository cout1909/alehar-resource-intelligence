"""Conservative HTML text extraction without executing scripts."""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.core.config import get_settings


@dataclass(frozen=True)
class PageData:
    title: str
    meta_description: str
    visible_text: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_metadata(html: str, max_length: int | None = None) -> PageData:
    limit = max_length or get_settings().max_source_text_length
    soup = BeautifulSoup(html, "html.parser")
    title = normalize_whitespace(soup.title.get_text(" ") if soup.title else "")[:500]
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.IGNORECASE)})
    description = normalize_whitespace(str(meta.get("content", "")) if meta else "")[:1000]
    for element in list(
        soup.select(
            "script, style, noscript, svg, nav, header, footer, title, "
            "[hidden], [aria-hidden='true'], [role='navigation']"
        )
    ):
        if element.parent is not None:
            element.decompose()
    for element in list(soup.find_all(style=True)):
        if element.parent is None:
            continue
        style = re.sub(r"\s+", "", element.get("style", "")).lower()
        if "display:none" in style or "visibility:hidden" in style:
            element.decompose()
    text = normalize_whitespace(soup.get_text(" ", strip=True))[:limit]
    return PageData(title=title, meta_description=description, visible_text=text)


def extract_visible_text(html: str, max_length: int | None = None) -> str:
    return extract_metadata(html, max_length).visible_text
