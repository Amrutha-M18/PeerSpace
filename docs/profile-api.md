# Profile backend

## Setup

Follow [backend setup](../README.md#backend-setup) for first-time installation,
or [updating a local database](../README.md#updating-your-local-database) after
pulling changes. Commands run from the repository root. The profile migration
runner is `python -m backend.migrations.profiles` when using the backend environment.
Application startup in `backend/main.py` also runs this migration runner.

The migration runs in one transaction and supports empty and existing databases.
It creates the profile tables and adds hobbies; application startup creates other
missing tables. `create_all()` alone does not upgrade existing tables. The migration
is repeatable. Migration `004` drops the retired teaching flag from existing skill
selections while preserving their user IDs, skill IDs, and proficiency levels.
Migration `005` drops the retired department and year columns from user profiles,
preserving accounts and all other profile data.
The migration also adds a unique index for skill
names ignoring case and surrounding spaces, preserving existing names and IDs.
If old catalog entries conflict under that rule, it fails without deleting or
merging them; resolve the conflicting names before retrying.
The old `users.skills` JSON column is retained
for compatibility but is no longer read or written by profile APIs. If it contains
nonempty data, the migration aborts without changes: explicitly map those names to
catalog skills, collect actual levels, and archive/clear
the legacy values before retrying. No proficiency values are inferred.

## Updating each teammate's local database

Each developer running Compose locally has a separate PostgreSQL database and
Docker volume. Follow the [README update steps](../README.md#updating-your-local-database)
on each machine. Pulling code does not update the database or copy another
developer's data. Use that developer's `DATABASE_URL` or the Compose defaults.

The migration adds the required schema while preserving existing user records.
It can be rerun after another pull without duplicating tables. A successful run
prints `Profile migration completed.` If it fails because of nonempty old JSON
skills or conflicting catalog names, existing data is preserved; resolve the
reported data conflict before retrying. Do not delete the Docker volume to upgrade.

A fresh database starts with an empty skill catalog. Signed-in students populate
it using `POST /api/skills`. Existing catalog entries remain, including any starter
skills inserted before the seed command was removed. A new skill is shared among
accounts using the same database; it is not copied to teammates' separate local
databases. IDs may differ between databases, so clients must obtain them from the API.

## Endpoints

Every endpoint below requires `Authorization: Bearer <JWT>`. Obtain a token through
`POST /api/auth/signup` or `POST /api/auth/login` as before. The existing
`GET /api/auth/me` still returns only `id`, `email`, and `name`.

| Endpoint | Request body | Response |
|---|---|---|
| `GET /api/me` | None | Full profile |
| `PUT /api/me` | All editable profile fields | Saved full profile |
| `PUT /api/me/skills` | Array of skill selections | Saved full profile |
| `GET /api/skills` | None | Array of `{id, name}`, ordered by name |
| `POST /api/skills` | `{"name": "Rust"}` | New or existing `{id, name}` |

Reads and profile saves use status `200`. Catalog creation uses `201` for a new
entry or `200` when the name already exists. Skill names are trimmed, nonblank,
and limited to 100 characters; additional fields are rejected. Names differing only
by capitalization or surrounding spaces share one ID, including simultaneous
submissions. The existing entry's name is preserved. Different spellings and synonyms
are not automatically merged.

Any signed-in student can add a missing skill; it immediately appears in the shared
catalog for other students. Creating it does not add it to anyone's profile.
The frontend should offer an "Add skill" action when the desired name is missing,
call `POST /api/skills`, and use its returned ID in the student's skill selection
with a level. Refresh the catalog to show new entries.

Students populate the catalog by adding skills. IDs are database assigned: obtain
them from `GET /api/skills` or the creation response.

Example full profile save (replace `1` with an ID from your catalog):

```json
{
  "name": "Asha",
  "availability": ["Weekends"],
  "hobbies": ["Photography", "Trekking"],
  "skills": [{"skill_id": 1, "level": 3}]
}
```

`PUT /api/me` requires every field shown; lists can be empty. Name, hobbies,
and availability entries are trimmed, nonblank strings of at most 100 characters.
Additional fields are rejected.

`PUT /api/me/skills` accepts just the selections array. Both writes replace the
entire selected skill list; `[]` clears it. Skill-only writes preserve all other
profile fields. Repeating a save does not create duplicate selections. Each skill
requires an existing positive integer `skill_id` and an integer `level` from 1–5.
Duplicate IDs and additional fields are rejected.
The whole save is atomic, including profile fields and skills.

Profile responses contain `id`, `email`, `name`, `availability`,
`hobbies`, `skills`, and `created_at`. Returned skill selections additionally
contain `name` from the catalog. New accounts have empty lists.
ID, email, and creation time are read-only; password hashes are never returned.

Missing/invalid/expired tokens return `401`; invalid fields, unknown skills, and
duplicate selections return `422`. Errors use FastAPI's `detail` property, which
can be a string or a validation-error list. Database failures roll back the save.
The current user is always derived from the JWT, never a submitted user ID.

Frontend integration: log in, load `/api/me` and `/api/skills`, add a missing catalog
skill if needed, edit, submit all
editable fields (or the skill-only array), and render the returned saved profile.
Hobbies describe a person; the existing `interests` table tracks opportunities
and is unrelated to this profile feature.

## Tests

See [running backend tests](../README.md#running-backend-tests) for the command.

All tests use PostgreSQL, including API, migration, and constraint tests. Start
PostgreSQL before running the suite. By default, tests use the server credentials
from `DATABASE_URL` to create a uniquely named temporary database, isolate each test
in its own schema, and remove everything afterward. The account needs permission
to create/drop databases and schemas. The default Compose account supports this.

If your test account cannot create databases, provision a dedicated test database
and select it explicitly:

```powershell
$env:PEERSPACE_TEST_DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/peerspace_profile_test'
.\backend\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:PEERSPACE_TEST_DATABASE_URL
```

With an explicit test URL, the suite creates/removes only its own schemas and leaves
the test database in place. That account needs permission to create/drop schemas.
Do not point this variable at a production or development application database.
Test clients do not run application startup against `DATABASE_URL`. PostgreSQL
connection or setup failures fail the suite; migration tests are always included.
