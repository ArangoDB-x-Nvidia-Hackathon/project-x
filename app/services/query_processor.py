import re
import json
import requests
from config import GROQ_API_KEY

def process_query(user_query: str) -> dict:
    """
    Process the user query into structured parameters for graph traversal
    using direct API calls to Groq instead of LangChain.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    template = """
    The user has provided the following query about world events: "{query}"
    
    Please extract the following information:
    1. Topic: What is the main topic or event being asked about?
    2. Time period: What time period is the query about? Extract start and end dates if possible.
    3. Locations: Are there any specific locations mentioned?
    4. Actors: Are there any specific actors (people, organizations, countries) mentioned?
    5. Sentiment: Is the query specifically about positive, negative, or neutral sentiment?
    
    Format the output as a JSON object with the following structure:
    {{
        "topic": "extracted topic",
        "time_period": {{
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null"
        }},
        "locations": ["location1", "location2"],
        "actors": ["actor1", "actor2"],
        "sentiment": "positive/negative/neutral/all"
    }}
    """
    
    # Format the template with the user query
    formatted_prompt = template.format(query=user_query)
    
    # Prepare the data for the API request
    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": formatted_prompt}],
        "temperature": 0
    }
    
    try:
        # Make the API request
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        result_json = response.json()
        result_text = result_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extract the JSON part of the response
        try:
            # Use regex to extract JSON object
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Fallback with minimal structure
                return {
                    "topic": user_query,
                    "time_period": {"start_date": None, "end_date": None},
                    "locations": [],
                    "actors": [],
                    "sentiment": "all"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return a minimal structure
            return {
                "topic": user_query,
                "time_period": {"start_date": None, "end_date": None},
                "locations": [],
                "actors": [],
                "sentiment": "all"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        # Return fallback response in case of API error
        return {
            "topic": user_query,
            "time_period": {"start_date": None, "end_date": None},
            "locations": [],
            "actors": [],
            "sentiment": "all"
        } 