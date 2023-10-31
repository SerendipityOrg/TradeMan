import requests
import os,sys
from dotenv import load_dotenv

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

def discord_bot(message, strategy):
    token = os.getenv('discord_bot_token')
    channel_id = os.getenv(f"{strategy.lower()}_channel_id")

    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }
    data = {
        "content": message
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise ValueError(f"Request to discord returned an error {response.status_code}, the response is:\n{response.text}")
    return response
