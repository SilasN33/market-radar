import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash

# IMPORTANT: Auto-apply patches (Postgres for production)
try:
    from . import patch
except ImportError:
    pass

# Path adjustment: src/database/database.py -> parents[2] is root
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "market_radar.db"

def get_connection():
    """Get a connection to the SQLite database."""
    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    from datetime import timezone
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marketplace TEXT NOT NULL,
        external_id TEXT, 
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        thumbnail TEXT,
        current_price REAL,
        currency TEXT DEFAULT 'BRL',
        last_updated DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(marketplace, url)
    )
    """)
    
    # 2. Price History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        price REAL NOT NULL,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        search_keyword TEXT,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    
    # 3. Scan Logs
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

    # 4. Intent Clusters
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intent_clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        confidence_score INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(cluster_name, created_at)
    )
    """)

    # 5. Opportunities (V2: Added scoring_breakdown)
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
        analysis TEXT, 
        scoring_breakdown TEXT, -- JSON V2 Breakdown
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(cluster_id) REFERENCES intent_clusters(id)
    )
    """)
    
    # REQUIRED for ON CONFLICT(keyword) to work in Postgres
    try:
        # 1. Clean duplicates first (keep latest)
        cursor.execute("""
            DELETE FROM opportunities 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM opportunities 
                GROUP BY keyword
            )
        """)
        conn.commit()
        
        # 2. Create Unique Index
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_opportunities_keyword ON opportunities(keyword)")
        conn.commit()
    except Exception as e:
        print(f"[db_warn] Index migration failed: {e}")
        conn.rollback()
    
    # Add column if not exists (migration)
    try:
        cursor.execute("ALTER TABLE opportunities ADD COLUMN scoring_breakdown TEXT")
        conn.commit()
    except: 
        conn.rollback()
        
    try:
        cursor.execute("ALTER TABLE opportunities ADD COLUMN last_updated DATETIME")
        conn.commit()
    except: 
        conn.rollback()

    # 6. Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'free',
        credits INTEGER DEFAULT 10,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Projects
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
        opportunity_id INTEGER,
        notes TEXT,
        saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
    )
    """)
    
    # 8. Search Term History (V2)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_term_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term TEXT NOT NULL,
        source TEXT,
        metric_value REAL,
        metric_type TEXT DEFAULT 'occurrence_rank',
        captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_term_time ON search_term_history(term, captured_at)")
    
    conn.commit()
    conn.close()
    print(f"[database] ✅ Banco de dados inicializado em: {DB_PATH}")

def upsert_product(product_data: Dict[str, Any], keyword: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    marketplace = product_data.get("marketplace", "Unknown")
    url = product_data.get("permalink") or product_data.get("url")
    title = product_data.get("title")
    price = product_data.get("price")
    thumbnail = product_data.get("thumbnail")
    
    if not url or not title:
        conn.close()
        return 0
        
    try:
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
        
        if price is not None:
            cursor.execute("""
                INSERT INTO price_history (product_id, price, search_keyword, recorded_at)
                VALUES (?, ?, ?, ?)
            """, (product_id, price, keyword, datetime.now()))
        
        cursor.execute("""
            INSERT INTO scan_logs (product_id, search_keyword, scanned_at)
            VALUES (?, ?, ?)
        """, (product_id, keyword, datetime.now()))
        conn.commit()
        return product_id
    except Exception as e:
        print(f"[db_error] Upsert product failed: {e}")
        return 0
    finally:
        conn.close()

def save_cluster(cluster_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    validated = json.dumps(cluster_data.get("validated_products", []))
    negatives = json.dumps(cluster_data.get("negative_keywords", []))
    sources = json.dumps(cluster_data.get("source_signals_used", []))
    price_range = cluster_data.get("price_range_brl", {})

    try:
        cursor.execute("""
            INSERT INTO intent_clusters (
                cluster_name, buying_intent, validated_products, 
                price_range_min, price_range_max, negative_keywords,
                why_trending, source_signals, competition_level,
                risk_factors, confidence_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """, (
            cluster_data.get("cluster_name"), cluster_data.get("buying_intent"), validated,
            price_range.get("min", 0), price_range.get("max", 0), negatives,
            cluster_data.get("why_trending"), sources, cluster_data.get("competition_level"),
            cluster_data.get("risk_factors"), cluster_data.get("confidence_score"), datetime.now()
        ))
        cluster_id = cursor.fetchone()[0]
        conn.commit()
        return cluster_id
    except Exception:
        return 0 # Duplicate probably
    finally:
        conn.close()

def save_opportunity(opp_data: Dict[str, Any], cluster_id: Optional[int] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    signals = opp_data.get("signals", {})
    meta = opp_data.get("meta", {})
    analysis = opp_data.get("analysis", {})
    scoring_breakdown = opp_data.get("scoring_breakdown", {})
    
    # If signals is just metrics, use directly
    conf = signals.get("intent_confidence", signals.get("v2_score", 0))

    try:
        cursor.execute("""
            INSERT INTO opportunities (
                keyword, cluster_id, score, 
                intent_confidence, market_validation, signal_diversity, 
                marketplace, url, thumbnail, price, analysis, scoring_breakdown,
                created_at, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(keyword) DO UPDATE SET
                cluster_id=excluded.cluster_id,
                score=excluded.score,
                intent_confidence=excluded.intent_confidence,
                marketplace=excluded.marketplace,
                url=excluded.url,
                thumbnail=excluded.thumbnail,
                price=excluded.price,
                scoring_breakdown=excluded.scoring_breakdown,
                last_updated=excluded.last_updated
            RETURNING id
        """, (
            opp_data.get("keyword"),
            cluster_id,
            opp_data.get("score"),
            conf,
            signals.get("market_validation", 0),
            signals.get("signal_diversity", 0),
            meta.get("marketplace"),
            meta.get("url"),
            meta.get("thumbnail"),
            meta.get("price"),
            json.dumps(analysis),
            json.dumps(scoring_breakdown),
            datetime.now(),
            datetime.now()
        ))
        row = cursor.fetchone()
        if row:
            opp_id = row[0] if isinstance(row, tuple) else row['id']
        else:
            # Fallback: INSERT failed to return, try SELECT
            cursor.execute("SELECT id FROM opportunities WHERE keyword = ?", (opp_data.get("keyword"),))
            select_row = cursor.fetchone()
            if select_row:
                 opp_id = select_row[0] if isinstance(select_row, tuple) else select_row['id']
            else:
                 # Should not happen after insert
                 print(f"[db_error] Could not retrieve ID for {opp_data.get('keyword')}")
                 return 0
        conn.commit()
        return opp_id
    except Exception as e:
        import traceback
        print(f"[db_error] Save opportunity failed: {e}")
        traceback.print_exc() # Uncomment for deep debug
        return 0
    finally:
        conn.close()

def get_cluster_id_by_name(cluster_name: str) -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM intent_clusters WHERE cluster_name = ? ORDER BY created_at DESC LIMIT 1", (cluster_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_latest_ranking(limit: int = 50) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    # Find latest ranked items (by score desc)
    cursor.execute("""
        SELECT o.*, c.cluster_name
        FROM opportunities o
        LEFT JOIN intent_clusters c ON o.cluster_id = c.id
        ORDER BY o.score DESC, o.last_updated DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        d = dict(r)
        try: d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else {}
        except: d["analysis"] = {}
        try: d["breakdown"] = json.loads(d["scoring_breakdown"]) if d.get("scoring_breakdown") else {}
        except: d["breakdown"] = {}
        
        d["meta"] = {
            "marketplace": d["marketplace"],
            "url": d["url"],
            "thumbnail": d["thumbnail"],
            "price": d["price"],
            "cluster": d.get("cluster_name")
        }
        results.append(d)
    return results

def get_db_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    try:
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        stats["total_opportunities"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        stats["total_products"] = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(score) FROM opportunities")
        avg = cursor.fetchone()[0]
        stats["avg_score"] = round(avg, 1) if avg else 0
        cursor.execute("SELECT MAX(score) FROM opportunities")
        top = cursor.fetchone()[0]
        stats["top_score"] = round(top, 1) if top else 0
    except: pass
    conn.close()
    return stats


# --- USER MANAGEMENT ---

def create_user(email: str, password: str, name: str = "", role: str = "free") -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return None
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (email, password_hash, name, role, credits) VALUES (?, ?, ?, ?, ?) RETURNING id",
                      (email, password_hash, name, role, 10))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except: return None
    finally: conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_password(user: Dict, password: str) -> bool:
    return check_password_hash(user["password_hash"], password)

def save_opportunity_for_user(user_id: int, opportunity_id: int, project_id: Optional[int] = None, notes: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO saved_opportunities (user_id, opportunity_id, project_id, notes) VALUES (?, ?, ?, ?) RETURNING id",
                  (user_id, opportunity_id, project_id, notes))
    saved_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return saved_id

def get_user_saved_opportunities(user_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, o.keyword, o.score, o.marketplace, o.url
        FROM saved_opportunities s JOIN opportunities o ON s.opportunity_id = o.id
        WHERE s.user_id = ? ORDER BY s.saved_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_project(user_id: int, name: str, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_projects (user_id, name, description) VALUES (?, ?, ?) RETURNING id", (user_id, name, description))
    pid = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return pid

def get_user_projects(user_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- SEARCH HISTORY V2 ---

def add_term_history_snapshot(term: str, metric_value: float, source: str = "pipeline", metric_type: str = "occurrence_rank"):
    conn = get_connection()
    try:
        from datetime import timezone
        cursor = conn.cursor()
        # Lazy init table
        cursor.execute('''CREATE TABLE IF NOT EXISTS search_term_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term TEXT NOT NULL, source TEXT,
            metric_value REAL, metric_type TEXT DEFAULT 'occurrence_rank', captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute("INSERT INTO search_term_history (term, source, metric_value, metric_type, captured_at) VALUES (?, ?, ?, ?, ?)",
                      (term, source, metric_value, metric_type, datetime.now(timezone.utc)))
        conn.commit()
    except Exception as e: print(f"[db_error] History snapshot failed: {e}")
    finally: conn.close()

def get_term_history(term: str, metric_type: str = "occurrence_rank", limit: int = 14) -> List[Dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT metric_value, captured_at FROM search_term_history WHERE term = ? AND metric_type = ? ORDER BY captured_at DESC LIMIT ?", 
                      (term, metric_type, limit))
        return [dict(row) for row in cursor.fetchall()]
    except: return []
    finally: conn.close()

if __name__ == "__main__":
    init_db()
