def analyze_event_sentiment(events):
    """
    Analyze the sentiment of events based on outcome field
    Returns overall sentiment and counts
    """
    sentiment_map = {
        "positive": 0,
        "negative": 0,
        "mixed": 0,
    }
    
    for event in events:
        outcome = event.get("outcome", "").lower()
        
        if "positive" in outcome:
            sentiment_map["positive"] += 1
            event["sentiment"] = "positive"
        elif "negative" in outcome:
            sentiment_map["negative"] += 1
            event["sentiment"] = "negative"
        elif "mixed" in outcome:
            sentiment_map["mixed"] += 1
            event["sentiment"] = "mixed"
    
    # Determine overall sentiment
    total_events = len(events)
    if total_events == 0:
        overall_sentiment = "mixed"
    else:
        max_sentiment = max(sentiment_map.items(), key=lambda x: x[1])
        overall_sentiment = max_sentiment[0]
    
    return {
        "overall_sentiment": overall_sentiment,
        "counts": sentiment_map,
        "total": total_events,
        "events": events
    }

def get_sentiment_color(sentiment):
    """Return color for sentiment visualization"""
    colors = {
        "positive": "green",
        "negative": "red",
        "mixed": "orange",
    }
    return colors.get(sentiment, "gray")

def get_icon_for_event_type(event_type):
    """Return appropriate icon for event type"""
    event_type = event_type.lower() if event_type else ""
    
    if "terror" in event_type or "attack" in event_type:
        return "warning"
    elif "disaster" in event_type or "earthquake" in event_type or "flood" in event_type:
        return "info"
    elif "political" in event_type or "election" in event_type:
        return "flag"
    elif "economic" in event_type or "financial" in event_type:
        return "money"
    else:
        return "circle"