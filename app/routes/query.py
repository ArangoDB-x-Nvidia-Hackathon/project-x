from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import folium
from folium.plugins import MarkerCluster

# Import our custom modules
from app.services.database import query_events_by_year, search_events
from app.services.groq_api import extract_query_parameters
from app.services.sentiment import analyze_event_sentiment, get_sentiment_color

router = APIRouter()

@router.post("/query", response_class=JSONResponse)
async def process_query(query: str = Form(...)):
    """Process natural language query using Groq"""
    
    # Extract parameters from query using Groq
    parameters = extract_query_parameters(query)
    
    # Initialize results
    events = []
    
    # Process based on extracted parameters
    if "year" in parameters:
        events = query_events_by_year(parameters["year"])
    else:
        # Use the query text directly for search
        events = search_events(query)
    
    # Analyze sentiment of events
    sentiment_analysis = analyze_event_sentiment(events)
    
    # Generate the map with events
    map_html = generate_map(events)
    
    return {
        "sentiment": sentiment_analysis["overall_sentiment"],
        "sentiment_counts": sentiment_analysis["counts"],
        "total_events": sentiment_analysis["total"],
        "events": events,
        "map_html": map_html
    }

def generate_map(events):
    """Generate a Folium map with event markers"""
    
    # Default to world view if no events
    if not events:
        m = folium.Map(location=[20, 0], zoom_start=2)
        return m._repr_html_()  # Use the built-in HTML representation instead

    # Calculate center of the map based on events
    latitudes = [float(event["latitude"]) for event in events if event.get("latitude")]
    longitudes = [float(event["longitude"]) for event in events if event.get("longitude")]
    
    if not latitudes or not longitudes:
        m = folium.Map(location=[20, 0], zoom_start=2)
    else:
        center_lat = sum(latitudes) / len(latitudes)
        center_lon = sum(longitudes) / len(longitudes)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

    # Add marker cluster
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each event
    for event in events:
        if event.get("latitude") and event.get("longitude"):
            sentiment = event.get("sentiment", "neutral")
            color = get_sentiment_color(sentiment)
            
            popup_content = f"""
            <div style="width: 250px;">
                <h4>{event['incident_name']}</h4>
                <p><strong>Year:</strong> {event['year']}</p>
                <p><strong>Location:</strong> {event['country']}</p>
                <p><strong>Type:</strong> {event['event_type']}</p>
                <p><strong>Outcome:</strong> {event['outcome']}</p>
                <button onclick="showEventDetails('{event['event_id']}')" 
                        class="btn btn-primary btn-sm">
                    View Details
                </button>
            </div>
            """

            folium.Marker(
                location=[float(event["latitude"]), float(event["longitude"])],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=event["incident_name"],
                icon=folium.Icon(color=color)
            ).add_to(marker_cluster)

    # Use the built-in HTML representation
    return m._repr_html_()