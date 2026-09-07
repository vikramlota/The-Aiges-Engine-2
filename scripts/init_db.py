"""
Database Initialization Script for The Aiges Engine.

Run:
    python3 scripts/init_db.py
"""
import sys
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import engine, Base
import backend.models  # Registers all SQLAlchemy tables on Base.metadata


def init_database():
    print("=" * 60)
    print("The Aiges Engine — Database Initialization")
    print("=" * 60)
    print(f"[*] Connecting to database engine: {engine.url}")
    
    table_names = list(Base.metadata.tables.keys())
    print(f"[*] Discovered {len(table_names)} model tables:")
    for t in table_names:
        print(f"    - {t}")

    print("[*] Creating all tables if not present...")
    Base.metadata.create_all(bind=engine)

    # Safe lightweight SQLite migration for added columns
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(mentions)")).fetchall()
        column_names = [row[1] for row in result]
        if column_names:
            migrations = [
                ("language", "ALTER TABLE mentions ADD COLUMN language VARCHAR DEFAULT 'en'"),
                ("drafted_reply", "ALTER TABLE mentions ADD COLUMN drafted_reply TEXT"),
                ("draft_explanation", "ALTER TABLE mentions ADD COLUMN draft_explanation TEXT"),
                ("approved_by", "ALTER TABLE mentions ADD COLUMN approved_by INTEGER"),
                ("approved_at", "ALTER TABLE mentions ADD COLUMN approved_at DATETIME"),
            ]
            for col_name, sql in migrations:
                if col_name not in column_names:
                    print(f"[*] Migrating mentions table: adding '{col_name}' column...")
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Column '{col_name}' added to mentions table.")

    print("✅ All tables and schemas verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    init_database()
