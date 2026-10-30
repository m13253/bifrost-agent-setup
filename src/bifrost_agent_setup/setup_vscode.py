# Installation:
# 1. Ctrl-Shift-P (Cmd-Shift-P): “Chat: Open Language Models (JSON)”, paste in the generated JSON
# 2. Ctrl-Shift-P (Cmd-Shift-P): “Developer: Reload Window”
# 3. Ctrl-Shift-P (Cmd-Shift-P): “Chat: Manage Language Models”
# 4. Right click a model, and choose “Update API Key”
#
# Reference:
#   https://code.visualstudio.com/docs/agent-customization/language-models#_model-configuration-reference

import pathlib
from typing import Any, cast

import platformdirs
import simplejson

from . import datasheet, schema, utils


def setup(config: schema.Config, models: schema.Models) -> pathlib.Path:
    models_path = (
        platformdirs.user_config_path("Code", appauthor=False, roaming=True)
        / "User"
        / "chatLanguageModels.json"
    )
    try:
        with models_path.open("rb") as f:
            providers_old = simplejson.load(f, use_decimal=True)
    except FileNotFoundError:
        providers_old = []
    if not isinstance(providers_old, list):
        raise TypeError("chatLanguageModels.json should contain a JSON array")

    for p in providers_old:
        if (
            isinstance(p, dict)
            and "name" in p
            and p["name"] == config.bifrost_name
            and "apiKey" in p
            and isinstance(p["apiKey"], str)
            and p["apiKey"].startswith("$")
        ):
            api_key = cast(str, p["apiKey"])
            break
    else:
        api_key = config.virtual_key
    api_url = utils.url_slash_join(config.bifrost_url, "v1/chat/completions")

    provider = utils.coalesce_dict(
        {
            "name": config.bifrost_name,
            "vendor": "customendpoint",
            "apiKey": api_key,
            "apiType": "chat-completions",
            "models": [
                setup_model(config, model, api_url)
                for model in models.data
                if datasheet.model_supports_chat(model)
            ],
        }
    )
    inserted = False
    providers_new = []
    for p in providers_old:
        if isinstance(p, dict) and "name" in p and p["name"] == config.bifrost_name:
            if not inserted:
                providers_new.append(provider)
            inserted = True
        else:
            providers_new.append(p)
    if not inserted:
        providers_new.append(provider)

    with utils.AtomicFile(models_path, "w") as f:
        simplejson.dump(
            providers_new,
            f,
            ensure_ascii=False,
            indent=4,
            use_decimal=True,
            sort_keys=False,
        )
        f.write("\n")

    return models_path


def setup_model(
    config: schema.Config, model: schema.Model, api_url: str
) -> dict[str, Any]:
    limits = datasheet.ModelContextLimits.guess(model)
    if limits.context_length is None:
        limits.context_length = config.fallback_metadata.context_length
        if limits.max_output_tokens is None:
            limits.max_output_tokens = min(
                config.fallback_metadata.max_output_tokens,
                config.fallback_metadata.context_length,
            )
    elif limits.max_output_tokens is None:
        limits.max_output_tokens = min(
            config.fallback_metadata.max_output_tokens, limits.context_length // 2
        )
    return utils.coalesce_dict(
        {
            "id": model.id,
            "name": model.name if model.name is not None else model.id,
            "url": api_url,
            "toolCalling": True,
            "vision": datasheet.model_supports_vision(model),
            # As of VS Code 1.144.0, turning on "thinking" has the following effects:
            # 1. Removes the "temperature" parameter
            # 2. Uses "max_completion_tokens" instead of "max_tokens"
            # 3. Sends back reasoning history when the protocol is chat-completions and if
            #    a) the user turns on "thinkingInHistory" through "github.copilot.chat.modelCapabilityOverrides",
            #    b) or the model is named kimi-k3
            # It does not actually affect thinking itself.
            "thinking": True,
            "maxInputTokens": limits.context_length - limits.max_output_tokens,
            "maxOutputTokens": limits.max_output_tokens,
            "supportsReasoningEffort": model.reasoning.supported_efforts
            if model.reasoning is not None
            else None,
        }
    )
