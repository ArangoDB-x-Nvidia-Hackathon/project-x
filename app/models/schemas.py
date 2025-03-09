from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Define Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str


class EventLocation(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class EventData(BaseModel):
    event_id: str
    date: str
    description: str
    label: str
    geo: Dict[str, Any]
    fatalities: int
    actors: List[str]
    locations: List[EventLocation]  # Changed from single location to list
    sentiment: str

class QueryResponse(BaseModel):
    query: str
    processed_query: Dict[str, Any]
    events: List[EventData]
    stats: Dict[str, Any]