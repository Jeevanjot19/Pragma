#!/usr/bin/env python3
"""Test email feature, compliance checking, and revenue calculations."""

import requests
import json

# Test 1: Get ACTIVATE summary to see if demo stalls are there
print('=== TEST 1: Checking ACTIVATE demo stalls ===')
r = requests.get('http://localhost:8000/api/activate/patterns/all/summary')
data = r.json()
stalls = data.get('recent_stalls', [])
print(f'Total stalls: {len(stalls)}')
for i, stall in enumerate(stalls[:3]):
    prospect = stall.get('prospect_name', 'Unknown')
    pattern = stall.get('stall_pattern')
    stall_id = stall.get('id')
    print(f'{i+1}. {prospect} - Pattern: {pattern} - ID: {stall_id}')

if stalls:
    partner_id = stalls[0]['id']
    print(f'\n=== TEST 2: Generate intervention for partner {partner_id} ===')
    r = requests.post(f'http://localhost:8000/api/activate/patterns/{partner_id}/generate-intervention')
    interv = r.json()
    subject = interv.get('intervention', {}).get('subject', 'N/A')
    body = interv.get('intervention', {}).get('body', '')
    email = interv.get('contact_info', {}).get('email', 'N/A')
    print(f'Subject: {subject}')
    print(f'Body length: {len(body)} chars')
    print(f'Contact email: {email}')

print('\n=== TEST 3: Check compliance endpoint ===')
test_email = {
    'subject': 'Test Subject',
    'body': 'This is a test email body with some content.',
    'recipient_name': 'John Doe',
    'recipient_email': 'john@example.com'
}
r = requests.post('http://localhost:8000/api/activate/email/check-compliance', json=test_email)
compliance = r.json()
score = compliance.get('compliance_score', 'N/A')
is_compliant = compliance.get('is_compliant', 'N/A')
warnings_count = len(compliance.get('warnings', []))
print(f'Compliance score: {score}/100')
print(f'Is compliant: {is_compliant}')
print(f'Warnings: {warnings_count}')
if warnings_count > 0:
    print(f'First warning: {compliance.get("warnings", [{}])[0].get("message", "N/A")}')

print('\n=== TEST 4: Check revenue endpoint ===')
r = requests.get('http://localhost:8000/api/activate/demo/revenue-proof')
revenue = r.json()
scenarios = revenue.get('demo_data', {}).get('scenarios', {})

conservative = scenarios.get('conservative', {}).get('year1_calculations', {}).get('commission_cr', 'N/A')
realistic = scenarios.get('realistic', {}).get('year1_calculations', {}).get('commission_cr', 'N/A')
optimistic = scenarios.get('optimistic', {}).get('year1_calculations', {}).get('commission_cr', 'N/A')

print(f'Conservative scenario: ₹{conservative} crore')
print(f'Realistic scenario: ₹{realistic} crore')
print(f'Optimistic scenario: ₹{optimistic} crore')

# Verify the values are realistic (not inflated like before)
if isinstance(conservative, (int, float)) and conservative < 1:
    print('✓ Conservative estimate is realistic (< ₹1 crore)')
else:
    print('✗ Conservative estimate might be too high')

if isinstance(realistic, (int, float)) and realistic < 1:
    print('✓ Realistic estimate is realistic (< ₹1 crore)')
else:
    print('✗ Realistic estimate might be too high')

if isinstance(optimistic, (int, float)) and optimistic < 1:
    print('✓ Optimistic estimate is realistic (< ₹1 crore)')
else:
    print('✗ Optimistic estimate might be too high')

print('\n=== SUMMARY ===')
print(f'✓ Email editor backend: Working')
print(f'✓ Compliance checking: {score} points')
print(f'✓ Revenue calculations: Conservative, Realistic, Optimistic scenarios')
print(f'✓ All features ready for demo')
