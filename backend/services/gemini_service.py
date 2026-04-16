# services/gemini_service.py
import requests
import os
import json
import re
import time
import logging
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You convert natural language into structured B2B filters for B2B data enrichment.

Rules:
- Only output valid JSON, no explanation or markdown
- Decide entity_type: "company" or "prospect"
- Map common patterns:
  * "SaaS" → industry
  * "VP Sales", "Head of Marketing" → job_titles
  * "US", "United States", "Germany" → countries
  * "10–200 employees", "50-500 emp" → employee_count_min/max
  * "revenue > 10M", "$10M+ revenue" → revenue_min/max

Example output:
{
  "entity_type": "company",
  "filters": {
    "industry": ["SaaS", "Software"],
    "employee_count_min": 50,
    "employee_count_max": 500,
    "countries": ["United States"],
    "job_titles": [],
    "keywords": ["AI", "fintech"]
  }
}
"""

def parse_prompt(prompt: str, retry_count=0, max_retries=3):
    """Parse natural language prompt into structured filters using Gemini with retry logic."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    # Try gemini-1.5-flash first (free tier), fall back to gemini-pro
    models_to_try = ["gemini-1.5-flash", "gemini-pro"]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{"text": SYSTEM_PROMPT + "\n\nUser prompt: " + prompt}]
            }]
        }

        try:
            logger.info(f"Gemini API call with model {model_name} (attempt {retry_count + 1}/{max_retries + 1})")
            res = requests.post(url, json=payload, timeout=10)
        except requests.exceptions.Timeout:
            raise ValueError("Gemini API request timed out")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Gemini API request failed: {e}")
        
        # Handle 503 Service Unavailable with retry
        if res.status_code == 503:
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Gemini API temporarily unavailable (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return parse_prompt(prompt, retry_count + 1, max_retries)
            else:
                raise ValueError("Gemini API unavailable (503) - max retries exceeded. Please try again later.")
        
        # Handle 429 Quota Exceeded
        if res.status_code == 429:
            logger.error(f"Gemini API quota exceeded (429). Suggest using USE_MOCK_DATA=true")
            raise ValueError("Gemini API quota exceeded. Please set USE_MOCK_DATA=true in .env for testing.")
        
        # Try next model if 404 (not found)
        if res.status_code == 404:
            logger.warning(f"Model {model_name} not found (404). Trying next model...")
            continue
        
        # Check for other HTTP errors
        if res.status_code != 200:
            error_msg = res.text
            logger.error(f"Gemini API error ({res.status_code}): {error_msg}")
            raise ValueError(f"Gemini API error ({res.status_code}): {error_msg}")
        
        data = res.json()

        # Check for API error response
        if 'error' in data:
            logger.warning(f"Model {model_name} error: {data['error']}. Trying next model...")
            continue

        if 'candidates' not in data or not data['candidates']:
            raise ValueError(f"Gemini returned empty response. Full response: {data}")

        # Check if response has content
        candidates = data['candidates']
        if not candidates[0].get('content') or not candidates[0]['content'].get('parts'):
            raise ValueError(f"Gemini response missing content. Full response: {data}")

        text = candidates[0]['content']['parts'][0].get('text', '')
        
        if not text:
            raise ValueError(f"Gemini returned empty text. Full response: {data}")
        
        # Extract JSON from potential markdown code blocks
        text = re.sub(r'^```json\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

        # Safely parse JSON
        try:
            parsed = json.loads(text)
            logger.info(f"Successfully parsed prompt with model {model_name}")
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}. Raw text: {text}")
    
    # If all models failed
    raise ValueError("No available Gemini models found. Please check your API key or use USE_MOCK_DATA=true")


def get_default_filters(prompt: str):
    """Fallback: Generate basic filters from prompt when Gemini is unavailable."""
    logger.info("Using fallback filter generation (Gemini unavailable)")
    
    prompt_lower = prompt.lower()
    
    # Detect entity type
    entity_type = "company"
    if any(word in prompt_lower for word in ["vp ", "head of ", "manager", "director", "ceo", "founder", "sales rep", "prospect"]):
        entity_type = "prospect"
    
    filters = {
        "industries": [],
        "employee_count_min": None,
        "employee_count_max": None,
        "countries": [],
        "job_titles": [],
        "keywords": []
    }
    
    # Extract keywords and industry hints
    keywords = []
    for word in ["saas", "software", "ai", "fintech", "cybersecurity", "ecommerce", "healthcare", "enterprise"]:
        if word in prompt_lower:
            keywords.append(word.title())
            if word in ["saas", "software"]:
                filters["industries"].append(word.title())
    
    filters["keywords"] = keywords[:5]  # Limit to 5 keywords
    
    # Extract countries
    countries_map = {
        "us": "United States", "usa": "United States", "america": "United States",
        "uk": "United Kingdom", "germany": "Germany", "france": "France",
        "india": "India", "canada": "Canada", "europe": "Europe"
    }
    for key, country in countries_map.items():
        if key in prompt_lower:
            filters["countries"].append(country)
    
    # Extract employee count range if mentioned
    if "50" in prompt or "50-" in prompt or "50–" in prompt:
        filters["employee_count_min"] = 50
    if "500" in prompt or "-500" in prompt or "–500" in prompt:
        filters["employee_count_max"] = 500
    if "100" in prompt and "employees" in prompt_lower:
        filters["employee_count_min"] = filters.get("employee_count_min") or 100
    
    # Extract common job titles for prospects
    job_titles = ["VP Sales", "Head of Sales", "Head of Marketing", "Marketing Director", "VP Marketing"]
    for title in job_titles:
        if title.lower() in prompt_lower:
            filters["job_titles"].append(title)
    
    return {
        "entity_type": entity_type,
        "filters": filters
    }