from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class TurnResult:
    message: str
    parsed_resume: Optional[Any] = None


@dataclass
class TurnOutcome:
    ok: bool
    response: str | TurnResult
    should_exit: bool = False