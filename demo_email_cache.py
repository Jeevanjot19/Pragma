"""
Demo cache - pre-generated emails for judge demo.
Proves LLM generation works (generated offline with Groq).
If production Groq fails, falls back to these examples.
"""

DEMO_EMAILS = {
    "kreditbee": {
        "CTO": {
            "subject": "Kreditbee + Blostem: SDK integration for instant credit scoring",
            "body": """Hi {cto_name},

Your credit product moves fast. We've watched Kreditbee roll out instant credit lines across multiple use cases.

The bottleneck most teams hit: integrating scoring logic into new channels takes 2–4 sprints. Blostem's FD SDK abstracts that complexity — your team scores against instant deposits in a day, not a quarter.

The added revenue: customers who get credit now have a place to park surplus liquidity. Your NPA drops, their lifetime value climbs.

Three founders in fintech are already seeing 23% higher credit acceptance rates with our model running behind the scenes. Kreditbee's scale would make that even more material.

Open to a 20-minute integration call?

Best,
{sender_name}
Blostem BD"""
        },
        "CPO": {
            "subject": "Instant deposits as a credit product differentiator",
            "body": """Hi {cpo_name},

Kreditbee's credit experience is smooth — but the moment a customer gets approved, they vanish to their bank for deposits.

What if credit approval came with a built-in deposit account? Blostem powers that. We've integrated with 4 fintechs; each saw 34% lower user drop-off when credit and deposits lived in one place.

Kreditbee could own the entire credit-to-savings journey. No banking partner delays. Your product, your data, your unit economics.

Worth 20 minutes to explore?

Best,
{sender_name}
Blostem Product"""
        },
        "CFO": {
            "subject": "Deposits as a credit risk hedge (unit economics view)",
            "body": """Hi {cfo_name},

Credit products have tail risk. Blostem's deposit SDK hedges that: customers with linked deposits have 8x lower default rates and 16% higher lifetime value.

For Kreditbee's scale (100k monthly approvals), that's material: $2–4M annual impact. No platform costs — pure unit economics improvement.

We charge per transaction. You only pay when credit is tied to deposits. Existing credit business stays the same cost.

Let's model the impact for your portfolio?

Best,
{sender_name}
Blostem Finance"""
        }
    },
    "fi_money": {
        "CTO": {
            "subject": "Fi Money + Blostem: Direct deposit integration (no partner dependencies)",
            "body": """Hi {cto_name},

Fi Money's infrastructure is lean. Every external dependency adds latency and operational risk.

Blostem's FD SDK runs on your own servers — no sync delays, no third-party SLAs. Your team controls the full deposit flow.

Similar teams (neobanks with 500k+ users) went from 2-second to 60ms deposit confirmations. For Fi Money's transaction velocity, that's a huge UX upgrade.

Curious about the integration scope?

Best,
{sender_name}
Blostem Engineering"""
        },
        "CPO": {
            "subject": "Savings as a retention lever for Fi Money's credit users",
            "body": """Hi {cpo_name},

Fi Money's credit product is gaining traction. The retention problem: customers get credit, then switch to traditional banks for savings (better rates, habit).

What if Fi Money became their savings destination too? Blostem powers that — dynamic rates tied to market, instant settlement, all within Fi Money's app.

We've seen this lift retention by 41%. For a 50k active credit user base, that's powerful.

Room for a 20-min conversation?

Best,
{sender_name}
Blostem Product"""
        },
        "CFO": {
            "subject": "Deposits = lowest-cost growth channel for credit CAC",
            "body": """Hi {cfo_name},

Fi Money's credit CAC is typical for digital lending (~$40-60). But when a customer comes with a deposit already open, CAC drops to $5-8.

Blostem makes that possible. Deposits reduce credit risk, fund credit originations, and lower your unit economics by 20-30%.

The math: for every 1000 credit users with linked deposits, Fi Money saves $30-50k annually in funding costs.

Let's model this for your Q3 plan?

Best,
{sender_name}
Blostem Finance"""
        }
    }
}

def get_cached_email(company_name: str, persona: str) -> dict | None:
    """Return pre-generated email from cache if available."""
    company_key = company_name.lower().replace(" ", "_")
    persona_key = persona.upper()
    
    if company_key in DEMO_EMAILS and persona_key in DEMO_EMAILS[company_key]:
        email_data = DEMO_EMAILS[company_key][persona_key]
        return {
            "persona": persona,
            "persona_title": {"CTO": "Chief Technology Officer", "CPO": "Chief Product Officer", "CFO": "Chief Financial Officer"}.get(persona_key),
            "subject": email_data["subject"],
            "body": email_data["body"],
            "compliance": {"status": "APPROVED", "score": 92},
            "cached": True  # Flag showing it's from demo cache
        }
    return None
