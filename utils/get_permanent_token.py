import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

APP_ID = os.getenv("FB_APP_ID", "2124930351775126")
APP_SECRET = os.getenv("FB_APP_SECRET", "8270797f314191338f50e459b633a307")
SHORT_LIVED_TOKEN = os.getenv("FB_SHORT_LIVED_TOKEN", "")
PAGE_ID = os.getenv("FB_PAGE_ID", "1174287672443215")


def upgrade_to_permanent_token(short_lived_token=None, app_id=None, app_secret=None, page_id=None):
    token = short_lived_token or SHORT_LIVED_TOKEN
    app = app_id or APP_ID
    secret = app_secret or APP_SECRET
    page = page_id or PAGE_ID

    if not token:
        print("[!] No short-lived token provided or found in environment.")
        return None

    print("🔄 Step 1: Trading 1-hour token for 60-day token...")
    exchange_url = "https://graph.facebook.com/v25.0/oauth/access_token"
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": app,
        "client_secret": secret,
        "fb_exchange_token": token,
    }
    
    response_1 = requests.get(exchange_url, params=exchange_params).json()
    
    if "access_token" not in response_1:
        print("[!] Failed to get 60-day token:", response_1)
        return None
        
    long_lived_user_token = response_1["access_token"]
    
    print("✅ Step 2: Trading 60-day user token for INFINITE Page token...")
    page_url = f"https://graph.facebook.com/v25.0/{page}"
    page_params = {
        "fields": "access_token",
        "access_token": long_lived_user_token,
    }
    
    response_2 = requests.get(page_url, params=page_params).json()
    
    if "access_token" in response_2:
        permanent_token = response_2["access_token"]
        print("\n🎉 SUCCESS! Your Permanent Page Token is:\n")
        print(permanent_token)
        print("\nPaste this into your .env file as IG_ACCESS_TOKEN. You will never need to refresh it.")
        return permanent_token
    else:
        print("[!] Failed to get permanent token:", response_2)
        return None


if __name__ == "__main__":
    upgrade_to_permanent_token()
