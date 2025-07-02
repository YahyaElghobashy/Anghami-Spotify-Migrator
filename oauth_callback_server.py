#!/usr/bin/env python3
"""
OAuth Callback Server for Spotify Authentication
Runs on port 8888 to handle OAuth redirects from Spotify
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession
import logging
from urllib.parse import urlencode
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MAIN_API_URL = "http://localhost:8000"
CALLBACK_PORT = 8888

async def handle_oauth_callback(request):
    """Handle OAuth callback from Spotify"""
    try:
        # Extract query parameters
        code = request.query.get('code')
        state = request.query.get('state')
        error = request.query.get('error')
        
        logger.info(f"OAuth callback received - Code: {'✓' if code else '✗'}, State: {'✓' if state else '✗'}, Error: {error or 'None'}")
        
        if error:
            return web.Response(
                text=f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #dc2626;">❌ Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>Please close this window and try again.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """,
                content_type='text/html'
            )
        
        if not code or not state:
            return web.Response(
                text="""
                <html>
                <head><title>Invalid Request</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #dc2626;">❌ Invalid Request</h1>
                    <p>Missing authorization code or state parameter.</p>
                    <p>Please close this window and try again.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """,
                content_type='text/html'
            )
        
        # Forward the callback to the main API server
        async with ClientSession() as session:
            callback_data = {
                "code": code,
                "state": state,
                "redirect_uri": "http://127.0.0.1:8888/callback"
            }
            
            logger.info(f"Forwarding OAuth data to main API: {MAIN_API_URL}/spotify/oauth/callback")
            
            async with session.post(
                f"{MAIN_API_URL}/spotify/oauth/callback",
                json=callback_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success") and result.get("verified"):
                        profile = result.get("spotify_profile", {})
                        display_name = profile.get("display_name", "User")
                        
                        logger.info(f"OAuth verification successful for user: {display_name}")
                        
                        return web.Response(
                            text=f"""
                            <html>
                            <head><title>Authorization Successful</title></head>
                            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                                <div style="max-width: 500px; margin: 0 auto;">
                                    <h1 style="color: #059669;">✅ Authorization Successful!</h1>
                                    <p><strong>Welcome, {display_name}!</strong></p>
                                    <p>Your Spotify account has been verified and connected successfully.</p>
                                    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #a7f3d0;">
                                        <h3 style="color: #059669; margin-top: 0;">🎵 Verification Complete</h3>
                                        <p style="margin: 5px 0;">✓ Real-time Spotify connection established</p>
                                        <p style="margin: 5px 0;">✓ Profile data synchronized</p>
                                        <p style="margin: 5px 0;">✓ Ready for playlist migration</p>
                                    </div>
                                    <p style="color: #6b7280; font-size: 14px;">You can now close this window and return to the application.</p>
                                    <div style="margin-top: 30px; padding: 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                                        <p style="margin: 0; font-size: 12px; color: #64748b;">
                                            🔒 Your Spotify account is now securely connected with real-time access.
                                        </p>
                                    </div>
                                </div>
                                <script>
                                    // Auto-close after 8 seconds with countdown
                                    let countdown = 8;
                                    const countdownElement = document.createElement('p');
                                    countdownElement.style.marginTop = '20px';
                                    countdownElement.style.fontSize = '14px';
                                    countdownElement.style.color = '#6b7280';
                                    document.body.appendChild(countdownElement);
                                    
                                    const timer = setInterval(() => {{
                                        countdownElement.textContent = `This window will close automatically in ${{countdown}} seconds...`;
                                        countdown--;
                                        if (countdown < 0) {{
                                            clearInterval(timer);
                                            window.close();
                                        }}
                                    }}, 1000);
                                    
                                    // Manual close button
                                    const closeButton = document.createElement('button');
                                    closeButton.textContent = 'Close Window';
                                    closeButton.style.padding = '10px 20px';
                                    closeButton.style.margin = '20px';
                                    closeButton.style.background = '#059669';
                                    closeButton.style.color = 'white';
                                    closeButton.style.border = 'none';
                                    closeButton.style.borderRadius = '6px';
                                    closeButton.style.cursor = 'pointer';
                                    closeButton.onclick = () => window.close();
                                    document.body.appendChild(closeButton);
                                </script>
                            </body>
                            </html>
                            """,
                            content_type='text/html'
                        )
                    else:
                        error_msg = result.get("error", "Unknown error occurred")
                        logger.error(f"OAuth verification failed: {error_msg}")
                        
                        return web.Response(
                            text=f"""
                            <html>
                            <head><title>Authorization Failed</title></head>
                            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                                <h1 style="color: #dc2626;">❌ Authorization Failed</h1>
                                <p>Error: {error_msg}</p>
                                <p>Please close this window and try again.</p>
                                <script>setTimeout(() => window.close(), 5000);</script>
                            </body>
                            </html>
                            """,
                            content_type='text/html'
                        )
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    
                    return web.Response(
                        text=f"""
                        <html>
                        <head><title>Authorization Error</title></head>
                        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                            <h1 style="color: #dc2626;">❌ Authorization Error</h1>
                            <p>Failed to communicate with the main application.</p>
                            <p>Status: {response.status}</p>
                            <p>Please close this window and try again.</p>
                            <script>setTimeout(() => window.close(), 5000);</script>
                        </body>
                        </html>
                        """,
                        content_type='text/html'
                    )
                    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return web.Response(
            text=f"""
            <html>
            <head><title>Authorization Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #dc2626;">❌ Authorization Error</h1>
                <p>An unexpected error occurred: {str(e)}</p>
                <p>Please close this window and try again.</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
            </html>
            """,
            content_type='text/html'
        )

async def handle_health(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "OAuth Callback Server",
        "port": CALLBACK_PORT,
        "main_api": MAIN_API_URL
    })

async def handle_root(request):
    """Root endpoint with server info"""
    return web.Response(
        text="""
        <html>
        <head><title>OAuth Callback Server</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🎵 Spotify OAuth Callback Server</h1>
            <p>This server handles OAuth redirects from Spotify.</p>
            <p>Port: 8888</p>
            <p>Status: Running</p>
            <div style="margin-top: 30px; padding: 20px; background: #f0fdf4; border-radius: 8px; max-width: 400px; margin: 30px auto;">
                <h3 style="color: #059669; margin-top: 0;">Endpoints:</h3>
                <p style="margin: 5px 0;"><code>/callback</code> - OAuth callback handler</p>
                <p style="margin: 5px 0;"><code>/health</code> - Health check</p>
            </div>
        </body>
        </html>
        """,
        content_type='text/html'
    )

async def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/callback', handle_oauth_callback)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/', handle_root)
    
    return app

async def main():
    """Main function to run the server"""
    app = await create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '127.0.0.1', CALLBACK_PORT)
    await site.start()
    
    logger.info(f"🎵 OAuth Callback Server started on http://127.0.0.1:{CALLBACK_PORT}")
    logger.info(f"📡 Forwarding callbacks to: {MAIN_API_URL}")
    logger.info("✅ Ready to handle Spotify OAuth redirects!")
    
    try:
        # Keep the server running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("🛑 Server shutting down...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 OAuth Callback Server stopped") 