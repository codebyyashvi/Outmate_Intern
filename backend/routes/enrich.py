# routes/enrich.py
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from models.schemas import EnrichRequest
from services.gemini_service import parse_prompt, get_default_filters
from services.explorium_service import fetch_data
from services.normalize import normalize
import logging

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

@router.post("/api/enrich")
@limiter.limit("10/minute")
def enrich(req: EnrichRequest, request: Request):
    """
    Main enrichment endpoint.
    
    Accepts natural language prompt, parses it with Gemini,
    fetches enriched data from Explorium, returns up to 3 results.
    Falls back to default filters if Gemini is unavailable.
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Empty prompt")

    if len(req.prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt too long (max 1000 chars)")

    client_ip = request.client.host
    prompt_len = len(req.prompt)
    
    logger.info(f"[{client_ip}] Enrichment request - prompt length: {prompt_len}")

    try:
        # Parse prompt into filters via Gemini
        try:
            parsed = parse_prompt(req.prompt)
            logger.info(f"[{client_ip}] Used Gemini to parse prompt")
        except ValueError as gemini_err:
            # Fallback: generate basic filters from prompt if Gemini fails
            logger.warning(f"[{client_ip}] Gemini failed: {str(gemini_err)}. Using fallback filters.")
            parsed = get_default_filters(req.prompt)
            logger.info(f"[{client_ip}] Generated fallback filters for prompt")
        
        entity = parsed.get("entity_type", "company")
        filters = parsed.get("filters", {})

        logger.info(f"[{client_ip}] Parsed entity_type: {entity}")

        # Fetch data from Explorium (or mock data if USE_MOCK_DATA=true)
        raw_data = fetch_data(entity, filters)
        result_count = len(raw_data.get("results", []))
        
        logger.info(f"[{client_ip}] Returned {result_count} results")

        # Normalize and return
        return normalize(raw_data)

    except ValueError as e:
        logger.error(f"[{client_ip}] Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid prompt: {str(e)}")
    
    except Exception as e:
        logger.error(f"[{client_ip}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error processing your request")