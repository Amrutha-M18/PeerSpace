-- Team creation: a description, members added by name, and skill requirements
-- in their own table (replacing the old teams.needed_skills JSON list).
-- SQLAlchemy creates the team tables at startup, so only upgrade databases that have them.
DO $$
BEGIN
    IF to_regclass('teams') IS NULL THEN
        RETURN;
    END IF;

    ALTER TABLE teams ADD COLUMN IF NOT EXISTS description VARCHAR(1000);

    -- Members can be people who are not on PeerSpace: a name and no user account.
    ALTER TABLE team_members ADD COLUMN IF NOT EXISTS name VARCHAR(100);
    UPDATE team_members SET name = users.name
    FROM users WHERE team_members.user_id = users.id AND team_members.name IS NULL;
    UPDATE team_members SET name = 'Member' WHERE name IS NULL;
    ALTER TABLE team_members ALTER COLUMN name SET NOT NULL;
    ALTER TABLE team_members ALTER COLUMN user_id DROP NOT NULL;

    CREATE TABLE IF NOT EXISTS team_skills (
        team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
        skill_id INTEGER NOT NULL REFERENCES skills(id),
        min_level INTEGER NOT NULL,
        is_hard BOOLEAN NOT NULL,
        count INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (team_id, skill_id),
        CONSTRAINT ck_team_skills_min_level CHECK (min_level BETWEEN 1 AND 5),
        CONSTRAINT ck_team_skills_count CHECK (count >= 1)
    );

    -- Move entries from the old needed_skills list ({"skill_id", "min_level", "must_have"}
    -- objects or plain skill IDs) into team_skills, then drop the column.
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'teams' AND column_name = 'needed_skills'
    ) THEN
        INSERT INTO team_skills (team_id, skill_id, min_level, is_hard, count)
        SELECT team_id, skill_id, min_level, is_hard, 1
        FROM (
            SELECT teams.id AS team_id,
                   CASE WHEN json_typeof(item) = 'number' THEN (item #>> '{}')::int
                        ELSE (item ->> 'skill_id')::int END AS skill_id,
                   CASE WHEN json_typeof(item) = 'number' THEN 1
                        ELSE LEAST(5, GREATEST(1, COALESCE((item ->> 'min_level')::int, 1))) END AS min_level,
                   CASE WHEN json_typeof(item) = 'number' THEN false
                        ELSE COALESCE((item ->> 'must_have')::boolean, false) END AS is_hard
            FROM teams, json_array_elements(teams.needed_skills::json) AS item
            WHERE json_typeof(item) IN ('number', 'object')
        ) AS old
        WHERE skill_id IN (SELECT id FROM skills)
        ON CONFLICT DO NOTHING;

        ALTER TABLE teams DROP COLUMN needed_skills;
    END IF;
END $$;
