-- Keep existing IDs and names; fail transactionally if old names conflict.
CREATE UNIQUE INDEX IF NOT EXISTS uq_skills_name_normalized
    ON skills (lower(btrim(name)));
