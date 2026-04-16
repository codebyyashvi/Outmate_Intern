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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")  # Default fallback model
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
    """Parse natural language prompt into structured filters using Gemini or Groq."""
    
    # **PRIORITIZE GROQ if available**
    if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
        logger.info(f"🚀 Groq API key found. Using Groq as PRIMARY LLM...")
        try:
            return parse_prompt_with_groq(prompt)
        except Exception as groq_err:
            logger.error(f"❌ Groq failed: {groq_err}. Falling back to Gemini...")
    
    # Fallback to Gemini
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.warning(f"⚠️ GEMINI_API_KEY not properly configured")
        raise ValueError("Neither Groq nor Gemini API keys configured")
    
    # Try gemini-1.5-flash first, then gemini-pro
    models_to_try = ["gemini-1.5-flash", "gemini-pro"]
    gemini_errors = []
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

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
                wait_time = 2 ** retry_count
                logger.warning(f"Gemini API temporarily unavailable (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return parse_prompt(prompt, retry_count + 1, max_retries)
            else:
                gemini_errors.append(f"Gemini {model_name}: 503 Service Unavailable")
                continue
        
        # Handle 429 Quota Exceeded
        if res.status_code == 429:
            logger.warning(f"Gemini API quota exceeded (429)...")
            gemini_errors.append(f"Gemini {model_name}: 429 Quota Exceeded")
            break
        
        # Try next model if 404 (not found)
        if res.status_code == 404:
            logger.warning(f"Model {model_name} not found (404). Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: 404 Not Found")
            continue
        
        # Check for other HTTP errors
        if res.status_code != 200:
            error_msg = res.text
            logger.warning(f"Gemini API error ({res.status_code}): {error_msg}. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: {res.status_code}")
            continue
        
        data = res.json()

        # Check for API error response
        if 'error' in data:
            logger.warning(f"Model {model_name} error: {data['error']}. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: API error")
            continue

        if 'candidates' not in data or not data['candidates']:
            logger.warning(f"Gemini returned empty response. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: empty response")
            continue

        # Check if response has content
        candidates = data['candidates']
        if not candidates[0].get('content') or not candidates[0]['content'].get('parts'):
            logger.warning(f"Gemini response missing content. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: missing content")
            continue

        text = candidates[0]['content']['parts'][0].get('text', '')
        
        if not text:
            logger.warning(f"Gemini returned empty text. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: empty text")
            continue
        
        # Extract JSON from potential markdown code blocks
        text = re.sub(r'^```json\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

        # Safely parse JSON
        try:
            parsed = json.loads(text)
            logger.info(f"✅ Successfully parsed prompt with Gemini {model_name}")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini {model_name} response as JSON. Trying next model...")
            gemini_errors.append(f"Gemini {model_name}: JSON parse error")
            continue
    
    # If all Gemini models also failed
    logger.error(f"❌ All Gemini models failed. Errors: {gemini_errors}")
    raise ValueError("All LLM providers failed. Both Groq and Gemini couldn't process the request.")


def parse_prompt_with_groq(prompt: str):
    """Parse natural language prompt using Groq API as fallback."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"User prompt: {prompt}"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        logger.info(f"📡 Calling Groq API with model: {GROQ_MODEL}")
        res = requests.post(url, json=payload, headers=headers, timeout=15)
    except requests.exceptions.Timeout:
        logger.error(f"❌ Groq API request timed out")
        raise ValueError("Groq API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Groq API request failed: {e}")
        raise ValueError(f"Groq API request failed: {e}")
    
    # Check for HTTP errors
    if res.status_code != 200:
        error_msg = res.text
        logger.error(f"❌ Groq API error ({res.status_code}): {error_msg}")
        raise ValueError(f"Groq API error ({res.status_code}): {error_msg}")
    
    data = res.json()
    
    # Check for API error response
    if 'error' in data:
        logger.error(f"❌ Groq API error: {data['error']}")
        raise ValueError(f"Groq API error: {data['error']}")
    
    # Extract text from choices
    if 'choices' not in data or not data['choices']:
        logger.error(f"❌ Groq returned empty choices")
        raise ValueError(f"Groq returned empty response: {data}")
    
    text = data['choices'][0]['message']['content']
    
    if not text:
        logger.error(f"❌ Groq returned empty text")
        raise ValueError("Groq returned empty text")
    
    # Extract JSON from potential markdown code blocks
    text = re.sub(r'^```json\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    text = text.strip()
    
    # Safely parse JSON
    try:
        parsed = json.loads(text)
        logger.info(f"✅ Successfully parsed prompt with Groq {GROQ_MODEL}")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse Groq response as JSON: {e}. Raw text: {text}")
        raise ValueError(f"Failed to parse Groq response as JSON: {e}. Raw text: {text}")


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