# PeerSpace

## Motivation

Currently, useful student interactions are scattered across WhatsApp groups, Discord,
LinkedIn, GitHub, Google Drive, and personal networks. PeerSpace brings these
interactions into one structured platform specifically designed for a college community.

PeerSpace is a student-driven knowledge and collaboration platform where students can
publish blogs, participate in discussions, solve doubts, review each other's work,
showcase projects, and collaborate on ideas.

## One Liner

We are building a discord like app specifically catered for being used in
educational settings.

## Features

- Create and participate in topic-based and course-based communities.
- Write, publish, and discover informative blogs.
- Share personal experiences, technical knowledge, tutorials, and learning resources
  through blogs.
- Ask doubts and receive answers from fellow students.
- Share personal projects and receive constructive feedback.
- Connect with people from similar places to ease up travel.

## Tech Stack

### Frontend
- Next.js 16 & React 19 – Building the user interface and handling frontend functionality.
- TypeScript – Type-safe frontend development.
- Tailwind CSS 4 – Styling and responsive design.
- shadcn/ui & Base UI React – Reusable and accessible UI components.
- Lucide React – Icons.

### Backend
- Python & FastAPI – Building backend services and REST API endpoints.
- Uvicorn – Running the FastAPI server.
- Requests – Fetching data from external websites.
- BeautifulSoup4 – Parsing HTML and extracting information from web pages.

## Opportunity Discovery POC

This repository now contains a small proof of concept for discovering public
student opportunities. A student selects a domain and PeerSpace shows a mix of
research projects and industry internships. The result cards always link back
to the original public source, so students can verify and apply there.

### What this POC includes

- A Next.js page with Computer Science, Electrical Engineering, and Mechanical
  Engineering as the currently supported domains.
- A small FastAPI endpoint that fetches selected public pages only when a
  student searches.
- One academic source and one industry-listing source per supported domain.
- Clear labels for `Research project` and `Industry internship` cards.
- Up to 10 industry internships and up to 10 research projects per search.

Live discovery does not use scheduled scraping or cover every engineering branch yet.
The backend also includes authentication and APIs for stored opportunities.

### Run locally

Open two terminals in the repository root.

Terminal 1 starts the backend:

```bash
docker compose up -d
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

The backend uses PostgreSQL. For a database created before the `organizer`
field was added, run this migration before starting the updated backend:

```bash
docker compose exec -T postgres psql -U postgres -d mydb -f - < backend/migrations/add_opportunity_organizer.sql
```

Alternatively, run the SQL file with `psql` against your configured database.
New databases receive the column automatically when the backend starts.

Terminal 2 starts the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in a browser. The frontend uses
`http://127.0.0.1:8000` by default. To change that address, copy
`frontend/.env.local.example` to `frontend/.env.local` and edit the value.

### API

```text
GET /api/opportunities?domain=cse
GET /api/opportunities?domain=electrical
GET /api/opportunities?domain=mechanical
```

The response includes `opportunities`, `warnings`, and `fetched_at`. If one
public page is unavailable, the backend returns results from the other source
and explains the missing source in `warnings`.

Stored opportunities use the same base path without a `domain` parameter:

```text
POST /api/opportunities
GET /api/opportunities
GET /api/opportunities?category=hackathon&q=campus&upcoming=true
GET /api/opportunities/{id}
```

The POST body accepts `title`, `category`, and optional `organizer`,
`description`, `starts_on`, `ends_on`, `official_url`, and `team_size`.
Categories are `hackathon`, `course project`, `study group`, `trek`, `sport`,
and `other`. Listing returns a JSON array. Search matches title or description,
and `upcoming=true` includes opportunities starting today or later. Do not
combine `domain` with stored-opportunity filters.

### Source coverage and limitations

The academic sources are IISc CSA SPARKS (CSE), IISc Spectrum Lab
(Electrical), and IIT Madras Mechanics of Materials Group (Mechanical).
Industry cards come from domain-specific public internship listing pages, and
their `View internship` buttons open the individual posting page rather than a
generic filter page. Research cards open the relevant official programme or lab
page. A category may have fewer than 10 cards when fewer readable public posts
are available.

The pages are fetched live, and their HTML layouts can change or temporarily
block a request. This is a small course POC, so users must confirm every
deadline, eligibility rule, and application detail using the linked original
source.
