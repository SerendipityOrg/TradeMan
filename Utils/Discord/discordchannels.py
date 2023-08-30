import requests
import os
import json

def discord_bot(message, strategy):
    channel_id = ""
    token = ""

    env_file_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Brokers', 'config.env'))
    
    with open(env_file_path, "r") as env_file:
        for line in env_file:
            if strategy in line:
                channel_id = line.split("=")[1].strip()
            elif "discord_bot_token" in line:
                token = line.split("=")[1].strip()

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




    
    
    

