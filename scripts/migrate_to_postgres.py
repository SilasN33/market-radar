"""
Migration script to create Postgres schema on Vercel
Run this once after setting up Vercel Postgres
"""
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not set. Please set it first:")
    print("   export DATABASE_URL='your-vercel-postgres-url'")
    exit(1)

print("🔄 Connecting to Vercel Postgres...")
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

print("📊 Creating tables...")

# 1. Products
cursor.execute("""
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
)
""")

# 2. Trends
cursor.execute("""
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    interest INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 3. Intent Clusters
cursor.execute("""
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
)
""")

# 4. Opportunities
cursor.execute("""
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
)
""")

# 5. Users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'free',
    credits INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 6. User Projects
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 7. Saved Opportunities
cursor.execute("""
CREATE TABLE IF NOT EXISTS saved_opportunities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    project_id INTEGER,
    opportunity_id INTEGER REFERENCES opportunities(id),
    notes TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create indexes for performance
print("🔍 Creating indexes...")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_created ON opportunities(created_at DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_clusters_created ON intent_clusters(created_at DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_keyword ON products(keyword)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

conn.commit()
conn.close()

print("✅ Postgres migration complete!")
print("📊 All tables created successfully.")
print("🚀 Ready for deployment!")
