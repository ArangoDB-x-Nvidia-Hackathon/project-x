from typing import List, Dict

def categorize_sentiment(tone: float) -> str:
    """
    Categorize the GDELT AvgTone value into positive, neutral, or negative.
    """
    if tone > 2.0:
        return "positive"
    elif tone < -2.0:
        return "negative"
    else:
        return "neutral"

def filter_by_sentiment(events: List[Dict], target_sentiment: str) -> List[Dict]:
    """
    Filter events by the target sentiment if specified.
    """
    if target_sentiment.lower() in ["positive", "negative", "neutral"]:
        return [event for event in events if event["sentiment"] == target_sentiment.lower()]
    return events

def calculate_stats(events: List[Dict]) -> Dict:
    """
    Calculate statistics about the events.
    """
    if not events:
        return {
            "total_events": 0,
            "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
            "avg_tone": 0,
            "most_mentioned_event": None
        }
    
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for event in events:
        sentiment_counts[event["sentiment"]] += 1
    
    most_mentioned = max(events, key=lambda x: x["mention_count"], default=None)
    
    return {
        "total_events": len(events),
        "sentiment_counts": sentiment_counts,
        "avg_tone": sum(event["tone"] for event in events) / len(events),
        "most_mentioned_event": most_mentioned["event_id"] if most_mentioned else None
    }