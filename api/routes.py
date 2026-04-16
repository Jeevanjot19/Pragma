"""
API Routes - Currently all routes are in main.py (800+ lines).
This file exists for future refactoring to separate concerns.

TODO: Migrate routes to this file to improve code organization:
  - /api/discover (WHO layer)
  - /api/prospects/* (WHO queries)
  - /api/how/* (HOW layer email generation)
  - /api/buyer-committee/* (ACTIVATE Innovation 1)
  - /api/bottleneck/* (ACTIVATE Innovation 2)
  - /api/playbooks/* (ACTIVATE Innovation 3)
  - /api/campaigns/* (ACTIVATE Innovation 4)

Status: Deferred pending stability validation. All endpoints currently 
hardwired in main.py to ensure 63/63 tests passing before refactoring.

See main.py for all current route implementations.
"""

# Routes will be consolidated here after testing freeze
