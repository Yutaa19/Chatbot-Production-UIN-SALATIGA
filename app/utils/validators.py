"""
Validation utilities for the chatbot application.
"""

def validate_query(query: str) -> bool:
    """
    Validate user query.
    
    Args:
        query (str): The user's query string
        
    Returns:
        bool: True if query is valid, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    # Check minimum length (3 characters as mentioned in error message)
    if len(query.strip()) < 3:
        return False
    
    # Check for empty or whitespace-only queries
    if not query.strip():
        return False
    
    return True

