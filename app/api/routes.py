from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.schemas import QueryRequest, QueryResponse, EventData, EventLocation
from services.query_processor import process_query
from services.graph_service import query_graph_database_nx
from services.visualization import create_map
import logging

# Initialize router and templates
router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("routes")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with the query form."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/api/query", response_model=QueryResponse)
async def query_events(query_request: QueryRequest):
    """Process a natural language query and return relevant GDELT events."""
    try:
        # Process the user query
        processed_query = process_query(query_request.query)

        # Query the graph database
        events_data = query_graph_database_nx(processed_query)

        # Convert to Pydantic models
        events = []
        for event in events_data:
            try:
                # Convert locations
                locations = [
                    EventLocation(
                        name=loc.get("name"),  # Can be None
                        country=loc.get("country"),  # Can be None
                        lat=loc.get("lat"),  # Can be None
                        lon=loc.get("lon")  # Can be None
                    )
                    for loc in event.get("locations", [])
                ]

                # Create EventData object
                event_obj = EventData(
                    event_id=str(event["event_id"]),
                    date=event["date"],
                    description=event.get("description", ""),
                    label=event.get("label", ""),
                    geo=event.get("geo", {}),
                    fatalities=event.get("fatalities", 0),
                    actors=event.get("actors", []),
                    locations=locations,
                    sentiment=event.get("sentiment", "neutral")
                )

                events.append(event_obj)
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                continue

        # Return the response
        return QueryResponse(
            query=query_request.query,
            processed_query=processed_query,
            events=events,
            stats={}  # Add stats calculation if needed
        )
    except Exception as e:
        logger.error(f"Error in query processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/visualize", response_class=HTMLResponse)
async def visualize_events(query_request: QueryRequest):
    """Process a query and return a Folium map visualization of the events."""
    try:
        processed_query = process_query(query_request.query)
        events_data = query_graph_database_nx(processed_query)

        if not events_data:
            return HTMLResponse(content="<div>No events found</div>")

        map_html = create_map(events_data)
        return HTMLResponse(content=map_html)
    except Exception as e:
        logger.error(f"Visualization error: {str(e)}", exc_info=True)
        return HTMLResponse(
            content="<div style='color: red'>Error generating map</div>",
            status_code=500
        )
