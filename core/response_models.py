from typing import Optional
from pydantic import BaseModel


class StructuredLLMTransport(BaseModel):
    message: str
    parsed_resume_json: Optional[str] = None