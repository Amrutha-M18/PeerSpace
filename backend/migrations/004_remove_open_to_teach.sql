-- Remove the retired flag while preserving skill selections and proficiency levels.
ALTER TABLE user_skills DROP COLUMN IF EXISTS open_to_teach;
