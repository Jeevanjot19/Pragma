#!/usr/bin/env python3
"""
Upload your local pragma.db (with good prospects) to Render.

This restores your 49 prospects from local development to the Render deployment.
Render's free tier uses ephemeral storage, so databases get wiped on redeploy.
Use this to copy your local DB up to Render's instance.

Usage:
    python upload_db_to_render.py

Requirements:
    - Local pragma.db file with your good data
    - Render instance running with the latest main.py (has /api/admin/restore-db)
"""

import base64
import json
import requests
import os
import sys

# Configuration
LOCAL_DB_PATH = "pragma.db"
RENDER_URL = "https://pragma-5xki.onrender.com"
RESTORE_ENDPOINT = f"{RENDER_URL}/api/admin/restore-db"

def main():
    print("=" * 70)
    print("Pragma Database Upload to Render")
    print("=" * 70)
    
    # Check local database exists
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"❌ ERROR: Local database not found at {LOCAL_DB_PATH}")
        print("   Make sure you run this from the Blostem directory")
        sys.exit(1)
    
    file_size = os.path.getsize(LOCAL_DB_PATH)
    print(f"✓ Found local database: {LOCAL_DB_PATH} ({file_size:,} bytes)")
    
    # Encode to base64
    print("\n📦 Encoding database to base64...")
    try:
        with open(LOCAL_DB_PATH, 'rb') as f:
            db_bytes = f.read()
        db_b64 = base64.b64encode(db_bytes).decode('utf-8')
        print(f"   Encoded size: {len(db_b64):,} characters")
    except Exception as e:
        print(f"❌ ERROR encoding database: {e}")
        sys.exit(1)
    
    # Upload to Render
    print(f"\n📡 Uploading to Render... ({RESTORE_ENDPOINT})")
    try:
        response = requests.post(
            RESTORE_ENDPOINT,
            json={"db_data": db_b64},
            timeout=120  # 2 minute timeout for upload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"\n📊 Database restored on Render:")
            print(f"   - Size: {result.get('size_bytes', 0):,} bytes")
            print(f"   - Prospects: {result.get('prospects_in_db', 0)}")
            print(f"   - Signals: {result.get('signals_in_db', 0)}")
            
            print("\n" + "=" * 70)
            print("NEXT STEPS:")
            print("=" * 70)
            print("1. Go to https://pragma-5xki.onrender.com")
            print("2. Click 'Run Discovery' to clean up bad seed data")
            print("   (This calls POST /api/admin/clean-seeds)")
            print("3. Refresh to see your 49 prospects with good scores!")
            print("\nOR manually call:")
            print(f"   POST {RENDER_URL}/api/admin/clean-seeds")
            print("\nOR just refresh - the data is already there!")
            return 0
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return 1
            
    except requests.exceptions.Timeout:
        print(f"❌ Upload timed out (took >120 seconds)")
        print("   The database file may be too large, or Render may be slow")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"❌ Failed to connect to Render")
        print(f"   Check that the URL is correct: {RENDER_URL}")
        print(f"   And that the server is running")
        return 1
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
