"""
Alternative migration using Supabase SQL Editor
Copy and paste this SQL directly into Supabase SQL Editor
"""

SQL_MIGRATION = """
-- Market Radar Database Schema for Supabase

-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    price TEXT,
    url TEXT,
    thumbnail TEXT,
    marketplace TEXT,
    free_shipping BOOLEAN,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    keyword TEXT
);

-- 2. Trends Table
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    interest INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Intent Clusters Table
CREATE TABLE IF NOT EXISTS intent_clusters (
    id SERIAL PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    buying_intent TEXT,
    validated_products TEXT,
    price_range_min REAL,
    price_range_max REAL,
    negative_keywords TEXT,
    why_trending TEXT,
    source_signals TEXT,
    competition_level TEXT,
    risk_factors TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Opportunities Table
CREATE TABLE IF NOT EXISTS opportunities (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    cluster_id INTEGER REFERENCES intent_clusters(id),
    score REAL,
    intent_confidence REAL,
    market_validation REAL,
    signal_diversity REAL,
    velocity_score REAL,
    marketplace TEXT,
    url TEXT,
    thumbnail TEXT,
    price TEXT,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'free',
    credits INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. User Projects Table
CREATE TABLE IF NOT EXISTS user_projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Saved Opportunities Table
CREATE TABLE IF NOT EXISTS saved_opportunities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    project_id INTEGER,
    opportunity_id INTEGER REFERENCES opportunities(id),
    notes TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_opportunities_created ON opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clusters_created ON intent_clusters(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_products_keyword ON products(keyword);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- All done!
"""

if __name__ == "__main__":
    print("=" * 70)
    print("SUPABASE SQL MIGRATION")
    print("=" * 70)
    print("\n📋 STEPS:")
    print("\n1. Open Supabase Dashboard: https://supabase.com/dashboard")
    print("2. Select your 'market-radar' project")
    print("3. Go to SQL Editor (left sidebar)")
    print("4. Click 'New Query'")
    print("5. Copy the SQL below and paste it")
    print("6. Click 'Run' or press Ctrl+Enter")
    print("\n" + "=" * 70)
    print("SQL TO COPY:")
    print("=" * 70)
    print(SQL_MIGRATION)
    print("=" * 70)
    print("\n✅ After running, you'll see all tables in Table Editor!")
    print("\n")
