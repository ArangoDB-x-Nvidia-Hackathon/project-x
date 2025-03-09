from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Define Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str

class EventLocation(BaseModel):
    lat: float
    lon: float
    country: str
    location_name: str
    
class EventData(BaseModel):
    event_id: str
    date: str
    actors: List[str]
    action: str
    tone: float  # AvgTone from GDELT
    sentiment: str  # "positive", "neutral", or "negative"
    mention_count: int
    location: EventLocation
    
class QueryResponse(BaseModel):
    query: str
    processed_query: Dict[str, Any]
    events: List[EventData]
    stats: Dict[str, Any]