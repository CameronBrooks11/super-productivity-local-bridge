"""Bridge error codes."""

# The SP instance is not reachable (connection refused, DNS failure, etc.)
SP_UNAVAILABLE = "SP_UNAVAILABLE"

# Request to SP timed out
TIMEOUT = "TIMEOUT"

# Operation name is not recognized
UNKNOWN_OPERATION = "UNKNOWN_OPERATION"

# Operation is recognized but not supported in the current configuration
UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"

# Payload validation failed
INVALID_INPUT = "INVALID_INPUT"

# Requested resource does not exist
TASK_NOT_FOUND = "TASK_NOT_FOUND"
PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"

# SP returned an error response
SP_ERROR = "SP_ERROR"

# Unexpected internal failure
INTERNAL_ERROR = "INTERNAL_ERROR"
