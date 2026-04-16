# OutMate Intern

OutMate is a full-stack demo that converts natural language prompts into structured B2B search intent, fetches enrichment data, normalizes it, and shows up to 3 records in a React UI.

## Project Overview

- Frontend: React + Vite client for prompt input, result cards, and raw JSON view.
- Backend: FastAPI service that validates input, applies rate limits, parses prompts with LLMs, fetches data from Explorium (or mock data), and returns normalized records.
- LLM parsing: Groq is tried first (if configured), then Gemini.
- Data source: Explorium API (or local mock mode via env toggle).

## Architecture

```text
+-------------------------------+
| Frontend (React + Vite)       |
| - Prompt input                |
| - Calls POST /api/enrich      |
| - Renders up to 3 results     |
+---------------+---------------+
                |
                v
+-------------------------------+
| Backend (FastAPI)             |
| - Request validation          |
| - Rate limit: 10/min per IP   |
| - LLM parse (Groq/Gemini)     |
| - Explorium fetch / mock data |
| - Normalize response          |
+---------+---------------------+
          |
          v
+-------------------------------+
| External Services             |
| - Groq API (optional)         |
| - Gemini API (optional)       |
| - Explorium API               |
+-------------------------------+
```

## Repository Structure

```text
.
|-- backend/
|   |-- app.py
|   |-- requirements.txt
|   |-- models/schemas.py
|   |-- routes/enrich.py
|   `-- services/
|       |-- gemini_service.py
|       |-- explorium_service.py
|       `-- normalize.py
`-- frontend/
    |-- package.json
    |-- .env.example
    `-- src/App.jsx
```

## Run Locally

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit backend/.env with your keys, then start server:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at http://localhost:8000

### 2) Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs at http://localhost:5173

## Environment Variables

### Backend (backend/.env)

- GEMINI_API_KEY
- GROQ_API_KEY
- GROQ_MODEL
- EXPLORIUM_API_KEY
- FRONTEND_URL
- USE_MOCK_DATA

Notes:
- If GROQ_API_KEY is set, Groq is used first.
- If USE_MOCK_DATA=true, the backend returns mock data and does not call Explorium.

### Frontend (frontend/.env)

- VITE_BACKEND_URL

## API Contract

### POST /api/enrich

Converts a natural language prompt into enriched records.

#### Request

- Method: POST
- Path: /api/enrich
- Content-Type: application/json

Body:

```json
{
  "prompt": "Find 3 fast-growing SaaS companies in the US with 50-500 employees"
}
```

Validation rules:
- prompt is required
- prompt cannot be empty/whitespace
- max prompt length is 1000 characters

#### Success Response

- Status: 200 OK

```json
{
  "results": [
    {
      "type": "company",
      "name": "Acme SaaS Inc",
      "domain": "acme-saas.com",
      "industry": "SaaS",
      "employee_count": 250,
      "revenue": "$50M",
      "country": "United States",
      "linkedin_url": "https://linkedin.com/company/acme-saas",
      "website": "www.acme-saas.com",
      "raw": {
        "name": "Acme SaaS Inc"
      }
    }
  ]
}
```

Behavior:
- Returns at most 3 records.
- Records may be company or prospect shaped, depending on inferred entity type.

#### Error Responses

- 400 Bad Request (validation / prompt parsing issue)

```json
{
  "detail": "Empty prompt"
}
```

or

```json
{
  "detail": "Invalid prompt: <reason>"
}
```

- 429 Too Many Requests (rate limit exceeded)

```json
{
  "error": "Too many requests. Max 10 requests per minute per IP."
}
```

- 500 Internal Server Error

```json
{
  "detail": "Server error processing your request"
}
```

## Additional Endpoint

### GET /api/health

- Status: 200 OK

```json
{
  "status": "ok"
}
```

## Request and Response Examples

### Example 1: Company Search

Request:

```json
{
  "prompt": "Find 3 SaaS companies in the US with 50-500 employees"
}
```

Typical response:

```json
{
  "results": [
    {
      "type": "company",
      "name": "CloudTech Solutions",
      "industry": "SaaS",
      "employee_count": 180,
      "country": "United States"
    },
    {
      "type": "company",
      "name": "DataFlow AI",
      "industry": "SaaS",
      "employee_count": 320,
      "country": "United States"
    }
  ]
}
```

### Example 2: Prospect Search

Request:

```json
{
  "prompt": "Give me VPs of Sales in US fintech startups"
}
```

Typical response:

```json
{
  "results": [
    {
      "type": "prospect",
      "name": "John Smith",
      "job_title": "VP of Sales",
      "country": "United States",
      "linkedin_url": "https://linkedin.com/in/johnsmith"
    }
  ]
}
```
