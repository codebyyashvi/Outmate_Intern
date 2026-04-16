# services/normalize.py
"""
Normalize Explorium API responses into consistent format for frontend.
"""

def normalize(data):
    """
    Convert raw Explorium API response into standardized result format.
    
    Args:
        data: Raw response from Explorium API
        
    Returns:
        dict with "results" key containing normalized records (max 3)
    """
    results = []

    for item in data.get("results", [])[:3]:
        # Build normalized company/prospect record
        normalized_item = {
            "type": item.get("type", "company"),
            "name": item.get("name", ""),
            "domain": item.get("domain", ""),
            "industry": item.get("industry", ""),
            "employee_count": item.get("employees") or item.get("employee_count"),
            "revenue": item.get("revenue", ""),
            "country": item.get("country", ""),
            "linkedin_url": item.get("linkedin") or item.get("linkedin_url", ""),
            "founded_year": item.get("founded_year"),
            "tech_stack": item.get("tech_stack", []),
            "key_contacts": item.get("key_contacts", []),
            "website": item.get("website") or item.get("domain"),
            # Prospect-specific fields
            "email": item.get("email", ""),
            "job_title": item.get("job_title") or item.get("title", ""),
            "company_name": item.get("company_name") or item.get("company", ""),
            "phone": item.get("phone", ""),
            # Raw data for debugging
            "raw": item
        }
        
        # Filter out None/empty values for cleaner display
        normalized_item = {k: v for k, v in normalized_item.items() if v}
        results.append(normalized_item)

    return {"results": results}
