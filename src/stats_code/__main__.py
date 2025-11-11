import argparse
import os
from stats_code.counter import counter_lines
from stats_code.render import render_stats
from stats_code.language_config import LanguageConfig
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Counter code lines in a github style."
    )
    parser.add_argument(
        "path", nargs="?", type=str, help="Path to the begin directory."
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Disable gitignore rules (enabled by default)",
    )

    args = parser.parse_args()
    path = args.path if args.path else os.getcwd()
    is_git_repo = not args.no_git

    abs_path = Path(os.path.abspath(path))
    result = counter_lines(abs_path, is_git_repo)
    render_stats(LanguageConfig.from_yaml(), result)


if __name__ == "__main__":
    main()
