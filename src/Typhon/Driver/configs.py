from typing import Literal

_language_backend: Literal["pyrefly", "pyright"] = "pyrefly"
# TODO: Basedpyright seems to hang on semantic tokens request
_language_backend = "pyright"


def set_language_backend(backend: Literal["pyrefly", "pyright"]):
    global _language_backend
    _language_backend = backend


def get_language_backend() -> Literal["pyrefly", "pyright"]:
    return _language_backend
