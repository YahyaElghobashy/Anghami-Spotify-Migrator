#!/usr/bin/env python3
"""
Spotify OAuth2 Authentication

Handles Spotify Web API authentication using Authorization Code Flow.
"""

import os
import json
import time
import webbrowser
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests
from dotenv import load_dotenv


class SpotifyAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for capturing OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from Spotify OAuth callback"""
        if self.path.startswith('/callback'):
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            
            if 'code' in query_params:
                self.server.auth_code = query_params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html_content = """
                <html>
                    <body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the migration tool.</p>
                        <script>setTimeout(function() { window.close(); }, 3000);</script>
                    </body>
                </html>
                """
                self.wfile.write(html_content.encode('utf-8'))
            elif 'error' in query_params:
                self.server.auth_error = query_params['error'][0]
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = f"<h1>Error: {query_params['error'][0]}</h1>"
                self.wfile.write(error_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logging"""
        pass


class SpotifyAuth:
    """Spotify OAuth2 Authentication Manager"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scopes: list):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def authenticate(self) -> bool:
        """Perform OAuth2 authentication flow"""
        print("🔐 Starting Spotify authentication...")
        
        # Generate authorization URL
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'show_dialog': 'true'
        }
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        
        # Start callback server
        parsed_uri = urllib.parse.urlparse(self.redirect_uri)
        port = parsed_uri.port or 8888
        
        server = HTTPServer(('localhost', port), SpotifyAuthHandler)
        server.auth_code = None
        server.auth_error = None
        
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()
        
        # Open browser
        print("📱 Opening browser for authorization...")
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("⏳ Waiting for authorization...")
        start_time = time.time()
        timeout = 300
        
        while time.time() - start_time < timeout:
            if server.auth_code:
                print("✅ Authorization code received")
                return self._exchange_code_for_tokens(server.auth_code)
            elif server.auth_error:
                print(f"❌ Authorization error: {server.auth_error}")
                return False
            time.sleep(0.5)
        
        print("❌ Authorization timeout")
        return False
    
    def _exchange_code_for_tokens(self, auth_code: str) -> bool:
        """Exchange authorization code for tokens"""
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print("✅ Successfully obtained access tokens")
            return True
            
        except Exception as e:
            print(f"❌ Failed to exchange tokens: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if not self.access_token:
            raise Exception("Not authenticated")
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make authenticated request with retry logic"""
        headers = kwargs.get('headers', {})
        headers.update(self.get_auth_headers())
        kwargs['headers'] = headers
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    print(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"⚠️ Request attempt {attempt + 1} failed")
                time.sleep(2 ** attempt)
        
        raise Exception(f"Request failed after {max_retries} attempts")


def create_spotify_auth() -> SpotifyAuth:
    """Create configured SpotifyAuth instance"""
    load_dotenv()
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
    
    if not client_id or not client_secret:
        raise Exception("Missing Spotify credentials in environment variables")
    
    scopes = [
        "playlist-read-private",
        "playlist-modify-private", 
        "playlist-modify-public",
        "ugc-image-upload"
    ]
    
    return SpotifyAuth(client_id, client_secret, redirect_uri, scopes)


if __name__ == "__main__":
    """Test the Spotify authentication system"""
    try:
        # Create auth instance
        auth = create_spotify_auth()
        
        # Authenticate
        if auth.authenticate():
            print("🎉 Authentication successful!")
            
            # Test the authentication
            try:
                response = auth.make_authenticated_request('GET', 'https://api.spotify.com/v1/me')
                user_data = response.json()
                print(f"✅ Authentication test successful - logged in as: {user_data.get('display_name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Authentication test failed: {e}")
        else:
            print("❌ Authentication failed")
            
    except Exception as e:
        print(f"💥 Error: {e}") 