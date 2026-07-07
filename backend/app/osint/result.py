from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkerResult:

    provider:str

    success:bool=True

    confidence:float=0

    latency_ms:int=0

    data:dict[str,Any]=field(default_factory=dict)

    errors:list[str]=field(default_factory=list)
