"""
The IdleRPG Discord Bot
Copyright (C) 2018-2021 Diniboy and Gelbpunkt

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import os
from typing import Any, Callable, TypeVar
from urllib.parse import quote, urlparse

import tomli

T = TypeVar("T")


def _resolve_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    expanded = os.path.expandvars(value)
    if expanded == value and value.startswith("${") and value.endswith("}"):
        return None
    return expanded


def _apply_override(
    *,
    value: Any,
    env_vars: tuple[str, ...],
    default: T,
    caster: Callable[[Any], T],
) -> T:
    for env_var in env_vars:
        env_value = os.getenv(env_var)
        if env_value:
            return _cast_value(env_value, caster, default)

    resolved = _resolve_string(value)
    if resolved is None:
        return default
    return _cast_value(resolved, caster, default)


def _cast_value(value: Any, caster: Callable[[Any], T], default: T) -> T:
    if isinstance(value, type(default)) or (default is None and value is not None):
        try:
            return caster(value)
        except (TypeError, ValueError):
            return default

    try:
        return caster(value)
    except (TypeError, ValueError):
        return default


def _parse_postgres_url(url: str | None) -> dict[str, Any]:
    if not url:
        return {}

    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return {}

    database = parsed.path.lstrip("/") or None
    result: dict[str, Any] = {}
    if parsed.hostname:
        result["postgres_host"] = parsed.hostname
    if parsed.port is not None:
        result["postgres_port"] = parsed.port
    if parsed.username:
        result["postgres_user"] = parsed.username
    if parsed.password:
        result["postgres_password"] = parsed.password
    if database:
        result["postgres_name"] = database
    return result


def _parse_redis_url(url: str | None) -> dict[str, Any]:
    if not url:
        return {}

    parsed = urlparse(url)
    if parsed.scheme not in {"redis", "rediss"}:
        return {}

    database = 0
    if parsed.path:
        try:
            database = int(parsed.path.lstrip("/"))
        except ValueError:
            database = 0

    result: dict[str, Any] = {"redis_url": url}
    if parsed.hostname:
        result["redis_host"] = parsed.hostname
    if parsed.port is not None:
        result["redis_port"] = parsed.port
    if parsed.password:
        result["redis_password"] = parsed.password
    result["redis_database"] = database
    return result


class BotSection:
    __slots__ = {
        "version",
        "token",
        "initial_extensions",
        "global_prefix",
        "is_beta",
        "is_custom",
        "global_cooldown",
        "donator_cooldown",
    }

    def __init__(self, data: dict[str, Any]) -> None:
        self.version = _resolve_string(data.get("version", "unknown")) or "unknown"
        self.token = _apply_override(
            value=data.get("token"),
            env_vars=("BOT_TOKEN", "DISCORD_TOKEN"),
            default=None,
            caster=str,
        )
        if not self.token:
            raise KeyError("token")
        self.initial_extensions = data.get("initial_extensions", [])
        self.global_prefix = _apply_override(
            value=data.get("global_prefix", "$"),
            env_vars=("BOT_GLOBAL_PREFIX",),
            default="$",
            caster=lambda v: str(v) if v is not None else "$",
        )
        self.is_beta = data.get("is_beta", True)
        self.is_custom = data.get("is_custom", False)
        self.global_cooldown = data.get("global_cooldown", 3)
        self.donator_cooldown = data.get("donator_cooldown", 2)


class DonatorRole:
    __slots__ = {"id", "tier"}

    def __init__(self, data: dict[str, Any]):
        self.id = data.get("id", 0)
        self.tier = data.get("tier", "basic")


class ExternalSection:
    __slots__ = {
        "patreon_token",
        "imgur_token",
        "okapi_token",
        "traviapi",
        "base_url",
        "okapi_url",
        "proxy_url",
        "donator_roles",
    }

    def __init__(self, data: dict[str, Any]) -> None:
        self.patreon_token = data.get("patreon_token", None)
        self.imgur_token = data.get("imgur_token", None)
        self.okapi_token = data.get("okapi_token", None)
        self.traviapi = data.get("traviapi", None)
        self.base_url = data.get("base_url", "https://idlerpg.xyz")
        self.okapi_url = data.get("okapi_url", "http://localhost:3000")
        self.proxy_url = data.get("proxy_url", None)
        self.donator_roles = [DonatorRole(i) for i in data.get("donator_roles", [])]


class DatabaseSection:
    __slots__ = {
        "postgres_name",
        "postgres_user",
        "postgres_port",
        "postgres_host",
        "postgres_password",
        "postgres_url",
        "redis_url",
        "redis_host",
        "redis_port",
        "redis_password",
        "redis_database",
        "redis_shard_announce_channel",
    }

    def __init__(self, data: dict[str, Any]) -> None:
        default_postgres = {
            "postgres_name": "idlerpg",
            "postgres_user": "jens",
            "postgres_port": 5432,
            "postgres_host": "127.0.0.1",
            "postgres_password": "owo",
        }

        postgres_url = _resolve_string(
            data.get("postgres_url")
            or os.getenv("POSTGRES_URL")
            or os.getenv("DATABASE_URL")
            or os.getenv("SUPABASE_DB_URL")
            or os.getenv("NEON_DB_URL")
        )
        postgres_defaults = {
            **default_postgres,
            **_parse_postgres_url(postgres_url),
        }

        self.postgres_url = postgres_url
        self.postgres_name = _apply_override(
            value=data.get("postgres_name", postgres_defaults["postgres_name"]),
            env_vars=("POSTGRES_DB", "POSTGRES_DATABASE", "DB_NAME", "PGDATABASE"),
            default=postgres_defaults["postgres_name"],
            caster=lambda v: str(v) if v is not None else None,
        )
        self.postgres_user = _apply_override(
            value=data.get("postgres_user", postgres_defaults["postgres_user"]),
            env_vars=(
                "POSTGRES_USER",
                "POSTGRES_USERNAME",
                "DB_USER",
                "SUPABASE_USER",
                "NEON_USER",
                "PGUSER",
            ),
            default=postgres_defaults["postgres_user"],
            caster=lambda v: str(v) if v is not None else None,
        )
        self.postgres_password = _apply_override(
            value=data.get(
                "postgres_password", postgres_defaults["postgres_password"]
            ),
            env_vars=(
                "POSTGRES_PASSWORD",
                "DB_PASSWORD",
                "SUPABASE_PASSWORD",
                "NEON_PASSWORD",
                "PGPASSWORD",
            ),
            default=postgres_defaults["postgres_password"],
            caster=lambda v: str(v) if v is not None else None,
        )
        self.postgres_host = _apply_override(
            value=data.get("postgres_host", postgres_defaults["postgres_host"]),
            env_vars=(
                "POSTGRES_HOST",
                "DB_HOST",
                "SUPABASE_HOST",
                "NEON_HOST",
                "PGHOST",
            ),
            default=postgres_defaults["postgres_host"],
            caster=lambda v: str(v) if v is not None else None,
        )
        self.postgres_port = _apply_override(
            value=data.get("postgres_port", postgres_defaults["postgres_port"]),
            env_vars=(
                "POSTGRES_PORT",
                "DB_PORT",
                "SUPABASE_PORT",
                "NEON_PORT",
                "PGPORT",
            ),
            default=postgres_defaults["postgres_port"],
            caster=lambda v: int(v) if v is not None else postgres_defaults["postgres_port"],
        )

        default_redis = {
            "redis_host": "127.0.0.1",
            "redis_port": 6379,
            "redis_database": 0,
            "redis_password": None,
        }

        redis_url = _resolve_string(
            data.get("redis_url")
            or os.getenv("REDIS_URL")
            or os.getenv("REDIS_TLS_URL")
            or os.getenv("UPSTASH_REDIS_URL")
        )
        redis_defaults = {
            **default_redis,
            **_parse_redis_url(redis_url),
        }

        self.redis_url = redis_defaults.get("redis_url")
        self.redis_host = _apply_override(
            value=data.get("redis_host", redis_defaults["redis_host"]),
            env_vars=("REDIS_HOST", "UPSTASH_REDIS_HOST"),
            default=redis_defaults["redis_host"],
            caster=lambda v: str(v) if v is not None else None,
        )
        self.redis_port = _apply_override(
            value=data.get("redis_port", redis_defaults["redis_port"]),
            env_vars=("REDIS_PORT", "UPSTASH_REDIS_PORT"),
            default=redis_defaults["redis_port"],
            caster=lambda v: int(v) if v is not None else redis_defaults["redis_port"],
        )
        self.redis_database = _apply_override(
            value=data.get("redis_database", redis_defaults["redis_database"]),
            env_vars=("REDIS_DB", "UPSTASH_REDIS_DB"),
            default=redis_defaults["redis_database"],
            caster=lambda v: int(v) if v is not None else redis_defaults["redis_database"],
        )
        self.redis_password = _apply_override(
            value=data.get("redis_password", redis_defaults.get("redis_password")),
            env_vars=(
                "REDIS_PASSWORD",
                "UPSTASH_REDIS_PASSWORD",
                "UPSTASH_REDIS_TOKEN",
            ),
            default=redis_defaults.get("redis_password"),
            caster=lambda v: str(v) if v is not None else None,
        )
        self.redis_shard_announce_channel = _apply_override(
            value=data.get("redis_shard_announce_channel", "guild_channel"),
            env_vars=("REDIS_SHARD_ANNOUNCE_CHANNEL",),
            default="guild_channel",
            caster=lambda v: str(v) if v is not None else "guild_channel",
        )

    def redis_connection_url(self) -> str:
        if self.redis_url:
            return self.redis_url

        if self.redis_password:
            password = quote(self.redis_password, safe="")
            auth_segment = f":{password}@"
        else:
            auth_segment = ""

        return (
            f"redis://{auth_segment}{self.redis_host}:{self.redis_port}/"
            f"{self.redis_database}"
        )


class StatisticsSection:
    __slots__ = {"topggtoken", "bfdtoken", "dbltoken", "join_channel", "sentry_url"}

    def __init__(self, data: dict[str, Any]) -> None:
        self.topggtoken = data.get("topggtoken", None)
        self.bfdtoken = data.get("bfdtoken", None)
        self.dbltoken = data.get("dbltoken", None)
        self.join_channel = data.get("join_channel", None)
        self.sentry_url = data.get("sentry_url", None)


class LauncherSection:
    __slots__ = {"additional_shards", "shards_per_cluster"}

    def __init__(self, data: dict[str, Any]) -> None:
        self.additional_shards = data.get("additional_shards", 8)
        self.shards_per_cluster = data.get("shards_per_cluster", 8)


class GameSection:
    __slots__ = {
        "game_masters",
        "banned_guilds",
        "support_server_id",
        "raid_channel",
        "gm_log_channel",
        "helpme_channel",
        "official_tournament_channel_id",
        "bot_event_channel",
        "primary_colour",
        "member_role",
        "support_team_role",
    }

    def __init__(self, data: dict[str, Any]) -> None:
        self.game_masters = data.get("game_masters", [])
        self.banned_guilds = data.get("banned_guilds", [])
        self.support_server_id = data.get("support_server_id", None)
        self.raid_channel = data.get("raid_channel", None)
        self.gm_log_channel = data.get("gm_log_channel", None)
        self.helpme_channel = data.get("helpme_channel", None)
        self.official_tournament_channel_id = data.get(
            "official_tournament_channel_id", None
        )
        self.bot_event_channel = data.get("bot_event_channel", None)
        self.primary_colour = data.get("primary_colour", 16759808)
        self.member_role = data.get("member_role", None)
        self.support_team_role = data.get("support_team_role", None)


class MusicSection:
    __slots__ = {"query_endpoint", "resolve_endpoint", "nodes"}

    def __init__(self, data: dict[str, Any]) -> None:
        self.query_endpoint = data.get("query_endpoint", None)
        self.resolve_endpoint = data.get("resolve_endpoint", None)
        self.nodes = data.get("nodes", [])


class ConfigLoader:
    """ConfigLoader provides methods for loading and reading values from a .toml file."""

    __slots__ = {
        "config",
        "values",
        "bot",
        "external",
        "database",
        "statistics",
        "launcher",
        "game",
        "cities",
        "music",
        "gods",
    }

    def __init__(self, path: str) -> None:
        # the path to the config file of this loader
        self.config = path
        # values initialized as empty dict, in case loading fails
        self.values = {}
        self.reload()

    def reload(self) -> None:
        """Loads the config using the path this loader was initialized with, overriding any previously stored values."""
        with open(self.config, "rb") as f:
            self.values = tomli.load(f)
        self.set_attributes()

    def set_attributes(self) -> None:
        """Sets all config attriutes on the loader."""
        self.bot = BotSection(self.values["bot"])
        self.external = ExternalSection(self.values.get("external", {}))
        self.database = DatabaseSection(self.values.get("database", {}))
        self.statistics = StatisticsSection(self.values.get("statistics", {}))
        self.launcher = LauncherSection(self.values.get("launcher", {}))
        self.game = GameSection(self.values.get("game", {}))
        self.cities = self.values.get("cities", [])
        self.music = MusicSection(self.values.get("music", {}))
        self.gods = self.values.get("gods", [])
