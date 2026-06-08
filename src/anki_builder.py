import genanki  # type: ignore
import hashlib
from typing import Dict, Sequence
from models import Section

def generate_id(string_identifier: str) -> int:
    """Generates a deterministic integer ID for Anki based on a string."""
    return int(hashlib.sha256(string_identifier.encode('utf-8')).hexdigest()[:15], 16)

def get_anki_model() -> genanki.Model:
    model_id = generate_id("TextbookTutorModel_v1")
    return genanki.Model(
        model_id,
        'Textbook Tutor Model',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
            {'name': 'Source'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '<div style="font-family: Arial; font-size: 20px; text-align: center; padding: 20px;">{{Question}}</div><br><div style="font-size: 12px; color: gray; text-align: center;">{{Source}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div style="font-family: Arial; font-size: 18px; text-align: left; padding: 20px;">{{Answer}}</div>',
            },
        ],
        css=""".card {
            font-family: arial;
            font-size: 20px;
            color: black;
            background-color: white;
        }"""
    )

def build_anki_deck(sections: Sequence[Section], root_deck_name: str, output_path: str) -> bool:
    """
    Builds an Anki .apkg file from a sequence of Sections containing flashcards.
    Returns True if successful, False if no flashcards were found.
    """
    model = get_anki_model()
    decks: Dict[str, genanki.Deck] = {}
    
    for section in sections:
        if not section.flashcards:
            continue
            
        # Clean up hierarchy strings to avoid breaking Anki's subdeck separator
        clean_hierarchy = [h.replace("::", " - ") for h in section.hierarchy]
        deck_name = f"{root_deck_name}::" + "::".join(clean_hierarchy)
        
        if deck_name not in decks:
            deck_id = generate_id(deck_name)
            decks[deck_name] = genanki.Deck(deck_id, deck_name)
            
        deck = decks[deck_name]
        
        source_label = " > ".join(clean_hierarchy)
        for fc in section.flashcards:
            note = genanki.Note(
                model=model,
                fields=[fc.question, fc.answer, source_label]
            )
            deck.add_note(note)
            
    if not decks:
        return False
        
    package = genanki.Package(list(decks.values()))
    package.write_to_file(output_path)
    return True
