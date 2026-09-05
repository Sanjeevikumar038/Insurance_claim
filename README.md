TRACK_ID=PS02

# CLAIMWISE — Insurance Claims Evidence Review Assistant

CLAIMWISE is an AI-assisted evidence review system for motor insurance claims.

It helps insurance examiners review claim evidence against policy coverage, exclusions, insured value, claim windows, required documentation, and consistency across submitted documents.

The system combines Gemini-based semantic analysis, local FAISS policy retrieval, and deterministic Python validation to produce an evidence-grounded recommendation:

- APPROVE
- REJECT
- REQUEST INFORMATION
- ESCALATE when material uncertainty or unresolved contradiction requires human review

---

## 1. Problem Statement

Motor insurance claim review requires an examiner to compare information from multiple sources, such as:

- Claim forms
- Customer incident descriptions
- FIR / police reports
- Repair estimates
- Vehicle and policy information

The examiner must determine:

1. Whether required evidence is available.
2. Whether the claim information is internally consistent.
3. Whether the incident falls within policy coverage.
4. Whether any policy exclusion applies.
5. Whether the claim is within the permitted reporting window.
6. Whether the claimed amount is within the insured value.
7. Whether the submitted evidence supports or contradicts the claim.
8. Whether more information is required before a decision can be made.

Manual review can be time-consuming and contradictions can be easy to miss.

CLAIMWISE provides a structured evidence-review workflow that connects findings to their source evidence and applicable policy clauses.

---

## 2. Solution Overview

CLAIMWISE follows this pipeline:

    Claim Evidence
          |
          v
    Gemini 3.5 Flash-Lite
    Semantic Evidence Analysis
          |
          v
    Evidence Findings
          |
          v
    Gemini Embedding 001
          |
          v
    Local FAISS Policy Retrieval
          |
          v
    Relevant Policy Clauses
          |
          v
    Python Deterministic Rules
          |
          v
    Final Decision Logic
          |
          v
    APPROVE / REJECT / REQUEST INFORMATION / ESCALATE

The system deliberately separates semantic AI analysis from deterministic insurance decision logic.

Gemini is used for language understanding and semantic comparison.

Python controls deterministic validation and the final recommendation.

---

## 3. Key Design Principles

### Evidence Grounding

Every important finding is linked to:

- Source document
- Source location
- Evidence snippet
- Applicable policy clause
- Finding status

This allows an examiner to trace a decision back to the evidence that supports it.

### Deterministic Decisioning

The LLM does not directly decide whether a claim should be approved or rejected.

Python performs deterministic checks and applies the final decision hierarchy.

### Explicit Uncertainty

The system uses:

- SUPPORTED
- CONTRADICTED
- UNKNOWN

Instead of forcing a conclusion when evidence is missing or ambiguous.

### Conservative Review

Missing information does not silently become approval.

Material contradictions and unresolved uncertainty can result in REQUEST INFORMATION or ESCALATE.

### Local Retrieval

Policy retrieval uses local FAISS rather than a hosted vector database.

---

## 4. Technology Stack

### Backend

- Python 3.11 compatible
- FastAPI
- Uvicorn
- Pydantic

### Generative AI

- Gemini 3.5 Flash-Lite
- Gemini Embedding 001

### Retrieval

- FAISS
- NumPy
- Precomputed local policy embeddings/index

### Frontend

- HTML
- CSS
- Vanilla JavaScript

### Data

- JSON-based policy and claim data
- Local evidence documents
- Local FAISS index

### External API

The only external AI API used by the application is the Gemini API.

No other AI provider or hosted vector database is required.

---

## 5. System Architecture

The application is intentionally implemented as a simple monolithic service.

    app.py
      |
      +-- FastAPI API
      |
      +-- Review Engine
      |     |
      |     +-- Deterministic Rules
      |     +-- Gemini Semantic Analysis
      |     +-- Policy Retrieval
      |
      +-- Static Frontend
            |
            +-- HTML
            +-- CSS
            +-- JavaScript

The application serves both the API and frontend from the same Python process.

---

## 6. Project Structure

    Insurance-Claim/
    |
    +-- app.py
    +-- requirements.txt
    +-- README.md
    +-- .env.example
    +-- .gitignore
    |
    +-- src/
    |   +-- config.py
    |   +-- models.py
    |   +-- rules.py
    |   +-- retrieval.py
    |   +-- gemini.py
    |   +-- review.py
    |
    +-- data/
    |   +-- policy/
    |   |   +-- POL-2026.json
    |   |
    |   +-- claims/
    |   |   +-- CLM-001.json
    |   |   +-- CLM-002.json
    |   |   +-- CLM-003.json
    |   |   +-- CLM-004.json
    |   |   +-- CLM-005.json
    |   |
    |   +-- documents/
    |   |
    |   +-- index/
    |       +-- policy.index
    |       +-- clause_mapping.json
    |
    +-- static/
        +-- index.html
        +-- style.css
        +-- app.js

---

## 7. AI Responsibilities

### Gemini 3.5 Flash-Lite

Gemini is responsible for semantic tasks that require language understanding.

Examples include:

- Understanding customer incident descriptions
- Extracting relevant evidence
- Comparing statements across documents
- Detecting semantic contradictions
- Connecting evidence to retrieved policy clauses
- Producing structured evidence findings

The model is instructed to ground its findings in the supplied evidence and retrieved policy context.

### Gemini Embedding 001

Gemini Embedding 001 is used to generate embeddings for policy retrieval.

The resulting vectors are stored in a local FAISS index.

---

## 8. FAISS Policy Retrieval

The policy is represented as individual clauses.

A precomputed FAISS index is stored locally under:

    data/index/

At review time:

1. The relevant claim/evidence context is converted into a query embedding.
2. FAISS searches the local policy index.
3. The most relevant policy clauses are returned.
4. These clauses are provided as grounded context for semantic analysis.

This avoids using a hosted vector database.

If query embedding is temporarily unavailable, the system has a local lexical retrieval fallback for policy search.

The fallback does not replace Gemini semantic analysis and does not independently make the insurance decision.

---

## 9. Deterministic Python Checks

Python performs checks where deterministic logic is more reliable than an LLM.

Current checks include:

### Vehicle Registration

Compares the claim vehicle registration with the policy registration.

### Policy Number

Checks whether the claim references the expected policy.

### Policy Coverage Period

Checks whether the incident date falls within the policy start and end dates.

### Claim Reporting Window

Checks whether the claim was reported within the policy's permitted reporting window.

### Claim Amount

Compares the claimed amount with the policy insured value.

### Required Documents

Checks whether required evidence such as an FIR is present.

### Structured Consistency

Checks structured claim fields for mismatches.

---

## 10. Evidence Status

Each finding can have one of three evidence statuses.

### SUPPORTED

The available evidence supports the finding.

Example:

    Customer states the vehicle was damaged in an accident.
    Policy contains accidental damage coverage.

### CONTRADICTED

Evidence conflicts with another source or contradicts the applicable condition.

Example:

    Customer: Vehicle was locked securely.
    FIR: Keys were left in the ignition.

### UNKNOWN

The available evidence is insufficient to determine the condition.

Example:

    No evidence establishes whether alcohol was involved.

UNKNOWN does not mean the exclusion or violation is proven.

---

## 11. Decision Logic

The final decision is controlled by deterministic Python logic.

The general hierarchy is:

1. Technical failure or malformed AI response
   -> ERROR

2. Clearly established policy exclusion with sufficient evidence
   -> REJECT

3. Material unresolved contradiction
   -> ESCALATE

4. Missing required information or documents
   -> REQUEST INFORMATION

5. Insufficient evidence to establish a required condition
   -> REQUEST INFORMATION or ESCALATE

6. Sufficient evidence with no blocking condition
   -> APPROVE

The exact recommendation depends on the evidence and applicable policy clauses.

The system does not allow an LLM-generated response to silently override deterministic blockers.

---

## 12. Evidence Traceability

Findings are represented with information such as:

    finding
    source_type
    source_id
    source_location
    evidence
    policy_clause
    status

The UI exposes these fields so the examiner can understand why a finding was produced.

Example:

    Source:
    FIR

    Evidence:
    "The complainant stated they had stepped out for
    5 minutes to buy water and left the keys in the ignition."

    Policy:
    EXCLUSION - Keys Left in Vehicle

    Status:
    CONTRADICTED

This creates a traceable path from evidence to policy to recommendation.

---

## 13. Example Claim Scenarios

The included sample claims demonstrate different review situations.

### CLM-001 — Accidental Damage

Demonstrates:

- Vehicle registration validation
- Policy coverage validation
- Claim amount validation
- Accidental damage evidence
- Missing claim-report-date information

Expected outcome:

    REQUEST INFORMATION

---

### CLM-002 — Theft

Demonstrates:

- Theft evidence
- Customer/FIR contradiction
- Authoritative FIR evidence
- Keys Left in Vehicle exclusion
- Evidence-to-policy traceability

Customer evidence indicates:

    Vehicle was locked securely.

FIR evidence indicates:

    Keys were left in the ignition.

The policy contains:

    EXCLUSION - Keys Left in Vehicle

Expected outcome:

    REJECT

---

### CLM-003 — Theft

Demonstrates:

- Missing required FIR
- Theft evidence
- Policy retrieval
- Incomplete evidence handling

Expected outcome:

    REQUEST INFORMATION

---

### CLM-004 — Accidental Damage

Demonstrates:

- Customer/FIR contradiction
- Breathalyzer evidence
- Drunk Driving exclusion
- Authoritative evidence handling

Customer evidence indicates sobriety while authoritative evidence establishes alcohol intoxication.

The policy contains:

    EXCLUSION - Drunk Driving

Expected outcome:

    REJECT

---

### CLM-005 — Accidental Damage

Demonstrates:

- Accident evidence
- Repair estimate
- Claim window evidence
- Unknown exclusion-related evidence
- Conservative handling of incomplete information

Expected outcome depends on the complete evidence and deterministic checks.

---

## 14. User Interface

The CLAIMWISE interface is designed as an insurance examiner workspace.

The main workflow includes:

1. Claim selection
2. Claim summary
3. Evidence review execution
4. Review outcome
5. Decision pipeline
6. Evidence overview
7. Deterministic policy checks
8. Semantic evidence findings
9. Source evidence
10. Policy references

The interface highlights:

- SUPPORTED findings
- CONTRADICTED findings
- UNKNOWN findings
- Missing information
- Applicable policy exclusions
- Final recommendation

---

## 15. Setup

### Requirements

- Python 3.11 recommended
- Gemini API key
- Internet access for Gemini API calls

### Install dependencies

From the repository root:

    pip install -r requirements.txt

### Configure API key

Create a local `.env` file:

    GEMINI_API_KEY=your_gemini_api_key_here

Do not commit `.env`.

A safe example file is provided as:

    .env.example

The `.env.example` file must contain only the variable name/template and must not contain a real API key.

---

## 16. Run the Application

From the repository root:

    python app.py

The application starts the complete system from a single command.

Open:

    http://localhost:8000

No separate frontend build command is required.

---

## 17. API

The application exposes the claim review functionality through the FastAPI backend.

The frontend communicates with the backend to:

- Retrieve available claims
- Run evidence reviews
- Return structured review results

The backend and frontend are served by the same application process.

---

## 18. Security

Secrets are loaded from environment variables.

The Gemini API key is not stored in source code.

The following should never be committed:

    .env
    virtual environments
    private credentials
    API keys

The repository contains `.env.example` only as a configuration template.

---

## 19. Performance and Startup

Policy embeddings are precomputed and stored locally in the FAISS index.

This avoids rebuilding the complete policy embedding index every time the application starts.

At runtime, the application performs only the retrieval and semantic analysis required for the selected claim.

This design helps keep startup and individual review operations within the hackathon constraints.

---

## 20. Design Trade-offs

### Why not let Gemini make the final decision?

Insurance decisions involve deterministic conditions such as dates, monetary limits and required documents.

Allowing an LLM to directly determine the final outcome could produce inconsistent or unsupported decisions.

Therefore:

    Gemini = semantic understanding
    Python = deterministic validation and decision control

### Why FAISS?

The policy corpus is small and local retrieval is sufficient.

FAISS provides efficient vector search without requiring a hosted vector database.

### Why local JSON data?

The hackathon requires a reproducible demonstration environment.

Sample policy, claim and evidence data are committed with the project.

### Why UNKNOWN?

Real claims frequently contain incomplete evidence.

Representing uncertainty explicitly is safer than inventing an answer.

---

## 21. Error Handling

The system distinguishes technical failures from insurance uncertainty.

If a required AI operation fails or returns malformed output, the system does not fabricate findings or decisions.

Technical failures are surfaced as errors rather than being treated as successful claim reviews.

For policy retrieval, a local lexical fallback can be used if the embedding request is temporarily unavailable.

---

## 22. Hackathon Compliance

This implementation follows the PS02 constraints:

- Backend implemented in Python
- Gemini used as the external AI API
- Gemini 3.5 Flash-Lite used for semantic analysis
- Gemini Embedding 001 used for embeddings
- FAISS used locally for vector retrieval
- No hosted vector database
- No additional AI providers
- API key supplied through environment variables
- Sample policy and claim data included locally
- Application starts with:

      python app.py

- Frontend is served by the Python application
- Deterministic Python logic controls the final recommendation

---

## 23. Demo Flow

A recommended demonstration sequence is:

### 1. CLM-003

Show:

    Missing FIR
          ↓
    REQUEST INFORMATION

This demonstrates incomplete evidence handling.

### 2. CLM-002

Show:

    Customer:
    "Vehicle was locked securely"

              VS

    FIR:
    "Keys left in ignition"

              ↓

    CONTRADICTED

              ↓

    Keys Left in Vehicle exclusion

              ↓

    REJECT

This demonstrates contradiction detection, authoritative evidence and policy exclusion.

### 3. CLM-004

Show:

    Customer:
    "I was sober"

              VS

    FIR / Breathalyzer:
    Alcohol intoxication

              ↓

    CONTRADICTED

              ↓

    Drunk Driving exclusion

              ↓

    REJECT

This demonstrates another real-world contradiction and exclusion case.

---

## 24. Core Value Proposition

CLAIMWISE reduces the manual effort required to review motor insurance claims while keeping the review traceable and conservative.

Instead of simply generating a decision, the system answers:

- What evidence was found?
- Where did it come from?
- What policy clause applies?
- Is the evidence supported, contradicted or unknown?
- What deterministic checks passed or failed?
- Why was the final recommendation produced?

The core design principle is:

    Gemini finds and grounds the evidence.
    FAISS retrieves the relevant policy.
    Python validates the rules and makes the decision.
