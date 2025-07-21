# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Biblioperson** is a multilingual personal digital library system with AI conversation capabilities. Users can interact with authors based on their literary works through a sophisticated full-stack application featuring document processing, semantic search, and conversational AI.

## Architecture & Tech Stack

### Frontend (Next.js App)
- **Location**: `/app/`
- **Framework**: Next.js 15 with App Router, TypeScript
- **Styling**: Tailwind CSS with custom components
- **State**: Zustand for client state management
- **Auth**: Supabase Auth (hybrid architecture)
- **Database**: Prisma ORM with SQLite (development)
- **Desktop**: Electron wrapper for cross-platform desktop app

### Backend Services
- **API Server**: Flask-based API (`scripts/api_conexion.py`)
- **Document Processing**: Python pipeline in `dataset/` directory
- **Search**: Meilisearch for full-text search + FAISS for semantic search
- **AI**: RAG system for author-based conversations

## Essential Development Commands

### Quick Start
```bash
# Start full development environment (cleans processes first)
npm run dev                   

# Development - individual services
npm run dev:frontend          # Next.js only (port 3000)
npm run dev:backend          # Flask API only (port 5000)
npm run desktop              # Desktop app with backend
npm run clean                # Kill all processes and clean cache
```

### Frontend Development (app/)
```bash
cd app/

# Development
npm run dev                  # Next.js dev server
npm run build                # Production build
npm run start                # Production server
npm run lint                 # ESLint check

# Database management
npx prisma generate          # Generate Prisma client
npx prisma db push           # Push schema changes
npx prisma studio            # Database GUI

# Desktop app
npm run electron:dev         # Development desktop app
npm run electron:pack        # Package for current platform
npm run electron:dist        # Build distributable
```

### Python/Backend Commands
```bash
# Main API server
python scripts/api_conexion.py              # Flask API (port 5000)

# Document processing
python dataset/scripts/cli.py               # CLI for document processing
python launch_gui.py                        # GUI for document processing

# Search & embeddings
python scripts/backend/generate_embeddings.py    # Generate vector embeddings
python scripts/backend/indexar_meilisearch.py    # Index full-text search
```

### Environment Setup
```bash
# Python environment
python -m venv venv
source venv/bin/activate     # Linux/Mac
.\venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt                  # Global backend deps
pip install -r dataset/requirements.txt          # Document processing
pip install PySide6==6.6.0                      # GUI interface

# Node.js
cd app && npm install        # Frontend dependencies
```

## Project Structure

```
/
├── app/                     # Next.js frontend application
│   ├── src/
│   │   ├── app/            # App Router pages & API routes
│   │   ├── components/     # React components
│   │   ├── lib/           # Database, auth, utilities
│   │   └── store/         # Zustand state stores
│   ├── prisma/            # Database schema & migrations
│   └── electron/          # Electron main process
├── scripts/               # Backend API server & utilities
│   ├── api_conexion.py    # Main Flask API server
│   └── backend/           # Processing scripts
├── dataset/               # Document processing pipeline
│   ├── processing/        # Core processing modules
│   ├── scripts/          # CLI tools & GUI interface
│   └── config/           # Processing configurations
├── src/                   # Core Python modules
│   ├── database/         # Database persistence layer
│   ├── embeddings/       # Vector embeddings client
│   ├── pipeline/         # Data ingestion pipeline
│   └── search/           # Search implementations
└── docs/                  # Project documentation
```

## Key API Endpoints

### Main Routes (`app/src/app/api/`)
- **Auth**: `/auth/login`, `/auth/register`, `/auth/callback`
- **Library**: `/library/` (document CRUD)
- **Documents**: `/documents/` and `/documents/[id]/`
- **Search**: `/search/` (full-text), `/search/semantic/` (vector)
- **Upload**: `/upload/` (document ingestion)
- **RAG/Chat**: `/rag/` (AI conversations with authors)
- **User**: `/user/config/`, `/user/sync/`

## Database Schema (Prisma)

### Main Models
- **User**: Basic user info (linked to Supabase)
- **Author**: Author metadata and biography
- **Document**: Document metadata and file information
- **Segment**: Text chunks for search and processing
- **Annotation**: User highlights and notes
- **Conversation**: AI chat history and context

## Development Workflows

### Document Processing Pipeline
1. **Input**: Place files in `backend/data/import/` (PDF, EPUB, TXT, DOCX, MD)
2. **Process**: Use GUI (`python launch_gui.py`) or CLI (`python dataset/scripts/cli.py`)
3. **Output**: Structured NDJSON with metadata and segments
4. **Index**: Auto-indexing in Meilisearch and FAISS for search

### Testing & Quality
```bash
# Frontend testing
cd app && npm test

# Python testing
python -m pytest dataset/
python dataset/test_*.py

# Health checks
curl http://localhost:3000/api/health     # Frontend
curl http://localhost:5000/health         # Backend API
```

### Build & Deployment
```bash
# Production builds
cd app && npm run build                   # Frontend
docker-compose --profile prod up -d      # Full stack

# Desktop distribution
cd app && npm run electron:dist
```

## Important Development Notes

### Multi-language Support
- **Frontend**: React i18next with ES/EN locales (`app/src/i18n.ts`)
- **Backend**: Spanish-first with English support
- **Content**: Multi-language document processing

### Performance Considerations
- **Embeddings**: Incremental generation (not regenerated)
- **Search**: Meilisearch handles large collections efficiently
- **Frontend**: Next.js optimized builds with caching

### Security Best Practices
- Never log or commit API keys or secrets
- Use environment variables for sensitive configuration
- Supabase handles auth, local DB for content storage

### Code Conventions
- **TypeScript**: Strict mode enabled, proper typing required
- **React**: Functional components with hooks, Zustand for state
- **Python**: PEP 8 style, type hints where applicable
- **Database**: Prisma schema-first approach

## Task Master AI Integration

This project uses Task Master AI for development workflow management. All Task Master functionality is available through both MCP tools and CLI commands.

### Essential Task Master Commands

```bash
# Project initialization
task-master init                          # Initialize Task Master
task-master parse-prd .taskmaster/docs/prd.txt  # Generate tasks from PRD

# Daily workflow
task-master list                          # Show all tasks with status  
task-master next                          # Get next available task
task-master show <id>                     # View detailed task info
task-master set-status --id=<id> --status=done  # Mark complete

# Task management
task-master add-task --prompt="description" --research
task-master expand --id=<id> --research --force
task-master update-task --id=<id> --prompt="changes"
```

### MCP Integration

Task Master MCP server provides tools for integrated development. Key MCP tools:
- `get_tasks` / `next_task` / `get_task` - Task retrieval
- `set_task_status` - Status updates  
- `add_task` / `expand_task` - Task creation
- `update_task` / `update_subtask` - Task modifications

### Task-Driven Development Process

1. **Start with** `task-master next` to identify work
2. **Plan implementation** with detailed exploration
3. **Log progress** using `update_subtask` with implementation notes
4. **Mark complete** only after testing and verification
5. **Update dependent tasks** when implementation differs from plan

### Configuration Files

- **`.taskmaster/tasks/tasks.json`** - Main task database (auto-managed)
- **`.taskmaster/config.json`** - AI model configuration
- **`.env`** - API keys for Task Master
- **`.mcp.json`** - MCP server configuration for Claude Code

For complete Task Master documentation, see the existing sections above this integration.

---

*This guide provides comprehensive context for both Biblioperson development and Task Master workflow integration.*