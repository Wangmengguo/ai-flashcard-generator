# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Flashcard Generator MVP - a FastAPI-based web application that converts Chinese text into high-quality Q&A flashcards using multiple AI models via OpenRouter API. The application focuses on content generation and export rather than implementing learning algorithms.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (primary)
source flashcard/bin/activate

# Alternative environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Local development (using refactored version)
uvicorn main_refactored:app --reload --host 127.0.0.1 --port 8000

# Production deployment
gunicorn main_refactored:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Testing
```bash
# Access application interface
# Open unified_index.html in browser

# Test API endpoints
curl http://127.0.0.1:8000/supported_models
```

## Architecture

The application follows a modern three-tier architecture:

1. **Frontend**: Unified interface with environment auto-detection
   - `unified_index.html` - Production-grade main interface (replaces multiple versions)

2. **Backend**: Refactored FastAPI application (`main_refactored.py`) with:
   - AI model configuration and management
   - OpenRouter API integration
   - Robust LLM output parsing with regex-based Q/A extraction
   - Error handling for different OpenRouter API error codes

3. **AI Integration**: Supports 8+ AI models through OpenRouter:
   - Gemini 2.5 Flash (recommended for cost-effectiveness)
   - Claude 3.7 Sonnet (highest quality)
   - GPT-4.1 Mini, Qwen 3, Grok 3 Mini, etc.

## Key Implementation Details

### LLM Output Parsing
The `parse_llm_output()` function implements sophisticated parsing logic:
- Supports multiple Q/A format variations (Q:, q:, Q：, etc.)
- Uses state machine pattern for robust extraction
- Handles edge cases like missing answers or malformed output
- Splits cards using `---` delimiter with flexible whitespace handling

### Error Handling
Comprehensive error mapping for OpenRouter API responses:
- 401: Invalid API key
- 402: Insufficient credits
- 429: Rate limiting
- 502/503: Service unavailability

### Export Formats
Supports multiple export formats for learning software integration:
- Anki Markdown (with deck/tag metadata)
- Anki Tab-separated
- CSV
- JSON

## File Structure Rationale

The dual HTML files (`index.html` vs `local_index.html`) are intentionally maintained separately to:
- Simplify local development (localhost URLs)
- Enable independent cloud deployment configuration
- Avoid complex environment switching logic

## Dependencies

Core requirements:
- FastAPI >= 0.104.0
- uvicorn >= 0.24.0 (development server)
- httpx >= 0.25.0 (async HTTP client)
- pydantic >= 2.4.2 (data validation)
- gunicorn >= 21.2.0 (production server)

## Development Notes

- The application uses a detailed system prompt optimized for Chinese text processing
- Default model is Gemini 2.5 Flash for optimal cost-performance ratio
- Maximum input text length is limited to 10,000 characters
- API keys are stored in localStorage for user convenience
- CORS is configured for development (should be restricted in production)