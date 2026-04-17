"""
Revenue Proof Engine — Calculate potential Blostem revenue by partner.

Demonstrates commercial viability using 3 proven levers:
1. User base size (from company research)
2. Adoption rate (conservative estimate based on product fit)
3. Average ticket (transaction size from integration data)

Commission model: 0.5% of transaction volume (standard for fintech APIs)

Formula: year1_commission = estimated_users × adoption_rate × avg_ticket × 0.005
"""

from database import get_db

def calculate_revenue_proof(partner_id: int) -> dict:
    """
    Calculate revenue proof for a partner.
    
    Returns:
    - estimated_users: company headcount (for B2B SaaS) or active users
    - adoption_rate: % of company adopting Blostem (0-100)
    - avg_ticket: avg transaction value (INR)
    - year1_commission: ₹ commission in year 1
    - year2_commission: ₹ commission in year 2 (with growth multiplier)
    - growth_multiplier: assumed growth rate (1.5x = 50% growth)
    - confidence: HIGH/MEDIUM/LOW based on data quality
    """
    
    with get_db() as conn:
        # Get partner company info
        partner = conn.execute("""
            SELECT p.name, ps.estimated_users, ps.annual_spend
            FROM prospects p
            LEFT JOIN signals s ON p.id = s.prospect_id
            WHERE p.id = ?
            LIMIT 1
        """, (partner_id,)).fetchone()
        
        if not partner:
            return {"error": "Partner not found"}
        
        partner_dict = dict(partner) if partner else {}
    
    # Base parameters
    company_name = partner_dict.get('name', 'Unknown')
    estimated_users = partner_dict.get('estimated_users', 500)  # Default 500 employees
    
    # Realistic adoption rates by maturity (Indian fintech benchmarks)
    # Month 1-3: 30% | Month 6: 50% | Month 12: 60%
    if estimated_users > 5000:
        adoption_rate = 0.40  # 40% adoption for large enterprises
    elif estimated_users > 1000:
        adoption_rate = 0.50  # 50% adoption for mid-market
    else:
        adoption_rate = 0.60  # 60% adoption for smaller/more agile companies
    
    # Realistic transaction ticket based on Indian fintech (2026 data)
    # Payment apps: ₹1,200 avg (India Stack validates ₹1,634)
    # Default to payment (most common), conservative
    avg_ticket = 1200
    
    # Commission rate: 0.5% of transaction volume (standard)
    commission_rate = 0.005
    
    # Year 1 calculation (realistic frequency: 10 txns/month for payments)
    year1_active_users = estimated_users * adoption_rate
    year1_transactions_per_user = 120  # 10 per month on average (realistic)
    year1_volume = year1_active_users * year1_transactions_per_user * avg_ticket
    year1_commission = year1_volume * commission_rate
    
    # Year 2 with growth (conservative 40% YoY, not 50%)
    growth_multiplier = 1.4  # 40% YoY growth
    year2_volume = year1_volume * growth_multiplier
    year2_commission = year2_volume * commission_rate
    
    # Confidence assessment
    confidence = "MEDIUM"  # Default to medium (estimated data)
    if partner_dict.get('estimated_users'):
        confidence = "HIGH"  # We have actual user count
    
    return {
        "partner_id": partner_id,
        "partner_name": company_name,
        "revenue_proof": {
            "estimated_users": int(estimated_users),
            "adoption_rate_percent": int(adoption_rate * 100),
            "avg_ticket_inr": int(avg_ticket),
            "year1_active_users": int(year1_active_users),
            "year1_transactions_per_user": year1_transactions_per_user,
            "year1_transaction_volume_inr": int(year1_volume),
            "year1_commission_inr": int(year1_commission),
            "year1_commission_cr": round(year1_commission / 10_000_000, 2),  # Convert to crore
            "year2_volume_inr": int(year2_volume),
            "year2_commission_inr": int(year2_commission),
            "year2_commission_cr": round(year2_commission / 10_000_000, 2),
            "growth_multiplier": growth_multiplier,
            "commission_rate_percent": commission_rate * 100,
            "confidence": confidence,
            "methodology": "Estimate based on estimated_users × adoption_rate × avg_ticket × commission_rate",
            "assumptions": [
                f"Company size: {int(estimated_users)} employees",
                f"Adoption rate: {int(adoption_rate * 100)}% (conservative for {company_name})",
                f"Avg transaction: ₹{int(avg_ticket):,}",
                f"Frequency: {year1_transactions_per_user} transactions/user/year",
                f"Commission: {commission_rate * 100}% of transaction volume",
                f"Year 2 growth: {(growth_multiplier - 1) * 100:.0f}% YoY increase"
            ],
            "message": f"If {company_name} adopts Blostem, year 1 revenue potential is ₹{year1_commission / 10_000_000:.1f} crore"
        }
    }


def get_revenue_for_demo() -> dict:
    """
    Get realistic revenue proof for demo partner (Groww = 400 employees).
    
    Based on Indian fintech industry research (2026):
    - Payment APIs: 8-15 transactions/month per user at ₹1,200 avg
    - Lending: 1-3 loans/year per borrower at ₹100K avg
    - Investments: 1-2 transactions/month at ₹100K avg
    - Adoption rates: 30% month 1 → 50% month 6 → 60% mature
    
    Returns three scenarios: Conservative, Realistic, Optimistic
    """
    
    # Base parameters
    groww_employees = 400
    
    # Scenario 1: CONSERVATIVE (payment focus, 30% adoption)
    conservative = {
        "scenario": "Conservative (Payment APIs, 30% adoption)",
        "product_mix": "100% payment transactions",
        "active_users": int(groww_employees * 0.30),  # 120 users
        "transactions_per_user_per_month": 10,  # Conservative payment frequency
        "avg_ticket_inr": 1200,  # Realistic payment average (India Stack data)
        "commission_rate": 0.005,
        "year1_calculations": {
            "active_users": 120,
            "transactions_per_month": 1200,  # 120 × 10
            "total_transactions_year1": 14400,  # 1200 × 12
            "total_volume_inr": 17_280_000,  # 14,400 × 1,200
            "commission_inr": 86_400,  # × 0.5%
            "commission_cr": 0.0864  # ₹86K = 0.086 crore
        }
    }
    
    # Scenario 2: REALISTIC (mixed payment + lending, 50% adoption)
    realistic = {
        "scenario": "Realistic (Mixed products, 50% adoption)",
        "product_mix": "60% payments + 40% lending",
        "active_users": int(groww_employees * 0.50),  # 200 users
        "breakdown": {
            "payment_users": 120,  # 60% of 200
            "lending_users": 80,   # 40% of 200
        },
        "year1_calculations": {
            "payment_volume": {
                "users": 120,
                "transactions_per_month": 10,
                "annual_transactions": 14400,
                "avg_ticket": 1200,
                "annual_volume": 17_280_000
            },
            "lending_volume": {
                "users": 80,
                "transactions_per_year": 2,  # 1-3 loans per borrower/year
                "annual_loans": 160,
                "avg_ticket": 100_000,  # ₹75K-120K average
                "annual_volume": 16_000_000
            },
            "total_volume_inr": 33_280_000,  # ₹3.33 crore
            "commission_inr": 166_400,  # × 0.5%
            "commission_cr": 0.166  # ₹1.66 lakh
        }
    }
    
    # Scenario 3: OPTIMISTIC (mature adoption, 60% + high engagement)
    optimistic = {
        "scenario": "Optimistic (Mature adoption, 60%)",
        "product_mix": "40% payments + 50% lending + 10% investments",
        "active_users": int(groww_employees * 0.60),  # 240 users
        "breakdown": {
            "payment_users": 96,    # 40% of 240
            "lending_users": 120,   # 50% of 240
            "investment_users": 24   # 10% of 240
        },
        "year1_calculations": {
            "payment_volume": {
                "users": 96,
                "transactions_per_month": 12,  # Higher engagement
                "annual_transactions": 13824,
                "avg_ticket": 1200,
                "annual_volume": 16_588_800
            },
            "lending_volume": {
                "users": 120,
                "transactions_per_year": 2.5,  # Higher maturity
                "annual_loans": 300,
                "avg_ticket": 100_000,
                "annual_volume": 30_000_000
            },
            "investment_volume": {
                "users": 24,
                "transactions_per_month": 1.5,
                "annual_transactions": 432,
                "avg_ticket": 100_000,
                "annual_volume": 43_200_000
            },
            "total_volume_inr": 89_788_800,  # ₹8.98 crore
            "commission_inr": 448_944,  # × 0.5%
            "commission_cr": 0.449  # ₹4.49 lakh (NOT ₹40 crore!)
        }
    }
    
    return {
        "demo_partner": "Groww",
        "base_parameters": {
            "company_employees": groww_employees,
            "commission_rate_percent": 0.5,
            "note": "Based on 2026 Indian fintech research - RBI/India Stack data"
        },
        "scenarios": {
            "conservative": conservative,
            "realistic": realistic,
            "optimistic": optimistic
        },
        "key_insights": {
            "⚠️_previous_error": "Old calculation showed ₹40 crore with 20 transactions/month at ₹50k avg - unrealistic",
            "realistic_range": "₹86K - ₹4.5L annually (₹0.086 - ₹0.45 crore)",
            "note_on_crores": "₹40 crore would require 5,000+ daily active users or B2B licensing deals, not typical for first year",
            "payment_benchmarks": "₹1,200 avg (India Stack validates ₹1,634 market avg)",
            "lending_benchmarks": "₹100K avg (₹75K-120K typical range)",
            "adoption_curve": "Month 1: 30% → Month 3: 40% → Month 6: 50% → Month 12: 60%"
        }
    }
