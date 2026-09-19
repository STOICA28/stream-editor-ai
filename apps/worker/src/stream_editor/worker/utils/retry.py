import pydantic

def is_retryable(exc: Exception) -> bool:
    """
    Centralized error taxonomy for Celery tasks.
    Returns True if the exception represents a transient failure (network, DB lock, timeout).
    Returns False if it is a permanent failure (ValidationError, unsupported media).
    """
    exc_type = type(exc).__name__
    
    # Non-retryable
    if isinstance(exc, pydantic.ValidationError):
        return False
    if exc_type in ["AIInvalidStructuredOutput", "ValueError", "TypeError", "FileNotFoundError", "NotImplementedError"]:
        return False
    
    # Retryable
    if exc_type in ["AIProviderTimeout", "AIProviderExecutionError", "AIProviderUnavailable", "OperationalError"]:
        return True
        
    return True
