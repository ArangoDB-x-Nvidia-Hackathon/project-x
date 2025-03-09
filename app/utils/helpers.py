# Place for any helper functions that don't fit in other service modules
# This file can be expanded as needed

def sanitize_query(query: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    """
    # Remove any potentially dangerous characters
    sanitized = query.replace(";", "").replace("'", "").replace('"', "")
    return sanitized