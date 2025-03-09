import re
import json
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

from config import GROQ_API_KEY

# Initialize Groq for query processing
llm = ChatGroq(
    temperature=0,
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    max_tokens=2048
)

def process_query(user_query: str) -> dict:
    """
    Use LangChain to process the user query into structured parameters
    for graph traversal using Groq's API.
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
    {
        "topic": "extracted topic",
        "time_period": {
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null"
        },
        "locations": ["location1", "location2"],
        "actors": ["actor1", "actor2"],
        "sentiment": "positive/negative/neutral/all"
    }
    """
    
    prompt = PromptTemplate(
        input_variables=["query"],
        template=template,
    )
    
    # Generate the structured query using Groq
    result = llm.invoke(prompt.format(query=user_query))
    
    # Extract the response content
    result_text = result.content
    
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