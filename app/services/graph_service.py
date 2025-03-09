import networkx as nx
from arango import ArangoClient
from datetime import datetime
from typing import List, Dict, Any
import logging

from config import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB
from services.sentiment import categorize_sentiment, filter_by_sentiment

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("graph_service")

# Initialize ArangoDB client
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB, username=ARANGO_USER, password=ARANGO_PASSWORD, verify=True)

def load_graph_from_arango(processed_query: Dict[str, Any]) -> nx.DiGraph:
    """
    Load the relevant subgraph from ArangoDB into a NetworkX DiGraph
    based on the processed query parameters.
    """
    G = nx.DiGraph()
    
    # Base query to fetch events
    aql = """
    WITH Event, Actor, Location, eventActor, hasLocation  // Declare all collections used in the query
    FOR e IN Event
    """
    
    filters = []
    
    # Time period filter
    if processed_query["time_period"]["start_date"]:
        start_timestamp = int(datetime.strptime(processed_query["time_period"]["start_date"], "%Y-%m-%d").timestamp() * 1000)
        filters.append(f"e.dateStamp >= {start_timestamp}")
    
    if processed_query["time_period"]["end_date"]:
        end_timestamp = int(datetime.strptime(processed_query["time_period"]["end_date"], "%Y-%m-%d").timestamp() * 1000)
        filters.append(f"e.dateStamp <= {end_timestamp}")
    
    # Topic filter
    if processed_query["topic"]:
        topic_terms = processed_query["topic"].lower().split()
        topic_filters = []
        for term in topic_terms:
            if term not in ["the", "and", "or", "in", "on", "at", "of", "to", "from", "with", "by"]:
                topic_filters.append(f'CONTAINS(LOWER(e.description), "{term}")')
        
        if topic_filters:
            filters.append(f"({' OR '.join(topic_filters)})")
    
    # Add all filters to the query
    if filters:
        aql += "FILTER " + " AND ".join(filters) + "\n"
    
    # Complete the query with sorting and limiting
    aql += """
    SORT e.dateStamp DESC
    LIMIT 1000
    RETURN {
        _id: e._id,
        _key: e._key,
        date: e.date,
        description: e.description,
        label: e.label,
        geo: e.geo,
        fatalities: e.fatalities
    }
    """
    
    try:
        # Execute the query
        logger.info("Executing base event query...")
        cursor = db.aql.execute(aql)
        events = list(cursor)
        logger.info(f"Retrieved {len(events)} base events")
        
        # Add events to NetworkX graph
        for event in events:
            G.add_node(
                event["_id"],
                type="Event",
                key=event["_key"],
                date=event.get("date", ""),
                description=event.get("description", ""),
                label=event.get("label", ""),
                geo=event.get("geo", {}),
                fatalities=event.get("fatalities", 0),
                sentiment=categorize_sentiment(event.get("tone", 0.0))  # Assuming tone is added later
            )
        
        # No events found, return empty graph
        if not events:
            return G
            
        # Fetch actor and location relationships
        event_ids = [e["_id"] for e in events]
        
        # Actor relationships
        actor_aql = f"""
        WITH Event, Actor, eventActor  // Declare collections for actor traversal
        FOR e IN Event
            FILTER e._id IN {event_ids}
            FOR a, edge IN 1..1 OUTBOUND e eventActor
                RETURN {{
                    event_id: e._id,
                    actor_id: a._id,
                    actor_name: a.name
                }}
        """
        
        logger.info("Fetching actor relationships...")
        actor_cursor = db.aql.execute(actor_aql)
        for edge in actor_cursor:
            if edge["actor_id"] not in G:
                G.add_node(edge["actor_id"], type="Actor", name=edge["actor_name"])
            G.add_edge(edge["event_id"], edge["actor_id"], type="eventActor")
        
        # Location relationships
        loc_aql = f"""
        WITH Event, Location, hasLocation  // Declare collections for location traversal
        FOR e IN Event
            FILTER e._id IN {event_ids}
            FOR l, edge IN 1..1 OUTBOUND e hasLocation
                RETURN {{
                    event_id: e._id,
                    location_id: l._id,
                    location_name: l.name,
                    lat: l.lat,
                    lon: l.lon,
                    country: l.country
                }}
        """
        
        logger.info("Fetching location relationships...")
        loc_cursor = db.aql.execute(loc_aql)
        for edge in loc_cursor:
            if edge["location_id"] not in G:
                G.add_node(
                    edge["location_id"],
                    type="Location",
                    name=edge["location_name"],
                    lat=edge.get("lat", 0.0),
                    lon=edge.get("lon", 0.0),
                    country=edge.get("country", "")
                )
            G.add_edge(edge["event_id"], edge["location_id"], type="hasLocation")
            
        return G
    
    except Exception as e:
        logger.error(f"Error loading graph from ArangoDB: {str(e)}")
        return G

def extract_events_from_graph(G: nx.DiGraph) -> List[Dict]:
    """Extract event data from NetworkX graph in the required format."""
    events = []
    
    for node_id, node_data in G.nodes(data=True):
        if node_data.get("type") == "Event":
            # Find connected actors
            actors = []
            for _, actor_id in G.out_edges(node_id):
                if G.nodes[actor_id].get("type") == "Actor":
                    actors.append(G.nodes[actor_id].get("name", ""))
            
            # Find connected locations (multiple possible)
            locations = []
            for _, loc_id in G.out_edges(node_id):
                if G.nodes[loc_id].get("type") == "Location":
                    loc_data = G.nodes[loc_id]
                    locations.append({
                        "name": loc_data.get("name"),  # Can be None
                        "country": loc_data.get("country"),  # Can be None
                        "lat": loc_data.get("lat"),  # Can be None
                        "lon": loc_data.get("lon")  # Can be None
                    })
            
            # Create event data object
            event = {
                "event_id": node_data.get("key", ""),
                "date": node_data.get("date", ""),
                "description": node_data.get("description", ""),
                "label": node_data.get("label", ""),
                "geo": node_data.get("geo", {}),
                "fatalities": node_data.get("fatalities", 0),
                "actors": actors,
                "locations": locations,  # Now a list of location dicts
                "sentiment": node_data.get("sentiment", "neutral")
            }
            
            events.append(event)
    
    return events

def query_graph_database_nx(processed_query: Dict[str, Any]) -> List[Dict]:
    """
    Query the ArangoDB graph database using NetworkX for efficient processing.
    """
    try:
        # Load relevant subgraph from ArangoDB
        logger.info("Loading graph from ArangoDB...")
        G = load_graph_from_arango(processed_query)
        logger.info(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Extract events in required format
        events = extract_events_from_graph(G)
        logger.info(f"Extracted {len(events)} events from graph")
        
        # Filter by sentiment if specified
        if processed_query["sentiment"] and processed_query["sentiment"].lower() != "all":
            events = filter_by_sentiment(events, processed_query["sentiment"])
            logger.info(f"After sentiment filtering: {len(events)} events")
        
        return events
    
    except Exception as e:
        logger.error(f"Error in NetworkX query processing: {str(e)}")
        return []