import argparse
import os
from stats_code.counter import counter_lines
from stats_code.render import render_stats
from stats_code.language_config import LanguageConfig
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Counter code lines in a github style.")
    parser.add_argument("path", nargs="?", type=str, help="Path to the begin directory.")
    parser.add_argument("-g", "--git-repo", action="store_true", default=True, help="Indicate the path is a git repository. If set, will implement gitignore rules.")

    args = parser.parse_args()
    path = args.path if args.path else os.getcwd()
    is_git_repo = args.git_repo

    abs_path = Path(os.path.abspath(path))
    result = counter_lines(abs_path, is_git_repo)
    render_stats(LanguageConfig.from_yaml(), result)

if __name__ == "__main__":
    main()