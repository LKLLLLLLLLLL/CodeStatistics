from pydantic import BaseModel, model_validator, Field, RootModel
from typing import Self

"""
This file models the configuration of linguist and stats-code.
"""
class LinguistVendor(RootModel[list[str]]):
    """
    Vendor.yml
    """
    pass

class LinguistDocumentation(RootModel[list[str]]):
    """
    Documentation.yml
    """
    pass

class LanguageEntry(BaseModel):
    type: str
    color: str | None = None
    group: str | None = None
    aliases: list[str] | None = None
    extensions: list[str] | None = None
    filenames: list[str] | None = None
    interpreters: list[str] | None = None
    ace_mode: str
    tm_scope: str
    codemirror_mode: str | None = None
    codemirror_mime_type: str | None = None
    language_id: int

class LinguistLanguages(RootModel[dict[str, LanguageEntry]]):
    """
    Languages.yml
    """
    pass

class LinguistHeuristics(BaseModel):
    """
    Heuristics.yml
    """
    class DisambiguationEntry(BaseModel):
        class RuleEntry(BaseModel):
            class PatternEntry(BaseModel):
                pattern: str | list[str] | None = None
                negative_pattern: str | list[str] | None = None
                named_pattern: str | None = None
                @model_validator(mode="after")
                def validate_pattern(self) -> Self:
                    # only allowed one of pattern, negative_pattern, named_pattern
                    patterns = set()
                    if self.pattern:
                        patterns.add("pattern")
                    if self.negative_pattern:
                        patterns.add("negative_pattern")
                    if self.named_pattern:
                        patterns.add("named_pattern")
                    if len(patterns) > 1:
                        raise ValueError("Only one of pattern, negative_pattern, named_pattern may be set")
                    return self

            language: str | list[str]
            pattern: PatternEntry | None = None
            and_: list[PatternEntry] | None = Field(default=None, alias="and")
            
            @model_validator(mode="before")
            def normalize_patterns(cls, values):
                if isinstance(values, dict):
                    # Normalize 'pattern' field
                    if "pattern" in values:
                        pat = values["pattern"]
                        if isinstance(pat, (str, list)):
                            values["pattern"] = {"pattern": pat}
                        elif isinstance(pat, dict):
                            # Already a dict, assume it's for PatternEntry
                            pass
                    # Normalize 'and' field
                    if "and" in values and isinstance(values["and"], list):
                        new_and = []
                        for item in values["and"]:
                            if isinstance(item, (str, list)):
                                new_and.append({"pattern": item})
                            elif isinstance(item, dict):
                                new_and.append(item)
                            else:
                                new_and.append(item)  # Assume already PatternEntry
                        values["and"] = new_and
                return values

        extensions: list[str]
        rules: list[RuleEntry]

    disambiguations: list[DisambiguationEntry]
    named_patterns: dict[str, list[str] | str]
    
    @model_validator(mode="after")
    def validate_named_patterns(self) -> Self:
        # ensure named patterns are in list
        named_patterns = set()
        for entry in self.disambiguations:
            for rule in entry.rules:
                if rule.pattern and rule.pattern.named_pattern:
                    named_patterns.add(rule.pattern.named_pattern)
                if rule.and_:
                    for and_entry in rule.and_:
                        if and_entry.named_pattern:
                            named_patterns.add(and_entry.named_pattern)
        for name in named_patterns:
            if name not in self.named_patterns:
                raise ValueError(f"Named pattern {name} not found in named_patterns")
        return self
