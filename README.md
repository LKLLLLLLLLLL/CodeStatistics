# Code Statistics
A full python tool to gather statistics from your codebase.
It can be customized flexibly to fit your needs.

## Quick Start
Install the package via pip:
```bash
pip install stats-code
```

Run the tool on your codebase:
```bash
stats-code
```

Or specify a directory:
```bash
stats-code /path/to/your/codebase
```

In default, the tool will read `.gitignore` file to exclude files and directories. But you can disable this behavior with `--no-git` flag:
```bash
stats-code --no-git
```

## Development
### Use uv (Recommand)
If you have `uv` installed, you can begin development with:
```bash
uv sync
```
Run the tool:
```bash
uv run -m src.stats_code
```

### Use pip
Install development dependencies:
```bash
pip install -e .
```
Run the tool:
```bash
python -m src.stats_code
```

