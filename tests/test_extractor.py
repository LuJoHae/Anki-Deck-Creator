import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from extractor import extract_sections, extract_toc_with_llm

def test_extract_sections_no_toc(mocker):
    mock_doc = MagicMock()
    mock_doc.get_toc.return_value = []
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 text. "
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 text."
    
    # Simulate iteration over doc
    mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
    
    mocker.patch('extractor.fitz.open', return_value=mock_doc)
    
    sections = extract_sections("dummy.pdf")
    
    assert len(sections) == 1
    assert sections[0].title == "Full Text"
    assert sections[0].hierarchy == ("Document",)
    assert sections[0].content == "Page 1 text. Page 2 text."

def test_extract_sections_with_toc(mocker):
    mock_doc = MagicMock()
    # level, title, page_num (1-indexed)
    mock_doc.get_toc.return_value = [
        [1, "Chapter 1", 1],
        [2, "Section 1.1", 1],
        [1, "Chapter 2", 2]
    ]
    mock_doc.page_count = 2
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Chap 1 and Sec 1.1 content."
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Chap 2 content."
    
    def load_page_side_effect(page_idx):
        if page_idx == 0: return mock_page1
        elif page_idx == 1: return mock_page2
        raise ValueError("Invalid page")
        
    mock_doc.load_page.side_effect = load_page_side_effect
    
    mocker.patch('extractor.fitz.open', return_value=mock_doc)
    
    sections = extract_sections("dummy.pdf")
    
    assert len(sections) == 3
    assert sections[0].title == "Chapter 1"
    assert sections[0].hierarchy == ("Chapter 1",)
    assert sections[0].content == "Chap 1 and Sec 1.1 content."
    
    assert sections[1].title == "Section 1.1"
    assert sections[1].hierarchy == ("Chapter 1", "Section 1.1")
    assert sections[1].content == "Chap 1 and Sec 1.1 content."
    
    assert sections[2].title == "Chapter 2"
    assert sections[2].hierarchy == ("Chapter 2",)
    assert sections[2].content == "Chap 2 content."

def test_extract_toc_with_llm(mocker):
    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Table of Contents\n1. Introduction ... 5"
    mock_doc.load_page.return_value = mock_page
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"items": [{"level": 1, "title": "Introduction", "page_number": 5}]}'
    mock_client.chat.completions.create.return_value = mock_response
    
    toc = extract_toc_with_llm(mock_doc, mock_client, "gpt-4o")
    
    assert toc == [[1, "Introduction", 5]]
