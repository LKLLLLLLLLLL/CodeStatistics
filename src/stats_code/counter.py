import chardet
import re
from pathlib import Path
from multiprocessing import Pool, cpu_count
from pathspec import PathSpec
from .utils import check_path
from .result import RepoStatsNode, Result
from .language_config import LanguageConfig, Language


TASK_THREASHOLD = 5000


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


def count_lines_task(file_path: Path) -> tuple[Path, int]:
    """Task for a worker process to count lines in a single file."""
    return file_path, _counter_lines_in_file(file_path)


def _collect_files(
    dir_path: Path,
    config: LanguageConfig,
    cur_node: RepoStatsNode,
    no_git_flag: bool,
    ignore: list[PathSpec],
) -> list[tuple[Path, RepoStatsNode, Language]]:
    """
    A recursive function to count lines in all files under a directory.
    Returns a list of tuples (file_path, repo_node, language).
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

    tasks = []
    for entry in dir_path.iterdir():
        git_files = r".*\.git.*?"  # pattern like `.gitignore`, `.gitsubmodule` ...
        if re.match(git_files, entry.name):
            continue
        if entry.is_dir():
            tasks.extend(_collect_files(entry, config, cur_node, no_git_flag, ignore))
        elif entry.is_file():
            if check_ignore(entry):
                continue
            if config.check_skip_by_config(entry):
                continue
            language = config.detect_language_by_path(entry)
            tasks.append((entry, cur_node, language))

    if ignore_append_flag:
        ignore.pop()
    return tasks


def counter(path: Path, no_git_flag: bool) -> Result:
    config = LanguageConfig.from_yaml()
    result = Result()
    tasks = _collect_files(path, config, result.root_repo, no_git_flag, [])

    if len(tasks) < TASK_THREASHOLD:
        # process in single process
        for file_path, repo_node, language in tasks:
            line_count = _counter_lines_in_file(file_path)
            repo_node.stats[language] = repo_node.stats.get(language, 0) + line_count
        return result

    task_result_map = {task[0]: (task[1], task[2]) for task in tasks}

    with Pool(processes=cpu_count()) as pool:
        file_paths = [task[0] for task in tasks]
        line_counts = pool.map(_counter_lines_in_file, file_paths)

    for file_path, line_count in zip(file_paths, line_counts):
        if file_path in task_result_map:
            repo_node, language = task_result_map[file_path]
            repo_node.stats[language] = repo_node.stats.get(language, 0) + line_count

    return result
