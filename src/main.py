import argparse
import os
from src.counter import counter_lines
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Counter code lines in a github style.")
    parser.add_argument("path", nargs="?", type=str, help="Path to the begin directory.")
    parser.add_argument("-g", "--git-repo", action="store_true", help="Indicate the path is a git repository. If set, will implement gitignore rules.")

    args = parser.parse_args()
    path = args.path if args.path else os.getcwd()
    is_git_repo = args.git_repo

    abs_path = Path(os.path.abspath(path))
    result = counter_lines(abs_path, is_git_repo)
    for lang, count in result.items():
        print(f"{lang}: {count}")

if __name__ == "__main__":
    main()