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
    if not API_KEY and not USE_MOCK:
        raise ValueError("EXPLORIUM_API_KEY environment variable not set")
    
    logger.info(f"Entity: {entity_type}")
    logger.info(f"Filters: {filters}")
    
    # Use mock data for testing if enabled
    if USE_MOCK:
        logger.info("Using mock data for testing")
        return get_mock_data(entity_type, filters)
    
    url = "https://api.explorium.ai/v1/search"

    payload = {
        "entity": entity_type,
        "filters": filters,
        "limit": 3
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
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
        logger.error(f"Explorium API error ({res.status_code}): {error_msg}")
        raise ValueError(f"Explorium API error ({res.status_code}): {error_msg}")
    
    data = res.json()
    
    # Check for API error response
    if 'error' in data:
        error_msg = data.get('error')
        logger.error(f"Explorium API error: {error_msg}")
        raise ValueError(f"Explorium API error: {error_msg}")
    
    logger.info(f"Explorium returned {len(data.get('results', []))} results")
    
    return data

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
        results.append({
            "type": item.get("type"),
            "name": item.get("name"),
            "domain": item.get("domain"),
            "industry": item.get("industry"),
            "employee_count": item.get("employees"),
            "revenue": item.get("revenue"),
            "country": item.get("country"),
            "linkedin_url": item.get("linkedin"),
            "raw": item
        })

    return {"results": results}