#!/usr/bin/env python3
"""
Cleanup utility for attendance logs.

Usage:
  python3 cleanup_attendance_logs.py
  python3 cleanup_attendance_logs.py --days 15
"""

import argparse

import attendance_service
import config


def main():
    parser = argparse.ArgumentParser(
        description="Delete attendance CSV files older than the configured retention window."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=config.LOG_RETENTION_DAYS,
        help=f"Number of days to retain (default: {config.LOG_RETENTION_DAYS}).",
    )
    args = parser.parse_args()

    result = attendance_service.cleanup_old_logs(retention_days=args.days)
    deleted_files = result.get("deleted_files", [])

    print(f"Retention days: {result['retention_days']}")
    print(f"Kept from date: {result['cutoff_date']}")
    print(f"Deleted files: {len(deleted_files)}")
    for path in deleted_files:
        print(f"- {path}")


if __name__ == "__main__":
    main()
