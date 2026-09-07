"""
Administrative and CLI Scripts Package for The Aiges Engine.

Available Scripts:
- scripts/demo.py: Runs sample ASCI compliance check on test posts.
- scripts/init_db.py: Initializes SQLite database and registers all model tables.
- scripts/seed_demo_data.py: Seeds demo user (demo@aiges.ai), compliance audits, multilingual mentions, and campaigns.
- scripts/cleanup_data.py: Enforces DPDP Act 90-day retention cleanup.
- scripts/run_dev.py: Quick development server launcher.
"""

__all__ = [
    "demo",
    "init_db",
    "seed_demo_data",
    "cleanup_data",
    "run_dev",
]
