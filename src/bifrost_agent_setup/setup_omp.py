# Install to ~/.omp/agent/models.yml
# Then, inside oh-my-pi, type /login to configure your API key.
#
# Reference:
#   https://github.com/can1357/oh-my-pi/blob/main/docs/models.md

import decimal
import pathlib

import simplejson
import yaml

from . import schema, setup_pi, utils


def setup(config: schema.Config, models: schema.Models) -> pathlib.Path:
    in_paths = [
        (pathlib.Path.home() / ".omp" / "agent" / "models.yml", "yaml"),
        (pathlib.Path.home() / ".omp" / "agent" / "models.yaml", "yaml"),
        (pathlib.Path.home() / ".omp" / "agent" / "models.json", "json"),
    ]
    models_path = pathlib.Path.home() / ".omp" / "agent" / "models.yml"
    providers = {}
    for in_path, in_format in in_paths:
        try:
            with in_path.open("rb") as f:
                match in_format:
                    case "yaml":
                        providers = yaml.safe_load(f)
                    case "json":
                        providers = simplejson.load(f)
            break
        except FileNotFoundError:
            pass
    if not isinstance(providers, dict):
        raise TypeError("models.yml should contain a JSON object")

    if "providers" not in providers:
        providers["providers"] = {}
    provider = setup_pi.setup_provider(config, models)
    if config.virtual_key:
        provider["apiKey"] = config.virtual_key
    for model in provider["models"]:
        if (
            not isinstance(model, dict)
            or "cost" not in model
            or not isinstance(model["cost"], dict)
        ):
            continue
        for k, v in model["cost"].items():
            if not isinstance(v, decimal.Decimal):
                continue
            try:
                model["cost"][k] = utils.decimal_as_int_exact(v)
            except decimal.Inexact, OverflowError, ValueError:
                model["cost"][k] = float(v)
    providers["providers"][config.bifrost_name] = provider

    with utils.AtomicFile(models_path, "w") as f:
        yaml.safe_dump(providers, f)

    return models_path
