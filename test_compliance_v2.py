"""
Test suite for compliance_rules.py v2 — validates all regulatory, tone, substantiation rules
"""

from outreach.compliance_rules import check_compliance

# Test cases: (email_body, subject, expected_status, description)
test_cases = [
    # ✅ CLEAR emails
    (
        "Hi Sarah,\n\nJar is a growing neobank platform. We've built a plug-and-play FD SDK that integrates in 7 days.\n\nWould a 20-minute call this week work?",
        "Jar + FD API = new revenue in 14 days",
        "CLEAR",
        "✅ Natural, personalized email — no violations"
    ),
    
    # 🚫 CRITICAL: Guaranteed returns
    (
        "Our FD product guarantees returns of 8.5% with zero risk and 100% safety.",
        "Guaranteed Returns Opportunity",
        "BLOCKED",
        "🚫 Guaranteed returns language + zero risk (R001, R002)"
    ),
    
    # 🚫 CRITICAL: False RBI approval
    (
        "We are RBI-approved and SEBI-certified. Our product is officially licensed.",
        "RBI-Approved Solution",
        "BLOCKED",
        "🚫 False RBI approval claim (R003)"
    ),
    
    # 🚫 CRITICAL: Unqualified interest rate
    (
        "Earn 8.5% interest on fixed deposits with our platform.",
        "FD Interest Opportunity",
        "BLOCKED",
        "🚫 Specific rate without qualifier (R004)"
    ),
    
    # ⚠️ WARNING: FOMO/urgency language
    (
        "Don't miss this opportunity! Act now — limited spots available. This is your last chance.",
        "Limited Time Offer",
        "WARNING",
        "⚠️ FOMO pressure tactics (T001)"
    ),
    
    # ⚠️ WARNING: Surveillance framing
    (
        "We noticed your Play Store listing and saw that you recently added a savings feature. We've been monitoring your app updates.",
        "Your Recent App Update",
        "WARNING",
        "⚠️ Surveillance language + Play Store mention (L001, L002)"
    ),
    
    # ⚠️ WARNING: Directive tone
    (
        "You must integrate our FD SDK immediately. You need to respond within 24 hours.",
        "Mandatory Integration Required",
        "WARNING",
        "⚠️ Commanding tone (T002)"
    ),
    
    # ⚠️ WARNING: Generic opener
    (
        "I hope this email finds you well. I wanted to reach out to you about a great opportunity.",
        "A Great Opportunity",
        "WARNING",
        "⚠️ Generic template opener (P001)"
    ),
    
    # ⚠️ WARNING: Unsubstantiated claims
    (
        "We are the industry-leading provider of financial infrastructure. Our revolutionary platform will transform your business.",
        "Revolutionary Financial Solution",
        "WARNING",
        "⚠️ Superlatives without evidence (S001, S002)"
    ),
    
    # ✅ CLEAR with TIPs: Good email but with suggestions
    (
        "MobiKwik is the leading payments platform in India. We've built integration for FDs that takes 7 days. Interested in a 20-minute call?",
        "New Revenue Stream",
        "CLEAR",
        "✅ Sendable, with structural suggestions"
    ),
    
    # 🚫 CRITICAL: Excessive caps (T003 — now case-sensitive)
    (
        "THIS IS AN AMAZING OPPORTUNITY!! Don't miss out on our REVOLUTIONARY PLATFORM!!!",
        "INCREDIBLE OFFER",
        "BLOCKED",
        "🚫 Excessive ALL CAPS and exclamation marks (T003)"
    ),
    
    # ✅ CLEAR: Legitimate acronyms NOT flagged (Q003 case-sensitive fix)
    (
        "DICGC insures deposits up to ₹5 lakh. Your NBFC can offer FDs via our API. CFO approval takes one call.",
        "Banking Infrastructure",
        "CLEAR",
        "✅ Legitimate acronyms (DICGC, NBFC, CFO) NOT flagged as spam"
    ),
]

print("\n" + "="*80)
print("COMPLIANCE ENGINE v2 — TEST SUITE")
print("="*80 + "\n")

passed = 0
failed = 0

for body, subject, expected_status, description in test_cases:
    result = check_compliance(body, subject=subject, company_name="Test Company")
    actual_status = result["status"]
    
    status_icon = "✅" if actual_status == expected_status else "❌"
    if actual_status == expected_status:
        passed += 1
    else:
        failed += 1
    
    print(f"{status_icon} {description}")
    print(f"   Expected: {expected_status} | Actual: {actual_status} | Score: {result['score']}/100")
    
    if result["violations"]:
        print(f"   Violations: {[v['code'] for v in result['violations']]}")
    if result["warnings"]:
        print(f"   Warnings: {[w['code'] for w in result['warnings']]}")
    print()

print("="*80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("="*80)
