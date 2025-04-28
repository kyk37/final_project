# Secret key (Change for Production)
SECRET_KEY = "supersecretkey"
# Algorithm type
ALGORITHM = "HS256"
# Token expirtation time (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 120
# Issuer
ISSUER = "https://event_manager.com" # APP URL or Name

ALLOWED_AUDIENCES = ["web_client", "mobile_client", "api_service"]