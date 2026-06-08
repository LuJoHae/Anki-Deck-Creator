import json
from pydantic import BaseModel
from typing import List, Tuple
from models import Section, Flashcard
from openai import OpenAI

class FlashcardList(BaseModel):
    flashcards: List[Flashcard]

def generate_flashcards(section: Section, client: OpenAI, model_name: str) -> Section:
    """
    Pure function: Returns a new Section with the generated flashcards.
    """
    if len(section.content.split()) < 10:
        return section

    prompt = f"""
You are an expert educational tutor. Your task is to generate Anki flashcards from the provided textbook section.
The flashcards should be atomic, clear, and focus on key concepts, definitions, and facts.

Section Title: {section.title}
Hierarchy: {" > ".join(section.hierarchy)}

Text:
{section.content}

Output your response strictly in JSON format matching the following schema:
{{
    "flashcards": [
        {{"question": "What is X?", "answer": "X is Y."}}
    ]
}}
"""
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful educational tutor that strictly outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
            
        parsed_data = json.loads(content)
        flashcard_list = FlashcardList(**parsed_data)
        
        # Return a new copy of the Section with flashcards added
        return section.model_copy(update={"flashcards": tuple(flashcard_list.flashcards)})
    except Exception as e:
        print(f"Error generating flashcards for '{section.title}': {e}")
        return section
