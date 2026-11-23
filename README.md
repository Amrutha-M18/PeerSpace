
# PeerSpace

PeerSpace is a student collaboration platform that helps students
discover opportunities, form teams, and collaborate with peers.

## Problem Statement

Students often struggle to find teammates for hackathons, course
projects, competitions, study groups, and other campus activities.

Information is scattered across WhatsApp groups and personal
networks, making it difficult to discover opportunities and
connect with interested students.

PeerSpace aims to solve this problem through a structured platform.

## Core Features

1. User registration and login.
2. Create and discover opportunities.
3. Create teams under opportunities.
4. Request to join existing teams.
5. Team owners can approve or reject join requests.
6. Discover teammates based on interests and skills.
7. Analyze opportunity and team participation data.

## Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL

### Development Tools
- Git and GitHub
- Docker
- Pytest

## Current Implementation Status

### Implemented
- Frontend and backend project setup
- PostgreSQL integration and database models
- Backend signup and login APIs
- Basic application homepage
- Backend health-check endpoint
- Authenticated profile read/update APIs, hobbies, and structured skills with proficiency

See [Profile backend setup and API reference](docs/profile-api.md) for migration,
teammate database updates, endpoint contracts, and tests. Profile frontend integration
is not yet implemented.

### In Progress
- Database-backed opportunity management
- Opportunity creation and discovery interface
- Team creation and management
- Join requests and approvals
- Skill-based matching
- Data analysis and visualizations

## Project Structure

- `docs/` - API reference and detailed development documentation
- `backend/migrations/` - SQL migrations and Python migration runners
- `frontend/` — Next.js application
- `backend/` — FastAPI application
- `backend/models.py` — Database models
- `backend/auth.py` — Authentication endpoints
- `backend/tests/` — Backend tests
- `docker-compose.yaml` — PostgreSQL configuration

## Backend Setup

Install Python 3.10+ and Docker with Compose. Run the following PowerShell commands
from the repository root (the directory containing `docker-compose.yaml`).

For first-time setup, create a local virtual environment and install dependencies:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
docker compose up -d postgres
```

Wait for PostgreSQL to be ready. With the default Compose settings, this command
should report `accepting connections` before you run migrations:

```powershell
docker compose exec postgres pg_isready -U postgres -d mydb
```

Then create the profile schema and start the backend:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.migrations.profiles
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The default database URL is `postgresql://postgres:postgres@localhost:5432/mydb`.
Set `DATABASE_URL` in your local environment or `.env` file if your connection
differs. Plain PostgreSQL URLs use the installed `psycopg2` driver. If you change
`PEERSPACE_DB_PORT`, update the port in `DATABASE_URL` too.

Each developer's virtual environment and database are local. Application startup
creates missing tables and runs the profile migrations to upgrade existing profile tables.
A fresh skill catalog is empty; signed-in students add skills through the API.

## Updating Your Local Database

After changes are committed and pushed, each teammate must pull the branch
containing them and migrate their own database. Stop the backend first with
`Ctrl+C`. Use the existing virtual environment, then run:

```powershell
git pull
docker compose up -d postgres
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Once PostgreSQL is accepting connections, apply the migration and restart:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.migrations.profiles
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The migration prints `Profile migration completed.` on success. It is safe to
rerun and preserves existing user and skill records. It runs the profile migrations
`002`, `003`, `004`, and `005`. Migration `004` drops the retired teaching flag from
skill selections; `005` drops department and year from user profiles.
Application startup also runs these profile migrations. The older opportunity
migration remains a separate script. See the
[profile migration details](docs/profile-api.md#setup) for data-conflict handling.

Pulling code does not update database structure automatically. Each local Docker
volume holds separate data: migrations update the schema, not another teammate's
users or skills. Do not delete the database volume to apply an upgrade.

## Running Backend Tests

Start PostgreSQL, then run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
```

Tests create a temporary PostgreSQL database and isolated schemas, then remove
them afterward. The database account needs permission to create/drop databases
and schemas; the default Compose account supports this. For an existing dedicated
test database, see the [test configuration](docs/profile-api.md#tests).

## Notes

This project is under active development.

The current homepage is temporary. Features listed as in progress
are not yet fully integrated into the application.
