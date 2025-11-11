from pathspec import PathSpec
from pathlib import Path


def check_path(path_spec: PathSpec, filepath: Path) -> bool:
    """
    Check if the given filepath should be skipped based on the skip config.
    """
    try:
        rel = filepath.relative_to(filepath.anchor)
    except Exception:
        # If cannot be made relative, use absolute but as posix
        rel = filepath
    rel_posix = rel.as_posix()
    return path_spec.match_file(rel_posix)
