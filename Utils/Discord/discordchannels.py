import requests
import os
import json
from dotenv import load_dotenv

def discord_bot(message, strategy):
    env_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Brokers', '.env'))
    load_dotenv(env_file_path)

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
