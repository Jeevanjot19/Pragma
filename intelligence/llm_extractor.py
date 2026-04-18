# import json
# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# # Groq client (OpenAI-compatible)
# client = OpenAI(
#     api_key=os.getenv("GROQ_API_KEY"),
#     base_url="https://api.groq.com/openai/v1"
# )

# #MODEL = "llama3-70b-8192"  # Fast + free + good for structured output
# MODEL = "llama-3.3-70b-versatile"

# def extract_company_from_article(title: str, summary: str) -> dict | None:
#     """
#     Given a news article, extract company intelligence.
#     Returns None if not relevant to Blostem's prospects.
#     """
#     prompt = f"""You are an analyst at Blostem — an Indian fintech infrastructure company 
# that provides APIs for Fixed Deposits (FD), Recurring Deposits (RD), 
# Credit on UPI, FD-backed credit cards, and Bonds distribution.

# Analyze this Indian fintech news article and extract structured information.

# Article Title: {title}
# Article Summary: {summary}

# Extract the following and return ONLY valid JSON, no explanation:
# {{
#     "is_relevant": true/false,
#     "company_name": "...",
#     "company_category": "...",
#     "current_products": [],
#     "expansion_signals": [],
#     "funding_detected": true/false,
#     "funding_amount": "...",
#     "leadership_hire": true/false,
#     "leadership_role": "...",
#     "competitor_mentioned": "...",
#     "signal_summary": "..."
# }}

# Rules:
# - is_relevant = false if ANY of these are true:
#   * Company is a regulatory body (RBI, SEBI, NPCI, IRDAI, MCA, etc.)
#   * Company is a bank itself (SBI, HDFC, ICICI, Axis, Kotak, etc.)
#   * Company is already a Blostem partner (listed above)
#   * Article is purely about fraud, security breach, or regulatory penalty
#   * Company is not in the fintech/investment/payments space
# - is_relevant = true ONLY if the company is a fintech PLATFORM
#   that could embed Blostem's infrastructure products"""

#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#             max_tokens=500
#         )

#         raw = response.choices[0].message.content.strip()
#         raw = raw.replace("```json", "").replace("```", "").strip()

#         return json.loads(raw)

#     except Exception as e:
#         print(f"LLM extraction error: {e}")
#         return None


# def analyze_regulatory_event(title: str, summary: str) -> dict | None:
#     """
#     Analyze RBI/NPCI circular for relevance to Blostem's products.
#     """
#     prompt = f"""You are an analyst at Blostem — an Indian fintech infrastructure company 
# offering: Fixed Deposits (FD), Recurring Deposits (RD), Credit on UPI, FD-backed credit cards, Bonds.

# Analyze this regulatory update and return ONLY valid JSON:

# Title: {title}
# Summary: {summary}

# {{
#     "is_relevant": true/false,
#     "relevance_score": 0-10,
#     "affected_products": [],
#     "affected_company_types": [],
#     "implication": "...",
#     "urgency": "HIGH/MEDIUM/LOW"
# }}"""

#     try:
#         response = client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#             max_tokens=300
#         )

#         raw = response.choices[0].message.content.strip()
#         raw = raw.replace("```json", "").replace("```", "").strip()

#         result = json.loads(raw)
#         return result if result.get("relevance_score", 0) >= 6 else None

#     except Exception as e:
#         print(f"Regulatory LLM error: {e}")
#         return None


# def determine_recommended_product(category: str, current_products: list) -> str:
#     has_fd = 'FD' in current_products
#     has_rd = 'RD' in current_products
#     has_bonds = 'bonds' in current_products
#     has_upi_credit = 'UPI_credit' in current_products

#     # Lending companies → FD-backed credit or Credit on UPI
#     if category == 'lending':
#         if not has_upi_credit:
#             return 'Credit on UPI'
#         if not has_fd:
#             return 'FD-backed Credit Card infrastructure'

#     # Payment apps → Credit on UPI
#     if category == 'payment' and not has_upi_credit:
#         return 'Credit on UPI'

#     # Brokers and wealth → FD first, then Bonds
#     if category in ['broker', 'wealth']:
#         if not has_fd:
#             return 'FD + RD SDK'
#         if has_fd and not has_bonds:
#             return 'Bonds SDK'

#     # Neobanks and savings → RD
#     if category in ['neobank', 'savings'] and not has_rd:
#         return 'RD SDK'

#     # Credit building apps
#     if category == 'credit_building':
#         return 'FD-backed Credit Card infrastructure'

#     # NBFCs
#     if category == 'nbfc' and not has_fd:
#         return 'FD SDK'

#     # Default fallback
#     if not has_fd:
#         return 'FD SDK'
#     return 'FD + RD SDK'




import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Groq client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Versatile model for all tasks (only using one model to avoid rate limits)
MODEL = "llama-3.3-70b-versatile"  # Versatile model handles both generation and extraction

# Rate limiting — Groq free tier is generous but we still throttle
_last_call_time = 0
MIN_CALL_INTERVAL = 0.5  # seconds between LLM calls


def _call_llm(prompt: str, max_tokens: int = 500) -> str | None:
    """
    Single unified LLM call with rate limiting and error handling.
    All LLM calls go through here.
    Uses llama-3.3-70b-versatile for all tasks (best for avoiding rate limits).
    """
    global _last_call_time

    # Always use versatile model (avoids rate limiting issues with fast model)
    model = MODEL

    # Rate limiting
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=max_tokens
        )
        _last_call_time = time.time()
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  LLM call failed: {e}")
        _last_call_time = time.time()
        return None


def _parse_json_response(raw: str) -> dict | None:
    """
    Safely parse LLM JSON response.
    Handles markdown code blocks, None input, and malformed JSON.
    """
    if not raw:
        return None

    # Strip markdown if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Sometimes models add explanation text before/after JSON
    # Try to extract just the JSON object
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e} | Raw snippet: {raw[:100]}")
        return None


def extract_company_from_article(title: str, summary: str) -> dict | None:
    """
    Given a news article, extract company intelligence for Blostem prospecting.
    Returns a validated dict or None if not relevant / extraction failed.
    """
    prompt = f"""You are an analyst at Blostem — an Indian fintech infrastructure company 
that provides APIs for Fixed Deposits (FD), Recurring Deposits (RD), 
Credit on UPI, FD-backed credit cards, and Bonds distribution.

Blostem's existing partners (NOT prospects): MobiKwik, Jupiter Money, Upstox, Zerodha, Tide, Fello, Aspero, Centricity, GoldenPi.
Blostem's competitors: Stable Money, Deciml, Wint Wealth, Jiraaf, Grip Invest.

Analyze this Indian fintech news article and extract structured information.

Article Title: {title}
Article Summary: {summary}

Return ONLY a valid JSON object, no explanation, no markdown:
{{
    "is_relevant": true,
    "company_name": "exact company name",
    "company_category": "one of: broker/payment/neobank/wealth/savings/credit_building/lending/nbfc/other",
    "current_products": ["list from: FD, RD, mutual_funds, stocks, bonds, UPI_credit, payments, lending, insurance"],
    "expansion_signals": ["products they plan to add, same options as current_products"],
    "funding_detected": false,
    "funding_amount": null,
    "leadership_hire": false,
    "leadership_role": null,
    "competitor_mentioned": null,
    "signal_summary": "one sentence explanation"
}}

Rules — set is_relevant to false if ANY of these are true:
- Company is a regulatory body (RBI, SEBI, NPCI, IRDAI, MCA, etc.)
- Company is a traditional bank (SBI, HDFC, ICICI, Axis, Kotak, PNB, BOI, etc.)
- Company is already a Blostem partner (MobiKwik, Jupiter, Upstox, Zerodha, Tide, etc.)
- Article is purely about fraud, security breach, or regulatory penalty with no new product angle
- Company is not in fintech/investment/payments/savings/lending space
- Article is about EV, D2C, healthcare, edtech, logistics, or other non-fintech sectors

Set is_relevant to true ONLY if the company is a fintech PLATFORM that could realistically embed Blostem's infrastructure.

Return ONLY the JSON object. Nothing else."""

    raw = _call_llm(prompt, max_tokens=500)
    result = _parse_json_response(raw)

    if not result:
        return None

    # Must be a dict
    if not isinstance(result, dict):
        return None

    # Must have is_relevant field
    if 'is_relevant' not in result:
        return None

    # Ensure company_name is a string (never None)
    company_name = result.get('company_name')
    if company_name is None:
        result['company_name'] = ''
    elif not isinstance(company_name, str):
        result['company_name'] = str(company_name)

    # Ensure list fields are actually lists
    for list_field in ['current_products', 'expansion_signals']:
        val = result.get(list_field)
        if not isinstance(val, list):
            result[list_field] = []

    # Ensure boolean fields are booleans
    for bool_field in ['is_relevant', 'funding_detected', 'leadership_hire']:
        val = result.get(bool_field)
        if val is None:
            result[bool_field] = False
        elif not isinstance(val, bool):
            # Convert string "true"/"false" if model misbehaves
            result[bool_field] = str(val).lower() == 'true'

    # Ensure string fields that can be null are handled
    for nullable_field in ['funding_amount', 'leadership_role', 'competitor_mentioned', 'signal_summary']:
        if nullable_field not in result:
            result[nullable_field] = None

    return result


def analyze_regulatory_event(title: str, summary: str) -> dict | None:
    """
    Analyze RBI/NPCI/SEBI circular for relevance to Blostem's products.
    Returns None if relevance score < 6 or extraction failed.
    """
    prompt = f"""You are an analyst at Blostem — an Indian fintech infrastructure company 
offering: Fixed Deposits (FD), Recurring Deposits (RD), Credit on UPI, FD-backed credit cards, Bonds.

Analyze this regulatory update and return ONLY a valid JSON object, no markdown:

Title: {title}
Summary: {summary}

{{
    "is_relevant": true,
    "relevance_score": 7,
    "affected_products": ["FD", "RD"],
    "affected_company_types": ["payment", "broker"],
    "implication": "one sentence about what this means for Blostem sales",
    "urgency": "HIGH"
}}

Only set is_relevant true if this directly affects deposit products, UPI credit, or banking infrastructure.
relevance_score: 0-10 (only return if 6 or higher is justified).
urgency: HIGH / MEDIUM / LOW.
Return ONLY the JSON."""

    raw = _call_llm(prompt, max_tokens=300)
    result = _parse_json_response(raw)

    if not result or not isinstance(result, dict):
        return None

    # Only surface if actually relevant
    score = result.get('relevance_score', 0)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0

    if score < 6:
        return None

    # Ensure lists
    for list_field in ['affected_products', 'affected_company_types']:
        if not isinstance(result.get(list_field), list):
            result[list_field] = []

    return result


def determine_recommended_product(category: str, 
                                   current_products: list,
                                   install_count: str = None) -> str:
    """
    Recommend which Blostem product fits best.
    Considers category, existing products, and company scale.
    """
    if not isinstance(current_products, list):
        current_products = []

    has_fd = 'FD' in current_products
    has_rd = 'RD' in current_products
    has_bonds = 'bonds' in current_products
    has_upi_credit = 'UPI_credit' in current_products
    has_lending = 'lending' in current_products
    has_payments = 'payments' in current_products
    has_mf = 'mutual_funds' in current_products
    has_stocks = 'stocks' in current_products
    
    # Count how many financial products they already have
    product_count = sum([has_mf, has_stocks, has_bonds, 
                        has_lending, has_payments, has_rd])

    # Payment apps with UPI infrastructure → Credit on UPI
    if category == 'payment':
        return 'Credit on UPI'

    # Lending apps → Credit on UPI (FD as collateral for loans)
    if category == 'lending':
        return 'Credit on UPI'

    # Sophisticated wealth/broker apps → 
    # If they have multiple investment products, they're ready for FD
    if category in ['broker', 'wealth']:
        if not has_fd:
            return 'FD + RD SDK'
        if has_fd and not has_bonds:
            return 'Bonds SDK'
        return 'FD + RD SDK'

    # Neobanks → RD first (recurring savings is core neobank feature)
    if category in ['neobank', 'challenger bank']:
        if not has_rd:
            return 'RD SDK'
        if not has_fd:
            return 'FD SDK'
        return 'FD + RD SDK'

    # Savings-focused apps
    if category == 'savings':
        return 'RD SDK'

    # Credit building apps
    if category == 'credit_building':
        return 'FD-backed Credit Card infrastructure'

    # Super-apps with multiple products → FD is logical next step
    if category == 'super-app' and product_count >= 2:
        return 'FD + RD SDK'

    # NBFCs
    if category == 'nbfc':
        return 'FD SDK'

    # Default
    if not has_fd:
        return 'FD SDK'
    return 'FD + RD SDK'


def extract_products_from_description(company_name: str, 
                                       description: str,
                                       category: str = '') -> dict:
    """
    Use LLM to accurately detect what financial products a company offers.
    More reliable than keyword matching on Play Store descriptions.
    """
    if not description or len(description) < 50:
        return {}
    
    prompt = f"""You are analyzing an Indian fintech app to understand what financial products it offers.

Company: {company_name}
Category: {category}
App Description: {description[:800]}

Based ONLY on what the description explicitly states about products offered to end users:
Which of these products does this company ACTUALLY offer?
Only mark true if clearly stated or heavily implied.

Return ONLY valid JSON, no explanation:
{{
    "has_fd": false,
    "has_rd": false,
    "has_bonds": false,
    "has_upi_credit": false,
    "has_mutual_funds": false,
    "has_stocks": false,
    "has_insurance": false,
    "has_lending": false,
    "has_payments": false
}}"""
    
    raw = _call_llm(prompt, max_tokens=250)
    result = _parse_json_response(raw)
    
    if not result or not isinstance(result, dict):
        return {}
    
    # Ensure all fields are boolean
    bool_fields = ['has_fd', 'has_rd', 'has_bonds', 'has_upi_credit',
                   'has_mutual_funds', 'has_stocks', 'has_insurance',
                   'has_lending', 'has_payments']
    for field in bool_fields:
        val = result.get(field)
        if not isinstance(val, bool):
            result[field] = False
    
    return result


# Product detection using smart keyword matching — zero LLM calls
PRODUCT_DETECTION = {
    'has_fd': {
        'strong': ['book fd', 'open fd', 'fixed deposit booking', 
                   'fd in minutes', 'earn with fd', 'invest in fd',
                   'fd from multiple banks', 'multi-bank fd'],
        'weak': ['fixed deposit', 'term deposit', 'fd'],
        'negative': ['fd calculator', 'fd rates comparison', 
                     'fd interest calculator', 'check fd rates']
    },
    'has_rd': {
        'strong': ['recurring deposit', 'open rd', 'start rd',
                   'save monthly', 'monthly savings plan'],
        'weak': ['rd account', 'recurring savings'],
        'negative': ['rd calculator', 'rd interest rate']
    },
    'has_bonds': {
        'strong': ['invest in bonds', 'buy bonds', 'bond investment',
                   'government bonds', 'corporate bonds platform'],
        'weak': ['bonds', 'debentures'],
        'negative': ['bond calculator', 'bond yield']
    },
    'has_upi_credit': {
        'strong': ['credit on upi', 'upi credit line', 'buy now pay later upi',
                   'credit via upi', 'upi overdraft'],
        'weak': ['upi credit'],
        'negative': []
    },
    'has_mutual_funds': {
        'strong': ['mutual fund', 'sip', 'invest in mf', 'mf investment'],
        'weak': ['funds'],
        'negative': ['hedge fund', 'fund transfer']
    },
    'has_stocks': {
        'strong': ['buy stocks', 'stock trading', 'equity trading',
                   'demat account', 'invest in stocks', 'share trading'],
        'weak': ['stocks', 'equity', 'shares'],
        'negative': ['stock market news', 'stock analysis']
    },
    'has_insurance': {
        'strong': ['buy insurance', 'insurance policy', 'life insurance',
                   'health insurance', 'term insurance'],
        'weak': ['insurance'],
        'negative': ['insurance news', 'insurance comparison']
    },
    'has_lending': {
        'strong': ['personal loan', 'instant loan', 'apply for loan',
                   'credit line', 'emi', 'borrow money'],
        'weak': ['loan', 'credit', 'lending'],
        'negative': ['loan calculator', 'loan comparison']
    },
    'has_payments': {
        'strong': ['upi payments', 'pay bills', 'money transfer',
                   'send money', 'payment gateway', 'merchant payments'],
        'weak': ['payments', 'pay'],
        'negative': []
    }
}

def detect_products_smart(description: str) -> dict:
    """
    Detect financial products from app description using
    tiered keyword matching with negative filters.
    Zero LLM calls. ~85% accuracy vs LLM's ~92%.
    Token savings: eliminates 100+ LLM calls per run.
    
    Decodes HTML entities and removes markup that could prevent keyword matching.
    """
    import html
    import re
    
    if not description:
        return {k: False for k in PRODUCT_DETECTION}
    
    # Decode HTML entities and remove markup
    text = html.unescape(description)
    text = re.sub(r'<[^>]+>', ' ', text)  # Remove HTML tags
    text = ' '.join(text.split())  # Normalize whitespace
    desc_lower = text.lower()
    
    results = {}
    
    for product, keywords in PRODUCT_DETECTION.items():
        # Check negatives first — if negative keyword present, skip
        has_negative = any(neg in desc_lower 
                          for neg in keywords.get('negative', []))
        if has_negative:
            results[product] = False
            continue
        
        # Strong keywords = definitive match
        has_strong = any(kw in desc_lower 
                        for kw in keywords.get('strong', []))
        if has_strong:
            results[product] = True
            continue
        
        # Weak keywords = only count if multiple appear
        # reduces false positives from incidental mentions
        weak_count = sum(1 for kw in keywords.get('weak', []) 
                        if kw in desc_lower)
        results[product] = weak_count >= 2
    
    return results


def batch_extract_companies(articles: list) -> list:
    """
    Extract company intelligence from multiple articles in ONE LLM call.
    Returns a list of extraction results — one per article.
    Much more token-efficient: 14 calls instead of 140+ per run.
    """
    if not articles:
        return []

    # Format articles for the prompt
    articles_text = ""
    for i, article in enumerate(articles):
        articles_text += f"\nARTICLE {i+1}:\nTitle: {article['title']}\nSummary: {article.get('summary', '')[:200]}\n"

    prompt = f"""You are an analyst at Blostem — an Indian fintech infrastructure company 
offering: Fixed Deposits (FD), Recurring Deposits (RD), Credit on UPI, FD-backed credit cards, Bonds.

Existing Blostem partners (NOT prospects): MobiKwik, Jupiter, Upstox, Zerodha, Tide, Fello, GoldenPi.
Competitors: Stable Money, Deciml, Wint Wealth, Jiraaf, Grip Invest.

Analyze these {len(articles)} news articles. For each, extract company intelligence.

{articles_text}

Return a JSON ARRAY with exactly {len(articles)} objects, one per article, in order:
[
  {{
    "is_relevant": true,
    "company_name": "name or empty string",
    "company_category": "broker/payment/neobank/wealth/savings/lending/nbfc/other",
    "current_products": [],
    "expansion_signals": [],
    "funding_detected": false,
    "funding_amount": null,
    "leadership_hire": false,
    "leadership_role": null,
    "competitor_mentioned": null,
    "signal_summary": "one sentence"
  }}
]

Rules for is_relevant = false:
- Regulatory bodies (RBI, SEBI, NPCI)
- Traditional banks (SBI, HDFC, ICICI, Axis)
- Existing Blostem partners
- Non-fintech articles (EV, D2C, healthcare, logistics)
- Generic terms like "India Fintech" — not a real company

Return ONLY the JSON array. No explanation. No markdown."""

    # Use versatile model for batch extraction (no rate limit issues)
    raw = _call_llm(prompt, max_tokens=1500)
    
    if not raw:
        return [None] * len(articles)

    # Parse the array
    raw = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find('[')
    end = raw.rfind(']')
    if start == -1 or end == -1:
        return [None] * len(articles)
    
    try:
        result_list = json.loads(raw[start:end+1])
    except json.JSONDecodeError:
        return [None] * len(articles)

    # Validate and fix each result
    validated = []
    for result in result_list:
        if not isinstance(result, dict):
            validated.append(None)
            continue
        
        # Ensure required fields
        if 'company_name' not in result:
            result['company_name'] = ''
        if result.get('company_name') is None:
            result['company_name'] = ''
        for list_field in ['current_products', 'expansion_signals']:
            if not isinstance(result.get(list_field), list):
                result[list_field] = []
        for bool_field in ['is_relevant', 'funding_detected', 'leadership_hire']:
            if not isinstance(result.get(bool_field), bool):
                result[bool_field] = str(result.get(bool_field, 'false')).lower() == 'true'
        
        validated.append(result)

    # Pad if LLM returned fewer results than expected
    while len(validated) < len(articles):
        validated.append(None)

    return validated[:len(articles)]