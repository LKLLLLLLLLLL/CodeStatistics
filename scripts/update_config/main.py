import yaml
from jinja2 import Environment, BaseLoader
import os
import sys
from pathlib import Path
from importlib.resources import files
from typing import Any
from .models.linguis_models import (
    LinguistVendor,
    LinguistDocumentation,
    LanguageEntry,
    LinguistLanguages,
    LinguistHeuristics,
)
from .models.config_model import Config

LINGUIST_BASE_DIR = Path(str(files(__name__).joinpath("../../linguist")))
LINGUIST_CONFIG_DIR = LINGUIST_BASE_DIR / "lib" / "linguist"
CONFIG_BASE_DIR = Path(__file__).parent.parent.parent / "src" / "stats_code" / "config"
CONFIG_PATH = CONFIG_BASE_DIR / "default.yml"
CONFIG_TEMPLATE_PATH = CONFIG_BASE_DIR / "default.yml.j2"


def _read_linguist_yaml() -> dict[str, dict]:
    if not os.path.exists(LINGUIST_CONFIG_DIR):
        print(f"Linguist config directory not found at {LINGUIST_CONFIG_DIR}")
        sys.exit(1)
    file_names = [
        "documentation.yml",
        "heuristics.yml",
        "languages.yml",
        "vendor.yml",
        # skip generic.yml and popular.yml
    ]
    results = {}
    for file_name in file_names:
        file_path = LINGUIST_CONFIG_DIR / file_name
        if not os.path.exists(file_path):
            print(f"Linguist config file not found at {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            results[file_name] = yaml.safe_load(f)
    return results


def _update_by_vendor(files: dict[str, dict], config: Config) -> None:
    skip_path_regs = files["vendor.yml"]
    assert isinstance(skip_path_regs, list)
    linguist_vendor = LinguistVendor(skip_path_regs)
    config.skip["path"] = linguist_vendor.model_dump()
    return


def _load_by_documentation(files: dict[str, dict], config: Config) -> None:
    skip_documentation_regs = files["documentation.yml"]
    assert isinstance(skip_documentation_regs, list)
    linguist_documentation = LinguistDocumentation(skip_documentation_regs)
    config.skip["documentation"] = (linguist_documentation.model_dump())
    return


def _load_by_languages(files: dict[str, dict], config: Config) -> None:
    languages = files["languages.yml"]
    linguist_languages: LinguistLanguages = LinguistLanguages(languages)
    for name, entry in linguist_languages.model_dump().items():
        entry = LanguageEntry(**entry)
        rules: list[Config.Language.Rule] = []
        for filename in entry.filenames or []:
            rules.append(Config.Language.Rule(name_pattern=filename))
        for extension in entry.extensions or []:
            rules.append(Config.Language.Rule(name_pattern=f"*{extension}"))
        config.languages[name] = Config.Language(
            color=entry.color,
            type=entry.type,
            rules=rules,
        )
    return


def _load_by_heuristics(files: dict[str, dict], config: Config) -> None:
    heuristics = files["heuristics.yml"]
    linguist_heuristics = LinguistHeuristics(**heuristics)
    def get_named_pattern(name: str) -> list[str]:
        named_patterns = linguist_heuristics.named_patterns
        patterns = named_patterns.get(name)
        assert patterns is not None
        if isinstance(patterns, list):
            return patterns
        return [patterns]
    for disambiguation in linguist_heuristics.disambiguations:
        for extension in disambiguation.extensions:
            for rule in disambiguation.rules:
                language_name = rule.language
                rule_index : int
                for language_rule in config.languages[language_name].rules:
                    if language_rule.name_pattern == f"*{extension}":
                        rule_index = config.languages[language_name].rules.index(language_rule)
                        break
                
                
    return


def _render_config_template(template_str: str, context: Config) -> str:
    env = Environment(loader=BaseLoader())

    def to_yaml(value: Any, prefix: int = 0) -> str:
        yaml_str = yaml.dump(value, default_flow_style=False, indent=4)
        if prefix > 0:
            prefix_str = " " * prefix
            yaml_str = "\n".join(prefix_str + line for line in yaml_str.split("\n"))
        return yaml_str

    env.filters["to_yaml"] = to_yaml
    template = env.from_string(template_str)
    return template.render(context.model_dump())


def main():
    files = _read_linguist_yaml()
    default_config: Config = Config()
    _update_by_vendor(files, default_config)
    _load_by_documentation(files, default_config)
    _load_by_languages(files, default_config)
    _load_by_heuristics(files, default_config)
    # print(default_config)
    with open(CONFIG_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_str = f.read()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        rendered_config = _render_config_template(template_str, default_config)
        f.write(rendered_config)
    print(f"Updated config written to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
