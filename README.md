# Anki Deck Creator

A powerful Python tool designed to automatically generate structured Anki flashcard decks from textbook PDFs using Large Language Models (LLMs). It seamlessly chunks textbooks by chapter and section, generates atomic Q&A flashcards using either cloud APIs (like OpenAI) or completely local models (like Ollama), and outputs ready-to-import `.apkg` files.

## Features

- **Hierarchical Subdecks**: Automatically reads your PDF's Table of Contents to organize flashcards into nested subdecks (e.g., `Biology 101::Chapter 1::Section 1.1`).
- **Smart TOC Fallback**: If your PDF lacks metadata for a built-in Table of Contents, the tool automatically reads the first 20 pages and asks the LLM to dynamically generate the structure!
- **Strict LaTeX Math Support**: Automatically preserves math formulas and equations using Anki's native MathJax (`\\(` and `\\[`) syntax.
- **Adjustable Question Density**: Use `--density` to configure whether you want just a few high-level summary questions or granular flashcards covering every specific detail.
- **Local & Cloud LLMs**: Works identically with OpenAI's `gpt-4o` or local offline models like `llama3` via Ollama.
- **Type-Safe & Fast**: Built using a strict functional programming paradigm, fully tested, and utilizes `uv` for blazing-fast dependency management.

---

## Installation

This project utilizes [uv](https://docs.astral.sh/uv/) for dependency management. If you don't have it installed, follow their installation guide.

1. Clone or download this repository.
2. Open your terminal in the project directory.

No need to manually create virtual environments—`uv run` handles everything automatically!

---

## Usage

### 1. Using OpenAI (Recommended for Quality)

If you have an OpenAI account and want to use models like `gpt-4o-mini`:

```bash
export OPENAI_API_KEY="sk-your-openai-api-key"

uv run python src/main.py /path/to/your/textbook.pdf \
    --deck-name "My Biology Book" \
    --output "biology.apkg" \
    --model "gpt-4o-mini" \
    --density "medium"
```

### 2. Using Local LLMs via Ollama (Free and Private)

If you want to keep your textbook completely private and have [Ollama](https://ollama.com/) installed:

1. Ensure Ollama is running and you have pulled a model (e.g., `ollama pull llama3.1`).
2. Run the script, making sure to append `/v1` to the base URL:

```bash
uv run python src/main.py /path/to/your/textbook.pdf \
    --deck-name "Local LLM Textbook" \
    --output "local_book.apkg" \
    --model "llama3.1" \
    --base-url "http://localhost:11434/v1" \
    --density "high"
```

> **Note**: Processing a large PDF with an 8B+ parameter model locally can take a long time! You can track the LLM's progress via the progress bar in your terminal, and detailed logs are written to `anki_creator.log`.

---

## Configuration Options

| Argument | Description | Default |
|----------|-------------|---------|
| `pdf_path` | **Required.** The path to your textbook PDF. | N/A |
| `--deck-name` | The root name for the generated Anki deck. | `Textbook Deck` |
| `--output` | The output path/filename for the generated `.apkg` file. | `output.apkg` |
| `--model` | The name of the LLM model to use. | `gpt-4o` |
| `--density` | How many questions to generate (`low`, `medium`, or `high`). | `medium` |
| `--base-url` | Base URL for the LLM API (Use `http://localhost:11434/v1` for Ollama). | None |
| `--api-key` | Optional override for `OPENAI_API_KEY`. | None |

---

## Running the Tests

To run the full test suite and verify static type safety:

```bash
uv run pytest tests/
uv run mypy src/
```
