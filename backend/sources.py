"""The small list of public pages used by this POC.

Keeping the URLs in one file makes it easy for students to add another
engineering branch later without changing the API code.
"""

DOMAIN_LABELS = {
    "cse": "Computer Science",
    "electrical": "Electrical Engineering",
    "mechanical": "Mechanical Engineering",
}

SOURCES = {
    "cse": [
        {
            "name": "IISc CSA",
            "url": "https://www.csa.iisc.ac.in/sparks-programme/",
            "type": "Research project",
            "parser": "cse_research",
        },
        {
            "name": "Internshala",
            "url": "https://internshala.com/internships/computer-science-internship/",
            "type": "Industry internship",
            "parser": "industry_listing",
        },
    ],
    "electrical": [
        {
            "name": "IISc Spectrum Lab",
            "url": "https://spectrum.ee.iisc.ac.in/opportunities/",
            "type": "Research project",
            "parser": "electrical_research",
        },
        {
            "name": "Internshala",
            "url": "https://internshala.com/internships/electrical-engineering-internship/",
            "type": "Industry internship",
            "parser": "industry_listing",
        },
    ],
    "mechanical": [
        {
            "name": "IIT Madras Mechanics of Materials Group",
            "url": "https://home.iitm.ac.in/ratna/position.html",
            "type": "Research project",
            "parser": "mechanical_research",
        },
        {
            "name": "Internshala",
            "url": "https://internshala.com/internships/mechanical-engineering-internship/",
            "type": "Industry internship",
            "parser": "industry_listing",
        },
    ],
}
