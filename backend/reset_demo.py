import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    tables = conn.execute(text("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename <> 'alembic_version'
    """)).fetchall()

    names = [row[0] for row in tables]

    if names:
        quoted = ", ".join(f'"{name}"' for name in names)
        conn.execute(
            text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
        )

print("DEMO DATABASE RESET SUCCESSFULLY")
print("All application data cleared.")
print("Alembic migration history preserved.")