from pathlib import Path
from stats_code.language_config import LanguageConfig
import os
import chardet

def _detect_file_encoding(file_path: Path) -> str | None:
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        confidence = result['confidence']
        if confidence and confidence > 0.7:
            return result['encoding']
        return None
    except Exception as e:
        print(f"Error detecting encoding for {file_path}: {e}")
        return None

def _counter_lines_in_file(file_path: Path, config: LanguageConfig) -> dict[str, int]:
    encoding = _detect_file_encoding(file_path)
    if not encoding:
        return {}
    ext = file_path.suffix
    if config.needs_skip(ext):
        return {}
    language = config.get_language_by_extension(ext)
    lines = []
    try:
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    lines_count = 0
    for line in lines:
        if not line.strip() == "":
            lines_count += 1
    return {language.name: lines_count}

def counter_lines(path: Path, is_git_repo: bool) -> dict[str, int]:
    config = LanguageConfig.from_yaml()
    total_counts: dict[str, int] = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            file_counts = _counter_lines_in_file(file_path, config)
            for lang, count in file_counts.items():
                if lang in total_counts:
                    total_counts[lang] += count
                else:
                    total_counts[lang] = count
    return total_counts
