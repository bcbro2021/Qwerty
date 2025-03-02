from pypresence import Presence
from dotenv import load_dotenv
import time, os

load_dotenv()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")

if not CLIENT_ID:
    raise ValueError("Discord Client ID is missing. Please set it in the .env file.")
rpc = Presence(CLIENT_ID)
rpc.connect()

def update():
    rpc.update(
        state=f"Coding Away in Qwerty",
        details=f"F off",
        start=time.time(),  # Start time for session
        large_image="logo",  # Must be uploaded in Discord Developer Portal
        large_text="Qwerty"
    )

def close():
    rpc.clear()
    rpc.close()