# OutMate – NLP Database Enrichment Demo

A full-stack application that converts natural language prompts into structured B2B database filters, fetches and enriches data from Explorium, and displays up to 3 records in a clean UI.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Tailwind)             │
│  - Prompt input box with example prompts                    │
│  - Results table with rich B2B fields                       │
│  - View JSON modal for debugging                            │
│  - Error handling & loading states                          │
└────────────────────┬────────────────────────────────────────┘
                     │ POST /api/enrich
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI + Python)                 │
│  - Request validation & rate limiting (10 req/min/IP)       │
│  - CORS enabled for frontend domains                        │
│  - Prompt parsing via Gemini API                            │
│  - Explorium API integration                                │
│  - Data normalization & max 3 results enforcement           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
    ┌─────────┐           ┌──────────────┐
    │ Gemini  │           │ Explorium    │
    │ API     │           │ API          │
    └─────────┘           └──────────────┘
```

## 📋 Project Structure

```
.
├── backend/                      # FastAPI backend
│   ├── app.py                   # Main app (CORS, rate limiting setup)
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables (secrets)
│   ├── .env.example             # Template for .env
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routes/
│   │   └── enrich.py            # POST /api/enrich endpoint
│   └── services/
│       ├── gemini_service.py    # Prompt → structured filters
│       ├── explorium_service.py # Explorium API calls
│       └── normalize.py         # Response normalization
│
└── frontend/                     # React + Vite frontend
    ├── package.json             # NPM dependencies
    ├── vite.config.js           # Vite configuration
    ├── tailwind.config.js       # Tailwind CSS config
    ├── .env                     # Frontend env vars
    ├── .env.example             # Template for .env
    ├── src/
    │   ├── App.jsx              # Main component (UI, API calls)
    │   ├── App.css              # Styles
    │   └── main.jsx             # Entry point
    └── public/                  # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gemini API key (from Google Cloud)
- Explorium API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy .env.example to .env
   cp .env.example .env
   
   # Edit .env and add your API keys:
   # GEMINI_API_KEY=your_key_here
   # EXPLORIUM_API_KEY=your_key_here
   ```

5. **Run the server:**
   ```bash
   uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
   ```

   Server will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # .env file already configured for local development
   # VITE_BACKEND_URL=http://localhost:8000
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

   App will be available at `http://localhost:5173`

5. **Build for production:**
   ```bash
   npm run build
   ```

## 📡 API Contract

### POST /api/enrich

**Request:**
```json
{
  "prompt": "Find 3 fast-growing SaaS companies in the US with 50–500 employees"
}
```

**Response (Success):**
```json
{
  "results": [
    {
      "type": "company",
      "name": "Acme Corp",
      "domain": "acme.com",
      "industry": "SaaS",
      "employee_count": 250,
      "revenue": "$50M",
      "country": "United States",
      "linkedin_url": "https://linkedin.com/company/acme",
      "founded_year": 2015,
      "tech_stack": ["React", "Python", "AWS"],
      "key_contacts": [...],
      "website": "acme.com",
      "raw": { /* raw Explorium data */ }
    }
  ]
}
```

**Response (Error):**
```json
{
  "detail": "Invalid prompt: <error message>"
}
```

**Status Codes:**
- `200 OK` - Successful enrichment
- `400 Bad Request` - Invalid prompt (empty, too long)
- `429 Too Many Requests` - Rate limit exceeded (10/min per IP)
- `500 Internal Server Error` - Gemini/Explorium error

### GET /api/health

**Response:**
```json
{
  "status": "ok"
}
```

## 🧠 Gemini Prompt Design

The backend sends a carefully crafted system prompt to Gemini that:
- Explains the task (converting NLP → structured filters)
- Lists supported fields (industry, employee_count, countries, job_titles, keywords, etc.)
- Provides output format specification (strict JSON)
- Handles ambiguous prompts with reasonable defaults

The parsed JSON is then mapped to Explorium API query parameters.

## 🔒 Security & Rate Limiting

- **Environment Variables**: All secrets (API keys) stored in `.env`, never hardcoded
- **CORS**: Frontend origin whitelist in `app.py` (configurable via `FRONTEND_URL` env var)
- **Rate Limiting**: Max 10 requests per minute per IP (via slowapi)
- **Prompt Validation**: Max 1000 characters, non-empty check
- **Error Handling**: User-friendly error messages (secrets not exposed)

## 📝 Sample Prompts to Test

1. "Find 3 fast-growing SaaS companies in the US with 50–500 employees, raising Series B or later."
2. "Give me 3 VPs of Sales in European fintech startups with more than 100 employees."
3. "Top AI infrastructure companies hiring machine learning engineers in India."
4. "3 marketing leaders at e-commerce brands in North America doing more than $50M in revenue."
5. "Cybersecurity firms with increasing web traffic and at least 200 employees."

## 🛠️ Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed: `python --version`
- Verify all dependencies: `pip install -r requirements.txt`
- Check API keys are set in `.env`
- Port 8000 in use? Change port: `uvicorn app.app:app --port 8001`

### Frontend can't connect to backend
- Verify backend is running on `http://localhost:8000`
- Check `VITE_BACKEND_URL` in `frontend/.env`
- CORS error? Ensure backend CORS is configured correctly

### Gemini/Explorium errors
- Verify API keys are valid in `.env`
- Check API quotas/rate limits
- Review error message in browser console or server logs

## 📦 Deployment

### Backend (Render, Railway, Heroku)
1. Push code to GitHub
2. Connect repository to deployment platform
3. Set environment variables (API keys) in platform dashboard
4. Deploy (platform will run `uvicorn app.app:app --host 0.0.0.0 --port $PORT`)

### Frontend (Vercel, Netlify)
1. Push code to GitHub
2. Connect repository to Vercel/Netlify
3. Set build command: `npm run build`
4. Set environment variables (e.g., `VITE_BACKEND_URL=https://your-backend-url.com`)
5. Deploy

## 📊 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19.2, Vite, Tailwind CSS |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **AI/ML** | Google Gemini API |
| **Data** | Explorium REST API |
| **Rate Limiting** | slowapi |
| **HTTP Client** | axios (frontend), requests (backend) |
| **Deployment** | Vercel/Netlify (frontend), Render/Railway (backend) |

## 📄 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app.py` | CORS, rate limiting, health check |
| `backend/routes/enrich.py` | Main `/api/enrich` endpoint |
| `backend/services/gemini_service.py` | Parse prompt with Gemini |
| `backend/services/explorium_service.py` | Fetch data from Explorium |
| `backend/services/normalize.py` | Standardize response format |
| `frontend/src/App.jsx` | Main UI, error handling, results display |

## 🐛 Logging

**Backend**: Each request logs:
- Client IP
- Prompt length
- Parsed entity_type
- Number of results returned
- Any errors (without exposing secrets)

View logs in terminal when running `uvicorn`

## 📞 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review logs in terminal/browser console
3. Inspect network requests in browser DevTools
4. Verify `.env` files are set up correctly

---

**Version**: 1.0  
**Last Updated**: April 2026
