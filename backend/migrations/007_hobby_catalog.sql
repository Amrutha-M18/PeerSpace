-- Interest (hobby) catalogue and which interests each user picked.
-- Unlike skills, interests have no level.
CREATE TABLE IF NOT EXISTS hobbies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_hobbies_name_normalized ON hobbies (lower(btrim(name)));

CREATE TABLE IF NOT EXISTS user_hobbies (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hobby_id INTEGER NOT NULL REFERENCES hobbies(id),
    PRIMARY KEY (user_id, hobby_id)
);
-- Databases created by an earlier draft of this migration had a level column.
ALTER TABLE user_hobbies DROP COLUMN IF EXISTS level;

-- Keep old free-text hobbies selectable by adding their names to the catalogue.
INSERT INTO hobbies (name)
SELECT DISTINCT btrim(value)
FROM users, json_array_elements_text(users.hobbies) AS value
WHERE btrim(value) <> ''
ON CONFLICT DO NOTHING;
