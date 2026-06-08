import json
import logging
from pydantic import BaseModel
from typing import List, Tuple
from models import Section, Flashcard
from openai import OpenAI

logger = logging.getLogger(__name__)

class FlashcardList(BaseModel):
    flashcards: List[Flashcard]

def generate_flashcards(section: Section, client: OpenAI, model_name: str, question_density: str = "medium") -> Section:
    """
    Pure function: Returns a new Section with the generated flashcards.
    """
    if len(section.content.split()) < 10:
        logger.debug(f"Skipping section '{section.title}' as it contains less than 10 words.")
        return section

    logger.info(f"Generating flashcards for section '{section.title}' using model {model_name}.")

    density_prompt = {
        "low": "Create only 1 to 3 high-level summary questions covering the most important concepts.",
        "medium": "Create a moderate amount of questions covering all main concepts and definitions.",
        "high": "Create a high volume of granular questions, testing every specific detail, definition, formula, and sub-concept found in the text."
    }.get(question_density.lower(), "Create a moderate amount of questions covering all main concepts and definitions.")

    prompt = f"""
You are an expert educational tutor. Your task is to generate Anki flashcards from the provided textbook section.
The flashcards should be atomic, clear, and focus on key concepts, definitions, and facts.

DENSITY INSTRUCTION: {density_prompt}

LATEX MATH INSTRUCTION: 
If the text contains mathematical formulas, equations, or symbols, you MUST preserve them perfectly using MathJax-compatible LaTeX syntax.
Use `\\(` and `\\)` for inline math (e.g., \\( x^2 + y^2 = r^2 \\)).
Use `\\[` and `\\]` for display block math.
Do NOT use single `$` or double `$$` signs.

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
        
        num_cards = len(flashcard_list.flashcards)
        logger.info(f"Successfully generated {num_cards} flashcards for section '{section.title}'.")
        
        # Return a new copy of the Section with flashcards added
        return section.model_copy(update={"flashcards": tuple(flashcard_list.flashcards)})
    except Exception as e:
        logger.error(f"Error generating flashcards for '{section.title}': {e}")
        return section
