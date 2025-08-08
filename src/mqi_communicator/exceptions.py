class MQIError(Exception):
    """Base exception for all application-specific errors."""
    pass

class ConfigurationError(MQIError):
    """Raised for configuration-related errors."""
    pass

class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass

class TransferError(MQIError):
    """Raised for file transfer related errors."""
    pass

class ExecutorError(MQIError):
    """Raised for errors during command execution."""
    pass
