from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models.schemas import QueryRequest, QueryResponse, EventData, EventLocation
from services.query_processor import process_query
from services.database import query_graph_database
from services.sentiment import calculate_stats
from services.visualization import create_map
from config import EVENT_CODES

# Create router
router = APIRouter()

# Initialize templates
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with the query form."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/api/query", response_model=QueryResponse)
async def query_events(query_request: QueryRequest):
    """
    Process a natural language query and return relevant GDELT events.
    """
    # Process the user query
    processed_query = process_query(query_request.query)
    
    # Query the graph database
    events_data = query_graph_database(processed_query)
    
    # Calculate statistics
    stats = calculate_stats(events_data)
    
    # Convert to Pydantic models
    events = []
    for event in events_data:
        try:
            # Create EventLocation object
            location = EventLocation(
                lat=event["location"]["lat"] if event["location"]["lat"] else 0.0,
                lon=event["location"]["lon"] if event["location"]["lon"] else 0.0,
                country=event["location"]["country"] if event["location"]["country"] else "",
                location_name=event["location"]["location_name"] if event["location"]["location_name"] else ""
            )
            
            # Create EventData object
            event_obj = EventData(
                event_id=str(event["event_id"]),
                date=event["date"],
                actors=[a for a in event["actors"] if a],
                action=event["action"],
                tone=float(event["tone"]),
                sentiment=event["sentiment"],
                mention_count=int(event["mention_count"]),
                location=location
            )
            
            events.append(event_obj)
        except Exception as e:
            print(f"Error processing event: {e}")
    
    # Return the response
    return QueryResponse(
        query=query_request.query,
        processed_query=processed_query,
        events=events,
        stats=stats
    )

@router.post("/api/visualize", response_class=HTMLResponse)
async def visualize_events(query_request: QueryRequest):
    """
    Process a query and return a Folium map visualization of the events.
    """
    # Process the user query
    processed_query = process_query(query_request.query)
    
    # Query the graph database
    events_data = query_graph_database(processed_query)
    
    # Create the map
    map_html = create_map(events_data)
    
    return map_html

@router.get("/api/event_codes")
async def get_event_codes():
    """Return a list of GDELT event codes and their meanings."""
    return {
        "event_codes": EVENT_CODES
    }