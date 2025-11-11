import chardet
import re
from pathlib import Path
from pathspec import PathSpec
from .utils import check_path
from .result import RepoStatsNode, Result
from .language_config import LanguageConfig


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


def _counter_dir(
    dir_path: Path,
    config: LanguageConfig,
    cur_node: RepoStatsNode,
    no_git_flag: bool,
    ignore: list[PathSpec],
) -> None:
    """
    A recursive function to count lines in all files under a directory.
    """
    ignore_append_flag: bool = False
    if not no_git_flag:
        if (dir_path / ".git").exists():
            # is a git repo
            if (dir_path / ".gitignore").exists():
                try:
                    with (dir_path / ".gitignore").open(
                        "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        ignore.append(
                            PathSpec.from_lines("gitwildmatch", f.readlines())
                        )
                        ignore_append_flag = True
                except Exception as e:
                    print(f"Error loading .gitignore in {dir_path}: {e}")
            new_repo_node = RepoStatsNode()
            cur_node.submodules[dir_path.name] = new_repo_node
            cur_node = new_repo_node

    def check_ignore(path: Path) -> bool:
        for spec in ignore:
            if check_path(spec, path):
                return True
        return False

    for entry in dir_path.iterdir():
        git_files = r".*\.git.*?"  # pattern like `.gitignore`, `.gitsubmodule` ...
        if re.match(git_files, entry.name):
            continue
        if entry.is_dir():
            _counter_dir(entry, config, cur_node, no_git_flag, ignore)
        elif entry.is_file():
            if check_ignore(entry):
                continue
            if config.check_skip_by_config(entry):
                continue
            language = config.detect_language_by_path(entry)
            file_counts = _counter_lines_in_file(entry)
            cur_node.stats[language] = cur_node.stats.get(language, 0) + file_counts

    if ignore_append_flag:
        ignore.pop()
    return


def counter(path: Path, no_git_flag: bool) -> Result:
    config = LanguageConfig.from_yaml()
    result = Result()
    _counter_dir(path, config, result.root_repo, no_git_flag, [])
    return result
