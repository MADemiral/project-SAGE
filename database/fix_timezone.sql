-- Fix timezone issue for calendar_events table
-- This removes timezone awareness from the datetime columns

-- First, let's see what we have
SELECT id, title, event_date, event_date AT TIME ZONE 'UTC' as utc_time FROM calendar_events LIMIT 5;

-- Convert existing timestamps from UTC to timezone-naive
-- (Assuming your local timezone is Turkey/Istanbul which is UTC+3)
UPDATE calendar_events 
SET event_date = event_date AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Istanbul';

UPDATE calendar_events 
SET end_date = end_date AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Istanbul'
WHERE end_date IS NOT NULL;

UPDATE calendar_events 
SET created_at = created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Istanbul'
WHERE created_at IS NOT NULL;

UPDATE calendar_events 
SET updated_at = updated_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Istanbul'
WHERE updated_at IS NOT NULL;

-- Now alter the columns to remove timezone
ALTER TABLE calendar_events 
ALTER COLUMN event_date TYPE timestamp WITHOUT TIME ZONE;

ALTER TABLE calendar_events 
ALTER COLUMN end_date TYPE timestamp WITHOUT TIME ZONE;

ALTER TABLE calendar_events 
ALTER COLUMN created_at TYPE timestamp WITHOUT TIME ZONE;

ALTER TABLE calendar_events 
ALTER COLUMN updated_at TYPE timestamp WITHOUT TIME ZONE;

-- Verify the fix
SELECT id, title, event_date FROM calendar_events LIMIT 5;
