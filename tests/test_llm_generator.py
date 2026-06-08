import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from models import Section
from llm_generator import generate_flashcards

def test_generate_flashcards_short_content():
    section = Section(title="Short", hierarchy=("Short",), content="Too short.")
    mock_client = MagicMock()
    
    new_section = generate_flashcards(section, mock_client, "gpt-4o")
    
    assert len(new_section.flashcards) == 0
    assert id(new_section) == id(section) # Should return unmodified if short
    
def test_generate_flashcards_success():
    section = Section(title="Long", hierarchy=("Long",), content="This is a long enough content to pass the ten word check limit that we have hardcoded.")
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"flashcards": [{"question": "Q?", "answer": "A."}]}'
    mock_client.chat.completions.create.return_value = mock_response
    
    new_section = generate_flashcards(section, mock_client, "gpt-4o")
    
    assert id(new_section) != id(section) # Must be a new instance
    assert len(new_section.flashcards) == 1
    assert new_section.flashcards[0].question == "Q?"
    assert new_section.flashcards[0].answer == "A."
