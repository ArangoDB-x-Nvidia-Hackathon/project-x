from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from functools import lru_cache
import folium
from folium.plugins import MarkerCluster
from typing import List, Dict
import logging

# Initialize logger
logger = logging.getLogger("visualization_service")

# Configure geocoder with timeout and retries
geolocator = Nominatim(
    user_agent="gdelt_map_app",
    timeout=10  # Increase timeout to 10 seconds
)
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1,
    max_retries=2,
    error_wait_seconds=5
)

@lru_cache(maxsize=1000)
def cached_geocode(search_query: str) -> tuple:
    """Cache geocoding results to reduce API calls."""
    try:
        location = geocode(search_query)
        if location:
            return (location.latitude, location.longitude)
        return (None, None)
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.warning(f"Geocoding failed for {search_query}: {str(e)}")
        return (None, None)
    except Exception as e:
        logger.error(f"Unexpected geocoding error: {str(e)}")
        return (None, None)

def create_map(events: List[Dict]) -> str:
    """Create a Folium map with event markers using location names."""
    m = folium.Map(location=[20, 0], zoom_start=2)
    marker_cluster = MarkerCluster().add_to(m)
    
    for event in events:
        if not event.get("locations"):
            continue
            
        for loc in event["locations"]:
            # Skip if location name is missing
            if not loc.get("name"):
                continue
                
            # Use coordinates if available, otherwise geocode
            if loc.get("lat") and loc.get("lon"):
                lat, lon = loc["lat"], loc["lon"]
            else:
                search_query = f"{loc.get('name', '')}, {loc.get('country', '')}"
                lat, lon = cached_geocode(search_query)
                
            if lat and lon:
                # Create popup content
                popup_content = f"""
                <div style="width: 250px;">
                    <h4>{event['label']}</h4>
                    <p><b>Date:</b> {event['date']}</p>
                    <p><b>Location:</b> {loc.get('name', 'Unknown')}</p>
                    <p><b>Country:</b> {loc.get('country', 'Unknown')}</p>
                    <p><b>Actors:</b> {', '.join(event['actors'])}</p>
                    <p><b>Sentiment:</b> {event['sentiment'].capitalize()}</p>
                </div>
                """
                
                # Add marker with cluster
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(
                        color='green' if event['sentiment'] == 'positive' 
                              else 'red' if event['sentiment'] == 'negative' 
                              else 'blue'
                    )
                ).add_to(marker_cluster)
                break  # Only add one marker per event
    
    return m._repr_html_()