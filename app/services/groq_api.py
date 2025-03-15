import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_query_parameters(user_query):
    """
    Use Groq to extract query parameters from natural language
    Example: "Show me terrorist attacks in Middle East during 2001"
    Should extract: year=2001, region="Middle East", event_type="terrorist attack"
    """
    prompt = f"""
    Extract search parameters from the following query: "{user_query}"
    
    Return a JSON object with these fields if present in the query:
    - year: Extract year mentions (e.g., 2001, 1990s)
    - country: Extract country or region names
    - event_type: Extract the type of event (e.g., terrorist attack, natural disaster)
    - group: Extract any mentioned groups or organizations
    
    If information is not present in the query, omit the field.
    Return only the JSON object without any explanations.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # Use an appropriate Groq model
            messages=[
                {"role": "system", "content": "You extract search parameters from natural language queries about global events."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        response_text = completion.choices[0].message.content
        
        # Parse the JSON response
        try:
            # In case the model returns additional text around the JSON
            response_text = response_text.strip()
            
            # Extract content between ``` if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            parameters = json.loads(response_text)
            # Type conversion for year
            if "year" in parameters:
                try:
                    raw_year = parameters["year"]
                    if isinstance(raw_year, str):
                        # Handle decade formats like "1990s"
                        if raw_year.lower().endswith("s"):
                            raw_year = raw_year[:-1]
                        parameters["year"] = int(raw_year)
                    else:
                        parameters["year"] = int(raw_year)
                except (ValueError, TypeError) as e:
                    print(f"Invalid year format: {raw_year} - {e}")
                    del parameters["year"]
            return parameters
        except json.JSONDecodeError:
            # Fallback for cases where model doesn't return valid JSON
            parameters = {}
            
            # Simple pattern matching extraction
            if "2001" in user_query:
                parameters["year"] = 2001
                
            return parameters
    except Exception as e:
        print(f"Error querying Groq API: {e}")
        return {}

def generate_event_summary(event_data):
    """
    Generate a summary of an event using Groq
    """
    event_info = f"""
    Event: {event_data['incident_name']}
    Type: {event_data['event_type']}
    Year: {event_data['year']}
    Country: {event_data['country']}
    Impact: {event_data['impact']}
    Outcome: {event_data['outcome']}
    Responsible Group: {event_data['responsible_group']}
    """
    
    prompt = f"""
    Provide a brief summary of the following event:
    
    {event_info}
    
    Create a concise 2-3 sentence summary that explains what happened, who was involved, and the outcome.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You generate concise summaries of historical events."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        summary = completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"In {event_data['year']}, {event_data['incident_name']} occurred in {event_data['country']}."