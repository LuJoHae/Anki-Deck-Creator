import typer
import os
import sys
import logging
from dotenv import load_dotenv
from typing import Optional
from openai import OpenAI
from tqdm import tqdm  # type: ignore

from extractor import extract_sections
from llm_generator import generate_flashcards
from anki_builder import build_anki_deck

load_dotenv()

# Configure logging
logging.basicConfig(
    filename='./logs/anki_creator.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = typer.Typer()

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
        # Update progress bar text with current section
        pbar.set_postfix({"section": section.title[:20]})
        processed_section = generate_flashcards(section, client, model_name, density)
        processed_sections.append(processed_section)
        
    typer.echo(f"Building Anki deck '{deck_name}'...")
    success = build_anki_deck(tuple(processed_sections), deck_name, output_path)
    
    if success:
        logger.info("Deck successfully created.")
        typer.secho("Done! Deck successfully created.", fg=typer.colors.GREEN)
    else:
        logger.warning("No flashcards were generated.")
        typer.secho("No flashcards were generated.", fg=typer.colors.YELLOW)

if __name__ == "__main__":
    app()
