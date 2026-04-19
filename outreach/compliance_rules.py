"""
HOW Layer — Compliance Engine (v2)

A holistic compliance checker that evaluates emails across five dimensions:
  1. Regulatory safety  — RBI, SEBI, DICGC, IRDAI hard rules
  2. Tone calibration   — collaborative vs. pushy/aggressive
  3. Substantiation     — claims backed by evidence, not buzzwords
  4. Structural quality — subject, CTA, length, formatting
  5. Personalization    — does it feel written for a person, or blasted at a list?

Design principles:
  - Score from 0–100 (not binary pass/fail)
  - Surface *why* something is flagged, not just *that* it is
  - Never flag legitimate business language as a violation
  - Distinguish severity: CRITICAL (blocks sending) vs. WARNING (review) vs. TIP (improve)
  - Track override history to prevent alert fatigue (Issue 2 Fix)
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Literal
from database import get_db


# ─────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────

Severity = Literal["CRITICAL", "WARNING", "TIP"]

@dataclass
class Finding:
    code: str
    severity: Severity
    category: str
    headline: str
    detail: str
    triggered_by: list[str] = field(default_factory=list)
    fix: str = ""


# ─────────────────────────────────────────────
# Regulatory rules (CRITICAL when triggered)
# These are hard legal requirements for fintech outreach in India.
# ─────────────────────────────────────────────

REGULATORY_PATTERNS: list[dict] = [
    {
        "code": "R001",
        "category": "Guaranteed Returns",
        "patterns": [
            r"\bguaranteed?\s+(returns?|interest|income|profits?)\b",
            r"\bassured?\s+(returns?|interest|income)\b",
            r"\bfixed\s+returns?\b",
            r"\b100%\s+(safe|secure|guaranteed?)\b",
            r"\bno\s+risk\b",
            r"\bzero[- ]risk\b",
        ],
        "headline": "Guaranteed returns language",
        "detail": "RBI prohibits implying deposits or investments carry guaranteed returns. Even high-quality FDs carry institutional risk.",
        "fix": 'Use "up to X% p.a. (subject to bank terms)" or "competitive rates from partner banks"',
    },
    {
        "code": "R002",
        "category": "DICGC Misrepresentation",
        "patterns": [
            r"\bfully\s+(insured|safe|protected)\b",
            r"\bcompletely\s+(insured|safe|protected)\b",
            r"\b100%\s+insured\b",
            r"\ball\s+(your\s+)?(deposits?|funds?)\s+(are\s+)?insured\b",
        ],
        "headline": "Overstated DICGC coverage",
        "detail": "DICGC insures up to ₹5 lakh per depositor per bank — not 100% of any amount.",
        "fix": 'Say "insured up to ₹5 lakh per depositor under DICGC" and nothing broader',
    },
    {
        "code": "R003",
        "category": "False Regulatory Approval",
        "patterns": [
            r"\brbi[- ](approved?|certified|endorsed|licensed)\b",
            r"\bsebi[- ](approved?|certified|endorsed)\b",
            r"\bregulated\s+by\s+rbi\b",
            r"\bnpci[- ]certified\b",
        ],
        "headline": "False/misleading regulatory approval claim",
        "detail": "Implying RBI or SEBI has approved your product (vs. your entity being registered) is a regulatory violation.",
        "fix": 'Use "RBI-compliant architecture" or "working with RBI-registered NBFCs/banks"',
    },
    {
        "code": "R004",
        "category": "Unqualified Interest Rates",
        "patterns": [
            # Catches bare "8.5% interest" or "earn 9%" without qualifiers
            r"\b(earn|get|offering?|giving)\s+\d+(?:\.\d+)?\s*%\s*(p\.?a\.?|interest|returns?)?\b(?!\s*(up\s+to|approximately|around|subject))",
            r"\b\d+(?:\.\d+)?\s*%\s*(p\.?a\.?|per\s+annum|annual(ly)?)\s*(?!up\s+to|approximately|around)",
        ],
        "headline": "Interest rate without qualifier",
        "detail": "Specific rates must be qualified: rates vary by bank, tenure, and market conditions.",
        "fix": 'Use "up to X% p.a." or "rates currently ranging from X% to Y% depending on bank and tenure"',
    },
    {
        "code": "R005",
        "category": "Misleading Competitor Comparison",
        "patterns": [
            r"\bbetter\s+than\s+(stable\s+money|deciml|wint|jiraaf|grip)\b",
            r"\b(stable\s+money|deciml|wint\s+wealth|jiraaf|grip\s+invest)\s+alternative\b",
            r"\breplace\s+(stable\s+money|deciml|wint|jiraaf|grip)\b",
            r"\bunlike\s+(stable\s+money|deciml|wint|jiraaf|grip)\b",
        ],
        "headline": "Potentially misleading competitor comparison",
        "detail": "Factual comparisons are fine; subjective superiority claims without evidence can be challenged.",
        "fix": "Remove the comparison, or state factual differentiation with specific evidence",
    },
]


# ─────────────────────────────────────────────
# Tone patterns (WARNING)
# Aggressive/pushy language that damages response rates.
# ─────────────────────────────────────────────

AGGRESSIVE_PATTERNS: list[dict] = [
    {
        "code": "T001",
        "patterns": [
            r"\b(don'?t\s+(miss|wait|delay|hesitate))\b",
            r"\b(last\s+chance|now\s+or\s+never|limited\s+time)\b",
            r"\b(act\s+now|respond\s+immediately|urgent(ly)?)\b",
            r"\b(hurry|rush|quickly)\b",
        ],
        "headline": "FOMO / scarcity pressure",
        "detail": "Urgency language in cold B2B outreach feels manipulative and reduces credibility with technical and finance decision-makers.",
    },
    {
        "code": "T002",
        "patterns": [
            r"\b(must|mandatory|required|you\s+need\s+to)\b",
            r"\byou\s+should\s+(?!consider|think|look|check)\b",  # "you should respond" not "you should consider"
            r"\bdemand(ing|s)?\b",
            r"\bexpect\s+(a\s+)?response\b",
        ],
        "headline": "Directive / commanding tone",
        "detail": "Telling a VP or CTO what they 'must' do creates friction. Offer, don't instruct.",
    },
    {
        "code": "T003",
        "case_sensitive": True,
        "patterns": [
            r"!{2,}",
            r"(?<!\?)\?{2,}",
            r"[A-Z]{6,}",
        ],
        "headline": "Spam-signal patterns: excessive capitalization or punctuation",
        "detail": "Multiple exclamations, question marks, or long runs of capital letters signal low-quality outreach.",
    },
    {
        "code": "T004",
        "patterns": [
            r"(?i)dear\s+(sir|ma'?am|madam|friend|valued\s+(customer|partner|client))\b",
            r"^(hi|hello|hey)\s*[,!.]?\s*$",
        ],
        "headline": "Impersonal or dated salutation",
        "detail": '"Dear Sir/Madam" and "Hi," with no name signals a mass blast, not a targeted email.',
    },
]


# ─────────────────────────────────────────────
# Substantiation patterns (WARNING)
# Claims that need evidence
# ─────────────────────────────────────────────

UNSUBSTANTIATED_PATTERNS: list[dict] = [
    {
        "code": "S001",
        "patterns": [
            r"\b(best[- ]in[- ]class|industry[- ]leading|world[- ]class|top[- ]tier|best\s+in\s+the\s+industry)\b",
            r"\b(pioneer(ing)?|disruptive|innovative|cutting[- ]edge|state[- ]of[- ]the[- ]art)\b",
            r"\bunbeatable\s+(?:quality|performance|reliability)\b",
        ],
        "headline": "Unsubstantiated superlative",
        "detail": "Superlatives without supporting data are dismissed by technical buyers. Replace with specifics.",
    },
    {
        "code": "S002",
        "patterns": [
            r"\b(transform(ing|ative|ation)|revolutionize|disrupt(ing)?)\b",
            r"\b(unlock\s+your\s+potential|supercharge|10x\s+your)\b",
            r"\bfully\s+automated\b(?!\s+(compliance|kyc|reporting))",
        ],
        "headline": "Vague transformation claim",
        "detail": "Fintech buyers are sceptical of transformation rhetoric. Name the specific outcome instead.",
    },
]


# ─────────────────────────────────────────────
# Signal leakage patterns (WARNING)
# Mentioning how you found them / what you're tracking
# ─────────────────────────────────────────────

SIGNAL_LEAKAGE_PATTERNS: list[dict] = [
    {
        "code": "L001",
        "patterns": [
            r"\bplay\s+store\b",
            r"\bapp\s+(description|listing|update|store\s+listing)\b",
            r"\binstall\s+(count|number|base)\b",
            r"\bapp\s+store\s+(change|update|rank)\b",
        ],
        "headline": "Reveals Play Store surveillance",
        "detail": "Mentioning that you track their app store listing feels invasive and damages trust. Frame the insight as category knowledge instead.",
    },
    {
        "code": "L002",
        "patterns": [
            r"\bwe\s+noticed\s+(your|that\s+you)\b(?=.*?(update|change|launch|new|add))",
            r"\bwe\s+(saw|spotted|detected|found|tracked)\b",
            r"\byour\s+(recent\s+)?(update|change|modification)\s+(to\s+)?(your\s+)?(app|product|platform|description)\b",
            r"\bmonitoring\s+your\b",
        ],
        "headline": "Surveillance framing",
        "detail": "Phrases like \"we noticed your update\" signal automated monitoring, which feels creepy. Lead with category insight instead.",
    },
    {
        "code": "L003",
        "patterns": [
            r"\byour\s+(install(ation)?\s+)?(count|number|base|data)\b",
            r"\bbased\s+on\s+your\s+(data|metrics|signals?|numbers?)\b",
            r"\bwe\s+(analyzed|analysed|scraped|pulled)\b",
        ],
        "headline": "Data collection disclosure",
        "detail": "Revealing that you scraped or analyzed their data without consent raises PDPA/DPDP concerns and destroys rapport.",
    },
]


# ─────────────────────────────────────────────
# Structure checks
# ─────────────────────────────────────────────

def _check_structure(subject: str, body: str) -> list[Finding]:
    findings = []

    # Subject line
    if not subject or len(subject.strip()) < 10:
        findings.append(Finding(
            code="Q001", severity="WARNING", category="Structure",
            headline="Subject line is too short or missing",
            detail="A subject under 10 characters won't be opened. Be specific about the value proposition.",
            fix="Try: '[Company] + [Product] = [Outcome]' format, e.g. 'Jar + FD API = new revenue in 14 days'",
        ))
    elif len(subject) > 60:
        findings.append(Finding(
            code="Q002", severity="TIP", category="Structure",
            headline="Subject line may truncate on mobile",
            detail=f"At {len(subject)} chars, most mobile clients show ~50-60 chars. The current subject might truncate.",
            fix="Trim to your most compelling 55 characters",
        ))

    if subject and subject.strip().endswith('?'):
        findings.append(Finding(
            code="Q003", severity="TIP", category="Structure",
            headline="Question-only subject lines underperform",
            detail="Subject lines that lead with a question have ~15% lower open rates vs. benefit-focused subjects in B2B.",
            fix="Lead with the outcome, not the question",
        ))

    # Body length
    word_count = len(body.split())
    if word_count < 30:
        findings.append(Finding(
            code="Q004", severity="WARNING", category="Structure",
            headline="Email body is too short",
            detail=f"At {word_count} words, this email doesn't give the reader enough to act on.",
            fix="A B2B cold email needs: hook → specific value prop → proof point → single clear CTA. Aim for 80–150 words.",
        ))
    elif word_count > 350:
        findings.append(Finding(
            code="Q005", severity="TIP", category="Structure",
            headline="Email is long — consider trimming",
            detail=f"At {word_count} words, response rates typically drop. Decision-makers read in <30 seconds.",
            fix="Cut to your 3 most important points. Save the detail for the call.",
        ))

    # CTA check
    cta_phrases = [
        "call", "chat", "meet", "15 minutes", "20 minutes", "30 minutes",
        "demo", "calendar", "schedule", "connect", "reply", "let me know",
        "thoughts?", "interested?", "available", "book",
    ]
    has_cta = any(phrase in body.lower() for phrase in cta_phrases)
    if not has_cta:
        findings.append(Finding(
            code="Q006", severity="WARNING", category="Structure",
            headline="No clear call-to-action detected",
            detail="Without a specific next step, even an interested reader won't know what to do.",
            fix='Add a low-friction ask: "Would a 15-minute call this week make sense?" or a calendar link',
        ))

    # Multiple CTAs
    strong_cta_count = sum(1 for p in ["schedule", "book", "click here", "sign up", "register"] if p in body.lower())
    if strong_cta_count >= 3:
        findings.append(Finding(
            code="Q007", severity="WARNING", category="Structure",
            headline="Multiple competing CTAs",
            detail="More than two action options creates decision paralysis. Pick one primary ask.",
            fix="One email, one ask.",
        ))

    # Link count
    links = re.findall(r'https?://\S+', body)
    if len(links) > 2:
        findings.append(Finding(
            code="Q008", severity="WARNING", category="Structure",
            headline=f"Too many links ({len(links)})",
            detail="Emails with 3+ links trigger spam filters and feel like marketing blasts.",
            fix="Keep to 1 link max in cold outreach — your calendar or a single resource",
        ))

    return findings


# ─────────────────────────────────────────────
# Personalization signals
# ─────────────────────────────────────────────

def _check_personalization(subject: str, body: str, recipient_name: str | None, company_name: str | None) -> list[Finding]:
    findings = []

    # Generic opener patterns
    generic_openers = [
        r"^(hi|hello|hey)\s*,?\s*(there|team|everyone|all)[\s,!.]",
        r"^i\s+(hope|trust)\s+this\s+(email\s+)?(finds|reaches)\s+you\s+well",
        r"^my\s+name\s+is\b",
        r"^i\s+am\s+reaching\s+out\s+to\s+you\b",
        r"^i\s+came\s+across\s+your\s+(company|organization|firm)\b",
        r"^we\s+are\s+a\s+leading\b",
        r"^i\s+wanted\s+to\s+connect\b",
        r"^i\s+would\s+like\s+to\s+introduce\b",
    ]
    body_lower = body.lower().strip()
    for pattern in generic_openers:
        if re.match(pattern, body_lower):
            findings.append(Finding(
                code="P001", severity="WARNING", category="Personalization",
                headline="Generic opener detected",
                detail='Openers like "I hope this finds you well" or "I wanted to connect" are instantly recognized as templates.',
                fix="Start with a specific, relevant observation about their business or a mutual point of context.",
            ))
            break

    # Missing name
    if recipient_name and recipient_name.strip():
        name_first = recipient_name.split()[0]
        if name_first.lower() not in body.lower() and name_first.lower() not in subject.lower():
            findings.append(Finding(
                code="P002", severity="TIP", category="Personalization",
                headline="Recipient's name not used",
                detail=f"Using {name_first}'s name (at least in the salutation) increases response rates by ~20%.",
                fix=f'Add "{name_first}," as your opening line',
            ))

    # Missing company reference
    if company_name and company_name.strip():
        if company_name.lower() not in body.lower() and company_name.lower() not in subject.lower():
            findings.append(Finding(
                code="P003", severity="WARNING", category="Personalization",
                headline="Company name not mentioned",
                detail="Not referencing the recipient's company makes the email feel generic.",
                fix=f"Mention {company_name} in context — e.g., their product category or a relevant business moment.",
            ))

    return findings


# ─────────────────────────────────────────────
# Core scoring engine
# ─────────────────────────────────────────────

def _run_pattern_checks(body: str, pattern_set: list[dict], severity: Severity) -> list[Finding]:
    findings = []

    for rule in pattern_set:
        matched = []
        
        # FIX: For case_sensitive rules (like T003), use the original body
        # Otherwise, convert to lowercase for pattern matching
        case_sensitive = rule.get("case_sensitive", False)
        text_to_search = body if case_sensitive else body.lower()
        
        # For case-sensitive, don't use re.IGNORECASE; for others, do
        case_flag = 0 if case_sensitive else re.IGNORECASE

        for pat in rule["patterns"]:
            for m in re.finditer(pat, text_to_search, case_flag | re.MULTILINE):
                matched.append(m.group(0))
        
        if matched:
            triggered = list(set(matched))[:3]  # show up to 3 examples
            findings.append(Finding(
                code=rule["code"],
                severity=severity,
                category=rule.get("category", ""),
                headline=rule["headline"],
                detail=rule.get("detail", ""),
                triggered_by=triggered,
                fix=rule.get("fix", ""),
            ))
    return findings


def _calculate_score(findings: list[Finding]) -> int:
    """
    Score starts at 100, deducted by severity.
    CRITICAL: -25 each
    WARNING:  -8 each
    TIP:      -2 each
    """
    score = 100
    for f in findings:
        if f.severity == "CRITICAL":
            score -= 25
        elif f.severity == "WARNING":
            score -= 8
        elif f.severity == "TIP":
            score -= 2
    return max(0, min(100, score))


def _apply_override_demotions(findings: list[Finding]) -> list[Finding]:
    """
    If a rule has been manually overridden 3+ times, demote CRITICAL→WARNING.
    Prevents alert fatigue for legitimate edge cases.
    """
    try:
        with get_db() as conn:
            overrides = {
                row["rule_id"]: row["override_count"]
                for row in conn.execute("SELECT * FROM compliance_overrides").fetchall()
            }
    except Exception:
        overrides = {}

    result = []
    for f in findings:
        if overrides.get(f.code, 0) >= 3 and f.severity == "CRITICAL":
            # Demote to WARNING with a note
            demoted = Finding(
                code=f.code,
                severity="WARNING",
                category=f.category,
                headline=f.headline + " (previously overridden 3× — now advisory)",
                detail=f.detail,
                triggered_by=f.triggered_by,
                fix=f.fix,
            )
            result.append(demoted)
        else:
            result.append(f)
    return result


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def check_compliance(
    body: str,
    subject: str = "",
    recipient_name: str | None = None,
    company_name: str | None = None,
) -> dict:
    """
    Run the full compliance check on an email.

    Returns:
    {
        "status":    "BLOCKED" | "WARNING" | "CLEAR",
        "score":     0–100,
        "is_sendable": bool,
        "violations": [...],   # CRITICAL findings
        "warnings":   [...],   # WARNING findings
        "tips":       [...],   # TIP findings
        "summary":   "..."     # human-readable one-liner
    }
    """
    all_findings: list[Finding] = []

    # Run all checks
    all_findings += _run_pattern_checks(body, REGULATORY_PATTERNS, "CRITICAL")
    all_findings += _run_pattern_checks(body, AGGRESSIVE_PATTERNS, "WARNING")
    all_findings += _run_pattern_checks(body, UNSUBSTANTIATED_PATTERNS, "WARNING")
    all_findings += _run_pattern_checks(body, SIGNAL_LEAKAGE_PATTERNS, "WARNING")
    all_findings += _check_structure(subject, body)
    all_findings += _check_personalization(subject, body, recipient_name, company_name)

    # Apply override demotions
    all_findings = _apply_override_demotions(all_findings)

    violations = [f for f in all_findings if f.severity == "CRITICAL"]
    warnings   = [f for f in all_findings if f.severity == "WARNING"]
    tips       = [f for f in all_findings if f.severity == "TIP"]

    score = _calculate_score(all_findings)
    is_blocked = len(violations) > 0
    status = "BLOCKED" if is_blocked else ("WARNING" if warnings else "CLEAR")

    # Summary sentence
    if is_blocked:
        summary = f"{len(violations)} regulatory issue(s) must be fixed before sending."
    elif warnings:
        summary = f"Sendable but {len(warnings)} issue(s) will hurt response rates."
    elif tips:
        summary = f"Looks good — {len(tips)} small improvement(s) available."
    else:
        summary = "Email passes all checks. Ready to send."

    def finding_to_dict(f: Finding) -> dict:
        return {
            "code": f.code,
            "severity": f.severity,
            "category": f.category,
            "headline": f.headline,
            "detail": f.detail,
            "triggered_by": f.triggered_by,
            "fix": f.fix,
        }

    return {
        "status": status,
        "score": score,
        "is_sendable": not is_blocked,
        # Legacy field aliases so existing frontend code doesn't break
        "violations": [finding_to_dict(f) for f in violations],
        "warnings":   [finding_to_dict(f) for f in warnings],
        "tips":       [finding_to_dict(f) for f in tips],
        "summary": summary,
    }


def log_compliance_override(rule_id: str, triggered_phrase: str) -> None:
    """
    Record a manual override so the same rule is demoted after 3 occurrences.
    """
    try:
        with get_db() as conn:
            existing = conn.execute(
                "SELECT * FROM compliance_overrides WHERE rule_id = ?", (rule_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE compliance_overrides SET override_count = override_count + 1, last_override_at = CURRENT_TIMESTAMP WHERE rule_id = ?",
                    (rule_id,),
                )
            else:
                conn.execute(
                    "INSERT INTO compliance_overrides (rule_id, triggered_phrase, override_count, last_override_at, first_override_at) VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (rule_id, triggered_phrase),
                )
            conn.commit()
    except Exception as e:
        print(f"Warning: could not log compliance override: {e}")
