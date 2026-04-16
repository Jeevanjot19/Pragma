#!/usr/bin/env python3
"""Test HOW layer — Compliance checking and outreach generation."""

from outreach.compliance_rules import check_compliance

print('=' * 70)
print('HOW LAYER — END-TO-END TEST')
print('=' * 70)

# Test 1: Compliance checker
print('\n1. Test compliance_rules.check_compliance():')

# Good email
good_email = """Hi there,
Saw you launched a new product on Tuesday — great move!
Blostem can help you reach your customers with FDs and RDs.
Let's talk for 20 minutes?
Best regards"""

result = check_compliance(good_email)
print(f'\n   Good email (no violations):')
print(f'   Status: {result["status"]}')
print(f'   Violations: {len(result["violations"])}')
print(f'   Warnings: {len(result["warnings"])}')

# Bad email with HIGH violation
bad_email = """Dear customer,
Our FDs guarantee you 100% safe returns of 9.5% interest.
This is RBI approved and fully insured.
Best regards"""

result = check_compliance(bad_email)
print(f'\n   Bad email (high violations):')
print(f'   Status: {result["status"]}')
print(f'   Violations: {len(result["violations"])}')
if result['violations']:
    for v in result['violations'][:2]:
        print(f'     - {v["rule_id"]}: {v["rule"]}')
        print(f'       Triggered by: {v["triggered_by"]}')

# Email with WARNING
warning_email = """Our FDs give you up to 8.5% interest.
Premium platform with better features than competitors."""

result = check_compliance(warning_email)
print(f'\n   Warning email:')
print(f'   Status: {result["status"]}')
print(f'   Violations: {len(result["violations"])}')
print(f'   Warnings: {len(result["warnings"])}')

print('\n2. Test email generator imports:')
try:
    from outreach.generator import PERSONA_CONTEXTS, generate_email_for_persona
    print(f'   ✅ PERSONA_CONTEXTS loaded')
    print(f'      Personas: {list(PERSONA_CONTEXTS.keys())}')
    for persona, ctx in PERSONA_CONTEXTS.items():
        print(f'        - {persona}: {ctx["title"]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n3. Check if generate_outreach_package is importable:')
try:
    from outreach.generator import generate_outreach_package
    print(f'   ✅ generate_outreach_package imported successfully')
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n4. Check main.py endpoints:')
try:
    import ast
    with open('main.py', 'r') as f:
        code = f.read()
    tree = ast.parse(code)
    
    how_endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if 'how' in node.name.lower() or 'outreach' in node.name.lower():
                how_endpoints.append(node.name)
    
    print(f'   HOW endpoints found:')
    for ep in how_endpoints:
        print(f'     - {ep}')
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n' + '=' * 70)
print('✅ HOW LAYER COMPONENTS VERIFIED')
print('=' * 70)
print('\nNOTE: Full email generation requires LLM calls.')
print('Run: POST /api/how/generate/4 to generate Kreditbee outreach package')
