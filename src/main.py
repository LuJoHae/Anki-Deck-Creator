import typer
import os
import sys
import logging
import json
from dotenv import load_dotenv
from typing import Optional, List
from openai import OpenAI
from tqdm import tqdm  # type: ignore

from extractor import extract_sections
from llm_generator import generate_flashcards
from anki_builder import build_anki_deck
from models import Section

load_dotenv()

# Configure logging
logging.basicConfig(
    filename='./logs/anki_creator.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = typer.Typer()

def load_resume_data(resume_path: str, pdf_path: str, model_name: str, density: str) -> Optional[List[Section]]:
    if not os.path.exists(resume_path):
        return None
    try:
        with open(resume_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate metadata
        if (data.get("pdf_path") != pdf_path or 
            data.get("model_name") != model_name or 
            data.get("density") != density):
            logger.info("Resume file found, but configuration parameters do not match. Discarding progress.")
            typer.echo("Resume file found, but configuration parameters do not match. Discarding progress.")
            return None
            
        sections = []
        for s_data in data.get("sections", []):
            sections.append(Section.model_validate(s_data))
        return sections
    except Exception as e:
        logger.warning(f"Failed to load resume data: {e}")
        return None

def save_resume_data(resume_path: str, pdf_path: str, model_name: str, density: str, sections: List[Section]) -> None:
    try:
        # Ensure directory exists
        resume_dir = os.path.dirname(resume_path)
        if resume_dir:
            os.makedirs(resume_dir, exist_ok=True)
            
        data = {
            "pdf_path": pdf_path,
            "model_name": model_name,
            "density": density,
            "sections": [s.model_dump() for s in sections]
        }
        with open(resume_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save resume data: {e}")

@app.command()
def create_deck(
    pdf_path: str = typer.Argument(..., help="Path to the textbook PDF"),
    deck_name: str = typer.Option("Textbook Deck", "--deck-name", "-d", help="Root name for the Anki deck"),
    output_path: str = typer.Option("output.apkg", "--output", "-o", help="Output path for the .apkg file"),
    model_name: str = typer.Option("gpt-4o", "--model", "-m", help="Name of the LLM model to use"),
    density: str = typer.Option("medium", "--density", help="Question density: low, medium, or high"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="Base URL for the LLM API (e.g., http://localhost:11434/v1 for Ollama)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API Key for the LLM. If not provided, will look for OPENAI_API_KEY environment variable.")
):
    """
    Extracts text from a PDF textbook, generates Anki flashcards using an LLM, and builds an Anki deck.
    """
    logger.info(f"Starting deck creation for {pdf_path}")
    client_api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")
    
    client = OpenAI(
        api_key=client_api_key,
        base_url=base_url
    )
    
    resume_path = f"{output_path}.resume.json"
    cached_sections = load_resume_data(resume_path, pdf_path, model_name, density)
    
    cache_map = {}
    if cached_sections:
        # Build cache map based on hierarchy and title
        cache_map = {
            (s.title, s.hierarchy): s.flashcards 
            for s in cached_sections 
            if s.flashcards
        }
        typer.echo(f"Found active progress file. Resuming deck creation...")
        logger.info(f"Loaded {len(cache_map)} cached sections from resume file.")

    typer.echo(f"Reading and chunking PDF: {pdf_path}...")
    try:
        sections = extract_sections(pdf_path, client, model_name)
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        typer.secho(f"Failed to read PDF: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    typer.echo(f"Extracted {len(sections)} sections. Detailed logs written to anki_creator.log")
    logger.info(f"Extracted {len(sections)} sections.")
    
    typer.echo(f"Generating flashcards using model '{model_name}' (Density: {density})...")
    processed_sections = []
    
    pbar = tqdm(sections, desc="Processing sections", file=sys.stdout)
    for section in pbar:
        cache_key = (section.title, section.hierarchy)
        if cache_key in cache_map:
            pbar.set_postfix({"section": f"Skipped: {section.title[:10]}"})
            # Reuse cached flashcards
            processed_section = section.model_copy(update={"flashcards": cache_map[cache_key]})
            processed_sections.append(processed_section)
        else:
            # Update progress bar text with current section
            pbar.set_postfix({"section": section.title[:20]})
            processed_section = generate_flashcards(section, client, model_name, density)
            processed_sections.append(processed_section)
            # Save progress immediately
            save_resume_data(resume_path, pdf_path, model_name, density, processed_sections)
        
    typer.echo(f"Building Anki deck '{deck_name}'...")
    success = build_anki_deck(tuple(processed_sections), deck_name, output_path)
    
    if success:
        logger.info("Deck successfully created.")
        typer.secho("Done! Deck successfully created.", fg=typer.colors.GREEN)
        if os.path.exists(resume_path):
            try:
                os.remove(resume_path)
            except Exception as e:
                logger.warning(f"Failed to remove resume file: {e}")
    else:
        logger.warning("No flashcards were generated.")
        typer.secho("No flashcards were generated.", fg=typer.colors.YELLOW)

if __name__ == "__main__":
    app()
