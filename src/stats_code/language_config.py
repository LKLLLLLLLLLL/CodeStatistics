import yaml
from pathlib import Path
from typing import Self
from pydantic import BaseModel, model_validator, PrivateAttr
from importlib.resources import files

CONFIG_PATH = str(files("stats_code").joinpath("config/default.yml"))

class Language(BaseModel):
    name: str
    exts: list[str]
    color: str | None

class LanguageConfig(BaseModel):
    languages: list[Language]
    skip_exts: list[str] = []
    skip_languages: list[str] = []
    _languages_map: dict[str, Language] = PrivateAttr()

    @model_validator(mode="after")
    def check_unknown(self) -> Self:
        unknown_langs = [lang for lang in self.languages if lang.name.lower() == "unknown"]
        if not unknown_langs:
            self.languages.append(Language(name="Unknown", exts=[], color=""))
        return self

    @model_validator(mode="after")
    def build_languages_map(self) -> Self:
        lang_map = {}
        for lang in self.languages:
            for ext in lang.exts:
                lang_map[ext] = lang
        self._languages_map = lang_map
        return self

    @classmethod
    def from_yaml(cls) -> "LanguageConfig":
        config_dict: dict
        path = Path(CONFIG_PATH)
        with open(path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        languages_list = []
        for key, value in config_dict["languages"].items():
            languages_list.append(
                Language(
                    name=key,
                    exts=value["exts"],
                    color=value["color"],
                )
            )
        return LanguageConfig(
            languages=languages_list,
            skip_exts=config_dict.get("skip_exts", []),
            skip_languages=config_dict.get("skip_languages", []),
        )
    
    def needs_skip(self, filename: str) -> bool:
        ext = Path(filename).suffix
        lang = self.get_language_by_extension(ext)
        if lang.name in self.skip_languages:
            return True
        return ext in self.skip_exts

    def get_language_by_extension(self, ext: str) -> Language:
        language = self._languages_map.get(ext)
        if language is None:
            for lang in self.languages:
                if lang.name.lower() == "unknown":
                    return lang
        assert language is not None
        return language

    def get_language_by_name(self, name: str) -> Language:
        for lang in self.languages:
            if lang.name == name:
                return lang
        for lang in self.languages:
            if lang.name.lower() == "unknown":
                return lang
        raise AssertionError("Unknown language not found in config.")