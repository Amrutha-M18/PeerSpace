-- Run transactionally before starting an upgraded backend (see docs/profile-api.md).
-- Never invent proficiency for legacy skills.
DO $$
DECLARE
    populated BIGINT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'users' AND column_name = 'skills'
    ) THEN
        EXECUTE 'SELECT COUNT(*) FROM users WHERE skills IS NOT NULL
                 AND skills::jsonb NOT IN (''[]''::jsonb, ''null''::jsonb)' INTO populated;
        IF populated > 0 THEN
            RAISE EXCEPTION 'Nonempty legacy user skills found. Explicitly migrate skill names and levels before retrying; existing data has been preserved.';
        END IF;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    skills JSON NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS hobbies JSON NOT NULL DEFAULT '[]';

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_skills (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    level INTEGER NOT NULL,
    PRIMARY KEY (user_id, skill_id),
    CONSTRAINT ck_user_skills_level CHECK (level BETWEEN 1 AND 5)
);
