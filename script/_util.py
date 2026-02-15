import shutil
from pathlib import Path


def get_project_root() -> str:
    """Get the root directory of the project."""
    return str(Path(__file__).resolve().parent.parent)


def gather_directory(dir_path: Path, filter_paths: list[str] = []) -> list[str]:
    if not dir_path.exists():
        return []
    test_py_files = dir_path.glob("*.py")
    test_files = [
        str(file)
        for file in test_py_files
        if file.is_file() and file.name != "__init__.py"
    ]
    if filter_paths:
        test_files = [  # Only include filtered paths
            file
            for file in test_files
            if Path(file).relative_to(dir_path) in [Path(p) for p in filter_paths]
        ]
    for subdir in dir_path.iterdir():
        if subdir.is_dir():
            sub_filter_paths: list[str] = []
            skip_subdir = True
            if filter_paths:  # Skip subdirs that don't contain any of the filter paths
                subdir_relative = subdir.relative_to(dir_path)
                for p in filter_paths:
                    p_path = Path(p)
                    sub_part = str(p_path.relative_to(p_path.parent))
                    if p_path.parent == subdir_relative:
                        # Filter for subdir, only include paths that are directly under the subdir
                        if sub_part:
                            sub_filter_paths.append(sub_part)
                        skip_subdir = False
                if skip_subdir:
                    continue
            test_files.extend(gather_directory(subdir, sub_filter_paths))
    return test_files


def cleanup_temp_dirs(
    dir_path: Path,
    target_dir_names: tuple[str, ...] = (".typhon", ".typhon-server"),
) -> None:
    if not dir_path.exists():
        return

    temp_dirs = {
        temp_dir
        for target_dir_name in target_dir_names
        for temp_dir in dir_path.rglob(target_dir_name)
    }
    for temp_dir in sorted(temp_dirs, key=lambda p: len(p.parts), reverse=True):
        if temp_dir.is_dir():
            shutil.rmtree(temp_dir, ignore_errors=True)
