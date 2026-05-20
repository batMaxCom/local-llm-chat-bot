from dataclasses import dataclass


@dataclass
class SemanticFact:
    category: str
    content: str