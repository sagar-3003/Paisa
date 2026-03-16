# Goal Description
Build "Paisa", an AI-powered accounting chatbot for Indian SMEs, following the provided execution prompt. The system consists of a FastAPI backend (with Supabase db, Render hosting), a React + Vite frontend (Vercel hosting), and integrations for LLMs (Groq, Mistral, OpenRouter), OCR, GST resolution, TDS rules, and Tally Prime.

## Proposed Setup

### Project Structure
The project will be housed in a root directory `paisa/` containing:
- `backend/` - FastAPI backend application handling business logic, LLM calls, GST/TDS engines, and OCR.
- `frontend/` - React SPA (Vite + TailwindCSS) for the chat interface and dashboard.
- `tally-bridge/` - Lightweight Python agent to bridge the cloud API to a local Tally Prime instance.

### Development Steps
1. **Initialize `paisa` directory** with the required basic folder structures in `/Users/sagargoyal/.gemini/antigravity/scratch/paisa`.
2. **Backend Setup**: Create FastAPI endpoints, LLM integration logic, SQLAlchemy models, and Alembic migrations.
3. **Frontend Setup**: Initialize Vite React project, install TailwindCSS, build the primary Chat interface.
4. **GST & TDS Engines**: Add data files (`hsn_master`, `tds_rules`) and implement fuzzy matching logic.
5. **OCR & File Upload**: Setup EasyOCR, pdfplumber, and processing endpoints.
6. **Local Tally Bridge**: Implement the HTTP polling script for local Tally instances.

## User Review Required
> [!IMPORTANT]
> The implementation of "Paisa" involves quite a few phases. I propose that we tackle them iteratively. First, we will generate the basic directory structure, set up the FastAPI server natively, and initialize the React frontend. We will store this project in the active scratchpad directory `/Users/sagargoyal/.gemini/antigravity/scratch/paisa`.
> Please review the `task.md` for our phased approach. If the plan looks good, we can transition to **Execution Mode** and begin scaffolding.

## Verification Plan

### Automated Tests
- We will write basic tests to verify data parsing logic using Python.
### Manual Verification
- We will start the API backend and Vite dev server locally to simulate chat interactions and manually verify the extracted cards format over the frontend.
