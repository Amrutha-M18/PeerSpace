# PeerSpace

## Motivation

Currently, useful student interactions are scattered across WhatsApp groups, Discord,
LinkedIn, GitHub, Google Drive, and personal networks. PeerSpace brings these
interactions into one structured platform specifically designed for a college community.

PeerSpace is a student-driven knowledge and collaboration platform where students can
publish blogs, participate in discussions, solve doubts, review each other's work,
showcase projects, and collaborate on ideas.

## One Liner

We are building a discordlike app specifically catered for being used in
educational settings.

## Features

- Create and participate in topic-based and course-based communities.
- Write, publish, and discover informative blogs.
- Share personal experiences, technical knowledge, tutorials, and learning resources
  through blogs.
- Ask doubts and receive answers from fellow students.
- Share personal projects and receive constructive feedback.
- Connect with people from similar places to ease up travel.

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

It intentionally does **not** include login, a database, automatic scheduled
scraping, saved opportunities, or support for every engineering branch yet.

### Run locally

Open two terminals in the repository root.

Terminal 1 starts the backend:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

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
