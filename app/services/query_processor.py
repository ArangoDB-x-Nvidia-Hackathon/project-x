import re
import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
print(GROQ_API_KEY)

def process_query(user_query: str) -> dict:
    """
    Process the user query into structured parameters for graph traversal
    using Groq API.
    """
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
    
    formatted_prompt = template.format(query=user_query)
    
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=0
        )
        
        result_text = response.choices[0].message.content
        
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
    except Exception as e:
        print(f"Groq API request error: {e}")
    
    return {
        "topic": user_query,
        "time_period": {"start_date": None, "end_date": None},
        "locations": [],
        "actors": [],
        "sentiment": "all"
    }
