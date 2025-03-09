import folium
from folium.plugins import MarkerCluster
from typing import List, Dict

def create_map(events: List[Dict]) -> str:
    """
    Create a Folium map with the event data and return the HTML.
    """
    # Create a base map centered at an average of event locations
    if not events:
        # Default center if no events
        m = folium.Map(location=[0, 0], zoom_start=2)
    else:
        # Calculate average position
        valid_events = [e for e in events if e["location"]["lat"] and e["location"]["lon"]]
        if valid_events:
            avg_lat = sum(e["location"]["lat"] for e in valid_events) / len(valid_events)
            avg_lon = sum(e["location"]["lon"] for e in valid_events) / len(valid_events)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=3)
        else:
            m = folium.Map(location=[0, 0], zoom_start=2)
    
    # Create marker clusters for different sentiments
    positive_cluster = MarkerCluster(name="Positive Events")
    neutral_cluster = MarkerCluster(name="Neutral Events")
    negative_cluster = MarkerCluster(name="Negative Events")
    
    # Add markers for each event
    for event in events:
        lat = event["location"]["lat"]
        lon = event["location"]["lon"]
        
        if not lat or not lon:
            continue
            
        # Create popup content
        popup_content = f"""
        <div style="width: 300px;">
            <h4>Event ID: {event["event_id"]}</h4>
            <p><b>Date:</b> {event["date"]}</p>
            <p><b>Actors:</b> {", ".join(filter(None, event["actors"]))}</p>
            <p><b>Action Code:</b> {event["action"]}</p>
            <p><b>Location:</b> {event["location"]["location_name"]}</p>
            <p><b>Sentiment:</b> {event["sentiment"].capitalize()} (Tone: {event["tone"]:.2f})</p>
            <p><b>Mentions:</b> {event["mention_count"]}</p>
        </div>
        """
        
        # Create marker with appropriate color based on sentiment
        if event["sentiment"] == "positive":
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                icon=folium.Icon(color="green", icon="plus")
            ).add_to(positive_cluster)
        elif event["sentiment"] == "negative":
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                icon=folium.Icon(color="red", icon="minus")
            ).add_to(negative_cluster)
        else:
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(neutral_cluster)
    
    # Add marker clusters to the map
    positive_cluster.add_to(m)
    neutral_cluster.add_to(m)
    negative_cluster.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Return the HTML string
    return m._repr_html_()