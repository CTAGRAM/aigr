
from dataclasses import dataclass, field


@dataclass
class Person:

    name:str=""

    github:str=""

    company:str=""

    website:str=""

    bio:str=""

    location:str=""

    aliases:list[str]=field(default_factory=list)

    evidence:list[dict]=field(default_factory=list)
