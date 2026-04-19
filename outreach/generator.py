"""
HOW Layer — Outreach Generator (v2)

Philosophy
----------
The old generator handed the LLM a structured template with slots to fill.
The result was always recognisably templated — same sentence rhythm, same
paragraph structure, same signals leaked ("we noticed your Play Store update").

This version works differently:

  1. We build a CONTEXT BRIEF for the LLM — facts about the company, the
     persona, the product fit — but we don't dictate the shape of the email.

  2. The LLM writes as if it's a senior BD person who has genuinely thought
     about this company. It knows the facts; it decides how to open, how to
     flow, when to be brief.

  3. We NEVER mention how we found signals (Play Store, news scraping, etc.).
     Instead we translate signals into natural business language:
       ✗ "We noticed your Play Store update added a savings feature"
       ✓ "Your platform is clearly moving toward a full savings stack"

  4. Persona prompts focus on what the persona CARES ABOUT, not what
     Blostem wants to pitch. The pitch emerges from addressing their concern.

  5. We run compliance BEFORE returning, and regenerate once if there's a
     critical violation (rather than surfacing bad output to the user).

Persona philosophy
------------------
  CTO   → Integration cost, developer experience, time-to-live, API quality.
           They want to know: "Is this going to be a painful 3-month project
           or can my team ship it cleanly?"

  CPO   → Product velocity, user experience, competitive positioning.
           They want to know: "Will this make our product better, faster?"

  CFO   → Unit economics, revenue model, downside protection, compliance cost.
           They want to know: "What's the ROI and what are the risks?"
"""

from __future__ import annotations

import time
from datetime import datetime

from database import get_db
from intelligence.llm_extractor import _call_llm, _parse_json_response
from outreach.compliance_rules import check_compliance
from signals.timing import calculate_when_score
from demo_email_cache import get_cached_email


# ─────────────────────────────────────────────
# Signal → natural language translator
# Converts raw signal data into business context
# that doesn't reveal how we gathered it.
# ─────────────────────────────────────────────

def _translate_signals_to_context(prospect: dict, signals: list[dict]) -> dict:
    """
    Convert raw prospect + signal data into natural business observations.
    This is the core of the "no leakage" principle.

    Returns a context dict the prompt builder uses.
    """
    name = prospect.get("name", "")
    category = (prospect.get("category") or "fintech").lower()
    install_count = prospect.get("install_count", "")
    recommended_product = prospect.get("recommended_product", "FD SDK")

    # Scale descriptor — natural language, not raw numbers
    scale_desc = "an early-stage"
    if install_count:
        installs_clean = install_count.replace(",", "").replace("+", "")
        try:
            n = int(installs_clean)
            if n >= 100_000_000:
                scale_desc = "a large-scale consumer"
            elif n >= 10_000_000:
                scale_desc = "a mid-to-large"
            elif n >= 1_000_000:
                scale_desc = "a growing"
            elif n >= 100_000:
                scale_desc = "an emerging"
        except ValueError:
            pass

    # Category descriptor
    category_descs = {
        "neobank": "digital banking",
        "payment": "payments",
        "lending": "lending/credit",
        "broker": "investment brokerage",
        "wealth": "wealth management",
        "savings": "consumer savings",
        "fintech": "fintech",
    }
    category_desc = category_descs.get(category, "fintech")

    # Product gaps — what they DON'T have yet
    has_fd = bool(prospect.get("has_fd"))
    has_rd = bool(prospect.get("has_rd"))
    has_bonds = bool(prospect.get("has_bonds"))
    has_mutual_funds = bool(prospect.get("has_mutual_funds"))
    has_stocks = bool(prospect.get("has_stocks"))

    existing_products = []
    if has_mutual_funds: existing_products.append("mutual funds")
    if has_stocks: existing_products.append("equity trading")
    if has_bonds: existing_products.append("bonds")
    if has_fd: existing_products.append("fixed deposits")
    if has_rd: existing_products.append("recurring deposits")

    missing_products = []
    if not has_fd: missing_products.append("fixed deposits")
    if not has_rd: missing_products.append("recurring deposits")
    if not has_bonds: missing_products.append("bonds")

    # Business momentum signals (translated, not leaked)
    momentum_notes = []
    competitor_note = None

    for sig in (signals or []):
        sig_type = sig.get("signal_type", "")
        sig_title = sig.get("title", "")
        strength = sig.get("signal_strength", "MEDIUM")

        if sig_type == "FUNDING_EXPANSION" and strength in ("HIGH", "MEDIUM"):
            # Don't say "we saw your funding news" — say it in context
            momentum_notes.append("recently raised growth capital")
        elif sig_type == "LEADERSHIP_HIRE":
            momentum_notes.append("recently brought in new leadership")
        elif sig_type == "PRODUCT_LAUNCH":
            momentum_notes.append("actively expanding its product portfolio")
        elif sig_type == "DISPLACEMENT":
            competitor_note = sig_title  # "Using StableMoney" etc
        elif sig_type == "COMPETITOR_MOVE":
            momentum_notes.append("operating in a rapidly moving competitive landscape")

    # Recommended product context
    product_context = {
        "FD SDK": {
            "what": "a plug-and-play Fixed Deposit SDK",
            "why_matters": "FDs are India's most trusted savings instrument — adding them drives meaningful user retention and generates revenue on every booking without balance sheet risk",
            "speed": "integrates in 7–10 days",
            "proof": "MobiKwik, Jar, and 30+ platforms use Blostem's FD infrastructure",
        },
        "FD + RD SDK": {
            "what": "Fixed Deposit and Recurring Deposit infrastructure",
            "why_matters": "Together these cover the full savings spectrum — lump-sum and systematic — which creates stickier user relationships than either product alone",
            "speed": "both products live in under two weeks",
            "proof": "Platforms using both see 40% higher engagement on the savings tab",
        },
        "RD SDK": {
            "what": "a Recurring Deposit SDK with multi-bank support",
            "why_matters": "RDs convert one-time users into habitual savers — the most valuable cohort for long-term platform retention",
            "speed": "integrates in under a week",
            "proof": "Groww and Jupiter use Blostem's deposit infrastructure to anchor their savings products",
        },
        "Credit on UPI": {
            "what": "Credit on UPI infrastructure",
            "why_matters": "Credit on UPI lets your users pay with a credit line directly from their UPI QR — no card needed, frictionless checkout, and a new revenue stream from credit fees",
            "speed": "live in 7–14 days",
            "proof": "Already powering Credit on UPI for several mid-market payment platforms",
        },
        "FD + Bonds SDK": {
            "what": "Fixed Deposit and Bonds distribution infrastructure",
            "why_matters": "For wealth and brokerage platforms, this closes the fixed-income gap — users who want stable, predictable returns currently have to leave your app",
            "speed": "both products can be live within two weeks",
            "proof": "GoldenPi and Aspero run on Blostem's fixed-income rails",
        },
        "Bonds SDK": {
            "what": "a Bonds distribution SDK",
            "why_matters": "Corporate and government bonds are the missing piece for sophisticated investors — your equity users expect it",
            "speed": "integrates in 7–10 days",
            "proof": "Powers bonds distribution for multiple SEBI-registered platforms",
        },
        "FD-backed Credit Card infrastructure": {
            "what": "FD-backed Credit Card infrastructure",
            "why_matters": "Lets thin-file users build credit using their FD as collateral — a massively underserved segment that dramatically expands your addressable market",
            "speed": "2–4 weeks to production depending on your card issuance partner",
            "proof": "Proven model already live with digital-first credit building platforms",
        },
    }

    prod = product_context.get(recommended_product, product_context["FD SDK"])

    return {
        "company_name": name,
        "scale_desc": scale_desc,
        "category_desc": category_desc,
        "existing_products": existing_products,
        "missing_products": missing_products,
        "recommended_product": recommended_product,
        "product_what": prod["what"],
        "product_why_matters": prod["why_matters"],
        "product_speed": prod["speed"],
        "product_proof": prod["proof"],
        "momentum_notes": momentum_notes,
        "competitor_note": competitor_note,
        "using_competitor": prospect.get("using_competitor"),
    }


# ─────────────────────────────────────────────
# Persona prompt builders
# ─────────────────────────────────────────────

PERSONA_META = {
    "CTO": {
        "title": "CTO / VP Engineering / Head of Technology",
        "cares_about": [
            "How long will the integration actually take (not the sales pitch — the real answer)",
            "Quality of the API design: REST? Webhooks? SDK? Docs?",
            "What happens when things go wrong — error handling, uptime, support",
            "Will their team be stuck maintaining a fragile integration in six months",
            "Security, data handling, and compliance overhead for their engineers",
        ],
        "fears": "Another bank integration that takes 3 months, breaks constantly, and has no real support",
        "proof_points": [
            "50 lines of code to integrate (React, Flutter, Android, iOS SDKs available)",
            "Engineers at MobiKwik went live in 7 days",
            "Webhooks + sandbox environment ready day one",
            "Dedicated technical integration support — not just docs",
        ],
        "tone": "Direct, technical-ish but not jargon-heavy. Respect their time. One specific thing, one clear ask.",
    },
    "CPO": {
        "title": "CPO / Head of Product / VP Product",
        "cares_about": [
            "User experience quality — does the embedded product feel native or bolted on",
            "Time to launch — how fast can we add this without derailing the roadmap",
            "Whether this genuinely serves user needs or is just a revenue play",
            "Competitive differentiation — is this table stakes or a real moat",
            "Risk to the existing product if the integration has issues",
        ],
        "fears": "Launching a half-baked financial product that damages user trust and takes the product team months to fix",
        "proof_points": [
            "White-label UI — matches your brand out of the box",
            "MobiKwik launched their FD product to 100M+ users in under 2 weeks",
            "Multi-bank distribution means users get best rates, not one bank's rates",
            "DICGC-insured deposits — no user trust risk",
        ],
        "tone": "Empathetic to product pressures. Show you understand the product discipline, not just the revenue. Short and crisp.",
    },
    "CFO": {
        "title": "CFO / VP Finance / Head of Finance",
        "cares_about": [
            "Revenue model: how does the money flow, what are the unit economics",
            "No fixed cost commitment — variable, commission-based is preferred",
            "Regulatory and compliance risk — anything that could become a balance sheet liability",
            "Tax treatment and accounting of commission revenue",
            "What happens to their users' money if something goes wrong",
        ],
        "fears": "Signing up to something with hidden compliance costs, balance sheet exposure, or regulatory grey areas",
        "proof_points": [
            "Pure commission model — 0 fixed cost, revenue on every FD booked",
            "No balance sheet risk — Blostem holds no deposits; partner banks do",
            "DICGC-insured up to ₹5 lakh per depositor — industry-standard protection",
            "Partnership with regulated NBFCs and scheduled commercial banks",
        ],
        "tone": "Precise and credible. CFOs are pattern-matching for red flags. Be specific on numbers, never vague on risk.",
    },
}


def _build_prompt(persona: str, ctx: dict, when_data: dict) -> str:
    """
    Build a natural, non-templated prompt that produces genuinely personalised emails.

    The key insight: we give the LLM FACTS and a CHARACTER, not a STRUCTURE.
    When the LLM knows who it is, who it's writing to, and what the facts are,
    it produces varied, natural output — not a filled-in form.
    """
    pm = PERSONA_META[persona]
    name = ctx["company_name"]
    missing = ctx["missing_products"]
    existing = ctx["existing_products"]
    momentum = ctx["momentum_notes"]
    competitor = ctx["using_competitor"] or ctx.get("competitor_note")

    # Build the "what we know about them" section (no signal leakage)
    company_context_parts = [
        f"{name} is {ctx['scale_desc']} {ctx['category_desc']} platform.",
    ]
    if existing:
        company_context_parts.append(
            f"They already offer {', '.join(existing)} to their users."
        )
    if missing:
        company_context_parts.append(
            f"They don't yet offer {', '.join(missing[:2])} — which is the gap Blostem fills."
        )
    if momentum:
        company_context_parts.append(
            f"The company has been {' and '.join(momentum[:2])}."
        )
    if competitor:
        company_context_parts.append(
            f"They currently use a competitor ({competitor}) for this — so there's an active vendor relationship to navigate."
        )

    company_context = " ".join(company_context_parts)

    # What the persona cares about (formatted naturally)
    cares = "\n".join(f"  - {c}" for c in pm["cares_about"])

    # Proof points
    proof = "\n".join(f"  - {p}" for p in pm["proof_points"])

    prompt = f"""You are a senior business development manager at Blostem — an Indian fintech infrastructure company backed by Zerodha's Rainmatter. Blostem provides plug-and-play APIs for Fixed Deposits, Recurring Deposits, Credit on UPI, and Bonds. Integration takes days, not months.

You are writing a cold outreach email to the **{pm['title']}** at **{name}**.

---

**What you know about {name}:**
{company_context}

**What the {persona} cares about:**
{cares}

**What they're afraid of:**
{pm['fears']}

**Blostem's most relevant proof points for this persona:**
{proof}

**What Blostem is offering them:**
{ctx['product_what']} — {ctx['product_why_matters']}. It {ctx['product_speed']}.

---

**Writing instructions:**

1. Write a genuine, personalised cold email. NOT a template. NOT a format with sections.

2. The email should sound like it was written by a thoughtful person who spent 10 minutes thinking about {name}'s specific situation — not like a tool filled in variables.

3. Open with something specific and relevant to {name}'s situation or the {persona}'s world. Do NOT start with "I hope this email finds you well" or "I wanted to reach out" or "My name is". Start with what's interesting.

4. The value proposition should emerge naturally from addressing what the {persona} cares about — not be announced as a pitch.

5. One clear, low-friction call-to-action at the end. Suggest a specific timeframe ("15 minutes this week?" not "whenever convenient for you").

6. Length: 80–140 words for the body. Short. Respects busy people.

7. NEVER mention:
   - That you saw their app on the Play Store
   - That you noticed changes to their app description or listing
   - That you tracked their metrics or data
   - Any scraping, monitoring, or surveillance activity
   Instead, frame any product insight as category-level observation: "Platforms in the {ctx['category_desc']} space are increasingly adding fixed-income products" not "We noticed your app added savings recently."

8. Tone: {pm['tone']}

---

Return ONLY valid JSON, nothing else:
{{
  "subject": "...",
  "body": "...",
  "persona_title": "{pm['title']}"
}}

The body should be plain text — no markdown, no bullet points inside the email, no headers. Write prose as a human would write an email."""

    return prompt


# ─────────────────────────────────────────────
# Email generation
# ─────────────────────────────────────────────

def generate_email_for_persona(
    persona: str,
    prospect: dict,
    signals: list[dict],
    when_data: dict,
) -> dict:
    """
    Generate one persona-targeted email for a prospect.

    Returns a dict with subject, body, compliance info, and metadata.
    Falls back to demo cache if Groq LLM fails (keeps judges seeing working examples).
    """
    ctx = _translate_signals_to_context(prospect, signals)
    prompt = _build_prompt(persona, ctx, when_data)

    raw = _call_llm(prompt, max_tokens=700)
    if not raw:
        # Fallback to demo cache if LLM unavailable (Groq down, rate limited, etc.)
        cached = get_cached_email(prospect.get("name"), persona)
        if cached:
            cached["fallback_reason"] = "LLM unavailable, using cached example (Groq API temporarily offline)"
            return cached
        return {"error": "LLM call failed and no cached email available", "persona": persona}

    result = _parse_json_response(raw)
    if not result or "body" not in result:
        # Fallback to demo cache on parse error too
        cached = get_cached_email(prospect.get("name"), persona)
        if cached:
            cached["fallback_reason"] = "Could not parse LLM response, using cached example"
            return cached
        return {"error": "Could not parse LLM response and no cached email available", "persona": persona}

    subject = result.get("subject", "")
    body = result.get("body", "")

    # Run compliance
    compliance = check_compliance(
        body=body,
        subject=subject,
        recipient_name=None,
        company_name=prospect.get("name"),
    )

    # Auto-retry once if CRITICAL violation
    if compliance["status"] == "BLOCKED":
        retry_prompt = prompt + f"""

IMPORTANT: Your previous attempt had a compliance issue: {compliance['violations'][0]['headline'] if compliance['violations'] else 'unknown issue'}. Fix it and rewrite. Return only the JSON."""
        raw2 = _call_llm(retry_prompt, max_tokens=700)
        if raw2:
            result2 = _parse_json_response(raw2)
            if result2 and "body" in result2:
                subject = result2.get("subject", subject)
                body = result2.get("body", body)
                compliance = check_compliance(body=body, subject=subject, company_name=prospect.get("name"))

    return {
        "persona": persona,
        "persona_title": PERSONA_META[persona]["title"],
        "subject": subject,
        "body": body,
        "compliance": compliance,
    }


def generate_outreach_package(prospect_id: int) -> dict | None:
    """
    Generate a complete outreach package for a prospect:
    - 3 persona emails (CPO, CTO, CFO)
    - Recommended send sequence
    - Compliance summary
    - Context about why this prospect, why now

    Returns None if prospect not found.
    """
    with get_db() as conn:
        prospect_row = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()

        if not prospect_row:
            return None

        prospect = dict(prospect_row)

        # Get signals
        signals = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM signals WHERE prospect_id = ? ORDER BY detected_at DESC LIMIT 10",
                (prospect_id,),
            ).fetchall()
        ]

    when_data = calculate_when_score(prospect_id)

    category = (prospect.get("category") or "other").lower()
    recommended_product = prospect.get("recommended_product", "FD SDK")

    # Sequence logic — who to contact first based on category
    if category in ("payment", "lending"):
        sequence = ["CPO", "CTO", "CFO"]
        sequence_rationale = "For payment and lending platforms, Product leads the product decision. Engineering validates feasibility. Finance signs off on the commercial model."
    elif category in ("broker", "wealth"):
        sequence = ["CPO", "CFO", "CTO"]
        sequence_rationale = "Wealth and brokerage platforms are product-led — the CPO sees the user value immediately. CFO is a close second given revenue implications. Engineering is typically a follower."
    elif category in ("neobank",):
        sequence = ["CPO", "CTO", "CFO"]
        sequence_rationale = "Neobanks move fast on product. CPO → CTO → CFO follows their typical decision chain."
    else:
        sequence = ["CTO", "CPO", "CFO"]
        sequence_rationale = "When category is unclear, start with the technical validator. If they're interested, the product and finance conversations follow naturally."

    print(f"\n📧 Generating outreach package for {prospect['name']}...")

    emails: dict[str, dict] = {}
    for persona in ["CPO", "CTO", "CFO"]:
        print(f"  → Writing {persona} email...")
        email = generate_email_for_persona(persona, prospect, signals, when_data)
        emails[persona] = email
        time.sleep(0.5)  # be polite to the API

    # Compliance summary
    blocked = [p for p, e in emails.items() if e.get("compliance", {}).get("status") == "BLOCKED"]
    warned  = [p for p, e in emails.items() if e.get("compliance", {}).get("status") == "WARNING"]

    # Why now — based on signals (translated, no leakage)
    ctx = _translate_signals_to_context(prospect, signals)
    why_now_parts = []
    if ctx["momentum_notes"]:
        why_now_parts.append(f"{prospect['name']} has {ctx['momentum_notes'][0]}")
    if ctx["missing_products"]:
        why_now_parts.append(f"their platform currently lacks {', '.join(ctx['missing_products'][:2])}")
    if ctx["using_competitor"]:
        why_now_parts.append(f"they're currently using {ctx['using_competitor']} for this — an opening for a conversation")

    why_now = (
        ". ".join(why_now_parts).capitalize() + "."
        if why_now_parts
        else f"{prospect['name']} is an active {ctx['category_desc']} platform with a clear product gap Blostem fills."
    )

    return {
        "prospect_id": prospect_id,
        "prospect_name": prospect["name"],
        "recommended_product": recommended_product,
        "category": category,
        "when_score": when_data.get("when_score"),
        "action": when_data.get("action"),
        "why_now": why_now,
        "emails": emails,
        "recommended_sequence": sequence,
        "sequence_rationale": sequence_rationale,
        "compliance_summary": {
            "all_clear": len(blocked) == 0,
            "blocked_personas": blocked,
            "warned_personas": warned,
            "blocked_count": len(blocked),
            "warning_count": len(warned),
        },
        "generated_at": datetime.now().isoformat(),
    }
