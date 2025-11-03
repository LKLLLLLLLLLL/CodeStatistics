import sys
from pathlib import Path
import subprocess
import shutil

def _get_uv_path() -> str:
    # get uv path
    uv_prefix = shutil.which("uv")
    if uv_prefix is None:
        print("uv command not found. Please check if uv is in your PATH.")
        sys.exit(1)
    return uv_prefix

def _install_dependencies():
    """Install required dependencies for building the package."""
    uv_prefix = _get_uv_path()
    # install python dependencies
    subprocess.run([uv_prefix, "sync"], check=True)
    # get git path
    git_prefix = shutil.which("git")
    if git_prefix is None:
        print("git command not found. Please check if git is in your PATH.")
        sys.exit(1)
    # install submodules
    subprocess.run([git_prefix, "submodule", "update", "--init", "--depth", "1"], check=True)

def _build_package():
    """Build the package using setuptools."""
    # remove previous build artifacts
    dist_path = Path("dist")
    if dist_path.exists() and dist_path.is_dir():
        shutil.rmtree(dist_path)
    # build the package
    uv_prefix = _get_uv_path()
    subprocess.run([uv_prefix, "build"], check=True)

def main():
    _install_dependencies()
    _build_package()
    print("Build completed successfully.")

if __name__ == "__main__":
    main()