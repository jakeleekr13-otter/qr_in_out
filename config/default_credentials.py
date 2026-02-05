"""
Default Administrator Credentials Configuration

⚠️ SECURITY WARNING:
These credentials are ONLY used for first-time setup.
Users will be FORCED to change them on first login.

To change default credentials:
1. Edit DEFAULT_USERNAME and DEFAULT_PASSWORD below
2. Restart the application
3. Delete data/admin_credentials.json if it exists (to reset)
"""

# Default credentials for first-time setup
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

# Security questions for account recovery
SECURITY_QUESTIONS = [
    "What was your first pet's name?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was your first car?",
    "What is your favorite teacher's name?",
    "What street did you grow up on?",
]

# Login security settings
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 5
