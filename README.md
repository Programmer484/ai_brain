# Personal AI Brain

A personal AI assistant system for organizing thoughts, notes, and tasks using Notion as the database backend.

## Overview

This project creates a personal AI brain that can:
- Interface with Notion databases
- Ingest and process various types of content
- Provide intelligent tagging, reminders, and insights
- Use AI embeddings for content discovery

## Project Structure

```
├── db/         # Notion DB interface + schema modules
├── ingest/     # All input/ingestion code (CLI first)
├── ai/         # AI logic (tagging, reminders, embeddings)
├── tests/      # Test files
└── main.py     # Main entrypoint
```

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   - `NOTION_TOKEN`: Your Notion integration token
   - `OPENAI_KEY`: Your OpenAI API key

## Usage

Run the main application:
```bash
python main.py
```

## Development

This project is in early development. See `Plan.txt` for the current development roadmap.

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

## License

This project is for personal use. 