from pathlib import Path
from multiprocessing import Pool, cpu_count
from .result import RepoStatsNode, Result
from .language_config import LanguageConfig
from .counter_worker import init_worker, process_file, Task

TASK_THRESHOLD = 1500


def collect_files(
    dir_path: Path,
    cur_node_id: int,
    no_git_flag: bool,
    ignore: list[Path],
) -> list[Task]:
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
                    ignore.append(dir_path / ".gitignore")
                    ignore_append_flag = True
                except Exception as e:
                    print(f"Error loading .gitignore in {dir_path}: {e}")
            new_repo_node = RepoStatsNode()
            RepoStatsNode.get_node_by_id(cur_node_id).submodules[dir_path.name] = (
                new_repo_node
            )
            cur_node_id = new_repo_node.id

    file_paths = []
    tasks = []
    for entry in dir_path.iterdir():
        if entry.is_dir():
            if entry.name == ".git":
                continue
            tasks.extend(collect_files(entry, cur_node_id, no_git_flag, ignore))
        elif entry.is_file():
            file_paths.append(entry)
    if file_paths:
        tasks.append((file_paths, cur_node_id, [p for p in ignore]))

    if ignore_append_flag:
        ignore.pop()
    return tasks


def counter(path: Path, no_git_flag: bool) -> Result:
    config = LanguageConfig.from_yaml()
    result = Result()

    # 1. collect tasks
    # each task process files in same dir (no recursion)
    tasks = collect_files(path, result.root_repo.id, no_git_flag, [])

    # 2. process tasks
    results: list[list[tuple[int, int, int]]] = []
    all_ignore_paths = {p for task in tasks for p in task[2]}
    if len(tasks) < TASK_THRESHOLD:
        # process in single process
        init_worker(config, all_ignore_paths)
        for task in tasks:
            results.append(process_file(task))
    else:
        print(f"Processing {len(tasks)} tasks with {cpu_count() + 1} processes...")
        with Pool(
            processes=cpu_count() + 1,
            initializer=init_worker,
            initargs=(config, all_ignore_paths),
        ) as pool:
            results = pool.map(process_file, tasks, chunksize=(cpu_count() + 1) * 2)

    # 3. aggregate results
    flatten_results = [item for sublist in results for item in sublist]
    for repo_node_id, language_id, line_count in flatten_results:
        repo_node = RepoStatsNode.get_node_by_id(repo_node_id)
        language = config.languages[language_id]
        repo_node.stats[language] = repo_node.stats.get(language, 0) + line_count
    return result
