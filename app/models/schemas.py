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
    event_id: str  # Corresponds to _key in the dataset
    date: str  # Date of the event
    description: str  # Event description
    label: str  # Event label (e.g., "Riots")
    geo: Dict[str, Any]  # GeoJSON object (e.g., {"type": "Point", "coordinates": [lat, lon]})
    fatalities: int  # Number of fatalities
    actors: List[str]  # List of actor names
    location: EventLocation  # Location details
    sentiment: str  # "positive", "neutral", or "negative"

class QueryResponse(BaseModel):
    query: str  # Original query
    processed_query: Dict[str, Any]  # Processed query parameters
    events: List[EventData]  # List of events matching the query
    stats: Dict[str, Any]  # Statistics about the results (e.g., count, sentiment distribution)