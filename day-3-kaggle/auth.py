def login():
    pass

def login_with_google(token):
    """
    Authenticate the user using a Google OAuth2 ID token.
    """
    if not token:
        raise ValueError("Google token is required.")
    
    # In a real app, verify the token using google.oauth2.id_token
    # and fetch the user info from Google's API.
    user_info = {
        "email": "google_user@example.com",
        "name": "Google User",
        "google_id": "google-oauth2|123456789"
    }
    return user_info
