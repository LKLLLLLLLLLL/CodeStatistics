from stats_code.language_config import LanguageConfig
from rich.console import Console
from rich.table import Table

def render_stats(language_config: LanguageConfig, stats: dict[str, int]) -> None:
    console = Console()
    table = Table(title="Code Statistics")

    table.add_column("Language", justify="left", style="cyan", no_wrap=True)
    table.add_column("Lines of Code", justify="right", style="magenta")

    for lang_name, line_count in stats.items():
        language = language_config.get_language_by_name(lang_name)
        color = (
            language.color
            if language and getattr(language, "color", None)
            else "white"
        )
        table.add_row(f"[{color}]{lang_name}[/{color}]", str(line_count))

    console.print(table)