import requests

from backend import scraper
from backend.scraper import parse_cse_research_page, parse_industry_listing


def test_cse_research_parser_returns_one_normalized_card():
    html = """
    <html><body>
      <h1>SPARKS: Scholars Pursuing Advanced Research</h1>
      <p>This programme lets students work with a faculty member on a research project.</p>
    </body></html>
    """
    source = {
        "name": "IISc CSA",
        "url": "https://example.com/sparks",
        "type": "Research project",
    }

    cards = parse_cse_research_page(html, source)

    assert len(cards) == 1
    assert cards[0]["domain"] == "Computer Science"
    assert cards[0]["type"] == "Research project"
    assert cards[0]["apply_url"] == source["url"]


def test_industry_parser_uses_individual_internship_links():
    html = """
    <html><body>
      <div class="individual_internship">
        <h2 class="job-internship-name"><a href="/internship/detail/python-development123">Python Development</a></h2>
        <p class="company_name">Example Software</p>
        <p>Remote, 3 months, paid internship.</p>
      </div>
      <div class="individual_internship">
        <h2 class="job-internship-name"><a href="/internship/detail/embedded-systems456">Embedded Systems</a></h2>
        <p class="company_name">Hardware Company</p>
        <p>Bengaluru, 6 months, paid internship.</p>
      </div>
    </body></html>
    """
    source = {
        "name": "Internshala",
        "url": "https://example.com/internships",
        "type": "Industry internship",
    }

    cards = parse_industry_listing(html, source, "electrical")

    assert len(cards) == 2
    assert cards[0]["title"] == "Python Development"
    assert cards[0]["type"] == "Industry internship"
    assert cards[0]["domain"] == "Electrical Engineering"
    assert cards[0]["organisation"] == "Example Software"
    assert cards[0]["apply_url"] == "https://example.com/internship/detail/python-development123"
    assert cards[0]["apply_url"] != source["url"]


def test_industry_parser_removes_duplicates_and_stops_at_ten_cards():
    cards_html = []
    for number in range(12):
        cards_html.append(
            f'<div class="individual_internship"><a href="/internship/detail/role-{number}">Role {number}</a>'
            f'<p class="company_name">Company {number}</p></div>'
        )
    cards_html.append('<a href="/internship/detail/role-0">Duplicate role</a>')
    source = {
        "name": "Internshala",
        "url": "https://internshala.com/internships/computer-science-internship/",
        "type": "Industry internship",
    }

    cards = parse_industry_listing("".join(cards_html), source, "cse")

    assert len(cards) == 10
    assert len({card["apply_url"] for card in cards}) == 10


def test_one_broken_source_becomes_a_warning_while_other_results_are_returned(monkeypatch):
    def pretend_to_fetch(url: str) -> str:
        if "iisc.ac.in" in url:
            raise requests.RequestException("temporary network problem")
        return """
        <div class="individual_internship">
          <a href="/internship/detail/software-engineering">Software Engineering</a>
          <p class="company_name">Example Company</p>
        </div>
        """

    monkeypatch.setattr(scraper, "fetch_html", pretend_to_fetch)

    cards, warnings = scraper.scrape_opportunities("cse")

    assert len(cards) == 1
    assert cards[0]["type"] == "Industry internship"
    assert warnings == ["Could not fetch IISc CSA right now."]


def test_research_results_are_capped_at_ten(monkeypatch):
    research_sources = [
        {"name": f"Lab {number}", "url": f"https://example.com/{number}", "type": "Research project", "parser": "cse_research"}
        for number in range(12)
    ]
    monkeypatch.setitem(scraper.SOURCES, "cse", research_sources)
    monkeypatch.setattr(scraper, "fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr(
        scraper,
        "parse_source",
        lambda html, source, domain: [{"title": source["name"], "type": source["type"]}],
    )

    cards, warnings = scraper.scrape_opportunities("cse")

    assert len(cards) == 10
    assert warnings == []
