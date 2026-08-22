from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class DocumentSection:
    section_id: str
    title: str
    text: str
    level: int
    parent_id: str | None = None
    source_index: int | None = None
    metadata: dict[str,Any] = field(default_factory=dict)
