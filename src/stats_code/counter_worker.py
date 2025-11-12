import re
from pathlib import Path
from pathspec import PathSpec
from .utils import check_path, counter_lines_in_file
from .language_config import LanguageConfig

# (file_path, repo_node_id, .gitignore_file_paths, language_config)
Task = tuple[list[Path], int, list[Path]]

worker_language_config: LanguageConfig | None = None
worker_ignore_specs: dict[Path, PathSpec] = {}
git_re: re.Pattern | None = None


def check_ignore(path: Path) -> bool:
    for spec in worker_ignore_specs.values():
        if check_path(spec, path):
            return True
    return False


def init_worker(config: LanguageConfig, ignore_paths: set[Path]) -> None:
    """
    Initializer for each worker process.
    """
    global worker_language_config, worker_ignore_specs, git_re
    worker_language_config = config
    for path in ignore_paths:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            worker_ignore_specs[path] = PathSpec.from_lines(
                "gitwildmatch", f.readlines()
            )
    git_re = re.compile(r".*\.git.*?")  # pattern like `.gitignore`, `.gitsubmodule` ...


def process_file(task: Task) -> list[tuple[int, int, int]]:
    """
    Task for a worker process to determin if a file needs to be counted and count lines.
    return:
        tuple of (repo_node_id, language_id, line_count)
    """
    file_paths, repo_node_id, ignores = task

    global worker_language_config, worker_ignore_specs, git_re
    assert worker_language_config is not None
    assert worker_ignore_specs is not None
    assert git_re is not None

    results: list[tuple[int, int, int]] = []
    assert len(file_paths) > 0
    for file_path in file_paths:
        if git_re.match(file_path.name):
            continue
        if check_ignore(file_path):
            continue
        if worker_language_config.check_skip_by_config(file_path):
            continue
        language_id = worker_language_config.detect_language_by_path(file_path)
        line_count = counter_lines_in_file(file_path)
        results.append((repo_node_id, language_id, line_count))

    return results
