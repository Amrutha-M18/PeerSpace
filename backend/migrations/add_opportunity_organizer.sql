-- Run once on an existing PostgreSQL database before starting the updated backend.
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS organizer VARCHAR(200);
