import contextlib
import copy
import decimal
import os
import pathlib
import tempfile
import urllib.parse
from collections.abc import Generator
from typing import IO, Any


def coalesce_dict[T, U](d: dict[T, U | None]) -> dict[T, U]:
    return {k: v for k, v in d.items() if v is not None}


def decimal_as_int_exact(n: decimal.Decimal) -> int:
    return int(n.to_integral_exact(context=decimal.Context(traps=[decimal.Inexact])))


def url_slash_join(base: str, url: str) -> str:
    base_split = urllib.parse.urlsplit(base, missing_as_none=True)
    if base_split.path and not base_split.path.endswith("/"):
        base_split = copy.replace(base_split, path=base_split.path + "/")
    return urllib.parse.urljoin(base_split.geturl(), url)


@contextlib.contextmanager
def AtomicFile(
    path: pathlib.Path, mode: str = "w+b", *args, **kwargs
) -> Generator[IO[Any]]:
    def cleanup(temp_path: str) -> None:
        try:
            os.unlink(temp_path)
        except Exception:  # noqa
            pass

    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    with (
        contextlib.ExitStack() as stack,
        tempfile.NamedTemporaryFile(
            *args, mode=mode, dir=dir_path, delete=False, **kwargs
        ) as f,
    ):
        stack.callback(cleanup, f.name)
        yield f
        try:
            os.chmod(f.name, path.stat().st_mode)
        except Exception:  # noqa
            # Either stat() or chmod() is not available on this OS or filesystem.
            pass
        os.replace(f.name, path)
        stack.pop_all()
