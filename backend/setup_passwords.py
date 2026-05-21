"""
AeroNetB — Password Setup Script
Run this ONCE after creating the PostgreSQL database to set real password hashes.
The DML script uses placeholder hashes. This script replaces them with real ones.

Usage:
  python setup_passwords.py

Then provide the PostgreSQL DSN when prompted (or set DATABASE_URL in .env).
"""

import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

DEMO_ACCOUNTS = [
    # (email, plain_password)
    ('sarah.mitchell@aeronetb.com',  'Demo1234!'),
    ('james.nakamura@aeronetb.com',  'Demo1234!'),
    ('fatima.alrashid@aeronetb.com', 'Demo1234!'),
    ('david.okafor@aeronetb.com',    'Demo1234!'),
    ('elena.vasquez@regulator.eu',   'Demo1234!'),
]

try:
    import psycopg2
    PG_DSN = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/aeronetb')
    conn = psycopg2.connect(PG_DSN)
    cur  = conn.cursor()

    print("Setting password hashes for demo accounts...")
    for email, password in DEMO_ACCOUNTS:
        h = generate_password_hash(password)
        cur.execute("UPDATE SystemUser SET password_hash=%s WHERE email=%s", (h, email))
        print(f"  ✓ {email}")

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ All demo account passwords set to: Demo1234!")
    print("   You can now log in at http://localhost:5000")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nAlternatively, run this SQL in psql to set passwords manually:")
    print()
    for email, password in DEMO_ACCOUNTS:
        h = generate_password_hash(password)
        print(f"UPDATE SystemUser SET password_hash='{h}' WHERE email='{email}';")
