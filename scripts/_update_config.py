import yaml
from jinja2 import Environment, BaseLoader
import os
import sys
from pathlib import Path
from importlib.resources import files
from typing import Any
import json

LINGUIST_BASE_DIR = Path(str(files(__name__).joinpath("../linguist")))
LINGUIST_CONFIG_DIR = LINGUIST_BASE_DIR / "lib" / "linguist"
CONFIG_BASE_DIR = Path(__file__).parent.parent / "src" / "stats_code" / "config"
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

def _update_by_vendor(files: dict[str, dict], config: dict[str, Any]) -> None:
    skip_path_regs = files["vendor.yml"]
    assert isinstance(skip_path_regs, list)
    config["skip"] = {"path": skip_path_regs}
    return
    
def _load_by_documentation(files: dict[str, dict], config: dict[str, Any]) -> None:
    skip_documentation_regs = files["documentation.yml"]
    assert isinstance(skip_documentation_regs, list)
    config["skip"]["documentation"] = skip_documentation_regs
    return

def _load_by_languages(files: dict[str, dict], config: dict[str, Any]) -> None:
    languages = files["languages.yml"]
    assert isinstance(languages, dict)
    lang_config: dict[str, dict[str, Any]] = {}
    for lang_name, lang_info in languages.items():
        if not isinstance(lang_info, dict):
            continue
        extensions = lang_info.get("extensions", [])
        filenames = lang_info.get("filenames", [])
        color = lang_info.get("color")
        type = lang_info.get("type")
        if not extensions and not filenames:
            continue
        lang_config[lang_name] = { "rules": [] }
        if color:
            lang_config[lang_name]["color"] = color
        if type:
            lang_config[lang_name]["type"] = type
        if extensions:
            lang_config[lang_name]["rules"].extend([{"name": "*" + extension} for extension in extensions])
        if filenames:
            lang_config[lang_name]["rules"].extend([{"name": filename} for filename in filenames])
    config["languages"] = lang_config
    return

def _load_by_heuristics(files: dict[str, dict], config: dict[str, Any]) -> None:
    heuristics = files["heuristics.yml"]
    assert isinstance(heuristics, dict)
    
    def gather_patterns(heuristics: dict) -> dict[tuple[str, str], tuple[list[str], list[str]]]:
        """
        Gather patterns from heuristics and return a mapping from (language, extension) to (positive_patterns, negative_patterns).
        """
        disambiguations = heuristics.get("disambiguations", [])
        pattern_map: dict[tuple[str, str], tuple[list[str], list[str]]] = {}
        def get_patterns_by_name(name: str) -> list[str]:
            patterns = heuristics.get("named_patterns", {})
            assert isinstance(patterns, dict)
            pattern_info = patterns.get(name, [])
            if isinstance(pattern_info, list):
                return pattern_info
            elif isinstance(pattern_info, str):
                return [pattern_info]
            else:
                return []
        def collect_patterns(rule: dict) -> tuple[list[str], list[str]]:
            pos_patterns: list[str] = []
            neg_patterns: list[str] = []
            if "pattern" in rule:
                pos_patterns.extend([rule["pattern"]] if isinstance(rule["pattern"], str) else rule["pattern"])
            if "named_pattern" in rule:
                pos_patterns.extend(get_patterns_by_name(rule["named_pattern"]))
            if "negative_pattern" in rule:
                neg_patterns.extend([rule["negative_pattern"]] if isinstance(rule["negative_pattern"], str) else rule["negative_pattern"])
            if "and" in rule:
                for sub_rule in rule["and"]:
                    assert isinstance(sub_rule, dict)
                    sub_pos, sub_neg = collect_patterns(sub_rule)
                    pos_patterns.extend(sub_pos)
                    neg_patterns.extend(sub_neg)
            return pos_patterns, neg_patterns

        for disambiguation in disambiguations:
            extensions: list[str] = disambiguation.get("extensions", [])
            extension_rules: list[dict[str, Any]] = disambiguation.get("rules", [])
            for extension in extensions:
                for extension_rule in extension_rules:
                    language = extension_rule.get("language")
                    pos_patterns, neg_patterns = collect_patterns(extension_rule)
                    if isinstance(language, str):
                        key = (language, extension)
                        if key not in pattern_map:
                            pattern_map[key] = ([], [])
                        pattern_map[key][0].extend(pos_patterns)
                        pattern_map[key][1].extend(neg_patterns)
                    elif isinstance(language, list):
                        for lang in language:
                            key = (lang, extension)
                            if key not in pattern_map:
                                pattern_map[key] = ([], [])
                            pattern_map[key][0].extend(pos_patterns)
                            pattern_map[key][1].extend(neg_patterns)
                    else:
                        raise AssertionError("language must be str or list")
            
    
    def update_pattern_to_language(language: str, extension: str, pattern_info: dict[str, Any]) -> None:
        assert isinstance(language, str)
        pos_patterns: list[str] = []
        neg_patterns: list[str] = []
        if "pattern" in pattern_info:
            pos_patterns.extend([pattern_info["pattern"]] if isinstance(pattern_info["pattern"], str) else pattern_info["pattern"])
        if "named_pattern" in pattern_info:
            pos_patterns.extend(get_patterns_by_name(pattern_info["named_pattern"]))
        if "negative_pattern" in pattern_info:
            neg_patterns.extend([pattern_info["negative_pattern"]] if isinstance(pattern_info["negative_pattern"], str) else pattern_info["negative_pattern"])
        if "and" in pattern_info:
            for pattern in pattern_info["and"]:
                assert isinstance(pattern, dict)
                if "pattern" in pattern:
                    pos_patterns.extend(pattern["pattern"] if isinstance(pattern["pattern"], list) else [pattern["pattern"]])
                if "named_pattern" in pattern:
                    pos_patterns.extend(get_patterns_by_name(pattern["named_pattern"]))
                if "negative_pattern" in pattern:
                    neg_patterns.extend(pattern["negative_pattern"] if isinstance(pattern["negative_pattern"], list) else [pattern["negative_pattern"]])
        else:
            return
        print(f"Updating language '{language}' for extension '{extension}' with patterns: +{pos_patterns}, -{neg_patterns}")
        old_rule = {"name": extension}
        language_rules = config["languages"][language]["rules"]
        if old_rule in language_rules:
            assert isinstance(old_rule, dict)
            index = language_rules.index(old_rule)
            if pos_patterns:
                language_rules[index] = language_rules[index] | {"patterns": pos_patterns}
            if neg_patterns:
                language_rules[index] = language_rules[index] | {"negative_patterns": neg_patterns}
        else:
            new_rule: dict[str, Any] = {"name": extension}
            if pos_patterns:
                new_rule["patterns"] = pos_patterns
            if neg_patterns:
                new_rule["negative_patterns"] = neg_patterns
            language_rules.append(new_rule)
    
    # add regex patterns to exists rules in languages
    for disambiguation in heuristics.get("disambiguations", []):
        extensions: list[str] = disambiguation.get("extensions", [])
        extension_rules: list[dict[str, Any]] = disambiguation.get("rules", [])
        for extension in extensions:
            for extension_rule in extension_rules:
                language = extension_rule.get("language")
                # print(language)
                if isinstance(language, str):
                    update_pattern_to_language(language, extension, extension_rule)
                elif isinstance(language, list):
                    for lang in language:
                        update_pattern_to_language(lang, extension, extension_rule)
                else:
                    raise AssertionError("language must be str or list")     
    # print(json.dumps(config["languages"], indent=4))  # Debug output
    return


def _render_config_template(template_str: str, context: dict[str, Any]) -> str:
    env = Environment(loader=BaseLoader())
    def to_yaml(value: Any, prefix: int = 0) -> str:
        yaml_str = yaml.dump(value, default_flow_style=False, indent=4)
        if prefix > 0:
            prefix_str = ' ' * prefix
            yaml_str = '\n'.join(prefix_str + line for line in yaml_str.split('\n'))
        return yaml_str
    env.filters["to_yaml"] = to_yaml
    template = env.from_string(template_str)
    return template.render(context)

def main():
    files = _read_linguist_yaml()
    default_config: dict[str, dict] = {}
    _update_by_vendor(files, default_config)
    _load_by_documentation(files, default_config)
    _load_by_languages(files, default_config)
    _load_by_heuristics(files, default_config)
    # print(default_config)
    with open(CONFIG_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_str = f.read()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(_render_config_template(template_str, default_config))
    print(f"Updated config written to {CONFIG_PATH}")

if __name__ == "__main__":
    main()