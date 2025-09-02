
ENV_LOCAL = "LOCAL"
ENV_PROD = "PROD"

LOG_DEBUG = "DEBUG" # Information useful during development
LOG_WARNING = "WARNING" # Warnings about something unexpected but not necessarily problematic
LOG_AUDITS = "AUDITS" # Information useful during development
LOG_TRACE ="TRACE" # Extremely detailed information for debugging
LOG_INFO ="INFO" # General information about what’s happening in the code
LOG_SUCCESS ="SUCCESS" # Notifications of successful operations
LOG_ERROR ="ERROR" # Errors for when something fails but the application continues running
LOG_CRITICAL ="CRITICAL" # Critical errors that are serious and urgent


RESPONSE_STATUS_KWD = "status"
RESPONSE_MSG_KWD = "msg"
RESPONSE_CODE_KWD = "code"
DEFAULT_API_RESPONSE_OBJ = {
    RESPONSE_CODE_KWD: 202,
    RESPONSE_STATUS_KWD: False,
    RESPONSE_MSG_KWD: "API request accepted.",
}
BAD_REQUEST_ERROR_MSG = "Bad request. The request is invalid or cannot be fulfilled."
INPUT_NOT_ACCEPTABLE_RESPONSE = (
    "Inputs given are not acceptable due to which we are not able to create"
)

# Column max length in db
DB_COLUMN_MAX_LENGTH = 255

# jwt
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hour