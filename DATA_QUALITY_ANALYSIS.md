# Pragma Database & Data Quality Analysis

## Overview
The Pragma system manages a prospects pipeline with enrichment, scoring, monitoring, and activation tracking. The database is SQLite with ~25 tables tracking prospects, signals, monitoring events, partner activation, and buyer committee intelligence.

---

## 1. WHAT DATA SHOULD BE IN THE DATABASE

### Core Prospect Data
✅ **Name**: Unique identifier for companies
✅ **Category**: Fintech category (broker, payment, neobank, wealth, savings, credit_building, lending, nbfc)
✅ **Product Flags**: Boolean columns for what products they already have
  - `has_fd`, `has_rd`, `has_bonds`, `has_upi_credit`, `has_mutual_funds`, `has_stocks`, `has_insurance`

✅ **Play Store Data**: 
  - `play_store_id`: App identifier
  - `install_count`: User scale (e.g., "1,000,000+")
  - `description`: First 500 chars of app description

✅ **Qualification Metrics**:
  - `who_score`: Composite signal score (0-100)
  - `status`: HOT (65+), WARM (35+), or WATCH (<35)
  - `is_existing_partner`: Boolean flag to exclude known partners

✅ **Contact & Outreach**:
  - `website`, `source`, `last_description_checked`, `last_news_check`
  - `recommended_product`: What Blostem product to pitch
  - `using_competitor`: Flag if using competitor (Stable Money, Deciml, etc.)

### Signal Data
✅ **Signals Table**: 
  - Signal type: PRODUCT_GAP, FUNDING_EXPANSION, COMPETITOR_MOVE, LEADERSHIP_HIRE, DISPLACEMENT
  - Signal strength: HIGH, MEDIUM, LOW
  - Title, evidence, source URL
  - Detection timestamp (used to dedupe same-day signals)

✅ **Monitoring Events**:
  - Event type, urgency level, title, evidence, source URL
  - Event date (when the real-world event happened)
  - Detection timestamp (when we found it)
  - Processed status

### Partner Activation Data
✅ **Partners Activated**: Milestone tracking, activation status, activity scores
✅ **Buyer Committee Members**: Contact info, roles, decision authority, engagement metrics
✅ **Stakeholder Engagement**: Email opens, clicks, calls, demos attended
✅ **Activation Campaigns**: Multi-stakeholder outreach campaigns

---

## 2. FILTERING & VALIDATION THAT HAPPENS

### Prospect Filtering
| Filter | Location | Purpose |
|--------|----------|---------|
| `is_qualified_prospect()` | database.py | Removes apps with <10K installs; filters B2B-only products |
| `remove_non_prospects()` | database.py | Deletes regulatory bodies (RBI, SEBI), traditional banks (SBI, HDFC), foreign companies (Revolut, Wise) |
| `NON_PROSPECTS` list | config.py | 40+ hardcoded company names to exclude |
| `EXISTING_PARTNERS` | config.py | 12 known Blostem partners to exclude |
| `COMPETITORS` | config.py | 6 competitor companies (Stable Money, Deciml, etc.) |

### Data Enrichment Validation
| Validation | Location | How It Works |
|-----------|----------|--------------|
| Case-insensitive deduping | database.py `upsert_prospect()` | LOWER() comparison for name matching |
| Install count qualification | play_store.py | Rejects apps <1M installs; flags if <1K |
| Play Store score check | play_store.py | Filters apps with score <3.5 |
| Strict name matching | play_store.py | Prospect name must appear in app title or vice versa |
| Product flag detection | play_store.py, intelligence/llm_extractor.py | Keyword matching for 7 product categories |
| Description length check | play_store.py | Truncates to first 500 chars |

### Signal Deduplication
| Dedup Strategy | Scope | Limitation |
|----------------|-------|-----------|
| Duplicate signal check | `add_signal()` | Prevents same signal TYPE on same DAY |
| Article URL tracking | `is_article_processed()` | Prevents re-processing same article |
| Monitoring event dedup | `event_already_recorded()` | Prevents same (prospect_id, source_url) pair |

### LLM Extraction Filtering
The `extract_company_from_article()` function validates:
- Company is not a regulatory body (RBI, SEBI, NPCI, IRDAI)
- Company is not a traditional bank (SBI, HDFC, ICICI, Axis, Kotak)
- Company is not an existing partner or competitor
- Not purely fraud/security breach articles
- Not from other sectors (EV, D2C, healthcare, edtech)

---

## 3. PLACES WHERE BAD DATA COULD SLIP THROUGH

### 🔴 CRITICAL GAPS

#### 1. **Incomplete NON_PROSPECTS Filtering**
**Problem**: The filtering is partially case-sensitive and uses LIKE pattern matching
```python
conn.execute("DELETE FROM prospects WHERE name LIKE ?", (f"%{name}%",))
```
**Risk**: 
- "HDFC BANK" won't match "hdfc bank" (LIKE is case-insensitive in SQLite by default, actually OK)
- But new regulatory bodies or banks can enter the database before removal runs
- Companies with slightly different names slip through: "HDFC Bank Limited" vs "HDFC Bank"

**Impact**: Manual verification burden to catch after prospects are added

---

#### 2. **No Email/Contact Validation**
**Problem**: The `buyer_committee_members` table has email, linkedin_profile fields with **ZERO validation**
```python
CREATE TABLE buyer_committee_members (
    email TEXT,  -- Can be ANYTHING
    linkedin_profile TEXT,  -- Can be ANYTHING
)
```
**Risk**:
- Invalid email formats (user@, @domain, no @)
- LinkedIn URLs with typos or invalid formats
- Manual entry errors without format checking
- Nulls and empty strings accepted

**Impact**: Outreach emails will fail; LinkedIn enrichment won't work; contact attempts waste effort

---

#### 3. **No Phone Number Validation**
**Problem**: `partner_contacts` table accepts name/email with NO format checks
**Risk**: Phone numbers could be missing, incomplete, or malformed with no validation

---

#### 4. **Product Detection is Keyword-Based Only**
**Problem**: Play Store enrichment uses simple substring matching
```python
def detect_products_smart(description: str) -> dict:
    # Just checks if keywords appear in description
    products[product] = any(kw in desc_lower for kw in keywords)
```
**Risk**:
- False positives: "no fixed deposit feature" → detects `has_fd=True` 
- False negatives: App might mention FD in tagline, not description
- Truncated descriptions (500 chars) might cut off product info
- LLM extraction (`extract_company_from_article()`) has similar issue but with slightly smarter parsing

**Example failure**: Article says "We're partnering with XYZ to offer FDs" but description in DB doesn't mention FD → missed opportunity

---

#### 5. **No Validation of Install Count Format**
**Problem**: Install count is stored as a TEXT string like "1,000,000+"
```python
install_count = details.get('installs', 'Unknown')  # Could be anything
```
**Risk**:
- Could be "Unknown", "1,000,000+", or malformed values
- Comparison in `is_qualified_prospect()` uses exact equality:
  ```python
  if install_count and any(ind == install_count for ind in LOW_SCALE_INDICATORS):
      return False
  ```
- If Play Store returns "1000000+" instead of "1,000,000+", qualification check fails silently

**Impact**: Prospects get wrongly qualified/disqualified based on formatting differences

---

#### 6. **WHO Score Calculation is Complex & Opaque**
**Problem**: The scoring algorithm in `signals/scorer.py` has many edge cases:
- PRODUCT_GAP weight reduced to 15 (from 35) but this is just a number with unclear calibration
- Convergence bonus logic: "3+ signal types = +20 points" — why 20? Why 3?
- Displacement floor: `score = max(score, 40)` — why 40?
- Scale bonus thresholds: different bonuses for different install ranges

**Risk**:
- No documentation linking score to real conversion probability
- Hard to debug why prospect A is HOT (67) and prospect B is WARM (33)
- Changes to weights require re-running `recalculate_all_scores()` on all prospects
- No A/B testing framework to validate scoring accuracy

**Impact**: Sales team doesn't trust score; might ignore HOT prospects and chase WATCH prospects

---

#### 7. **Signal Type Detection Has No Validation**
**Problem**: The `extract_company_from_article()` LLM function can return ANY signal type in "expansion_signals"
```python
"expansion_signals": ["products they plan to add"],
```
There's **no whitelist validation** to ensure these match expected types.

**Risk**: LLM might return "FD-like products" or "deposits" instead of "FD"
- Downstream code expects: FD, RD, mutual_funds, stocks, bonds, UPI_credit, payments, lending, insurance
- Could get: "fixed income bonds", "credit facility", "deposit mechanism"

**Impact**: Signals not properly categorized; scoring breaks

---

#### 8. **Monitoring Events Can Record Duplicate Evidence**
**Problem**: `record_monitoring_event()` checks for duplicates by (prospect_id, source_url)
```python
if event_already_recorded(prospect_id, source_url):
    return False
```
**Risk**:
- Same article URL from different sources (news aggregators) might have different URLs
- Manual events (from researcher) have null source_url → can't dedupe
- Same event detected from 3 different news sources = 3 separate entries with redundant data

**Impact**: Bloated monitoring_events table; harder to identify unique issues

---

#### 9. **No Timestamp Consistency Validation**
**Problem**: Fields like `first_contact_at`, `last_engagement_at`, `detected_at` can be in any order
**Risk**:
- `last_engagement_at` before `first_contact_at` → data corruption
- `resolved_at` before `detected_at` → logical error
- No database-level constraints to prevent this

**Impact**: Business logic based on time sequences produces garbage results

---

#### 10. **No Mutual Exclusivity Validation for Roles**
**Problem**: Buyer committee member can have multiple boolean role flags:
```python
is_champion INTEGER DEFAULT 0,
is_blocker INTEGER DEFAULT 0,
is_economic_buyer INTEGER DEFAULT 0,
is_user INTEGER DEFAULT 0,
```
**Risk**:
- A person could be marked as both `is_champion` AND `is_blocker`
- No business logic prevents nonsensical combinations
- No constraint that at least ONE role is true

**Impact**: Playbook selection logic might use wrong persona; outreach becomes ineffective

---

#### 11. **Compliance Overrides Have No Expiration**
**Problem**: The `compliance_overrides` table tracks phrases we've overridden, but stores them forever:
```python
override_count INTEGER DEFAULT 1,
review_status TEXT DEFAULT 'TRACKING'
```
**Risk**:
- "Must verify" in a domain-specific email is flagged, we override once
- If we later decide "Must verify" should always be flagged, the override persists
- No expiration or review cycle

**Impact**: Compliance checking gradually becomes less effective as overrides accumulate

---

#### 12. **No Data Types Enforced**
**Problem**: Most "score" fields are stored as INTEGER but without constraints:
```python
who_score INTEGER DEFAULT 0,  -- Can be -1, 999, NULL
engagement_score REAL DEFAULT 0.0,  -- Can be -0.5, 2.1
activation_score INTEGER DEFAULT 0,  -- Unclear if 0-100 or 0-1000
```
**Risk**:
- who_score should be 0-100 but nothing prevents 150
- engagement_score should be 0-1 but might be 0-100
- Scale bonuses might go negative from bad math
- Comparisons like `if score >= 65:` silently fail if score is NULL

**Impact**: Reports and dashboards show garbage numbers; confidence in data decreases

---

## 4. RECOMMENDED VALIDATIONS TO ADD

### Tier 1: CRITICAL (Security + Data Integrity)

```python
# 1. Email validation for all contact tables
import re
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_email(email: str) -> bool:
    return email and re.match(EMAIL_REGEX, email) is not None

# 2. Install count normalization
def normalize_install_count(count: str) -> str:
    """Standardize install count format."""
    if not count or count == 'Unknown':
        return 'Unknown'
    # Ensure consistent format: "1,000,000+"
    count = count.replace(',', '')
    if count.endswith('+'):
        count = count[:-1]
    
    try:
        num = int(count)
        if num >= 1_000_000:
            return f"{num:,}+"
        elif num >= 1000:
            return f"{num:,}+"
        else:
            return f"{num:,}+"
    except:
        return 'Unknown'

# 3. WHO score bounds checking
def is_valid_who_score(score: int) -> bool:
    return isinstance(score, int) and 0 <= score <= 100

# 4. Timestamp ordering validation
def validate_timestamps(first: str, last: str) -> bool:
    """Ensure first <= last."""
    if first is None or last is None:
        return True
    return first <= last

# 5. Role exclusivity for buyer committee
def validate_buyer_roles(is_champion: int, is_blocker: int) -> bool:
    """Can't be both champion and blocker."""
    return not (is_champion == 1 and is_blocker == 1)
```

### Tier 2: HIGH (Data Quality)

```python
# 1. Signal type whitelist validation
VALID_SIGNAL_TYPES = {
    'PRODUCT_GAP',
    'FUNDING_EXPANSION',
    'COMPETITOR_MOVE',
    'LEADERSHIP_HIRE',
    'DISPLACEMENT'
}

def validate_signal_type(signal_type: str) -> bool:
    return signal_type in VALID_SIGNAL_TYPES

# 2. Product flag validation
VALID_PRODUCTS = {
    'has_fd', 'has_rd', 'has_bonds', 'has_upi_credit',
    'has_mutual_funds', 'has_stocks', 'has_insurance'
}

def validate_product_flags(flags: dict) -> bool:
    return all(k in VALID_PRODUCTS for k in flags.keys())

# 3. LinkedIn URL validation
import re
LINKEDIN_REGEX = r'linkedin\.com/(in|company)/[\w-]+'

def validate_linkedin_url(url: str) -> bool:
    return url is None or re.match(LINKEDIN_REGEX, url) is not None

# 4. Status value validation
VALID_STATUSES = {'HOT', 'WARM', 'WATCH'}

def validate_prospect_status(status: str) -> bool:
    return status in VALID_STATUSES
```

### Tier 3: MEDIUM (Deduplication & Consistency)

```python
# 1. Strict company name deduping
def normalize_company_name(name: str) -> str:
    """Normalize for comparison: lowercase, trim, remove Ltd/Inc/etc."""
    name = name.lower().strip()
    suffixes = [' ltd', ' limited', ' inc', ' incorporated', ' pvt', ' india']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name

# 2. Prevent duplicate monitoring events
def record_monitoring_event_safe(prospect_id, event_type, title, source_url):
    """
    Dedupe by (prospect_id, source_url) but also check title similarity.
    Prevents same article re-recorded with different titles.
    """
    # Existing check: (prospect_id, source_url)
    # NEW: Also check if we have event with similar title from last 7 days
    # Use string similarity (e.g., difflib.SequenceMatcher)
    pass

# 3. Prevent score calculations with missing data
def calculate_who_score_safe(prospect_id: int) -> tuple[int, str]:
    """
    Only calculate if prospect has:
    - At least one signal
    - Valid install_count
    - Description data
    """
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?",
            (prospect_id,)
        ).fetchone()
    
    # Validation
    if not prospect:
        return 0, 'WATCH'
    
    if prospect['install_count'] is None or prospect['install_count'] == 'Unknown':
        return 0, 'WATCH'  # Can't score without scale indicator
    
    if not prospect['description']:
        return 0, 'WATCH'  # Missing description = incomplete data
    
    # ... rest of calculation
    return calculate_who_score(prospect_id)
```

### Tier 4: NICE-TO-HAVE (Analytics & Debugging)

```python
# Add data quality metrics table
CREATE TABLE data_quality_metrics (
    id INTEGER PRIMARY KEY,
    check_name TEXT NOT NULL,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_records INTEGER,
    passing_records INTEGER,
    failing_records INTEGER,
    failure_reason TEXT,
    failure_examples TEXT  -- JSON list of examples
);

# Run nightly validation
def run_data_quality_checks():
    checks = [
        check_email_validity(),
        check_install_count_format(),
        check_timestamp_ordering(),
        check_who_score_bounds(),
        check_signal_types_valid(),
    ]
    
    for check in checks:
        name, total, passing, failing, examples = check
        record_check_result(name, total, passing, failing, examples)
```

---

## 5. DATA FLOW RISK MAP

### High-Risk Paths

| Data Path | Risk | Mitigation |
|-----------|------|-----------|
| **Manual entry → buyer_committee_members** | Invalid emails, typos, wrong roles | ✅ Add email regex validation, role constraints |
| **Play Store → install_count → WHO score** | Formatting differences break qualification | ✅ Normalize install counts; unit test threshold logic |
| **LLM → signal_type → scorer.py** | Signal type misspelling breaks weights | ✅ Whitelist signal types before insert |
| **News article → monitoring_event dedup** | Different URLs, same event → duplicates | ✅ Add title similarity dedup; review duplicates weekly |
| **compliance_overrides → email checks** | Overrides accumulate, weaken filtering | ✅ Add expiration dates; quarterly override audit |
| **Historical data → WHO score recalc** | Old data might be corrupt; recalc breaks | ✅ Add data quality check before recalc; backup scores |

---

## 6. SUMMARY: WHAT'S WORKING vs BROKEN

### ✅ What's Working
- Basic prospect deduping (case-insensitive name matching)
- Play Store enrichment with minimum scale filter
- Signal type diversity bonus encourages multi-signal prospects
- Monitoring event source URL dedup prevents immediate re-processing
- Partner table structure for activation tracking

### ❌ What's Broken
- **Email validation**: No format checking at all
- **Install count**: No format normalization; qualification logic fragile
- **Product detection**: Simple keyword matching; prone to false positives
- **Score calibration**: Weights and thresholds undocumented and unvalidated
- **Data type safety**: Scores can go out of bounds with no constraints
- **Timestamp logic**: No ordering validation
- **Role constraints**: Can be nonsensical combinations

### ⚠️ Workarounds Currently in Place
1. Manual review before outreach (catches some bad emails)
2. Sales team skepticism of scores (avoids over-relying on broken scoring)
3. Weekly prospect audits (catches non-prospect creep)
4. Signal type assumption (assuming LLM returns correct types)

**These workarounds should be replaced with systematic validation.**

---

## Implementation Priority

1. **Month 1**: Email validation + Install count normalization
2. **Month 2**: WHO score bounds checking + Signal type validation
3. **Month 3**: Timestamp ordering + Role constraints
4. **Month 4**: Data quality metrics dashboard
5. **Ongoing**: Weekly deduplication audits for edge cases
