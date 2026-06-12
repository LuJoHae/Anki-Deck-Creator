# Ensure homebrew and local bin paths are included in PATH for macOS/Linux compatibility
export PATH := /opt/homebrew/bin:/usr/local/bin:$(PATH)

# Detect uv executable path
UV ?= $(shell command -v uv 2>/dev/null || (test -f /opt/homebrew/bin/uv && echo "/opt/homebrew/bin/uv") || (test -f /usr/local/bin/uv && echo "/usr/local/bin/uv") || echo "uv")

# Variables
DECKS_DIR ?= decks
BOOKS_DIR ?= books

# Find all PDFs in the books directory
BOOKS = $(wildcard $(BOOKS_DIR)/*.pdf)
# Map book PDFs to target APKG files in the decks directory
DECKS = $(patsubst $(BOOKS_DIR)/%.pdf,$(DECKS_DIR)/%.apkg,$(BOOKS))

# Default configuration settings for the LLM generator
MODEL ?= gpt-4o
DENSITY ?= medium
BASE_URL ?=
API_KEY ?=

.PHONY: all clean test lint help

# Default target: process all PDFs
all: $(DECKS)

# Rule to process a single PDF into an Anki deck
$(DECKS_DIR)/%.apkg: $(BOOKS_DIR)/%.pdf src/main.py src/extractor.py src/anki_builder.py src/llm_generator.py src/models.py
	@mkdir -p $(DECKS_DIR)
	@mkdir -p logs
	$(UV) run python src/main.py "$<" \
		--deck-name "$*" \
		--output "$@" \
		--model "$(MODEL)" \
		--density "$(DENSITY)" \
		$(if $(strip $(BASE_URL)),--base-url "$(strip $(BASE_URL))",) \
		$(if $(strip $(API_KEY)),--api-key "$(strip $(API_KEY))",)

# Clean up generated decks and log files
clean:
	rm -f $(DECKS_DIR)/*.apkg logs/*.log

# Run tests
test:
	$(UV) run pytest tests/

# Run static type checks
lint:
	$(UV) run mypy src/

# Display help information
help:
	@echo "Anki Deck Creator - Makefile Help"
	@echo ""
	@echo "Available Targets:"
	@echo "  all             Process all PDFs in '$(BOOKS_DIR)/' to Anki decks in '$(DECKS_DIR)/' (Default)"
	@echo "  clean           Remove generated .apkg files and logs"
	@echo "  test            Run unit tests using pytest"
	@echo "  lint            Run static analysis and type check with mypy"
	@echo "  help            Show this help menu"
	@echo ""
	@echo "Configuration Variables:"
	@echo "  MODEL           The LLM model to use (default: gpt-4o)"
	@echo "  DENSITY         Question density: low, medium, high (default: medium)"
	@echo "  BASE_URL        Custom Base URL for LLM API (e.g. http://localhost:11434/v1 for Ollama)"
	@echo "  API_KEY         Custom API key to override environment settings"
	@echo ""
	@echo "Example usage:"
	@echo "  make"
	@echo "  make MODEL=gpt-4o-mini DENSITY=high"
	@echo "  make BASE_URL=http://localhost:11434/v1 MODEL=llama3.1"
