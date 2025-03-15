from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Import our custom modules
from app.database import get_event_details
from app.groq_api import generate_event_summary

router = APIRouter()

@router.get("/event/{event_id}", response_class=JSONResponse)
async def get_event(event_id: str):
    """Get detailed information about an event"""
    event_details = get_event_details(event_id)
    
    if not event_details:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Generate a summary using Groq
    event_data = {
        "incident_name": event_details["event"]["incident_name"],
        "event_type": event_details["event"]["event_type"],
        "year": event_details["event"]["year"],
        "country": event_details["country"]["name"],
        "impact": event_details["event"]["impact"],
        "outcome": event_details["event"]["outcome"],
        "responsible_group": event_details["event"]["responsible_group"]
    }
    
    summary = generate_event_summary(event_data)
    
    return {
        "event": event_details["event"],
        "country": event_details["country"],
        "groups": event_details["groups"],
        "summary": summary
    }