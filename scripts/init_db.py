#!/usr/bin/env python3
"""Initialize the IdleRPG PostgreSQL schema from the provided config file."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import asyncpg

from utils.config import ConfigLoader


async def _run(schema_path: Path, config_path: Path) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    config = ConfigLoader(str(config_path))
    database_config = config.database

    print(
        "Connecting to PostgreSQL...",
        f"host={database_config.postgres_host}",
        f"port={database_config.postgres_port}",
        f"database={database_config.postgres_name}",
    )

    conn = await asyncpg.connect(
        database=database_config.postgres_name,
        user=database_config.postgres_user,
        password=database_config.postgres_password,
        host=database_config.postgres_host,
        port=database_config.postgres_port,
    )

    try:
        schema_sql = schema_path.read_text(encoding="utf-8")
        await conn.execute(schema_sql)
        print("Database schema applied successfully.")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply schema.sql to the PostgreSQL database configured in config.toml.",
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to the IdleRPG configuration file (default: config.toml)",
    )
    parser.add_argument(
        "--schema",
        default="schema.sql",
        help="Path to the SQL schema file (default: schema.sql)",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()

    asyncio.run(_run(schema_path, config_path))


if __name__ == "__main__":
    main()
