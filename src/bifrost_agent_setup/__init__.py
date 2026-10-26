import argparse
import pathlib
from typing import cast

import dacite
import requests
import simplejson

from . import dispatch, schema, utils


def main(argv: list[str] | None = None) -> None:
    # Parse arguments
    argparser = argparse.ArgumentParser(
        prog="bifrost-agent-setup",
        description="Automatically set up your coding agents and LLM clients from Bifrost model catalog",
    )
    argparser.add_argument(
        "-c",
        "--config",
        default=pathlib.Path("config.json"),
        type=pathlib.Path,
        help="configuration file [default: config.json]",
    )
    argparser.add_argument(
        "agent",
        nargs="+",
        type=str.lower,
        help=f"coding agents and LLM clients to set up [supports: {', '.join(dispatch.DISPATCH_TABLE)}]",
        metavar="AGENT",
    )
    args = argparser.parse_args(argv[1:] if argv is not None else None)

    agents = set(cast(list[str], args.agent))
    for agent in agents:
        if agent not in dispatch.DISPATCH_TABLE:
            raise ValueError(f"Unsupported agent type: {agent}")

    # Load the config
    with cast(pathlib.Path, args.config).open("rb") as f:
        config = schema.from_dict_cast_int(
            schema.Config, simplejson.load(f, use_decimal=True)
        )

    # Download the model catalog
    models_url = utils.url_slash_join(config.bifrost_url, "v1/models")
    request_headers = utils.coalesce_dict(
        {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.virtual_key}"
            if config.virtual_key
            else None,
            "User-Agent": "bifrost-agent-setup",
        }
    )
    print(f"Loading {models_url}… ", end="", flush=True)
    with requests.get(models_url, headers=request_headers) as r:
        r.raise_for_status()
        models_json = r.text
    models = dacite.from_dict(
        schema.Models, simplejson.loads(models_json, use_decimal=True)
    )
    print(
        f"{len(models.data)} models loaded."
        if len(models.data) != 1
        else "1 model loaded.",
        flush=True,
    )

    # Dispatch into the setup functions
    for agent in agents:
        print(f"Setting up {agent}… ", end="", flush=True)
        path = dispatch.DISPATCH_TABLE[agent](config, models)
        if path is not None:
            print(f"Wrote {path}.", flush=True)
        else:
            print(flush=True)


if __name__ == "__main__":
    main()
