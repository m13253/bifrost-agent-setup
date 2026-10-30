# Install to ~/.config/zed/global_settings.json
# Then, go to Zed Settings → User → AI → General → LLM Providers to configure your API key.
#
# Reference:
#   https://zed.dev/docs/ai/use-api-access#openai-compatible
#   zed://schemas/settings

import pathlib
from typing import Any

import simplejson

from . import datasheet, schema, utils


def setup(config: schema.Config, models: schema.Models) -> pathlib.Path:
    settings_path = pathlib.Path.home() / ".config" / "zed" / "global_settings.json"
    try:
        with settings_path.open("rb") as f:
            settings = simplejson.load(f, use_decimal=True)
    except FileNotFoundError:
        settings = {}
    if not isinstance(settings, dict):
        raise TypeError("global_settings.json should contain a JSON object")

    if "language_models" not in settings:
        settings["language_models"] = {}
    if "openai_compatible" not in settings["language_models"]:
        settings["language_models"]["openai_compatible"] = {}
    settings["language_models"]["openai_compatible"][config.bifrost_name] = {
        "api_url": utils.url_slash_join(config.bifrost_url, "v1"),
        "available_models": [
            setup_model(config, model)
            for model in models.data
            if datasheet.model_supports_chat(model)
        ],
    }

    with utils.AtomicFile(settings_path, "w") as f:
        simplejson.dump(
            settings,
            f,
            ensure_ascii=False,
            indent=4,
            use_decimal=True,
            sort_keys=False,
        )
        f.write("\n")

    return settings_path


def setup_model(config: schema.Config, model: schema.Model) -> dict[str, Any]:
    limits = datasheet.ModelContextLimits.guess(model)
    return {
        "name": model.id,
        "display_name": model.name if model.name is not None else model.id,
        "max_tokens": limits.context_length
        if limits.context_length is not None
        else config.fallback_metadata.context_length,
        "capabilities": {
            "tools": True,
            "images": datasheet.model_supports_vision(model),
            "parallel_tool_calls": True,
            "prompt_cache_key": True,
            "chat_completions": False,
            "interleaved_reasoning": True,
        },
    }
