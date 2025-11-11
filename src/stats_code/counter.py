from pathlib import Path
from stats_code.language_config import LanguageConfig, Language
import os
import chardet
from typing import Optional
from pathspec import PathSpec
from stats_code.utils import check_path

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

def _counter_lines_in_file(file_path: Path) -> int:
    encoding = _detect_file_encoding(file_path)
    if not encoding:
        return 0
    lines = []
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    lines_count = sum(1 for line in lines if line.strip())
    return lines_count

def counter_lines(path: Path, is_git_repo: bool) -> dict[Language, int]:
    config = LanguageConfig.from_yaml()
    total_counts: dict[Language, int] = {}

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
                if check_path(spec, dir_path):
                    dirs.remove(d)

        for file in files:
            file_path = root_path / file
            # if pathspec loaded, check the relative path against the spec
            if spec is not None and check_path(spec, file_path):
                continue
            if config.check_skip_by_config(file_path):
                continue
            language = config.detect_language_by_path(file_path)
            file_counts = _counter_lines_in_file(file_path)
            total_counts[language] = total_counts.get(language, 0) + file_counts
    return total_counts
