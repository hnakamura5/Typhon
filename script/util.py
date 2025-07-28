import pathlib


def get_project_root() -> str:
    """Get the root directory of the project."""
    return str(pathlib.Path(__file__).resolve().parent.parent)
