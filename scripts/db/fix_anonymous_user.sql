-- Fix anonymous user issue for existing databases
-- This script creates an 'admin' user if it doesn't exist
-- and updates any 'anonymous' references to 'admin'

-- Check if admin user exists, create if not
INSERT INTO users (id, username, password_hash, is_active, created_at)
SELECT
    'admin',
    'admin',
    '$2b$12$INVALID_HASH_FOR_SECURITY',  -- This hash won't match any password
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE username = 'admin' OR id = 'admin'
);

-- Update any existing conversations with user_id = 'anonymous' to 'admin'
UPDATE conversations
SET user_id = 'admin'
WHERE user_id = 'anonymous';

-- Verify the fix
SELECT
    'Total conversations with anonymous user:' as description,
    COUNT(*) as count
FROM conversations
WHERE user_id = 'anonymous'
UNION ALL
SELECT
    'Total conversations with admin user:' as description,
    COUNT(*) as count
FROM conversations
WHERE user_id = 'admin';
