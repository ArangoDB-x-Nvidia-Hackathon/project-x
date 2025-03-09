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
            "most_frequent_label": None,
            "total_fatalities": 0
        }
    
    # Sentiment distribution
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for event in events:
        sentiment = event.get("sentiment", "neutral")
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    # Most frequent label
    label_counts = {}
    for event in events:
        label = event.get("label", "Unknown")
        label_counts[label] = label_counts.get(label, 0) + 1
    most_frequent_label = max(label_counts, key=label_counts.get, default=None)
    
    # Total fatalities
    total_fatalities = sum(event.get("fatalities", 0) for event in events)
    
    # Average tone
    avg_tone = sum(event.get("tone", 0) for event in events) / len(events)
    
    return {
        "total_events": len(events),
        "sentiment_counts": sentiment_counts,
        "avg_tone": avg_tone,
        "most_frequent_label": most_frequent_label,
        "total_fatalities": total_fatalities
    }