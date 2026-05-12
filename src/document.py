from dataclasses import dataclass,field
from typing import Any,Dict

@dataclass
class Document():
    page_context:str
    metadata:Dict[str,Any] = field(default_factory=dict)
    