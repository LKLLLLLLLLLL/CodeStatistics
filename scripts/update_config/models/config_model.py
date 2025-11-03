from pydantic import BaseModel
from typing import Literal

class Config(BaseModel):
    class Language(BaseModel):
        class Rule(BaseModel):
            name_pattern: str
            content_patterns: list[str] | None = None

        color: str | None = None
        type: str
        rules: list[Rule] = []

    skip: dict[
        Literal["path", "documentation", "files", "category", "languages"],
        list[str]
    ] = {
        "path": [],
        "documentation": [],
        "files": [],
        "category": [],
        "languages": [],
    }
    languages: dict[str, Language] = {}