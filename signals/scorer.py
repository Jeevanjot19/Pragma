from database import get_db
from config import SIGNAL_WEIGHTS, HOT_THRESHOLD, WARM_THRESHOLD

def calculate_who_score(prospect_id: int) -> tuple[int, str]:
    with get_db() as conn:
        signals = conn.execute(
            "SELECT signal_type, signal_strength FROM signals WHERE prospect_id = ?",
            (prospect_id,)
        ).fetchall()
        
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?",
            (prospect_id,)
        ).fetchone()
    
    if not prospect:
        return 0, 'WATCH'
    
    prospect = dict(prospect)
    score = 0
    signal_counts = {}
    
    # Count all signals, including duplicates, by type
    for signal in signals:
        signal_type = signal['signal_type']
        strength = signal['signal_strength']
        
        if signal_type not in signal_counts:
            signal_counts[signal_type] = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        signal_counts[signal_type][strength] += 1
    
    # Score signals — but PRODUCT_GAP has reduced weight
    # It's a prerequisite not a buying signal
    for signal_type, severities in signal_counts.items():
        if signal_type == 'PRODUCT_GAP':
            base = 15  # Reduced from 35
        else:
            base = SIGNAL_WEIGHTS.get(signal_type, 10)
        
        # First instance of signal
        if severities['HIGH'] > 0:
            score += int(base * 1.0)
        if severities['MEDIUM'] > 0:
            score += int(base * 0.6)
        if severities['LOW'] > 0:
            score += int(base * 0.3)
        
        # Additional signal instances show strength/depth
        additional = severities['HIGH'] + severities['MEDIUM'] + severities['LOW'] - 1
        if additional > 0:
            score += int((base * 0.5) * additional)
    
    # Scale bonus — larger companies are higher priority
    install_count = prospect.get('install_count', '')
    SCALE_BONUSES = {
        '100,000,000+': 30,
        '50,000,000+': 25,
        '10,000,000+': 20,
        '5,000,000+': 15,
        '1,000,000+': 10,
        '500,000+': 7,
        '100,000+': 4,
    }
    for threshold, bonus in SCALE_BONUSES.items():
        if install_count and threshold == install_count:
            score += bonus
            break
    
    # Convergence bonus — reward combining different signal types
    event_types = {'FUNDING_EXPANSION', 'DISPLACEMENT', 
                   'LEADERSHIP_HIRE', 'COMPETITOR_MOVE'}
    event_signal_count = len(set(signal_counts.keys()) & event_types)
    
    if event_signal_count >= 3:
        score += 20
    elif event_signal_count >= 2:
        score += 10
    elif event_signal_count == 1:
        score += 5
    
    # Displacement floor
    if prospect.get('using_competitor'):
        score = max(score, 40)
    
    score = min(score, 100)
    
    # Classify
    if score >= 65:
        status = 'HOT'
    elif score >= 35:
        status = 'WARM'
    else:
        status = 'WATCH'
    
    with get_db() as conn:
        conn.execute(
            "UPDATE prospects SET who_score = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (score, status, prospect_id)
        )
        conn.commit()
    
    return score, status


def recalculate_all_scores():
    """Recalculate WHO scores for all prospects."""
    with get_db() as conn:
        prospects = conn.execute("SELECT id, name FROM prospects").fetchall()
    
    for p in prospects:
        score, status = calculate_who_score(p['id'])
        print(f"  {p['name']}: {score} ({status})")