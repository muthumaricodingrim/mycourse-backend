import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes required for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    """
    Runs the OAuth2 flow and prints a refresh token.
    Make sure you have 'credentials.json' in the same directory.
    """
    credentials_path = '../credentials.json'
    if not os.path.exists(credentials_path):
        # Try local directory if not found in parent (depending on where it's run)
        credentials_path = 'credentials.json'
    
    if not os.path.exists(credentials_path):
        print("Error: credentials.json not found. Please ensure it is in the backend directory.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    
    # Using a fixed port to make it easier to add to Google Console
    # IMPORTANT: You must add 'http://localhost:8080/' to your Authorized redirect URIs
    # in the Google Cloud Console for this to work with a "Web" client type.
    try:
        creds = flow.run_local_server(port=8080, prompt='consent')
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPossible solutions:")
        print("1. Ensure 'http://localhost:8080/' is added to 'Authorized redirect URIs' in Google Cloud Console.")
        print("2. Ensure you downloaded the LATEST 'credentials.json' after adding the redirect URI.")
        print("3. Check if your app is in 'Testing' mode in the OAuth Consent Screen and add your email as a test user.")
        return

    print("\n--- GMAIL API REFRESH TOKEN ---")
    print(creds.refresh_token)
    print("-------------------------------\n")
    print("Copy the token above and paste it into your .env file as GMAIL_REFRESH_TOKEN.")

if __name__ == '__main__':
    main()
