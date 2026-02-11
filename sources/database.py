import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market_radar.db"

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Products Table (The items we are tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marketplace TEXT NOT NULL,
        external_id TEXT, -- Unique ID from the marketplace (e.g., extracted from URL)
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        thumbnail TEXT,
        current_price REAL,
        currency TEXT DEFAULT 'BRL',
        last_updated DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(marketplace, url) -- Simplified constraint using URL as ID for now
    )
    """)
    
    # 2. Price History (To track inflation/discounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        price REAL NOT NULL,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        search_keyword TEXT, -- Context: which keyword found this price?
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    
    # 3. Validation Logs (Why was this product picked?)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        search_keyword TEXT,
        intent_cluster TEXT,
        scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # 4. Intent Clusters (AI Output)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intent_clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_name TEXT NOT NULL,
        buying_intent TEXT,
        validated_products TEXT, -- JSON
        price_range_min REAL,
        price_range_max REAL,
        negative_keywords TEXT, -- JSON
        why_trending TEXT,
        source_signals TEXT, -- JSON
        competition_level TEXT,
        risk_factors TEXT,
        confidence_score INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(cluster_name, created_at) -- Prevent dupes in same run
    )
    """)

    # 5. Opportunities (Final Ranking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        cluster_id INTEGER,
        score REAL,
        intent_confidence REAL,
        market_validation REAL,
        signal_diversity REAL,
        velocity_score REAL,
        marketplace TEXT,
        url TEXT,
        thumbnail TEXT,
        price TEXT,
        analysis TEXT, -- JSON with why, risk, etc.
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(cluster_id) REFERENCES intent_clusters(id)
    )
    """)

    # 6. Users (SaaS Core)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'free', -- free, pro, admin
        credits INTEGER DEFAULT 10,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Projects / Saved Items (Multi-tenancy)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_id INTEGER,
        opportunity_id INTEGER, -- Link to global opp
        notes TEXT,
        saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[database] ✅ Banco de dados inicializado em: {DB_PATH}")

def upsert_product(product_data: Dict[str, Any], keyword: str = "") -> int:
    """Insert or Update a product and record its price history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    marketplace = product_data.get("marketplace", "Unknown")
    url = product_data.get("permalink") or product_data.get("url")
    title = product_data.get("title")
    price = product_data.get("price")
    thumbnail = product_data.get("thumbnail")
    
    if not url or not title:
        return 0
        
    # 1. UPSERT Product
    cursor.execute("""
        INSERT INTO products (marketplace, title, url, thumbnail, current_price, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(marketplace, url) DO UPDATE SET
            current_price = excluded.current_price,
            last_updated = excluded.last_updated,
            thumbnail = excluded.thumbnail
        RETURNING id
    """, (marketplace, title, url, thumbnail, price, datetime.now()))
    
    product_id = cursor.fetchone()[0]
    
    # 2. Record Price History
    if price is not None:
        cursor.execute("""
            INSERT INTO price_history (product_id, price, search_keyword, recorded_at)
            VALUES (?, ?, ?, ?)
        """, (product_id, price, keyword, datetime.now()))
    
    # 3. Log Scan (Traceability)
    cursor.execute("""
        INSERT INTO scan_logs (product_id, search_keyword, scanned_at)
        VALUES (?, ?, ?)
    """, (product_id, keyword, datetime.now()))

    conn.commit()
    conn.close()
    return product_id

def get_product_history(product_id: int) -> List[Dict]:
    """Get price history for a specific product."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT price, recorded_at, search_keyword 
        FROM price_history 
        WHERE product_id = ? 
        ORDER BY recorded_at ASC
    """, (product_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_cluster(cluster_data: Dict[str, Any]) -> int:
    """Insert a new Intent Cluster."""
    conn = get_connection()
    cursor = conn.cursor()

    # Serialize JSON fields
    validated = json.dumps(cluster_data.get("validated_products", []))
    negatives = json.dumps(cluster_data.get("negative_keywords", []))
    sources = json.dumps(cluster_data.get("source_signals_used", []))
    
    price_range = cluster_data.get("price_range_brl", {})
    p_min = price_range.get("min", 0)
    p_max = price_range.get("max", 0)

    cursor.execute("""
        INSERT INTO intent_clusters (
            cluster_name, buying_intent, validated_products, 
            price_range_min, price_range_max, negative_keywords,
            why_trending, source_signals, competition_level,
            risk_factors, confidence_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (
        cluster_data.get("cluster_name"),
        cluster_data.get("buying_intent"),
        validated,
        p_min,
        p_max,
        negatives,
        cluster_data.get("why_trending"),
        sources,
        cluster_data.get("competition_level"),
        cluster_data.get("risk_factors"),
        cluster_data.get("confidence_score"),
        datetime.now()
    ))
    
    cluster_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return cluster_id

def save_opportunity(opp_data: Dict[str, Any], cluster_id: Optional[int] = None) -> int:
    """Insert a ranked Opportunity."""
    conn = get_connection()
    cursor = conn.cursor()

    signals = opp_data.get("signals", {})
    meta = opp_data.get("meta", {})
    analysis = opp_data.get("analysis", {})
    
    analysis_json = json.dumps(analysis)

    cursor.execute("""
        INSERT INTO opportunities (
            keyword, cluster_id, score, 
            intent_confidence, market_validation, signal_diversity, velocity_score,
            marketplace, url, thumbnail, price, analysis, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (
        opp_data.get("keyword"),
        cluster_id,
        opp_data.get("score"),
        signals.get("intent_confidence", 0),
        signals.get("market_validation", 0),
        signals.get("signal_diversity_count", 0), # Note: kept simpler in DB
        0.0, # Velocity score not explicitly exposed in to_dict signals usually, but calculated in score()
        meta.get("marketplace"),
        meta.get("url"),
        meta.get("thumbnail"),
        meta.get("price"),
        analysis_json,
        datetime.now()
    ))

    opp_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return opp_id

def get_cluster_id_by_name(cluster_name: str) -> Optional[int]:
    """Find the most recent cluster ID by name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM intent_clusters 
        WHERE cluster_name = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (cluster_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_latest_ranking(limit: int = 50) -> List[Dict]:
    """Fetch the latest batch of opportunities."""
    conn = get_connection()
    cursor = conn.cursor()
    # Find latest created_at date for opportunities to get the whole batch
    cursor.execute("SELECT MAX(created_at) FROM opportunities")
    latest = cursor.fetchone()[0]
    
    if not latest:
        conn.close()
        return []
        
    cursor.execute("""
        SELECT o.*, c.cluster_name, c.buying_intent, c.why_trending as cluster_why
        FROM opportunities o
        LEFT JOIN intent_clusters c ON o.cluster_id = c.id
        WHERE o.created_at = ?
        ORDER BY o.score DESC
        LIMIT ?
    """, (latest, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        d = dict(r)
        # Parse JSON fields
        try:
            d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else {}
        except: d["analysis"] = {}
        
        # reconstruct meta for API compatibility
        d["meta"] = {
            "marketplace": d["marketplace"],
            "url": d["url"],
            "thumbnail": d["thumbnail"],
            "price": d["price"],
            "buying_intent": d["buying_intent"],
            "why_trending": d["cluster_why"] or d.get("analysis", {}).get("why")
        }
        d["signals"] = {
            "intent_confidence": d["intent_confidence"],
            "market_validation": d["market_validation"],
            "diversity": d["signal_diversity"]
        }
        results.append(d)
        
    return results

def get_db_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM opportunities")
    stats["total_opportunities"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    stats["total_products"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(score) FROM opportunities WHERE created_at = (SELECT MAX(created_at) FROM opportunities)")
    avg = cursor.fetchone()[0]
    stats["avg_score"] = round(avg, 1) if avg else 0
    
    cursor.execute("SELECT MAX(score) FROM opportunities WHERE created_at = (SELECT MAX(created_at) FROM opportunities)")
    top = cursor.fetchone()[0]
    stats["top_score"] = round(top, 1) if top else 0

    conn.close()
    return stats

# --- USER MANAGEMENT (Phase 2: SaaS Core) ---

def create_user(email: str, password: str, name: str = "", role: str = "free") -> Optional[int]:
    """Create a new user account."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return None  # User already exists
    
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, role, credits)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
        """, (email, password_hash, name, role, 10 if role == "free" else 100))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return user_id
    except Exception as e:
        print(f"[error] Failed to create user: {e}")
        conn.close()
        return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch user by email."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Fetch user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def verify_password(user: Dict, password: str) -> bool:
    """Verify user password."""
    return check_password_hash(user["password_hash"], password)

def save_opportunity_for_user(user_id: int, opportunity_id: int, project_id: Optional[int] = None, notes: str = "") -> int:
    """Save an opportunity to user's favorites."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO saved_opportunities (user_id, opportunity_id, project_id, notes)
        VALUES (?, ?, ?, ?)
        RETURNING id
    """, (user_id, opportunity_id, project_id, notes))
    
    saved_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return saved_id

def get_user_saved_opportunities(user_id: int) -> List[Dict]:
    """Get all saved opportunities for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, o.keyword, o.score, o.marketplace, o.url
        FROM saved_opportunities s
        JOIN opportunities o ON s.opportunity_id = o.id
        WHERE s.user_id = ?
        ORDER BY s.saved_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_project(user_id: int, name: str, description: str = "") -> int:
    """Create a new project for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_projects (user_id, name, description)
        VALUES (?, ?, ?)
        RETURNING id
    """, (user_id, name, description))
    
    project_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return project_id

def get_user_projects(user_id: int) -> List[Dict]:
    """Get all projects for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM user_projects WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
