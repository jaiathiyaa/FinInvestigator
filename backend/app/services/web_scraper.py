from typing import Any, Dict
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/140.0 Safari/537.36"
)


def _clean_text(text: str) -> str:
    """
    Clean excessive whitespace while preserving paragraph boundaries.
    """

    lines = []

    for line in text.splitlines():
        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


def _extract_article_content(soup: BeautifulSoup) -> str:
    """
    Try to extract the main article content.

    Preference:
    1. <article>
    2. common article containers
    3. <main>
    4. entire body
    """

    # Remove elements that are usually not useful as article content.
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "iframe",
            "svg",
            "button",
        ]
    ):
        tag.decompose()

    # First preference: article tag
    article = soup.find("article")

    if article:
        text = article.get_text(
            separator="\n",
            strip=True,
        )

        if len(text) >= 300:
            return _clean_text(text)

    # Common article containers
    selectors = [
        "[class*='article-body']",
        "[class*='article-content']",
        "[class*='article-body-content']",
        "[class*='story-body']",
        "[class*='story-content']",
        "[class*='post-content']",
        "[class*='entry-content']",
        "[class*='content-body']",
    ]

    for selector in selectors:

        element = soup.select_one(selector)

        if element:

            text = element.get_text(
                separator="\n",
                strip=True,
            )

            if len(text) >= 300:
                return _clean_text(text)

    # Try main
    main = soup.find("main")

    if main:

        text = main.get_text(
            separator="\n",
            strip=True,
        )

        if len(text) >= 300:
            return _clean_text(text)

    # Last fallback: body
    body = soup.find("body")

    if body:

        text = body.get_text(
            separator="\n",
            strip=True,
        )

        return _clean_text(text)

    return ""


async def scrape_page(url: str) -> Dict[str, Any]:
    """
    Fetch and extract readable content from a webpage.
    """

    if not url or not url.strip():
        raise ValueError("URL cannot be empty.")

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers=headers,
    ) as client:

        response = await client.get(url)

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    title = ""

    if soup.title:
        title = soup.title.get_text(
            strip=True
        )

    content = _extract_article_content(soup)

    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "title": title,
        "content": content,
        "content_length": len(content),
    }