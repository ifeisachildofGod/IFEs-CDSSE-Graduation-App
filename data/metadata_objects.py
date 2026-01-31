
from dataclasses import dataclass
@dataclass
class CharacterName:
    sur: str
    first: str
    middle: str
    abrev: str
    other: str | None = None
    
    def full_name(self):
        return f"{self.sur} {self.first}, {self.middle}"

@dataclass
class Department:
    id: str
    
    name: str

