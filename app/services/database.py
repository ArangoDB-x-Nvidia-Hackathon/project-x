import os
from dotenv import load_dotenv
from arango import ArangoClient

# Load environment variables
load_dotenv()

# ArangoDB connection details
HOST = os.getenv("ARANGO_HOST")
USERNAME = os.getenv("ARANGO_USER")
PASSWORD = os.getenv("ARANGO_PASSWORD")
DB_NAME = os.getenv("ARANGO_DB")

def get_db_connection():
    """Establish connection to ArangoDB"""
    client = ArangoClient(hosts=HOST)
    db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    return db

def query_events_by_year(year):
    """Query events by year"""
    db = get_db_connection()
    
    aql_query = """
    WITH events, countries
    FOR event IN events
        FILTER event.year == @year
        LET country = (
            FOR c IN OUTBOUND event located_in
                RETURN c
        )[0]
        RETURN {
            "event_id": event._key,
            "incident_name": event.incident_name,
            "event_type": event.event_type,
            "impact": event.impact,
            "responsible_group": event.responsible_group,
            "outcome": event.outcome,
            "country": country.name,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "year": event.year
        }
    """
    
    cursor = db.aql.execute(aql_query, bind_vars={"year": year})
    return [doc for doc in cursor]

def search_events(query_text):
    """Search events based on text query"""
    db = get_db_connection()
    
    # Simple implementation - can be expanded with full-text search
    aql_query = """
    WITH events  // Still needed for collection visibility
    FOR event IN events
        SEARCH ANALYZER(
            TOKENS(@query, "text_en") ANY == event.incident_name OR
            TOKENS(@query, "text_en") ANY == event.event_type OR
            TOKENS(@query, "text_en") ANY == event.outcome,
            "text_en"
        )
        LET country = (
            FOR c IN OUTBOUND event located_in
                RETURN c
        )[0]
        RETURN {
            "event_id": event._key,
            "incident_name": event.incident_name,
            "event_type": event.event_type,
            "impact": event.impact,
            "responsible_group": event.responsible_group,
            "outcome": event.outcome,
            "country": country.name,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "year": event.year
        }
    """
    
    cursor = db.aql.execute(aql_query, bind_vars={"query": query_text})
    return [doc for doc in cursor]

def get_event_details(event_id):
    """Get detailed information about an event"""
    db = get_db_connection()
    
    aql_query = """
    WITH events, countries, groups  // Add all involved collections
    LET event = DOCUMENT(CONCAT('events/', @event_id))
    LET country = (
        FOR c IN OUTBOUND event located_in
            RETURN c
    )[0]
    LET groups = (
        FOR g IN INBOUND event caused_by
            RETURN g
    )
    
    RETURN {
        "event": event,
        "country": country,
        "groups": groups
    }
    """
    
    cursor = db.aql.execute(aql_query, bind_vars={"event_id": event_id})
    results = [doc for doc in cursor]
    
    if results:
        return results[0]
    return None