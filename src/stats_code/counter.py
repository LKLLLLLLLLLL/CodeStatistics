from pathlib import Path
from stats_code.language_config import LanguageConfig
import os
import chardet
from typing import Optional
from pathspec import PathSpec

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

def _counter_lines_in_file(file_path: Path, config: LanguageConfig) -> dict[str, int]:
    encoding = _detect_file_encoding(file_path)
    if not encoding:
        return {}
    ext = file_path.suffix
    if config.needs_skip(filename=file_path.name):
        return {}
    language = config.get_language_by_extension(ext)
    lines = []
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    lines_count = sum(1 for line in lines if line.strip())
    return {language.name: lines_count}


def _is_ignored(path_obj: Path, base: Path, spec: Optional[PathSpec]) -> bool:
    """Return True if path_obj (file or dir) is matched by spec.
    Use POSIX-style relative path for matching.
    """
    if not spec:
        return False
    try:
        rel = path_obj.relative_to(base)
    except Exception:
        # If cannot be made relative, use absolute but as posix
        rel = path_obj
    rel_posix = rel.as_posix()
    return spec.match_file(rel_posix)


def counter_lines(path: Path, is_git_repo: bool) -> dict[str, int]:
    config = LanguageConfig.from_yaml()
    total_counts: dict[str, int] = {}

    # Load .gitignore as a PathSpec when requested
    spec: Optional[PathSpec] = None
    if is_git_repo:
        gitignore_path = path / ".gitignore"
        if gitignore_path.exists():
            try:
                with gitignore_path.open("r", encoding="utf-8", errors="ignore") as f:
                    spec = PathSpec.from_lines("gitwildmatch", f.readlines())
            except Exception as e:
                print(f"Error loading .gitignore: {e}")
                spec = None

    for root, dirs, files in os.walk(path):
        root_path = Path(root)
        # avoid recursing into .git directory
        if is_git_repo and ".git" in dirs:
            dirs.remove(".git")

        # Remove ignored directories from dirs so os.walk won't descend into them
        if spec:
            for d in list(dirs):
                dir_path = root_path / d
                if _is_ignored(dir_path, path, spec):
                    dirs.remove(d)
                    # optional debug:
                    # print(f"Skipping ignored directory: {dir_path}")

        for file in files:
            file_path = root_path / file
            # if pathspec loaded, check the relative path against the spec
            if _is_ignored(file_path, path, spec):
                # optional debug:
                # print(f"Skipping ignored file: {file_path}")
                continue
            file_counts = _counter_lines_in_file(file_path, config)
            for lang, count in file_counts.items():
                if lang in total_counts:
                    total_counts[lang] += count
                else:
                    total_counts[lang] = count
    return total_counts
