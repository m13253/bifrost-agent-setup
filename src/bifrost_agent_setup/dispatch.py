import pathlib
from collections.abc import Callable

from . import schema, setup_omp, setup_pi, setup_vscode, setup_zed

type SetupFunction = Callable[[schema.Config, schema.Models], pathlib.Path | None]

DISPATCH_TABLE: dict[str, SetupFunction] = {
    "omp": setup_omp.setup,
    "pi": setup_pi.setup,
    "vscode": setup_vscode.setup,
    "zed": setup_zed.setup,
}
