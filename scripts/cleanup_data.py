"""
Data Retention Maintenance Script (DPDP Act Compliance).

Deletes comment mentions older than the specified retention window (default: 90 days).

Run:
    python3 scripts/cleanup_data.py [--days 90]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import SessionLocal
from backend.models import Mention


def cleanup_old_mentions(days: int = 90):
    print("=" * 60)
    print("The Aiges Engine — DPDP Act Retention Cleanup")
    print("=" * 60)
    print(f"[*] Retention Policy: Purging records older than {days} days...")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    db = SessionLocal()
    try:
        deleted_count = (
            db.query(Mention)
            .filter(Mention.detected_at < cutoff_date)
            .delete(synchronize_session=False)
        )
        db.commit()
        print(f"✅ Successfully deleted {deleted_count} mentions detected before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during cleanup: {e}")
    finally:
        db.close()
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge mentions older than N days.")
    parser.add_argument("--days", type=int, default=90, help="Retention period in days (default: 90)")
    args = parser.parse_args()
    cleanup_old_mentions(days=args.days)
