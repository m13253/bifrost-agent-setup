# Install to ~/.pi/agent/models.json
# Then, inside Pi, type /login to configure your API key.
#
# Reference:
#   https://pi.dev/docs/latest/models-configuration

import decimal
import pathlib
from typing import Any

import simplejson

from . import datasheet, schema, utils


def setup(config: schema.Config, models: schema.Models) -> pathlib.Path:
    auth_path = pathlib.Path.home() / ".pi" / "agent" / "auth.json"
    models_path = pathlib.Path.home() / ".pi" / "agent" / "models.json"

    if config.virtual_key:
        try:
            with auth_path.open("rb") as f:
                auth = simplejson.load(f, use_decimal=True)
        except FileNotFoundError:
            auth = {}
    else:
        auth = {}
    if not isinstance(auth, dict):
        raise TypeError("auth.json should contain a JSON object")

    try:
        with models_path.open("rb") as f:
            providers = simplejson.load(f, use_decimal=True)
    except FileNotFoundError:
        providers = {}
    if not isinstance(providers, dict):
        raise TypeError("models.json should contain a JSON object")

    if config.virtual_key:
        auth[config.bifrost_name] = {
            "type": "api_key",
            "key": config.virtual_key,
        }

    if "providers" not in providers:
        providers["providers"] = {}
    providers["providers"][config.bifrost_name] = setup_provider(config, models)

    with utils.AtomicFile(models_path, "w") as f:
        simplejson.dump(
            providers,
            f,
            ensure_ascii=False,
            indent=4,
            use_decimal=True,
            sort_keys=False,
        )

    if config.virtual_key:
        with utils.AtomicFile(auth_path, "w") as f:
            simplejson.dump(
                auth,
                f,
                ensure_ascii=False,
                indent=4,
                use_decimal=True,
                sort_keys=False,
            )

    return models_path


def setup_provider(config: schema.Config, models: schema.Models) -> dict[str, Any]:
    return utils.coalesce_dict(
        {
            "baseUrl": utils.url_slash_join(config.bifrost_url, "v1"),
            "api": "openai-responses",
            "authHeader": True if config.virtual_key else None,
            "models": [
                setup_model(config, model)
                for model in models.data
                if datasheet.model_supports_chat(model)
            ],
            "compat": {
                "supportsStore": True,
            },
        }
    )


def setup_model(config: schema.Config, model: schema.Model) -> dict[str, Any]:
    limits = datasheet.ModelContextLimits.guess(model)
    return utils.coalesce_dict(
        {
            "id": model.id,
            "name": model.name if model.name is not None else None,
            "reasoning": True if model.reasoning is not None else None,
            "thinkingLevelMap": generate_thinking_level_map(model),
            "input": ["text", "image"]
            if datasheet.model_supports_vision(model)
            else None,
            "cost": {
                "input": decimal.Decimal(model.pricing.prompt or 0)
                .scaleb(6)
                .normalize(),
                "output": decimal.Decimal(model.pricing.completion or 0)
                .scaleb(6)
                .normalize(),
                "cacheRead": decimal.Decimal(model.pricing.input_cache_read or 0)
                .scaleb(6)
                .normalize(),
                "cacheWrite": decimal.Decimal(model.pricing.input_cache_write or 0)
                .scaleb(6)
                .normalize(),
            }
            if model.pricing is not None
            else None,
            "contextWindow": limits.context_length,
            "maxTokens": limits.max_output_tokens,
        }
    )


def generate_thinking_level_map(model: schema.Model) -> dict[str, str | None] | None:
    if model.reasoning is None:
        return None
    thinking_level_map = {}
    if model.reasoning.mandatory:
        thinking_level_map["off"] = None
    if model.reasoning.supported_efforts is not None:
        thinking_levels = set(model.reasoning.supported_efforts)
        for level in ["minimal", "low", "medium", "high"]:
            if level not in thinking_levels:
                thinking_level_map[level] = None
        for level in ["xhigh", "max"]:
            if level in thinking_levels:
                thinking_level_map[level] = level
    return thinking_level_map or None
