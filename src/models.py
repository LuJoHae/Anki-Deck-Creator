from pydantic import BaseModel, ConfigDict, Field
from typing import Tuple

class Flashcard(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    question: str
    answer: str

class Section(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    title: str
    hierarchy: Tuple[str, ...]
    content: str
    flashcards: Tuple[Flashcard, ...] = Field(default_factory=tuple)

class TocItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    level: int
    title: str
    page_number: int

class TocList(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    items: Tuple[TocItem, ...]
