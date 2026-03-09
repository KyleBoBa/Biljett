from __future__ import annotations

import tomllib
from pathlib import Path

from biljett.config.models import AppConfig


def config_dir() -> Path:
    base = Path.home() / ".config" / "biljett"
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_path() -> Path:
    return config_dir() / "config.toml"


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return AppConfig.model_validate(raw)


def save_config(config: AppConfig) -> Path:
    path = config_path()
    path.write_text(_to_toml(config), encoding="utf-8")
    return path


def initialize_default_config() -> Path:
    return save_config(AppConfig())


def _to_toml(config: AppConfig) -> str:
    lines = [
        f'default_region = "{config.default_region.value}"',
        f'default_profile = "{config.default_profile.value}"',
        "",
        "[cache]",
        f'sqlite_path = "{config.cache.sqlite_path}"',
        f"default_ttl_seconds = {config.cache.default_ttl_seconds}",
        f"sites_ttl_seconds = {config.cache.sites_ttl_seconds}",
        "",
    ]

    if config.api_keys:
        lines.append("[api_keys]")
        for key, value in sorted(config.api_keys.items()):
            lines.append(f'{key} = "{value}"')
        lines.append("")

    for name, favorite in sorted(config.favorites.items()):
        lines.append(f"[favorites.{name}]")
        lines.append(f'name = "{favorite.name}"')
        lines.append(f'stop_id = "{favorite.stop_id}"')
        if favorite.site_id is not None:
            lines.append(f"site_id = {favorite.site_id}")
        lines.append(f'region = "{favorite.region.value}"')
        lines.append("")

    for name, scenario in sorted(config.commute_scenarios.items()):
        lines.append(f"[commute_scenarios.{name}]")
        lines.append(f'name = "{scenario.name}"')
        lines.append(f'origin = "{scenario.origin}"')
        lines.append(f'destination = "{scenario.destination}"')
        lines.append(f'start_date = "{scenario.start_date.isoformat()}"')
        lines.append(f'end_date = "{scenario.end_date.isoformat()}"')
        lines.append(f"include_weekends = {str(scenario.include_weekends).lower()}")
        lines.append(f"rides_per_day = {scenario.rides_per_day}")
        lines.append(f'region = "{scenario.region.value}"')
        lines.append(f'profile = "{scenario.profile.value}"')
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
