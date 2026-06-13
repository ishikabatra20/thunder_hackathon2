from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int
    col: int
