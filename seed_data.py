"""
Seed data for Render deployment.
Pre-populates database with prospects so dashboard works without running discovery.
"""

import sqlite3
from datetime import datetime

SEED_PROSPECTS = [
    ("Kreditbee", "fintech", "kreditbee.com", "com.inflame.kreditbee", "10,000,000+", "Instant credit on UPI", 75, 45, "HOT"),
    ("PhonePe", "fintech", "phonepe.com", "com.phonepe", "100,000,000+", "Digital payment platform", 85, 55, "HOT"),
    ("Groww", "fintech", "groww.in", "com.groww", "5,000,000+", "Investment platform", 65, 35, "WARM"),
    ("Upstox", "fintech", "upstox.com", "com.upstox", "10,000,000+", "Stock trading platform", 70, 40, "WARM"),
    ("Jupiter", "fintech", "jupiter.money", "money.jupiter.app", "5,000,000+", "Digital banking", 68, 38, "WARM"),
    ("Fi Money", "fintech", "fi.money", "com.fifinity", "1,000,000+", "Savings platform", 55, 28, "WARM"),
    ("Arya.ag", "agtech", "arya.ag", "com.arya.main", "500,000+", "Agricultural services", 50, 25, "WATCH"),
    ("OneCard", "fintech", "onecard.io", "com.onecard", "1,000,000+", "Credit card", 60, 32, "WARM"),
    ("Niyo Global", "fintech", "niyoglobal.com", "com.niyo.globalmoney", "500,000+", "International payments", 58, 30, "WARM"),
    ("PayU", "fintech", "payu.in", "com.payu.payments", "5,000,000+", "Payment processing", 72, 42, "HOT"),
    ("Cashfree", "fintech", "cashfree.com", "com.cashfree.payments", "100,000+", "Payment gateway", 65, 35, "WARM"),
    ("Razorpay", "fintech", "razorpay.com", "com.razorpay", "1,000,000+", "Payment infrastructure", 78, 48, "HOT"),
    ("Instamojo", "fintech", "instamojo.com", "com.instamojo.app", "500,000+", "Payments & invoicing", 60, 32, "WARM"),
    ("BharatPe", "fintech", "bharatpe.in", "com.bharatpe", "5,000,000+", "Digital payments", 68, 38, "WARM"),
    ("Yubi", "fintech", "getyubi.com", "com.yubi", "1,000,000+", "Credit services", 62, 33, "WARM"),
    ("Slice", "fintech", "sliceit.me", "com.slice", "1,000,000+", "Digital lending", 64, 34, "WARM"),
    ("ZestMoney", "fintech", "zestmoney.in", "com.zestmoney.app", "1,000,000+", "Buy-now-pay-later", 66, 36, "WARM"),
    ("Walnut", "fintech", "walnut.gg", "in.walnut.app", "100,000+", "Finance management", 55, 28, "WATCH"),
    ("Moneyview", "fintech", "moneyview.in", "com.moneyview", "5,000,000+", "Digital lending", 63, 33, "WARM"),
    ("Lendenclub", "fintech", "lendenclub.com", "com.lendenclub", "100,000+", "Peer lending", 52, 26, "WATCH"),
    ("IndiaStack", "fintech", "indiastack.org", None, None, "Fintech infrastructure", 70, 40, "WARM"),
    ("NAVI", "fintech", "naviapp.io", "com.navi.app", "5,000,000+", "Digital lending", 65, 35, "WARM"),
    ("LazyPay", "fintech", "lazypay.in", "com.lazypay", "5,000,000+", "Buy-now-pay-later", 62, 32, "WARM"),
    ("KreditBee", "fintech", "kreditbee.com", "com.kreditbee", "10,000,000+", "Instant credit", 72, 42, "HOT"),
    ("CoinSwitch", "fintech", "coinswitch.co", "com.coinswitch.me", "1,000,000+", "Crypto exchange", 58, 30, "WATCH"),
]

def seed_database():
    """Populate initial prospects for Render deployment."""
    conn = sqlite3.connect('pragma.db')
    c = conn.cursor()
    
    count = 0
    for name, category, website, play_id, installs, recommended, who_score, when_score, status in SEED_PROSPECTS:
        try:
            c.execute('''
                INSERT OR IGNORE INTO prospects 
                (name, category, website, play_store_id, install_count, recommended_product, who_score, when_score, status, is_existing_partner, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, category, website, play_id, installs, recommended, who_score, when_score, status, False, datetime.now(), datetime.now()))
            count += 1
        except Exception as e:
            print(f"Error inserting {name}: {e}")
    
    conn.commit()
    conn.close()
    return count

if __name__ == "__main__":
    count = seed_database()
    print(f"✓ Seeded {count} prospects")
