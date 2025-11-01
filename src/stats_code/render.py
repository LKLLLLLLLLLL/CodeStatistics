from stats_code.language_config import LanguageConfig
from rich.console import Console
from rich.table import Table
from rich.progress_bar import ProgressBar

def render_stats(language_config: LanguageConfig, stats: dict[str, int]) -> None:
    console = Console()
    table = Table(title="Code Statistics")

    table.add_column("Language", justify="left", style="cyan", no_wrap=True)
    table.add_column("Lines of Code", justify="right", style="magenta")
    table.add_column("Distribution", justify="left", style="yellow")
    table.add_column("Percentage", justify="right", style="green")
    sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1], reverse=True))

    total_lines = sum(sorted_stats.values())
    total_bar = ProgressBar(total=100.0, completed=100.0, width=30, complete_style="white", finished_style="white")
    table.add_row("Total", str(total_lines), total_bar, None, style="bold white")
    for lang_name, line_count in sorted_stats.items():
        language = language_config.get_language_by_name(lang_name)
        color = (
            language.color
            if language and getattr(language, "color", None)
            else "white"
        )
        assert color is not None
        percentage = (line_count / total_lines * 100) if total_lines > 0 else 0
        bar = ProgressBar(total=100.0, completed=percentage, width=30, complete_style=color, finished_style=color)
        table.add_row(f"[{color}]{lang_name}[/{color}]", str(line_count), bar, f"{percentage:.2f}%")

    console.print(table)