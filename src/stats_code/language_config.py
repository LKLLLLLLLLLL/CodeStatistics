import yaml
from pathlib import Path
from importlib.resources import files
from pathspec import PathSpec
from .utils import check_path

"""
Utils class for reading, validating the config provided by user.
It will provide detailed error message when encountering invalid config.s
"""

DEFAULT_CONFIG_PATH = Path(str(files("stats_code").joinpath("config/default.yml")))


class Language:
    def __init__(
        self,
        language_name: str,
        names: list[str],
        type: str,
        color: str,
    ) -> None:
        # validate inputs
        if not isinstance(language_name, str):
            raise TypeError("language_name must be a string.")
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            raise TypeError("names must be a list of strings.")
        if not isinstance(color, str):
            raise TypeError("color must be a string.")
        if not Language._validate_color_code(color):
            raise ValueError("color must be a valid hex color code.")
        # construct attributes
        self.language_name: str = language_name
        self.names: list[str] = names
        self.color: str = color
        self.type: str = type
        self._spec: PathSpec = PathSpec.from_lines("gitwildmatch", self.names)

    @staticmethod
    def _validate_color_code(color: str) -> bool:
        if len(color) != 7 or not color.startswith("#"):
            return False
        hex_digits = "0123456789abcdefABCDEF"
        for char in color[1:]:
            if char not in hex_digits:
                return False
        return True

    def __hash__(self) -> int:
        return hash(self.language_name)


class SkipConfig:
    def __init__(
        self,
        paths: list[str],
        language_types: list[str],
        languages: list[str],
    ) -> None:
        # validate inputs
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise TypeError("paths must be a list of strings.")
        if not isinstance(language_types, list) or not all(
            isinstance(lt, str) for lt in language_types
        ):
            raise TypeError("language_types must be a list of strings.")
        if not isinstance(languages, list) or not all(
            isinstance(lang, str) for lang in languages
        ):
            raise TypeError("languages must be a list of strings.")
        # construct attributes
        self.paths: list[str] = paths
        self.language_types: list[str] = language_types
        self.languages: list[str] = languages
        self._spec: PathSpec = PathSpec.from_lines("gitwildmatch", self.paths)


class LanguageConfig:
    class LookupTable:
        """
        A lookup table for quick language detection.
        """

        def __init__(self, languages: list[Language]) -> None:
            # exact filename -> language index
            self._exact_name_map: dict[str, int] = {}
            # extension -> language index
            self._extension_map: dict[str, int] = {}
            # pattern -> language index
            self._pattern_map: list[tuple[PathSpec, int]] = []
            self._unknown_language_index: int = len(languages) - 1

            # construct the maps
            for lang_index, lang in enumerate(languages):
                complex_patterns = []
                for pattern in lang.names:
                    # L1: exact filename match
                    if "*" not in pattern and "?" not in pattern and "[" not in pattern:
                        if pattern not in self._exact_name_map:
                            if (
                                pattern not in self._exact_name_map
                                or self._exact_name_map[pattern] > lang_index
                            ):
                                self._exact_name_map[pattern] = (
                                    lang_index  # only keep highest priority
                                )

                    # L2: simple extension pattern (*.ext)
                    elif (
                        pattern.startswith("*.")
                        and "*" not in pattern[2:]
                        and "?" not in pattern[2:]
                    ):
                        ext = pattern[1:]
                        if (
                            ext not in self._extension_map
                            or self._extension_map[ext] > lang_index
                        ):
                            self._extension_map[ext] = lang_index

                    # L3: complex patterns
                    else:
                        complex_patterns.append(pattern)
                if complex_patterns:
                    spec = PathSpec.from_lines("gitwildmatch", complex_patterns)
                    self._pattern_map.append((spec, lang_index))

        def lookup(self, filepath: Path) -> int | None:
            """
            Return the index of the language in the languages list.
            If no match found, return None.
            """
            filename = filepath.name

            # L1: match in O(1) time
            if filename in self._exact_name_map:
                return self._exact_name_map[filename]

            # L2: match in O(1) time
            if filepath.suffix:
                if filepath.suffix in self._extension_map:
                    ext_lang_index = self._extension_map[filepath.suffix]
                    # check if there is a higher priority complex pattern
                    for pattern, pattern_lang in self._pattern_map:
                        if pattern_lang < ext_lang_index:  # higher priority
                            if check_path(pattern, filepath):
                                return pattern_lang
                    return ext_lang_index

            # L3: match in O(n) time
            for pattern, lang_index in self._pattern_map:
                if check_path(pattern, filepath):
                    return lang_index

            # Fallback to Unknown language
            return self._unknown_language_index

    def __init__(
        self,
        skip: SkipConfig,
        languages: list[Language],
    ) -> None:
        self.skip = skip
        self.languages = languages
        try:
            self.validate()
        except ValueError as e:
            print(f"Error in LanguageConfig: {e}")
            raise e
        # construct a extension map for quick lookup
        self._lut = LanguageConfig.LookupTable(self.languages)

    def validate(self) -> None:
        # validate skip.language_types match languages
        for skip_lt in self.skip.language_types:
            if not any(lang.type == skip_lt for lang in self.languages):
                raise ValueError(
                    f"skip.language_types contains invalid type: {skip_lt}"
                )
        # validate skip.languages match languages
        for skip_lang in self.skip.languages:
            if not any(lang.language_name == skip_lang for lang in self.languages):
                raise ValueError(
                    f"skip.languages contains invalid language: {skip_lang}"
                )
        # validate if "Unknown" language exists
        if not any(lang.language_name == "Unknown" for lang in self.languages):
            raise ValueError('Language "Unknown" is not defined.')

    @classmethod
    def from_yaml(cls) -> "LanguageConfig":
        config_dict: dict
        path = DEFAULT_CONFIG_PATH
        with open(path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        # construct skip config
        try:
            skip_config = SkipConfig(
                paths=config_dict.get("skip", {}).get("paths", []),
                language_types=config_dict.get("skip", {}).get("language_types", []),
                languages=config_dict.get("skip", {}).get("languages", []),
            )
        except TypeError as e:
            print(f"Error in skip config: {e}")
            raise e
        # construct languages list
        languages_list = []
        for key, value in config_dict["languages"].items():
            try:
                language_obj = Language(
                    language_name=key,
                    names=value["names"],
                    color=value["color"],
                    type=value["type"],
                )
            except TypeError as e:
                print(f"Error in language config for '{key}': {e}")
                raise e
            languages_list.append(language_obj)
        return LanguageConfig(
            skip=skip_config,
            languages=languages_list,
        )

    def check_skip_by_config(self, filepath: Path) -> bool:
        """
        Check if the given filepath should be skipped based on the skip config.
        """
        if check_path(self.skip._spec, filepath):
            return True
        language = self.detect_language_by_path(filepath)
        if language.language_name in self.skip.languages:
            return True
        if language.type in self.skip.language_types:
            return True
        return False

    def detect_language_by_path(self, filepath: Path) -> Language:
        """
        Detect the language of the given filepath based on the language config.
        If no match found, throw assert error.
        """
        index = self._lut.lookup(filepath)
        if index is not None:
            return self.languages[index]
        raise AssertionError(f"No matching language found for file: {filepath}")

        # old, slow implementation
        # for language in self.languages:
        #     if check_path(language._spec, filepath):
        #         return language
        # raise AssertionError(f"No matching language found for file: {filepath}")
