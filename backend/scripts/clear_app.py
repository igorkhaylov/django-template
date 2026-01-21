#!/usr/bin/env python
"""
Clear all tables and migrations for a Django app.

Usage:
    python clear_app.py <app_name>
    python clear_app.py market
    python clear_app.py forum --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

# Get the project root directory (parent of scripts folder)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def setup_django():
    """Setup Django environment."""
    # Add project root to Python path
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()


def get_app_models(app_name):
    """Get all models for the given app."""
    from django.apps import apps
    try:
        app_config = apps.get_app_config(app_name)
        return app_config.get_models()
    except LookupError:
        return None


def get_table_names(models):
    """Get database table names for models."""
    return [model._meta.db_table for model in models]


def drop_tables(table_names, dry_run=False):
    """Drop tables from the database."""
    from django.db import connection

    if not table_names:
        print("No tables to drop.")
        return

    print(f"\nDropping {len(table_names)} table(s):")
    for table in table_names:
        print(f"  - {table}")

    if dry_run:
        print("\n[DRY RUN] No tables were actually dropped.")
        return

    with connection.cursor() as cursor:
        for table in table_names:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

    print("Tables dropped successfully.")


def clear_migration_records(app_name, dry_run=False):
    """Remove migration records from django_migrations table."""
    from django.db import connection

    print(f"\nClearing migration records for '{app_name}'...")

    if dry_run:
        print("[DRY RUN] No migration records were actually deleted.")
        return

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM django_migrations WHERE app = %s;",
            [app_name]
        )
        deleted_count = cursor.rowcount

    print(f"Deleted {deleted_count} migration record(s).")


def delete_migration_files(app_name, dry_run=False):
    """Delete migration files from the app's migrations folder."""
    from django.apps import apps

    try:
        app_config = apps.get_app_config(app_name)
        migrations_dir = Path(app_config.path) / "migrations"
    except LookupError:
        print(f"Could not find app '{app_name}'")
        return

    if not migrations_dir.exists():
        print(f"\nNo migrations directory found at {migrations_dir}")
        return

    migration_files = [
        f for f in migrations_dir.glob("*.py")
        if f.name != "__init__.py"
    ]

    if not migration_files:
        print("\nNo migration files to delete.")
        return

    print(f"\nDeleting {len(migration_files)} migration file(s):")
    for f in migration_files:
        print(f"  - {f.name}")

    if dry_run:
        print("[DRY RUN] No files were actually deleted.")
        return

    for f in migration_files:
        f.unlink()

    print("Migration files deleted successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Clear all tables and migrations for a Django app."
    )
    parser.add_argument(
        "app_name",
        help="Name of the Django app to clear"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Setup Django
    setup_django()

    # Validate app exists
    models = get_app_models(args.app_name)
    if models is None:
        print(f"Error: App '{args.app_name}' not found.")
        print("\nAvailable apps:")
        from django.apps import apps
        for app in apps.get_app_configs():
            print(f"  - {app.label}")
        sys.exit(1)

    table_names = get_table_names(models)

    print(f"=" * 50)
    print(f"Clear App: {args.app_name}")
    print(f"=" * 50)

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***")

    # Confirmation
    if not args.dry_run and not args.no_confirm:
        print(f"\nThis will permanently delete:")
        print(f"  - {len(table_names)} database table(s)")
        print(f"  - All migration records for '{args.app_name}'")
        print(f"  - All migration files in the app")

        response = input("\nAre you sure? Type 'yes' to confirm: ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    # Execute
    drop_tables(table_names, args.dry_run)
    clear_migration_records(args.app_name, args.dry_run)
    delete_migration_files(args.app_name, args.dry_run)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done!")

    if not args.dry_run:
        print(f"\nTo recreate migrations, run:")
        print(f"  python manage.py makemigrations {args.app_name}")
        print(f"  python manage.py migrate {args.app_name}")


if __name__ == "__main__":
    main()
