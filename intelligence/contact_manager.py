#!/usr/bin/env python3
"""
Contact Manager
Tracks known contacts for partners by persona.
Integrates with activation interventions.
"""

from datetime import datetime
from database import get_db


def add_partner_contact(partner_id: int, name: str, email: str, persona: str, added_by: str = "system") -> dict:
    """
    Add a known contact for a partner.
    
    Personas: "CTO", "Business Contact", "CFO", "CPO", "CEO"
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_contacts (partner_id, name, email, persona, added_by, verified)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (partner_id, name, email, persona, added_by))
        conn.commit()
    
    return {
        "status": "contact_added",
        "partner_id": partner_id,
        "email": email,
        "persona": persona
    }


def get_contacts_for_partner(partner_id: int) -> dict:
    """
    Get all known contacts for a partner, grouped by persona.
    
    Returns: {
        "CTO": {"name": "...", "email": "...", "verified": True},
        "Business Contact": null,
        ...
    }
    """
    with get_db() as conn:
        contacts = conn.execute("""
            SELECT persona, name, email, verified, added_at
            FROM partner_contacts
            WHERE partner_id = ?
            ORDER BY added_at DESC
        """, (partner_id,)).fetchall()
    
    result = {
        "CTO": None,
        "Business Contact": None,
        "CFO": None,
        "CPO": None,
        "CEO": None
    }
    
    # Group by persona (take most recent for each)
    seen_personas = set()
    for contact in contacts:
        persona = contact['persona']
        if persona not in seen_personas:
            result[persona] = {
                "name": contact['name'],
                "email": contact['email'],
                "verified": bool(contact['verified']),
                "added_at": contact['added_at']
            }
            seen_personas.add(persona)
    
    return result


def check_contact_available(partner_id: int, persona: str) -> dict:
    """
    Check if we have contact info for a specific persona at a partner.
    
    Returns:
    {
        "has_contact": True/False,
        "email": "..." if available,
        "name": "..." if available,
        "verified": True/False,
        "recommendation": "Send to this email" or "No contact available"
    }
    """
    with get_db() as conn:
        contact = conn.execute("""
            SELECT name, email, verified
            FROM partner_contacts
            WHERE partner_id = ? AND persona = ?
            ORDER BY added_at DESC LIMIT 1
        """, (partner_id, persona)).fetchone()
    
    if not contact:
        return {
            "has_contact": False,
            "email": None,
            "name": None,
            "verified": False,
            "recommendation": f"No {persona} contact available. Check CSM or manual research needed."
        }
    
    return {
        "has_contact": True,
        "email": contact['email'],
        "name": contact['name'],
        "verified": bool(contact['verified']),
        "recommendation": f"Send to {contact['email']}" if contact['verified'] else f"Try {contact['email']} (unverified)"
    }


def record_intervention_outcome(partner_id: int, stall_pattern: str, outcome: str, notes: str = "", sent_to: str = "") -> dict:
    """
    Record the outcome of an intervention.
    
    Outcomes: "responded", "resolved", "no_response", "bounced", "sent"
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO intervention_outcomes 
            (partner_id, stall_pattern, outcome, outcome_recorded_at, notes, intervention_sent_to_email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (partner_id, stall_pattern, outcome, datetime.now().isoformat(), notes, sent_to))
        conn.commit()
    
    return {
        "status": "outcome_recorded",
        "partner_id": partner_id,
        "stall_pattern": stall_pattern,
        "outcome": outcome,
        "recorded_at": datetime.now().isoformat()
    }


def get_intervention_metrics() -> dict:
    """
    Get success metrics for interventions.
    
    Returns statistics on intervention outcomes by pattern.
    """
    with get_db() as conn:
        # Count by pattern and outcome
        stats = conn.execute("""
            SELECT 
                stall_pattern,
                outcome,
                COUNT(*) as count
            FROM intervention_outcomes
            WHERE outcome_recorded_at > datetime('now', '-90 days')
            GROUP BY stall_pattern, outcome
        """).fetchall()
    
    result = {}
    for row in stats:
        pattern = row['stall_pattern']
        if pattern not in result:
            result[pattern] = {
                "total": 0,
                "responded": 0,
                "resolved": 0,
                "no_response": 0,
                "bounced": 0,
                "sent": 0
            }
        
        outcome = row['outcome']
        count = row['count']
        result[pattern]["total"] += count
        if outcome in result[pattern]:
            result[pattern][outcome] = count
    
    # Calculate rates
    for pattern in result:
        total = result[pattern]["total"]
        if total > 0:
            result[pattern]["response_rate"] = round(100 * (result[pattern]["responded"] + result[pattern]["resolved"]) / total, 1)
            result[pattern]["resolution_rate"] = round(100 * result[pattern]["resolved"] / total, 1)
    
    return result
