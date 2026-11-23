-- Remove retired profile fields while preserving users and their other data.
ALTER TABLE users
    DROP COLUMN IF EXISTS department,
    DROP COLUMN IF EXISTS year;
