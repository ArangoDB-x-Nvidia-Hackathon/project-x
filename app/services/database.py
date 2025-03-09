from arango import ArangoClient
from datetime import datetime
from typing import List, Dict, Any

from config import ARANGO_HOST, ARANGO_DB, ARANGO_USER, ARANGO_PASSWORD
from services.sentiment import categorize_sentiment, filter_by_sentiment

# Initialize ArangoDB client
client = ArangoClient(hosts=ARANGO_HOST)
db = client.db(username=ARANGO_USER, password=ARANGO_PASSWORD , verify=True )

def build_aql_query(processed_query: Dict[str, Any]) -> str:
    """
    Build an AQL query based on the processed user query to retrieve
    relevant GDELT events from ArangoDB.
    """
    # Base query
    aql = """
    FOR event IN gdelt_events
        LET event_date = DATE_TIMESTAMP(event.Day)
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
                topic_filters.append(f"LOWER(event.EventDescriptions) LIKE '%{term}%'")
        
        if topic_filters:
            filters.append(f"({' OR '.join(topic_filters)})")
    
    # Actor filter
    if processed_query["actors"]:
        actor_filters = []
        for actor in processed_query["actors"]:
            actor_filters.append(f"LOWER(event.Actor1Name) LIKE '%{actor.lower()}%' OR LOWER(event.Actor2Name) LIKE '%{actor.lower()}%'")
        if actor_filters:
            filters.append(f"({' OR '.join(actor_filters)})")
    
    # Location filter
    if processed_query["locations"]:
        location_filters = []
        for location in processed_query["locations"]:
            location_filters.append(f"""
                LOWER(event.Actor1Geo_Fullname) LIKE '%{location.lower()}%' OR 
                LOWER(event.Actor2Geo_Fullname) LIKE '%{location.lower()}%' OR 
                LOWER(event.ActionGeo_Fullname) LIKE '%{location.lower()}%'
            """)
        if location_filters:
            filters.append(f"({' OR '.join(location_filters)})")
    
    # Add all filters to the query
    if filters:
        aql += "FILTER " + " AND ".join(filters) + "\n"
    
    # Complete the query with sorting and limiting
    aql += """
    SORT event.DATEADDED DESC
    LIMIT 1000
    RETURN {
        event_id: event.GlobalEventID,
        date: event.Day,
        actors: [event.Actor1Name, event.Actor2Name],
        action: event.EventCode,
        tone: event.AvgTone,
        mention_count: event.NumMentions,
        location: {
            lat: TO_NUMBER(event.ActionGeo_Lat),
            lon: TO_NUMBER(event.ActionGeo_Long),
            country: event.ActionGeo_CountryCode,
            location_name: event.ActionGeo_Fullname
        }
    }
    """
    
    return aql

def query_graph_database(processed_query: Dict[str, Any]) -> List[Dict]:
    """
    Query the ArangoDB graph database using the processed query parameters.
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
            
        return events
    
    except Exception as e:
        print(f"Error querying graph database: {str(e)}")
        return []