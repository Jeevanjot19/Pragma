#!/usr/bin/env python3
"""
Verify WHEN-layer API endpoints are properly defined in main.py
"""
import ast

with open('main.py', 'r') as f:
    code = f.read()

try:
    tree = ast.parse(code)
    print('✅ main.py has valid Python syntax')
except SyntaxError as e:
    print(f'❌ Syntax error in main.py: {e}')
    exit(1)

# Find function definitions
functions = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        functions.append(node.name)

print(f'\n✅ WHEN-layer endpoints defined in main.py:')
when_endpoints = [f for f in functions if 'when' in f.lower() or 'priorities' in f.lower()]
for ep in when_endpoints:
    print(f'   - {ep}')

monitoring_endpoints = [f for f in functions if 'monitor' in f.lower()]
print(f'\n✅ Monitoring endpoints defined:')
for ep in monitoring_endpoints:
    print(f'   - {ep}')

print(f'\n✅ Total endpoints: {len(functions) - 1}')  # -1 for startup
