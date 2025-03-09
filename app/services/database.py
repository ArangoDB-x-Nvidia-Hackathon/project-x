from arango import ArangoClient
from datetime import datetime
from typing import List, Dict, Any
import logging

from config import ARANGO_HOST, ARANGO_USER, ARANGO_PASSWORD, ARANGO_DB
from services.sentiment import categorize_sentiment, filter_by_sentiment

# Import the NetworkX implementation
from services.graph_service import query_graph_database_nx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("database")

# Initialize ArangoDB client
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(ARANGO_DB, username=ARANGO_USER, password=ARANGO_PASSWORD, verify=True)

def build_aql_query(processed_query: Dict[str, Any]) -> str:
    """
    Build an AQL query based on the processed user query to retrieve
    relevant events from ArangoDB using the provided collection structure.
    """
    # Base query
    aql = """
    FOR event IN Event
        LET event_date = DATE_TIMESTAMP(event.date)
    """
    
    # Add filters
    filters = []
    
    # Time period filter
    if processed_query["time_period"]["start_date"]:
        start_timestamp = int(datetime.strptime(processed_query["time_period"]["start_date"], "%Y-%m-%d").timestamp() * 1000)
        filters.append(f"event_date >= {start_timestamp}")
    
    if processed_query["time_period"]["end_date"]:
        end_timestamp = int(datetime.strptime(processed_query["time_period"]["end_date"], "%Y-%m-%d").timestamp() * 1000)
        filters.append(f"event_date <= {end_timestamp}")
    
    # Topic filter - search in event descriptions
    if processed_query["topic"]:
        topic_terms = processed_query["topic"].lower().split()
        topic_filters = []
        for term in topic_terms:
            if term not in ["the", "and", "or", "in", "on", "at", "of", "to", "from", "with", "by"]:
                topic_filters.append(f"LOWER(event.description) LIKE '%{term}%'")
        
        if topic_filters:
            filters.append(f"({' OR '.join(topic_filters)})")
    
    # Actor filter
    if processed_query["actors"]:
        actor_filters = []
        for actor in processed_query["actors"]:
            actor_filters.append(f"""
                actor IN (
                    FOR v, e IN 1..1 OUTBOUND event eventActor
                    FILTER LOWER(v.name) LIKE '%{actor.lower()}%'
                    RETURN v
                )
            """)
        if actor_filters:
            filters.append(f"({' OR '.join(actor_filters)})")
    
    # Location filter
    if processed_query["locations"]:
        location_filters = []
        for location in processed_query["locations"]:
            location_filters.append(f"""
                location IN (
                    FOR v, e IN 1..1 OUTBOUND event hasLocation
                    FILTER LOWER(v.name) LIKE '%{location.lower()}%'
                    RETURN v
                )
            """)
        if location_filters:
            filters.append(f"({' OR '.join(location_filters)})")
    
    # Add all filters to the query
    if filters:
        aql += "FILTER " + " AND ".join(filters) + "\n"
    
    # Complete the query with sorting and limiting
    aql += """
    SORT event.date DESC
    LIMIT 1000
    RETURN {
        event_id: event._key,
        date: event.date,
        actors: (
            FOR v, e IN 1..1 OUTBOUND event eventActor
            RETURN v.name
        ),
        action: event.action,
        tone: event.tone,
        mention_count: event.mention_count,
        location: (
            FOR v, e IN 1..1 OUTBOUND event hasLocation
            RETURN {
                lat: v.lat,
                lon: v.lon,
                country: v.country,
                location_name: v.name
            }
        )[0]
    }
    """
    
    return aql

def query_graph_database_original(processed_query: Dict[str, Any]) -> List[Dict]:
    """
    Original implementation for querying the ArangoDB graph database.
    """
    try:
        # Build the AQL query
        aql_query = build_aql_query(processed_query)
        
        # Execute the query
        cursor = db.aql.execute(aql_query)
        
        # Process the results
        events = list(cursor)
        
        # Add sentiment categorization to each event
        for event in events:
            event["sentiment"] = categorize_sentiment(event["tone"])
        
        # Filter by sentiment if specified
        if processed_query["sentiment"] and processed_query["sentiment"].lower() != "all":
            events = filter_by_sentiment(events, processed_query["sentiment"])
        
        logger.info(f"Query returned {len(events)} events")
        return events
    
    except Exception as e:
        logger.error(f"Error querying graph database: {str(e)}")
        return []

def query_graph_database(processed_query: Dict[str, Any], use_networkx: bool = True) -> List[Dict]:
    """
    Query the ArangoDB graph database using the processed query parameters.
    Can use either NetworkX implementation or original implementation.
    
    Args:
        processed_query: The processed query parameters
        use_networkx: Whether to use NetworkX implementation (default: True)
        
    Returns:
        List of event dictionaries
    """
    if use_networkx:
        logger.info("Using NetworkX implementation for graph query")
        return query_graph_database_nx(processed_query)
    else:
        logger.info("Using original implementation for graph query")
        return query_graph_database_original(processed_query)