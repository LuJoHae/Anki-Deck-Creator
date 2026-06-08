import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from models import Section, Flashcard
from anki_builder import build_anki_deck

def test_build_anki_deck_empty():
    section = Section(title="Empty", hierarchy=("Empty",), content="Content")
    assert not build_anki_deck((section,), "Test Deck", "output.apkg")

def test_build_anki_deck_success(mocker):
    fc = Flashcard(question="Q?", answer="A.")
    section = Section(title="Populated", hierarchy=("Chapter 1", "Section 1"), content="Content", flashcards=(fc,))
    
    mock_package_cls = mocker.patch('anki_builder.genanki.Package')
    mock_package_instance = MagicMock()
    mock_package_cls.return_value = mock_package_instance
    
    success = build_anki_deck((section,), "Test Deck", "test_output.apkg")
    
    assert success
    mock_package_instance.write_to_file.assert_called_once_with("test_output.apkg")
