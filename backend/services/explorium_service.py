# services/explorium_service.py
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EXPLORIUM_API_KEY")
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
logger = logging.getLogger(__name__)

def fetch_data(entity_type, filters):
    """Fetch data from Explorium API with error handling and logging."""
    logger.info(f"📊 fetch_data called - USE_MOCK_DATA={USE_MOCK}, API_KEY={'set' if API_KEY else 'not set'}")
    logger.info(f"Entity: {entity_type}")
    logger.info(f"Filters: {filters}")
    
    if not API_KEY and not USE_MOCK:
        raise ValueError("EXPLORIUM_API_KEY environment variable not set")
    
    # **USE MOCK DATA FIRST if enabled**
    if USE_MOCK:
        logger.info("✅ USE_MOCK_DATA=true. Using mock B2B data for testing...")
        return get_mock_data(entity_type, filters)
    
    # Only call real API if mock is disabled
    logger.info("🌐 USE_MOCK_DATA=false. Calling real Explorium API...")
    
    url = "https://api.explorium.ai/v1/prospects"

    payload = {
        "mode": "full",
        "page": 1,
        "page_size": 3
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api_key": API_KEY
    }

    logger.info(f"Calling Explorium API: {url}")
    logger.info(f"Payload: {payload}")

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise ValueError(f"Request failed: {e}")
    
    # Check for HTTP errors
    if res.status_code != 200:
        error_msg = res.text
        logger.error(f"❌ Explorium API error ({res.status_code}): {error_msg}")
        raise ValueError(f"Explorium API error ({res.status_code}): {error_msg}")
    
    data = res.json()
    
    logger.info(f"📥 Explorium response: {data}")
    
    # Check for API error response
    if 'error' in data:
        error_msg = data.get('error')
        logger.error(f"❌ Explorium API error: {error_msg}")
        raise ValueError(f"Explorium API error: {error_msg}")
    
    # Handle different response structures from Explorium
    results = data.get('results', [])
    if not results and 'data' in data:
        results = data.get('data', [])
    if not results and 'prospects' in data:
        results = data.get('prospects', [])
    
    # Reformat to our standard structure for normalization
    standardized = {"results": results}
    logger.info(f"✅ Explorium returned {len(results)} results")
    
    # Normalize results to our standard format
    normalized = normalize(standardized)
    logger.info(f"📤 Normalized response: {normalized}")
    
    return normalized

def get_mock_data(entity_type, filters):
    """Return mock B2B data for testing purposes."""
    if entity_type == "company":
        return {
            "results": [
                {
                    "type": "company",
                    "name": "Acme SaaS Inc",
                    "domain": "acme-saas.com",
                    "industry": "SaaS",
                    "employees": 250,
                    "revenue": "$50M",
                    "country": "United States",
                    "linkedin": "https://linkedin.com/company/acme-saas",
                    "founded_year": 2015,
                    "tech_stack": ["React", "Node.js", "AWS"],
                    "website": "www.acme-saas.com"
                },
                {
                    "type": "company",
                    "name": "CloudTech Solutions",
                    "domain": "cloudtech.io",
                    "industry": "SaaS",
                    "employees": 180,
                    "revenue": "$35M",
                    "country": "United States",
                    "linkedin": "https://linkedin.com/company/cloudtech",
                    "founded_year": 2017,
                    "tech_stack": ["Vue.js", "Python", "GCP"],
                    "website": "www.cloudtech.io"
                },
                {
                    "type": "company",
                    "name": "DataFlow AI",
                    "domain": "dataflow-ai.com",
                    "industry": "SaaS",
                    "employees": 320,
                    "revenue": "$75M",
                    "country": "United States",
                    "linkedin": "https://linkedin.com/company/dataflow-ai",
                    "founded_year": 2016,
                    "tech_stack": ["TypeScript", "Go", "Kubernetes"],
                    "website": "www.dataflow-ai.com"
                }
            ]
        }
    else:  # prospect
        return {
            "results": [
                {
                    "type": "prospect",
                    "name": "John Smith",
                    "job_title": "VP of Sales",
                    "company": "TechCorp",
                    "email": "john.smith@techcorp.com",
                    "country": "United States",
                    "linkedin": "https://linkedin.com/in/johnsmith",
                    "phone": "+1-555-0100"
                },
                {
                    "type": "prospect",
                    "name": "Sarah Johnson",
                    "job_title": "Head of Marketing",
                    "company": "InnovateLabs",
                    "email": "sarah.j@innovatelabs.io",
                    "country": "United States",
                    "linkedin": "https://linkedin.com/in/sarahjohnson",
                    "phone": "+1-555-0101"
                }
            ]
        }

def normalize(data):
    results = []

    for item in data.get("results", [])[:3]:
        # Handle both company and prospect response structures
        name = item.get("name") or item.get("full_name")
        domain = item.get("domain") or item.get("company_website")
        company = item.get("company_name")
        linkedin_url = item.get("linkedin_url") or item.get("linkedin")
        if not linkedin_url and item.get("linkedin_url_array"):
            linkedin_url = item.get("linkedin_url_array")[0]
        
        # Add https:// if missing from LinkedIn URL
        if linkedin_url and not linkedin_url.startswith("http"):
            linkedin_url = "https://" + linkedin_url
        
        results.append({
            "type": item.get("type", "prospect"),
            "name": name,
            "company": company,
            "domain": domain,
            "industry": item.get("industry"),
            "employee_count": item.get("employees"),
            "revenue": item.get("revenue"),
            "country": item.get("country") or item.get("country_name"),
            "job_title": item.get("job_title"),
            "seniority": item.get("job_level_main"),
            "linkedin_url": linkedin_url,
            "website": domain,
            "raw": item
        })

    return {"results": results}