#!/usr/bin/env python3
"""Interactive configuration helper for IdleRPG."""

from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

try:  # Python 3.11+
    import tomllib as toml_parser  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover - fallback for 3.10 runtimes
    try:
        import tomli as toml_parser  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        toml_parser = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config.toml"

DEFAULT_EXTENSIONS = [
    "cogs.locale",
    "cogs.owner",
    "cogs.game_master",
    "cogs.gambling",
    "cogs.adventure",
    "cogs.ranks",
    "cogs.trading",
    "cogs.miscellaneous",
    "cogs.server",
    "cogs.profile",
    "cogs.battles",
    "cogs.help",
    "cogs.vote",
    "cogs.crates",
    "cogs.patreon",
    "cogs.store",
    "cogs.marriage",
    "cogs.guild",
    "cogs.tournament",
    "cogs.classes",
    "cogs.images",
    "cogs.global_events",
    "cogs.raid",
    "cogs.gods",
    "cogs.transaction",
    "cogs.races",
    "cogs.hungergames",
    "cogs.maths",
    "cogs.shard_communication",
    "cogs.alliance",
    "cogs.trivia",
    "cogs.chess",
    "cogs.werewolf",
    "cogs.scheduler",
    "cogs.error_handler",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guide an operator through building config.toml",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to write the generated TOML file (default: %(default)s)",
    )
    return parser.parse_args()


def prompt_required(prompt: str, *, transform: Callable[[str], str] | None = None) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return transform(value) if transform else value
        print("This value is required. Please provide a response.")


def prompt_with_default(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")


def prompt_optional(prompt: str) -> str | None:
    value = input(prompt).strip()
    return value or None


def prompt_optional_int(prompt: str) -> int | None:
    value = input(prompt).strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        print("Invalid integer. Leaving this value unset.")
        return None
    return parsed


def prompt_port(prompt: str, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            port = int(raw)
        except ValueError:
            print("Ports must be numeric (1-65535). Try again.")
            continue
        if 1 <= port <= 65535:
            return port
        print("Ports must be between 1 and 65535.")


def prompt_non_negative_int(prompt: str, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number (0 or greater).")
            continue
        if value < 0:
            print("The value cannot be negative.")
            continue
        return value


def prompt_positive_int(prompt: str, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number greater than zero.")
            continue
        if value <= 0:
            print("The value must be greater than zero.")
            continue
        return value


def validate_postgres_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return False
    if not parsed.hostname:
        return False
    if not parsed.path or parsed.path in {"", "/"}:
        return False
    return True


def validate_redis_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"redis", "rediss"}:
        return False
    return bool(parsed.hostname)


def collect_postgres() -> dict[str, Any]:
    print("\nPostgreSQL configuration")
    print("-------------------------")
    print(
        "Provide a full PostgreSQL connection string if you have one, or leave it blank "
        "to enter the individual fields manually."
    )
    while True:
        url = input("PostgreSQL connection URL: ").strip()
        if url:
            if validate_postgres_url(url):
                return {"postgres_url": url}
            print(
                "The URL must start with postgres:// or postgresql:// and include a database name."
            )
            continue
        host = prompt_required("PostgreSQL host: ")
        port = prompt_port("PostgreSQL port", 5432)
        database = prompt_required("PostgreSQL database name: ")
        user = prompt_required("PostgreSQL user: ")
        password = getpass("PostgreSQL password: ").strip()
        if not password:
            print("A password is required for IdleRPG to authenticate with PostgreSQL.")
            continue
        return {
            "postgres_host": host,
            "postgres_port": port,
            "postgres_name": database,
            "postgres_user": user,
            "postgres_password": password,
        }


def collect_redis() -> dict[str, Any]:
    print("\nRedis configuration")
    print("--------------------")
    print(
        "IdleRPG can connect with a redis:// or rediss:// URL. Leave the URL blank to "
        "enter host, port, and database manually."
    )
    while True:
        url = input("Redis connection URL: ").strip()
        if url:
            if validate_redis_url(url):
                return {"redis_url": url}
            print("The URL must start with redis:// or rediss:// and include a hostname.")
            continue
        host = prompt_required("Redis host: ")
        port = prompt_port("Redis port", 6379)
        database = prompt_optional_int("Redis database index [0]: ")
        password = getpass("Redis password (leave blank if none): ").strip() or None
        result: dict[str, Any] = {
            "redis_host": host,
            "redis_port": port,
            "redis_database": database if database is not None else 0,
        }
        if password:
            result["redis_password"] = password
        return result


def sanitize_section(section: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in section.items() if value not in {None, ""}}


def format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
        return f'"{escaped}"'
    raise TypeError(f"Unsupported value type: {type(value)!r}")


def format_value(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return "[]"
        formatted_items = [format_scalar(item) for item in value]
        if len(formatted_items) <= 4 and all(len(item) <= 20 for item in formatted_items):
            return f"[{', '.join(formatted_items)}]"
        joined = ",\n    ".join(formatted_items)
        return f"[\n    {joined}\n]"
    return format_scalar(value)


def render_toml(data: dict[str, dict[str, Any]]) -> str:
    sections: list[str] = []
    for name, values in data.items():
        sanitized = sanitize_section(values)
        if not sanitized:
            continue
        section_lines = [f"[{name}]"]
        for key, value in sanitized.items():
            section_lines.append(f"{key} = {format_value(value)}")
        sections.append("\n".join(section_lines))
    return "\n\n".join(sections) + "\n"


def ensure_writable(path: Path) -> None:
    if path.exists():
        overwrite = prompt_yes_no(
            f"{path} already exists. Overwrite it?",
            default=False,
        )
        if not overwrite:
            print("Aborted without writing a configuration file.")
            sys.exit(0)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    config_path = args.config.expanduser().resolve()

    print("IdleRPG configuration helper")
    print("============================")
    print(
        "This tool collects the minimum information required to launch IdleRPG and writes "
        "a config.toml file. Press Ctrl+C at any time to cancel."
    )

    token = prompt_required("Discord bot token: ")
    prefix = prompt_with_default("Command prefix", "$")
    is_beta = prompt_yes_no("Mark this instance as beta?", default=False)
    is_custom = prompt_yes_no(
        "Is this a custom community build (disables owner-only commands)?",
        default=False,
    )

    postgres_section = collect_postgres()
    redis_section = collect_redis()

    print("\nOptional integrations")
    print("----------------------")
    base_url = prompt_with_default(
        "Public website URL", "https://idlerpg.xyz"
    )
    okapi_url = prompt_with_default("Okapi API URL", "http://localhost:3000")
    proxy_url = prompt_optional("HTTP proxy URL (leave blank to skip): ")
    patreon_token = prompt_optional("Patreon token (leave blank to skip): ")
    imgur_token = prompt_optional("Imgur client token (leave blank to skip): ")
    okapi_token = prompt_optional("Okapi token (leave blank to skip): ")
    traviapi = prompt_optional("Travi API token (leave blank to skip): ")
    topgg_token = prompt_optional("top.gg token (leave blank to skip): ")
    dbl_token = prompt_optional("Discord Bot List token (leave blank to skip): ")
    bfd_token = prompt_optional("Bots For Discord token (leave blank to skip): ")
    join_channel = prompt_optional_int(
        "Statistics join channel ID (leave blank to skip): "
    )
    sentry_url = prompt_optional("Sentry DSN (leave blank to skip): ")
    redis_announce_channel = prompt_optional(
        "Redis shard announce channel key [guild_channel]: "
    )

    launcher_additional_shards = prompt_non_negative_int(
        "Additional shards per cluster", 8
    )
    launcher_shards_per_cluster = prompt_positive_int(
        "Shards per cluster", 8
    )

    bot_section = {
        "version": "4.11.1",
        "token": token,
        "initial_extensions": DEFAULT_EXTENSIONS,
        "global_prefix": prefix,
        "is_beta": is_beta,
        "is_custom": is_custom,
        "global_cooldown": 3,
        "donator_cooldown": 2,
    }

    external_section = sanitize_section(
        {
            "base_url": base_url,
            "okapi_url": okapi_url,
            "proxy_url": proxy_url,
            "patreon_token": patreon_token,
            "imgur_token": imgur_token,
            "okapi_token": okapi_token,
            "traviapi": traviapi,
        }
    )

    database_section = {**postgres_section, **redis_section}
    if redis_announce_channel:
        database_section["redis_shard_announce_channel"] = redis_announce_channel

    statistics_section = sanitize_section(
        {
            "topggtoken": topgg_token,
            "dbltoken": dbl_token,
            "bfdtoken": bfd_token,
            "join_channel": join_channel,
            "sentry_url": sentry_url,
        }
    )

    launcher_section = {
        "additional_shards": launcher_additional_shards,
        "shards_per_cluster": launcher_shards_per_cluster,
    }

    config_data = {
        "bot": bot_section,
        "external": external_section,
        "database": database_section,
        "statistics": statistics_section,
        "launcher": launcher_section,
    }

    config_text = render_toml(config_data)

    if toml_parser is not None:
        try:
            toml_parser.loads(config_text)
        except Exception as exc:  # pragma: no cover - defensive guard
            print("Failed to validate the generated TOML:", exc)
            return 1

    ensure_writable(config_path)
    config_path.write_text(config_text, encoding="utf-8")

    print(f"\nWrote configuration to {config_path}")
    print("You can rerun this helper at any time to update the file.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAborted by user.")
        raise SystemExit(1)
