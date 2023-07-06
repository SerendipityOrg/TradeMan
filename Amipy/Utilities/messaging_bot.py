import requests

token='5994380365:AAFv0GSI78IxP6nI7g_xJPoqY3zWSfDHndQ'
chat_id='683309417'

def telegram_bot_sendtext_AK(bot_message): 
    print(bot_message) 
    bot_token = '5994380365:AAFv0GSI78IxP6nI7g_xJPoqY3zWSfDHndQ'
    bot_chatID_AK = '-367108102'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID_AK + '&parse_mode=Markdown&text=' + bot_message
    print(send_text)
    response = requests.get(send_text)
    print(response.json())
    return response.json()

def telegram_bot_omkar(bot_message):  
    bot_token = '1181910093:AAEZxu2JjdI93zn9cBUGbZQa9DJs6xt7HeQ'
    bot_chatID_KH = '-1001483256385'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID_KH + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def telegram_bot_vimala(bot_message):    
    bot_token = '1181910093:AAEZxu2JjdI93zn9cBUGbZQa9DJs6xt7HeQ'
    bot_chatID_BY = '-1001494618225'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID_BY + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def discord_bot(message):
    CHANNEL_ID = "1125674485744402505"
    TOKEN = "MTEyNTY3MTgxODQxMDM0ODU2Ng.GQ5DLZ.BVLPrGy0AEX9ZiZOJsB6cSxOlf8hC2vaANuilA"
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "content": message
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        raise ValueError(f"Request to discord returned an error {response.status_code}, the response is:\n{response.text}")
    return response



