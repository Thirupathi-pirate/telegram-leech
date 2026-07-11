# oauth_server.py — Per-user Google Drive OAuth system
# Extracted from telegram-drive-bot, adapted for mirrorbot137
import os
import json
import logging
import threading
import asyncio
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from aiohttp import web

USER_CREDS_DIR = "user_creds"
SCOPES = ["https://www.googleapis.com/auth/drive"]

LOGGER = logging.getLogger(__name__)


def _build_oauth_client_config():
    return {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.environ.get("OAUTH_REDIRECT_URI", "")],
        }
    }


def get_user_creds_path(user_id: int) -> str:
    return os.path.join(USER_CREDS_DIR, f"{user_id}.json")


def user_has_credentials(user_id: int) -> bool:
    return os.path.exists(get_user_creds_path(user_id))


def get_user_service(user_id: int):
    """Load credentials for a user, refresh if expired, build and return Drive service."""
    creds_path = get_user_creds_path(user_id)
    if not os.path.exists(creds_path):
        raise RuntimeError(
            "Google account not connected. Use /connect first."
        )
    creds = Credentials.from_authorized_user_file(creds_path, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def handle_oauth_callback(request):
    """aiohttp handler for the OAuth redirect URI."""
    code = request.query.get("code")
    state = request.query.get("state")
    if not code or not state:
        return web.Response(text="Missing code or state parameter.", status=400)
    try:
        user_id = int(state)
    except ValueError:
        return web.Response(text="Invalid state parameter.", status=400)
    try:
        flow = Flow.from_client_config(
            _build_oauth_client_config(),
            scopes=SCOPES,
            redirect_uri=os.environ.get("OAUTH_REDIRECT_URI", ""),
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        os.makedirs(USER_CREDS_DIR, exist_ok=True)
        creds_path = get_user_creds_path(user_id)
        with open(creds_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        bot = request.app.get("telegram_bot")
        if bot:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: bot.send_message(
                    chat_id=user_id,
                    text="\u2705 Google account connected successfully!\n\n"
                    "You can now use /mirror to upload to your Drive.",
                ))
            except Exception as e:
                LOGGER.warning(f"Failed to notify user {user_id}: {e}")

        return web.Response(
            text="<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                 "<h2>\u2705 Google account connected!</h2>"
                 "<p>You can close this tab and return to Telegram.</p></body></html>",
            content_type="text/html",
        )
    except Exception as e:
        LOGGER.error(f"OAuth callback failed for user {user_id}: {e}")
        return web.Response(text=f"Authorization failed: {e}", status=500)


def start_oauth_server(bot_instance=None):
    """Start the aiohttp OAuth callback server in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = web.Application()
    app.router.add_get("/oauth/callback", handle_oauth_callback)
    if bot_instance:
        app["telegram_bot"] = bot_instance
    port = int(os.environ.get("OAUTH_SERVER_PORT", "8080"))
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", port)
    loop.run_until_complete(site.start())
    LOGGER.info(f"OAuth server started on port {port}")
    loop.run_forever()


# ---- python-telegram-bot v13 command handlers ----
def connect_command(update, context):
    """Handle /connect — generate OAuth URL and send to user."""
    user = update.effective_user
    if not user:
        return
    flow = Flow.from_client_config(
        _build_oauth_client_config(),
        scopes=SCOPES,
        redirect_uri=os.environ.get("OAUTH_REDIRECT_URI", ""),
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=str(user.id),
    )
    update.message.reply_text(
        "Click the link below to connect your Google Drive:\n\n"
        f"{auth_url}\n\n"
        "After authorizing, you'll receive a confirmation message here.",
        disable_web_page_preview=True,
    )


def disconnect_command(update, context):
    """Handle /disconnect — remove saved OAuth credentials."""
    user = update.effective_user
    if not user:
        return
    creds_path = get_user_creds_path(user.id)
    if os.path.exists(creds_path):
        os.remove(creds_path)
        update.message.reply_text(
            "\u2705 Google account disconnected successfully."
        )
    else:
        update.message.reply_text(
            "\u26a0\ufe0f No Google account is connected."
        )
