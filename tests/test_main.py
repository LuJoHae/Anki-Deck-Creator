import pytest
import sys
import os
import json
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from models import Section, Flashcard
from main import load_resume_data, save_resume_data, create_deck

def test_resume_save_and_load(tmp_path):
    resume_file = tmp_path / "test.resume.json"
    resume_path = str(resume_file)
    pdf_path = "books/test.pdf"
    model_name = "gpt-4o"
    density = "medium"
    
    fc = Flashcard(question="Q?", answer="A.")
    sections = [
        Section(title="Sec 1", hierarchy=("Chap 1", "Sec 1"), content="Content 1", flashcards=(fc,)),
        Section(title="Sec 2", hierarchy=("Chap 1", "Sec 2"), content="Content 2", flashcards=())
    ]
    
    save_resume_data(resume_path, pdf_path, model_name, density, sections)
    
    # 1. Successful load
    loaded = load_resume_data(resume_path, pdf_path, model_name, density)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].title == "Sec 1"
    assert loaded[0].flashcards[0].question == "Q?"
    assert loaded[1].title == "Sec 2"
    assert len(loaded[1].flashcards) == 0

    # 2. Config mismatch: model
    loaded_mismatched_model = load_resume_data(resume_path, pdf_path, "gpt-4o-mini", density)
    assert loaded_mismatched_model is None

    # 3. Config mismatch: density
    loaded_mismatched_density = load_resume_data(resume_path, pdf_path, model_name, "high")
    assert loaded_mismatched_density is None

    # 4. Config mismatch: pdf_path
    loaded_mismatched_pdf = load_resume_data(resume_path, "books/other.pdf", model_name, density)
    assert loaded_mismatched_pdf is None

def test_create_deck_with_resume(tmp_path, mocker):
    output_path = tmp_path / "deck.apkg"
    resume_file = tmp_path / "deck.apkg.resume.json"
    
    pdf_path = "books/test.pdf"
    model_name = "gpt-4o"
    density = "medium"
    
    # Pre-populate resume file with 1 section having a flashcard
    fc = Flashcard(question="Q1?", answer="A1.")
    cached_sec = Section(title="Sec 1", hierarchy=("Chap 1", "Sec 1"), content="Content 1", flashcards=(fc,))
    save_resume_data(str(resume_file), pdf_path, model_name, density, [cached_sec])
    
    # Mock extract_sections to return two sections
    sec1 = Section(title="Sec 1", hierarchy=("Chap 1", "Sec 1"), content="Content 1")
    sec2 = Section(title="Sec 2", hierarchy=("Chap 1", "Sec 2"), content="Content 2")
    mocker.patch("main.extract_sections", return_value=(sec1, sec2))
    
    # Mock generate_flashcards to only be called for Sec 2 (since Sec 1 is cached)
    fc2 = Flashcard(question="Q2?", answer="A2.")
    mock_gen = mocker.patch("main.generate_flashcards", return_value=sec2.model_copy(update={"flashcards": (fc2,)}))
    
    # Mock build_anki_deck
    mock_build = mocker.patch("main.build_anki_deck", return_value=True)
    
    # Mock OpenAI client
    mocker.patch("main.OpenAI")
    
    # Run create_deck using typer runner
    from typer.testing import CliRunner
    from main import app
    
    runner = CliRunner()
    result = runner.invoke(app, [
        pdf_path,
        "--output", str(output_path),
        "--model", model_name,
        "--density", density
    ])
    
    assert result.exit_code == 0
    
    # Verify generate_flashcards was called once (only for Sec 2)
    mock_gen.assert_called_once()
    # Verify build_anki_deck was called with both sections (one from cache, one from LLM generator)
    called_sections = mock_build.call_args[0][0]
    assert len(called_sections) == 2
    assert called_sections[0].title == "Sec 1"
    assert called_sections[0].flashcards[0].question == "Q1?"
    assert called_sections[1].title == "Sec 2"
    assert called_sections[1].flashcards[0].question == "Q2?"
    
    # Verify the resume file is deleted upon successful deck generation
    assert not os.path.exists(str(resume_file))
