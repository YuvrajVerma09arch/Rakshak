class ProviderNotConfigured(Exception):
    """Raised when an API key is missing — agents catch this and fall back to
    their deterministic local behavior, so the demo never dies on stage."""
