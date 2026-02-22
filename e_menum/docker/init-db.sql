-- =============================================================================
-- E-Menum Database Initialization Script
-- =============================================================================
-- This script runs when the PostgreSQL container is first created.
-- It sets up necessary extensions and configurations for the E-Menum application.
-- =============================================================================

-- Enable useful PostgreSQL extensions
-- UUID generation support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search in Turkish (for menu search)
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Cryptographic functions (for tokens, hashing)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Case-insensitive text type
CREATE EXTENSION IF NOT EXISTS "citext";

-- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- Database Configuration
-- =============================================================================

-- Set default text search configuration to Turkish
-- ALTER DATABASE emenum SET default_text_search_config = 'turkish';

-- Set timezone
ALTER DATABASE emenum SET timezone TO 'Europe/Istanbul';

-- Log statement for confirmation
DO $$
BEGIN
    RAISE NOTICE 'E-Menum database initialized with required extensions';
END
$$;
