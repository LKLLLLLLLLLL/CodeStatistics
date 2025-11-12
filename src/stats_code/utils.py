import chardet
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


def _detect_file_encoding(file_path: Path) -> str | None:
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        confidence = result["confidence"]
        if confidence and confidence > 0.7:
            return result["encoding"]
        return None
    except Exception as e:
        print(f"Error detecting encoding for {file_path}: {e}")
        return None


def counter_lines_in_file(file_path: Path) -> int:
    encoding = _detect_file_encoding(file_path)
    if not encoding:
        return 0
    lines = []
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    # lines_count = sum(1 for line in lines if line.strip())
    lines_count = len(lines)
    return lines_count
