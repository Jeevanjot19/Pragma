from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, remove_non_prospects
from discovery.news_monitor import run_news_monitor
from discovery.play_store import discover_from_play_store
from signals.scorer import recalculate_all_scores
from database import get_db

app = FastAPI(title="Pragma — Blostem GTM Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    print("Pragma is running.")

@app.get("/")
def root():
    return {"status": "Pragma WHO layer running"}

@app.post("/api/discover")
def trigger_discovery():
    news_result = run_news_monitor()
    remove_non_prospects()
    
    # Enrich known prospects with Play Store data
    from discovery.play_store import enrich_all_prospects
    enrich_all_prospects()
    
    recalculate_all_scores()
    return {"status": "complete", **news_result}

@app.get("/api/prospects")
def get_prospects(status: str = None, limit: int = 50):
    """Get all prospects, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                """SELECT p.*, 
                   COUNT(s.id) as signal_count
                   FROM prospects p
                   LEFT JOIN signals s ON s.prospect_id = p.id
                   WHERE p.status = ? AND p.is_existing_partner = 0
                   GROUP BY p.id
                   ORDER BY p.who_score DESC
                   LIMIT ?""",
                (status.upper(), limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT p.*,
                   COUNT(s.id) as signal_count
                   FROM prospects p
                   LEFT JOIN signals s ON s.prospect_id = p.id
                   WHERE p.is_existing_partner = 0
                   GROUP BY p.id
                   ORDER BY p.who_score DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
    
    return [dict(r) for r in rows]

@app.get("/api/prospects/{prospect_id}")
def get_prospect_detail(prospect_id: int):
    """Get full detail for one prospect including all signals."""
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        
        signals = conn.execute(
            """SELECT * FROM signals 
               WHERE prospect_id = ? 
               ORDER BY detected_at DESC""",
            (prospect_id,)
        ).fetchall()
    
    if not prospect:
        return {"error": "Not found"}
    
    return {
        "prospect": dict(prospect),
        "signals": [dict(s) for s in signals]
    }

@app.get("/api/stats")
def get_stats():
    """Dashboard stats for WHO layer."""
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE is_existing_partner = 0"
        ).fetchone()['c']
        
        hot = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE status = 'HOT'"
        ).fetchone()['c']
        
        warm = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE status = 'WARM'"
        ).fetchone()['c']
        
        displacement = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE using_competitor IS NOT NULL"
        ).fetchone()['c']
        
        by_product = conn.execute(
            """SELECT recommended_product, COUNT(*) as count 
               FROM prospects 
               WHERE is_existing_partner = 0
               GROUP BY recommended_product"""
        ).fetchall()
    
    return {
        "total_prospects": total,
        "hot": hot,
        "warm": warm,
        "displacement_targets": displacement,
        "by_recommended_product": [dict(r) for r in by_product]
    }

@app.post("/api/reset")
def reset_discovery():
    """Clear processed articles so next discovery run is fresh."""
    with get_db() as conn:
        conn.execute("DELETE FROM processed_articles")
        conn.commit()
    return {"status": "reset complete — next discover will reprocess all articles"}