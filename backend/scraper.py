"""Small, readable scrapers for the pages listed in sources.py.

This POC intentionally uses simple HTML parsing instead of a crawler, database,
or background job. Each parser returns cards in the same shape for the frontend.
"""

from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .sources import DOMAIN_LABELS, SOURCES

REQUEST_HEADERS = {
    "User-Agent": "PeerSpaceOpportunityPOC/1.0 (student project)",
}
REQUEST_TIMEOUT_SECONDS = 10
MAX_INDUSTRY_RESULTS = 10
MAX_RESEARCH_RESULTS = 10


def clean_text(value: str) -> str:
    """Turn page text into one readable line."""
    return " ".join(value.split())


def fetch_html(url: str) -> str:
    """Download one public page with a short timeout."""
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def make_opportunity(
    *,
    title: str,
    organisation: str,
    domain: str,
    opportunity_type: str,
    description: str,
    source_name: str,
    source_url: str,
    apply_url: str | None = None,
) -> dict[str, str]:
    """Build the one card format shared by every source."""
    return {
        "title": title,
        "organisation": organisation,
        "domain": DOMAIN_LABELS[domain],
        "type": opportunity_type,
        "description": description,
        "apply_url": apply_url or source_url,
        "source_name": source_name,
        "source_url": source_url,
    }


def first_useful_paragraph(soup: BeautifulSoup) -> str:
    """Find the first substantial paragraph on a source page."""
    for paragraph in soup.find_all("p"):
        text = clean_text(paragraph.get_text(" ", strip=True))
        if len(text) > 80:
            return text[:500]
    return "Open the original source to read the opportunity details."


def parse_cse_research_page(html: str, source: dict[str, str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    title = clean_text(heading.get_text()) if heading else "SPARKS research programme"
    return [
        make_opportunity(
            title=title,
            organisation="Indian Institute of Science, Computer Science and Automation",
            domain="cse",
            opportunity_type=source["type"],
            description=first_useful_paragraph(soup),
            source_name=source["name"],
            source_url=source["url"],
        )
    ]


def parse_electrical_research_page(html: str, source: dict[str, str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    title = clean_text(heading.get_text()) if heading else "Spectrum Lab opportunities"
    return [
        make_opportunity(
            title=title,
            organisation="IISc Bangalore, Spectrum Lab",
            domain="electrical",
            opportunity_type=source["type"],
            description=first_useful_paragraph(soup),
            source_name=source["name"],
            source_url=source["url"],
        )
    ]


def parse_mechanical_research_page(html: str, source: dict[str, str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    title = clean_text(heading.get_text()) if heading else "Mechanics of Materials project positions"
    return [
        make_opportunity(
            title=title,
            organisation="IIT Madras, Department of Mechanical Engineering",
            domain="mechanical",
            opportunity_type=source["type"],
            description=first_useful_paragraph(soup),
            source_name=source["name"],
            source_url=source["url"],
        )
    ]


def parse_industry_listing(html: str, source: dict[str, str], domain: str) -> list[dict[str, str]]:
    """Read direct internship-detail links from a public listing page."""
    soup = BeautifulSoup(html, "html.parser")
    opportunities: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        if "/internship/detail/" not in link["href"]:
            continue

        direct_url = urljoin(source["url"], link["href"])
        if direct_url in seen_urls:
            continue
        seen_urls.add(direct_url)

        title = clean_text(link.get_text(" ", strip=True))
        if len(title) < 3:
            continue

        card = link.find_parent("div", class_="individual_internship")
        if card is None:
            card = link.find_parent(["article", "li", "div"])

        company = card.select_one(".company_name") if card else None
        organisation = clean_text(company.get_text(" ", strip=True)) if company else "Company listed on Internshala"
        description = clean_text(card.get_text(" ", strip=True)) if card else ""
        if not description:
            description = "Open the internship page for the complete role details."

        opportunities.append(
            make_opportunity(
                title=title[:120],
                organisation=organisation[:120],
                domain=domain,
                opportunity_type=source["type"],
                description=description[:500],
                source_name=source["name"],
                source_url=source["url"],
                apply_url=direct_url,
            )
        )
        if len(opportunities) == MAX_INDUSTRY_RESULTS:
            break

    return opportunities


def parse_source(html: str, source: dict[str, str], domain: str) -> list[dict[str, str]]:
    """Choose the small parser required for this source."""
    parser_name = source["parser"]
    if parser_name == "cse_research":
        return parse_cse_research_page(html, source)
    if parser_name == "electrical_research":
        return parse_electrical_research_page(html, source)
    if parser_name == "mechanical_research":
        return parse_mechanical_research_page(html, source)
    return parse_industry_listing(html, source, domain)


def scrape_opportunities(domain: str) -> tuple[list[dict[str, str]], list[str]]:
    """Fetch all configured sources for one domain.

    A broken source should not hide results from the other source, so failures
    become warnings that the frontend can show.
    """
    research_opportunities: list[dict[str, str]] = []
    industry_opportunities: list[dict[str, str]] = []
    warnings: list[str] = []

    for source in SOURCES[domain]:
        try:
            html = fetch_html(source["url"])
            parsed_items = parse_source(html, source, domain)
            if parsed_items:
                if source["type"] == "Research project":
                    remaining = MAX_RESEARCH_RESULTS - len(research_opportunities)
                    research_opportunities.extend(parsed_items[:remaining])
                else:
                    remaining = MAX_INDUSTRY_RESULTS - len(industry_opportunities)
                    industry_opportunities.extend(parsed_items[:remaining])
            else:
                warnings.append(f"{source['name']} did not return readable listings today.")
        except requests.RequestException:
            warnings.append(f"Could not fetch {source['name']} right now.")
        except Exception:
            # A public page can change its HTML without warning. Treat that as
            # one unavailable source instead of failing the whole search.
            warnings.append(f"Could not read {source['name']} right now.")

    return industry_opportunities + research_opportunities, warnings
