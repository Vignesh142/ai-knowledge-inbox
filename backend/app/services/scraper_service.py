import re
import json
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import validate_url_security
from backend.app.core.exceptions import ScrapingError

class ScraperService:
    """Service to fetch, clean, and extract rich structured metadata and content from web pages."""

    def __init__(self, timeout: float = settings.SCRAPER_TIMEOUT_SECONDS):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 AIKnowledgeInbox/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        domain = parsed.netloc

        # Title extraction hierarchy
        title = ""
        og_title = soup.find("meta", property="og:title")
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if og_title and og_title.get("content"):
            title = str(og_title["content"]).strip()
        elif twitter_title and twitter_title.get("content"):
            title = str(twitter_title["content"]).strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        else:
            title = f"Page from {domain}"

        # Multiple Description sources (meta, og, twitter)
        descriptions: List[str] = []
        for attr, val in [
            ("name", "description"),
            ("property", "og:description"),
            ("name", "twitter:description"),
        ]:
            tag = soup.find("meta", attrs={attr: val})
            if tag and tag.get("content"):
                c = str(tag["content"]).strip()
                if c and c not in descriptions:
                    descriptions.append(c)

        primary_desc = descriptions[0] if descriptions else ""

        # Author extraction
        author = ""
        meta_author = soup.find("meta", attrs={"name": "author"})
        article_author = soup.find("meta", property="article:author")
        if meta_author and meta_author.get("content"):
            author = str(meta_author["content"]).strip()
        elif article_author and article_author.get("content"):
            author = str(article_author["content"]).strip()

        # Keywords extraction
        keywords = ""
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            keywords = str(meta_keywords["content"]).strip()

        # Favicon extraction
        favicon = ""
        icon_link = soup.find("link", rel=lambda x: x and ("icon" in x.lower() or "shortcut" in x.lower()))
        if icon_link and icon_link.get("href"):
            favicon = urljoin(url, icon_link["href"])
        else:
            favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

        # JSON-LD structured data
        json_ld_data = []
        for s in soup.find_all("script", type="application/ld+json"):
            if s.string:
                try:
                    data = json.loads(s.string)
                    json_ld_data.append(data)
                except Exception:
                    pass

        return {
            "title": title[:200],
            "description": primary_desc[:500],
            "all_descriptions": descriptions,
            "author": author[:100],
            "keywords": keywords[:200],
            "domain": domain,
            "favicon": favicon,
            "json_ld": json_ld_data,
        }

    def _clean_html_to_markdown(self, soup: BeautifulSoup) -> str:
        # Clone soup or operate on clean copy
        content_soup = BeautifulSoup(str(soup), "html.parser")
        
        # Remove noisy tags
        for tag in content_soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form", "iframe"]):
            tag.decompose()

        main_content = content_soup.find("article") or content_soup.find("main") or content_soup.find("div", role="main") or content_soup.body or content_soup

        text_lines = []
        for element in main_content.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre", "code"]):
            tag_name = element.name.lower()
            text = element.get_text(separator=" ", strip=True)
            if not text:
                continue

            if tag_name == "h1":
                text_lines.append(f"\n# {text}\n")
            elif tag_name == "h2":
                text_lines.append(f"\n## {text}\n")
            elif tag_name == "h3":
                text_lines.append(f"\n### {text}\n")
            elif tag_name == "li":
                text_lines.append(f"- {text}")
            elif tag_name == "blockquote":
                text_lines.append(f"> {text}")
            else:
                text_lines.append(text)

        cleaned_text = "\n\n".join(text_lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()
        return cleaned_text

    def _build_rich_document(self, metadata: Dict[str, Any], body_text: str, url: str) -> str:
        """
        Combines title, author, OpenGraph descriptions, keywords, JSON-LD,
        and body text into a coherent, rich Markdown document for RAG indexing.
        """
        sections = [f"# {metadata['title']}"]

        header_info = []
        if metadata.get("author"):
            header_info.append(f"**Author / Creator:** {metadata['author']}")
        if metadata.get("domain"):
            header_info.append(f"**Source URL:** {url} ({metadata['domain']})")
        if metadata.get("keywords"):
            header_info.append(f"**Keywords:** {metadata['keywords']}")

        if header_info:
            sections.append("\n".join(header_info))

        all_desc = metadata.get("all_descriptions", [])
        if all_desc:
            sections.append("## Overview & Summary")
            for d in all_desc:
                sections.append(f"- {d}")

        if metadata.get("json_ld"):
            sections.append("## Structured Schema Metadata")
            for item in metadata["json_ld"][:2]:
                sections.append(f"```json\n{json.dumps(item, indent=2)}\n```")

        # Add main body content if substantive
        clean_body = body_text.strip()
        if clean_body and len(clean_body.split()) > 10:
            # Check if body is not just repeating the title
            if clean_body != metadata['title']:
                sections.append("## Page Content")
                sections.append(clean_body)

        full_doc = "\n\n".join(sections)
        return full_doc[:settings.MAX_SCRAPE_CONTENT_LENGTH]

    async def scrape_url(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Scrapes a URL server-side and returns (title, rich_cleaned_content, source_metadata).
        """
        safe_url = validate_url_security(url)
        logger.info(f"Scraping validated URL: {safe_url}")

        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                response = await client.get(safe_url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    raw_text = response.text[:settings.MAX_SCRAPE_CONTENT_LENGTH]
                    parsed = urlparse(safe_url)
                    meta = {
                        "title": parsed.path.split("/")[-1] or parsed.netloc,
                        "description": "",
                        "author": "",
                        "domain": parsed.netloc,
                        "favicon": f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64",
                    }
                    return meta["title"], raw_text, meta

                soup = BeautifulSoup(response.text, "html.parser")
                metadata = self._extract_metadata(soup, safe_url)
                raw_body_markdown = self._clean_html_to_markdown(soup)

                # Build rich, contextual markdown document combining metadata + body
                rich_content = self._build_rich_document(metadata, raw_body_markdown, safe_url)

                metadata["word_count"] = len(rich_content.split())
                metadata["char_count"] = len(rich_content)

                logger.info(
                    f"Successfully scraped '{metadata['title']}' ({metadata['domain']}): "
                    f"{metadata['word_count']} words, {metadata['char_count']} chars."
                )
                return metadata["title"], rich_content, metadata

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            raise ScrapingError(url, f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
        except httpx.RequestError as e:
            logger.error(f"Request error scraping {url}: {str(e)}")
            raise ScrapingError(url, f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            raise ScrapingError(url, str(e))

scraper_service = ScraperService()
