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
    
    # Start with simpler AQL query to get base events
    aql = """
    FOR event IN Event
        LET event_date = DATE_TIMESTAMP(event.date)
    """
    
    filters = []
    
    # Time period filter
    if processed_query["time_period"]["start_date"]:
        try:
            start_timestamp = int(datetime.strptime(processed_query["time_period"]["start_date"], "%Y-%m-%d").timestamp() * 1000)
            filters.append(f"event_date >= {start_timestamp}")
        except ValueError:
            logger.warning(f"Invalid start date format: {processed_query['time_period']['start_date']}")
    
    if processed_query["time_period"]["end_date"]:
        try:
            end_timestamp = int(datetime.strptime(processed_query["time_period"]["end_date"], "%Y-%m-%d").timestamp() * 1000)
            filters.append(f"event_date <= {end_timestamp}")
        except ValueError:
            logger.warning(f"Invalid end date format: {processed_query['time_period']['end_date']}")
    
    # Topic filter with simplified approach
    if processed_query["topic"]:
        topic_terms = processed_query["topic"].lower().split()
        topic_filters = []
        for term in topic_terms:
            if term not in ["the", "and", "or", "in", "on", "at", "of", "to", "from", "with", "by"]:
                topic_filters.append(f"LOWER(event.description) LIKE '%{term}%'")
        
        if topic_filters:
            filters.append(f"({' OR '.join(topic_filters)})")
    
    # Add all filters to the query
    if filters:
        aql += "FILTER " + " AND ".join(filters) + "\n"
    
    # Complete the query with sorting and limiting
    aql += """
    SORT event.date DESC
    LIMIT 1000
    RETURN {
        _id: event._id,
        _key: event._key,
        date: event.date,
        action: event.action,
        description: event.description,
        tone: event.tone,
        mention_count: event.mention_count
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
            G.add_node(event["_id"], 
                      type="Event", 
                      key=event["_key"],
                      date=event["date"],
                      action=event["action"],
                      description=event.get("description", ""),
                      tone=event["tone"],
                      mention_count=event["mention_count"],
                      sentiment=categorize_sentiment(event["tone"]))
        
        # No events found, return empty graph
        if not events:
            return G
            
        # Format list of event IDs for subsequent queries
        event_ids = [e["_id"] for e in events]
        
        # Get actor relationships in a batch
        actor_filter = ""
        if processed_query["actors"]:
            actor_conditions = []
            for actor in processed_query["actors"]:
                actor_conditions.append(f"LOWER(a.name) LIKE '%{actor.lower()}%'")
            actor_filter = f"FILTER {' OR '.join(actor_conditions)}"
            
        actor_aql = f"""
        FOR event IN Event
            FILTER event._id IN {event_ids}
            FOR a, edge IN 1..1 OUTBOUND event eventActor
                {actor_filter}
                RETURN {{
                    event_id: event._id,
                    actor_id: a._id,
                    actor_name: a.name
                }}
        """
        
        logger.info("Fetching actor relationships...")
        actor_cursor = db.aql.execute(actor_aql)
        actor_edges = list(actor_cursor)
        logger.info(f"Retrieved {len(actor_edges)} actor relationships")
        
        # Add actors and relationships to graph
        for edge in actor_edges:
            if edge["actor_id"] not in G:
                G.add_node(edge["actor_id"], type="Actor", name=edge["actor_name"])
            G.add_edge(edge["event_id"], edge["actor_id"], type="eventActor")
        
        # Get location relationships
        loc_filter = ""
        if processed_query["locations"]:
            loc_conditions = []
            for location in processed_query["locations"]:
                loc_conditions.append(f"LOWER(l.name) LIKE '%{location.lower()}%'")
            loc_filter = f"FILTER {' OR '.join(loc_conditions)}"
            
        loc_aql = f"""
        FOR event IN Event
            FILTER event._id IN {event_ids}
            FOR l, edge IN 1..1 OUTBOUND event hasLocation
                {loc_filter}
                RETURN {{
                    event_id: event._id,
                    location_id: l._id,
                    location_name: l.name,
                    lat: l.lat,
                    lon: l.lon,
                    country: l.country
                }}
        """
        
        logger.info("Fetching location relationships...")
        loc_cursor = db.aql.execute(loc_aql)
        loc_edges = list(loc_cursor)
        logger.info(f"Retrieved {len(loc_edges)} location relationships")
        
        # Add locations and relationships to graph
        for edge in loc_edges:
            if edge["location_id"] not in G:
                G.add_node(edge["location_id"], 
                          type="Location", 
                          name=edge["location_name"],
                          lat=edge["lat"],
                          lon=edge["lon"],
                          country=edge["country"])
            G.add_edge(edge["event_id"], edge["location_id"], type="hasLocation")
            
        return G
    
    except Exception as e:
        logger.error(f"Error loading graph from ArangoDB: {str(e)}")
        return G

def extract_events_from_graph(G: nx.DiGraph) -> List[Dict]:
    """
    Extract event data from NetworkX graph in the required format
    for visualization.
    """
    events = []
    
    for node_id, node_data in G.nodes(data=True):
        if node_data.get("type") == "Event":
            # Find connected actors
            actors = []
            for _, actor_id in G.out_edges(node_id):
                if G.nodes[actor_id].get("type") == "Actor":
                    actors.append(G.nodes[actor_id].get("name", ""))
            
            # Find connected location
            location = {
                "lat": 0.0,
                "lon": 0.0,
                "country": "",
                "location_name": ""
            }
            
            for _, loc_id in G.out_edges(node_id):
                if G.nodes[loc_id].get("type") == "Location":
                    loc_data = G.nodes[loc_id]
                    location = {
                        "lat": loc_data.get("lat", 0.0),
                        "lon": loc_data.get("lon", 0.0),
                        "country": loc_data.get("country", ""),
                        "location_name": loc_data.get("name", "")
                    }
                    break
            
            # Create event data object
            event = {
                "event_id": node_data.get("key", ""),
                "date": node_data.get("date", ""),
                "actors": actors,
                "action": node_data.get("action", ""),
                "tone": node_data.get("tone", 0.0),
                "sentiment": node_data.get("sentiment", "neutral"),
                "mention_count": node_data.get("mention_count", 0),
                "location": location
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