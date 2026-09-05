TRACK_ID=PS02

# Insurance Claims Evidence Review Assistant

## Problem & Solution
Claims investigators spend hours assembling contradictory evidence. This system automates the assembly and review of motor insurance claims against policy wordings, highlighting exclusions, contradictions, and missing documents.

## Architecture & Setup
The architecture is a lightweight FastAPI Python monolith serving a vanilla HTML/JS frontend. 
1. `pip install -r requirements.txt`
2. Define `GEMINI_API_KEY=` in a `.env` file.
3. `python app.py`
4. Access at `http://localhost:8000`

## AI & Retrieval
- **LLM**: `gemini-3.5-flash-lite` (strictly for semantic evidence extraction)
- **Embeddings**: `gemini-embedding-001`
- **Retrieval**: In-memory local FAISS CPU index. No external databases used.

## Deterministic Decision Engine
Gemini is intentionally forbidden from making the final claim decision. 
Instead, Python strictly handles:
- 30-day reporting window math
- Registration and Policy ID matching
- Insured value limits
- Document completeness

The Python hierarchy deterministically triggers `REJECT` for authoritative exclusions, `ESCALATE` for conflicting human evidence, and `REQUEST INFORMATION` for missing data.

## Demo / Edge Cases
- Missing documents trigger REQUEST INFORMATION.
- Authoritative exclusions (e.g. Police FIR proving Drunk Driving) correctly override customer statements and trigger REJECT.
- Contradictory evidence (non-authoritative) triggers ESCALATE.
