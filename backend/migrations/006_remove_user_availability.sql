-- Remove the retired profile field while preserving users and their other data.
ALTER TABLE users DROP COLUMN IF EXISTS availability;
