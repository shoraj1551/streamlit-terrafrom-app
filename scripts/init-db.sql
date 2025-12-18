-- Initialize database with required extensions and settings

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create indexes for common queries
-- (Will be created by Alembic migrations)

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE terraform_app TO terraform_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO terraform_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO terraform_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO terraform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO terraform_user;
