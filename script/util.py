from pathlib import Path


def get_project_root() -> str:
    """Get the root directory of the project."""
    return str(Path(__file__).resolve().parent.parent)


def gather_directory(dir_path: Path) -> list[str]:
    test_py_files = dir_path.glob("*.py")
    test_files = [
        str(file)
        for file in test_py_files
        if file.is_file() and file.name != "__init__.py"
    ]
    for subdir in dir_path.iterdir():
        if subdir.is_dir():
            test_files.extend(gather_directory(subdir))
    return test_files
