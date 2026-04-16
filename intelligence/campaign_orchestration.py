#!/usr/bin/env python3
"""
INNOVATION 4: Multi-Stakeholder Campaign Orchestration
Orchestrates outreach sequences across 5-7 decision makers with optimal timing and messaging.
Builds consensus by intelligently sequencing contacts to create momentum without mail bombing.

Key Insight: Most B2B deals fail because sales contact the wrong person at the wrong time
with the wrong message. This innovation orchestrates across ALL stakeholders with:
1. Optimal timing (respect inbox fatigue, build momentum)
2. Strategic sequencing (executives first, then skeptics, then users)
3. Role-specific messaging (use Innovation 3 playbooks)
4. Mail bombing prevention (max 2 emails/week per person)
5. Bottleneck awareness (don't send technical content to CFO)
"""

from datetime import datetime, timedelta
from database import get_db
from enum import Enum

class ContactPriority(Enum):
    ECONOMIC_BUYER = 1      # CFO, VP Finance - controls budget
    EXECUTIVE_SPONSOR = 2   # CEO, VP Operations - strategic fit
    TECHNICAL_GATEKEEPER = 3  # CTO, VP Engineering - has veto
    USER = 4                # VP Product, Ops team - will use daily
    INFLUENCER = 5          # Anyone else who can sway opinion
    BLOCKER = 6            # Known skeptics - save for last if needed

# ============================================================================
# SECTION 1: Campaign Strategy
# ============================================================================

def get_contact_sequence_strategy(buyer_roles: list) -> dict:
    """
    Determine optimal contact sequence based on buyer committee roles.
    
    Strategy:
    1. ECONOMIC_BUYER (CFO) - contacts first (controls budget)
    2. EXECUTIVE_SPONSOR (CEO/COO) - contacts second (strategic alignment)
    3. TECHNICAL_GATEKEEPER (CTO) - contacts third (needs tech details)
    4. USERS (multiple) - contacts fourth (build momentum)
    5. BLOCKERS - contacts last if needed (overcome objections)
    """
    
    sequence = []
    roles_by_priority = {}
    
    for role_info in buyer_roles:
        role = role_info.get("role")
        buyer_id = role_info.get("buyer_id")
        sentiment = role_info.get("sentiment")
        is_blocker = role_info.get("is_blocker", False)
        
        # Determine priority
        if is_blocker:
            priority = ContactPriority.BLOCKER.value
        elif role in ["CFO", "VP_FINANCE"]:
            priority = ContactPriority.ECONOMIC_BUYER.value
        elif role in ["CEO", "VP_OPERATIONS"]:
            priority = ContactPriority.EXECUTIVE_SPONSOR.value
        elif role in ["CTO", "VP_PRODUCT"]:
            priority = ContactPriority.TECHNICAL_GATEKEEPER.value
        elif role in ["VP_SALES", "SUCCESS_MANAGER"]:
            priority = ContactPriority.USER.value
        else:
            priority = ContactPriority.INFLUENCER.value
        
        # Skip already engaged/blocked
        if sentiment == "EAGER":
            priority = 0  # Contact immediately
        elif sentiment == "BLOCKED":
            priority = 99  # Contact last (if at all)
        
        if priority not in roles_by_priority:
            roles_by_priority[priority] = []
        
        roles_by_priority[priority].append({
            "buyer_id": buyer_id,
            "role": role,
            "sentiment": sentiment,
            "is_blocker": is_blocker,
            "priority": priority
        })
    
    # Build sequence from highest to lowest priority
    for priority in sorted(roles_by_priority.keys()):
        sequence.extend(roles_by_priority[priority])
    
    return {
        "sequence": sequence,
        "total_contacts": len(sequence),
        "strategy": "Economic buyer → Sponsors → Technical → Users → Blockers"
    }

# ============================================================================
# SECTION 2: Campaign Timing Optimization
# ============================================================================

def calculate_optimal_contact_timing(sequence_length: int, start_date: datetime = None) -> list:
    """
    Calculate optimal timing for campaign contacts.
    
    Strategy:
    - Space contacts 2-3 days apart (respect inbox fatigue)
    - Never send >2 emails/week to same person
    - Stagger across week (Mon-Thu better than Fri)
    - Build momentum (each success enables next contact)
    
    Returns: List of (contact_index, target_date, day_of_week)
    """
    
    if start_date is None:
        start_date = datetime.utcnow()
    
    # Skip weekends
    if start_date.weekday() == 5:  # Saturday
        start_date += timedelta(days=2)
    elif start_date.weekday() == 6:  # Sunday
        start_date += timedelta(days=1)
    
    timing_schedule = []
    current_date = start_date
    
    for i in range(sequence_length):
        # Skip weekends
        while current_date.weekday() in [5, 6]:
            current_date += timedelta(days=1)
        
        # Prefer Mon-Thu (9 AM)
        timing_schedule.append({
            "sequence_index": i,
            "contact_date": current_date,
            "day_of_week": current_date.strftime("%A"),
            "timing": "09:00 AM",
            "days_from_start": (current_date - start_date).days
        })
        
        # Space contacts 2-3 days apart, vary slightly for randomness
        days_to_add = [2, 2, 3, 2, 3][i % 5]  # Rotate between 2-3 days
        current_date += timedelta(days=days_to_add)
    
    return timing_schedule

# ============================================================================
# SECTION 3: Campaign Creation
# ============================================================================

def create_activation_campaign(
    partner_id: int,
    prospect_id: int,
    campaign_name: str = None,
    target_completion_days: int = 30
) -> dict:
    """
    Create a multi-stakeholder activation campaign.
    
    Flow:
    1. Get buyer committee for prospect
    2. Determine contact sequence
    3. Calculate optimal timing
    4. Create campaign record
    5. Create individual sends
    """
    
    from intelligence.buyer_committee import get_buyer_committee
    from intelligence.playbooks import get_playbook_for_role
    
    # Get buyer committee
    committee = get_buyer_committee(prospect_id=prospect_id)
    
    # Handle error case
    if isinstance(committee, dict) and "error" in committee:
        return {"error": f"No buyer committee found for prospect {prospect_id}"}
    
    # Committee should be a list at this point
    if not isinstance(committee, list):
        committee = [committee] if committee else []
    
    if len(committee) == 0:
        return {"error": f"No buyer committee members found for prospect {prospect_id}"}
    
    # Flatten to list of role info
    buyer_roles = [
        {
            "buyer_id": member.get("id"),
            "role": member.get("role"),
            "sentiment": member.get("sentiment", "NEUTRAL"),
            "is_blocker": member.get("is_blocker", False),
            "name": member.get("name")
        }
        for member in committee
    ]
    
    # Get contact sequence
    sequence_info = get_contact_sequence_strategy(buyer_roles)
    sequence = sequence_info["sequence"]
    
    # Calculate timing
    timing = calculate_optimal_contact_timing(len(sequence))
    
    # Create campaign record
    campaign_name = campaign_name or f"Activation Campaign - {datetime.utcnow().strftime('%Y-%m-%d')}"
    
    with get_db() as conn:
        result = conn.execute("""
            INSERT INTO activation_campaigns
            (partner_id, prospect_id, campaign_name, status, total_contacts, 
             target_completion_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            partner_id,
            prospect_id,
            campaign_name,
            "PENDING",
            len(sequence),
            (datetime.utcnow() + timedelta(days=target_completion_days)).isoformat()
        ))
        conn.commit()
        campaign_id = result.lastrowid
    
    # Create individual sends
    sends = []
    for seq_index, buyer_info in enumerate(sequence):
        timing_info = timing[seq_index]
        
        # Get playbook for this role
        playbook = get_playbook_for_role(buyer_info["role"])
        
        send = create_campaign_send(
            campaign_id=campaign_id,
            buyer_id=buyer_info["buyer_id"],
            contact_sequence=seq_index + 1,
            role=buyer_info["role"],
            scheduled_date=timing_info["contact_date"],
            playbook_template=playbook.get("name") if "error" not in playbook else None
        )
        sends.append(send)
    
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "partner_id": partner_id,
        "prospect_id": prospect_id,
        "status": "PENDING",
        "total_contacts": len(sequence),
        "sequence_info": sequence_info,
        "timing_schedule": timing,
        "sends_created": len(sends),
        "sends": sends
    }

# ============================================================================
# SECTION 4: Campaign Sends
# ============================================================================

def create_campaign_send(
    campaign_id: int,
    buyer_id: int,
    contact_sequence: int,
    role: str,
    scheduled_date: datetime,
    playbook_template: str = None
) -> dict:
    """Create individual send record for campaign."""
    
    with get_db() as conn:
        result = conn.execute("""
            INSERT INTO activation_campaign_sends
            (campaign_id, buyer_id, contact_sequence, role, scheduled_date, 
             playbook_template, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            campaign_id,
            buyer_id,
            contact_sequence,
            role,
            scheduled_date.isoformat() if isinstance(scheduled_date, datetime) else scheduled_date,
            playbook_template,
            "SCHEDULED"
        ))
        conn.commit()
        send_id = result.lastrowid
    
    return {
        "send_id": send_id,
        "campaign_id": campaign_id,
        "buyer_id": buyer_id,
        "contact_sequence": contact_sequence,
        "role": role,
        "scheduled_date": scheduled_date.isoformat() if isinstance(scheduled_date, datetime) else scheduled_date,
        "status": "SCHEDULED"
    }

def get_campaign_timeline(campaign_id: int) -> dict:
    """Get full campaign timeline with all sends."""
    
    with get_db() as conn:
        campaign = conn.execute("""
            SELECT * FROM activation_campaigns WHERE id = ?
        """, (campaign_id,)).fetchone()
        
        if not campaign:
            return {"error": f"Campaign {campaign_id} not found"}
        
        sends = conn.execute("""
            SELECT * FROM activation_campaign_sends 
            WHERE campaign_id = ? 
            ORDER BY contact_sequence ASC
        """, (campaign_id,)).fetchall()
    
    return {
        "campaign": dict(campaign),
        "sends": [dict(s) for s in sends],
        "total_scheduled": len(sends),
        "status_summary": get_campaign_status_summary(campaign_id)
    }

# ============================================================================
# SECTION 5: Campaign Analytics
# ============================================================================

def get_campaign_status_summary(campaign_id: int) -> dict:
    """Get campaign status: pending, sent, opened, clicked, responses."""
    
    with get_db() as conn:
        stats = conn.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM activation_campaign_sends
            WHERE campaign_id = ?
            GROUP BY status
        """, (campaign_id,)).fetchall()
    
    summary = {str(status): count for status, count in stats}
    
    return {
        "scheduled": summary.get("SCHEDULED", 0),
        "sent": summary.get("SENT", 0),
        "opened": summary.get("OPENED", 0),
        "clicked": summary.get("CLICKED", 0),
        "responded": summary.get("RESPONDED", 0),
        "total": sum(summary.values())
    }

def get_campaign_effectiveness(campaign_id: int) -> dict:
    """
    Calculate campaign effectiveness metrics.
    
    Metrics:
    - Send rate (% sent vs scheduled)
    - Open rate (% opened vs sent)
    - Click rate (% clicked vs opened)
    - Response rate (% responded vs sent)
    - Days to first response
    """
    
    with get_db() as conn:
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status IN ('SENT', 'OPENED', 'CLICKED', 'RESPONDED') THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status IN ('OPENED', 'CLICKED', 'RESPONDED') THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN status IN ('CLICKED', 'RESPONDED') THEN 1 ELSE 0 END) as clicked,
                SUM(CASE WHEN status = 'RESPONDED' THEN 1 ELSE 0 END) as responded
            FROM activation_campaign_sends
            WHERE campaign_id = ?
        """, (campaign_id,)).fetchone()
    
    if not stats:
        return {"error": f"Campaign {campaign_id} not found"}
    
    total = stats[0] or 1
    sent = stats[1] or 0
    opened = stats[2] or 0
    clicked = stats[3] or 0
    responded = stats[4] or 0
    
    return {
        "campaign_id": campaign_id,
        "total_contacts": total,
        "send_rate": round((sent / total * 100) if total else 0, 1),
        "open_rate": round((opened / sent * 100) if sent else 0, 1),
        "click_rate": round((clicked / opened * 100) if opened else 0, 1),
        "response_rate": round((responded / sent * 100) if sent else 0, 1),
        "contacts_sent": sent,
        "contacts_opened": opened,
        "contacts_clicked": clicked,
        "contacts_responded": responded
    }

# ============================================================================
# SECTION 6: Campaign Execution
# ============================================================================

def get_next_campaign_sends(limit: int = 10) -> list:
    """Get next sends ready for execution (scheduled for today or earlier)."""
    
    with get_db() as conn:
        sends = conn.execute("""
            SELECT 
                acs.*,
                bcm.email as buyer_email,
                bcm.name as buyer_name,
                bcm.role,
                ac.campaign_name
            FROM activation_campaign_sends acs
            JOIN activation_campaigns ac ON acs.campaign_id = ac.id
            JOIN buyer_committee_members bcm ON acs.buyer_id = bcm.id
            WHERE acs.status = 'SCHEDULED'
            AND acs.scheduled_date <= CURRENT_TIMESTAMP
            ORDER BY acs.scheduled_date ASC
            LIMIT ?
        """, (limit,)).fetchall()
    
    return [dict(s) for s in sends]

def mark_send_as_sent(send_id: int, email_subject: str = None, email_body: str = None) -> dict:
    """Mark a send as sent."""
    
    with get_db() as conn:
        conn.execute("""
            UPDATE activation_campaign_sends
            SET status = 'SENT', sent_at = CURRENT_TIMESTAMP,
                email_subject = ?, email_body = ?
            WHERE id = ?
        """, (email_subject, email_body, send_id))
        conn.commit()
    
    return {"send_id": send_id, "status": "SENT"}

def mark_send_as_opened(send_id: int) -> dict:
    """Mark a send as opened (from email tracking)."""
    
    with get_db() as conn:
        conn.execute("""
            UPDATE activation_campaign_sends
            SET status = 'OPENED', opened_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (send_id,))
        conn.commit()
    
    return {"send_id": send_id, "status": "OPENED"}

def mark_send_as_clicked(send_id: int) -> dict:
    """Mark a send as clicked (from link tracking)."""
    
    with get_db() as conn:
        conn.execute("""
            UPDATE activation_campaign_sends
            SET status = 'CLICKED', clicked_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (send_id,))
        conn.commit()
    
    return {"send_id": send_id, "status": "CLICKED"}

def mark_send_as_responded(send_id: int, response_notes: str = None) -> dict:
    """Mark a send as responded (manual or automatic)."""
    
    with get_db() as conn:
        conn.execute("""
            UPDATE activation_campaign_sends
            SET status = 'RESPONDED', responded_at = CURRENT_TIMESTAMP, 
                response_notes = ?
            WHERE id = ?
        """, (response_notes, send_id))
        conn.commit()
    
    return {"send_id": send_id, "status": "RESPONDED"}

# ============================================================================
# SECTION 7: Mail Bombing Prevention
# ============================================================================

def get_buyer_email_volume(buyer_id: int, days: int = 7) -> dict:
    """Get email volume for a buyer in last N days."""
    
    with get_db() as conn:
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total_emails,
                SUM(CASE WHEN status != 'SCHEDULED' THEN 1 ELSE 0 END) as sent_emails,
                MAX(sent_at) as last_email_date
            FROM activation_campaign_sends
            WHERE buyer_id = ?
            AND sent_at > datetime('now', '-' || ? || ' days')
        """, (buyer_id, days)).fetchone()
    
    return {
        "buyer_id": buyer_id,
        "period_days": days,
        "total_emails": stats[0] or 0,
        "sent_emails": stats[1] or 0,
        "last_email_date": stats[2],
        "exceeds_limit": (stats[1] or 0) > 2  # Max 2 sent per week
    }

def is_safe_to_send(buyer_id: int) -> dict:
    """Check if safe to send email to buyer (mail bombing prevention)."""
    
    volume = get_buyer_email_volume(buyer_id, days=7)
    
    is_safe = volume["sent_emails"] <= 2
    
    return {
        "buyer_id": buyer_id,
        "is_safe": is_safe,
        "volume_this_week": volume["sent_emails"],
        "max_allowed": 2,
        "reason": "OK to send" if is_safe else "Exceeded email limit this week"
    }
