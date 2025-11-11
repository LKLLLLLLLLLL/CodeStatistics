import argparse
import os
from .counter import counter
from .render import render_stats
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
    no_git_flag = bool(args.no_git)

    abs_path = Path(os.path.abspath(path))
    result = counter(abs_path, no_git_flag)
    render_stats(result)


if __name__ == "__main__":
    main()
