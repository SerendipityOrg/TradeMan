from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.events import NewMessage
import re
from siricalc import *
from siriplaceorders import *


# Your API ID, API HASH, and phone number
api_id = '22941664'
api_hash = '2ee02d39b9a6dae9434689d46e0863ca'
phone = '+918618221715'

# Keywords to search for
keywords = ['nifty', 'finnifty', 'banknifty']  # Add your keywords here

# Group URL or ID
group_url = 'https://t.me/+q5YqbjHMpds0MjU1'  # Replace with your group URL or ID

script_dir = os.path.dirname(os.path.abspath(__file__))   
parent_dir = os.path.abspath(os.path.join(script_dir, '..'))
broker_filepath = os.path.join(parent_dir, 'Utils', 'broker.json')

# Connect to Telegram
with TelegramClient(phone, api_id, api_hash) as client:
    # Ensure you're authorized
    if not client.is_user_authorized():
        client.send_code_request(phone)
        client.sign_in(phone, input('Enter the code: '))

    # Get the group entity
    group = client.get_entity(group_url)

    @client.on(NewMessage(chats=group))
    async def handler(event):
        message_content = event.message.message
        if message_content:
            message_content_lower = message_content.lower()
            for keyword in keywords:
                # Use regex to match the keyword as a whole word
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', message_content_lower):

                    # Extract Base_symbol, strike_prc, and option_type
                    match = re.search(r'(\d{5})\s+(ce|pe)\s+(\w+)', message_content_lower)
                    if match:
                        strike_prc = match.group(1)
                        option_type = match.group(2).upper()
                        base_symbol = match.group(3).upper()

                        print(f"Base_symbol: {base_symbol}")
                        print(f"strike_prc: {strike_prc}")
                        print(f"option_type: {option_type}")

                    entry_match = re.search(r'entry\s+(\d+)', message_content_lower)
                    if entry_match:
                        entry = entry_match.group(1)
                        print(f"entry: {entry}")

                    # Extract stoploss value
                    sl_match = re.search(r'sl\s+(\d+)', message_content_lower)
                    if sl_match:
                        stoploss = sl_match.group(1)
                        print(f"stoploss: {stoploss}")

                    # Extract target value (assuming you want the first target)
                    target_matches = re.findall(r'target(?:\s+\d)?\s+(\d+)', message_content_lower)
                    if target_matches:
                        print(f"target: {target_matches[0]}")
                        for i, t in enumerate(target_matches[1:], 2):
                            print(f"target_{i}: {t}")
                    
                    break 

        users_to_trade = get_siri_users(broker_filepath)
        print(users_to_trade)

        expiry = get_expiry_dates()
        if base_symbol == 'NIFTY' or 'BANKNIFTY':
            expiry_date = expiry[0]
        elif base_symbol == 'FINNIFTY':
            expiry_date = expiry[1]

        tokens, trading_symbol_list, trading_symbol_aliceblue = get_option_tokens(base_symbol, expiry_date, option_type, strike_prc)

        for broker,user in users_to_trade:
            if 'zerodha' in broker:
                avg_prc = place_zerodha_order(trading_symbol_list,'BUY', 'BUY', strike_prc, base_symbol, user)
                diff = float(avg_prc) - float(entry)
                limit_prc = float(stoploss) + diff
                stoploss_order = place_stoploss_zerodha(trading_symbol_list, 'SELL', 'SELL', strike_prc, base_symbol, limit_prc, user, broker='zerodha')    
            elif 'aliceblue' in broker:
                avg_prc = place_aliceblue_order(trading_symbol_aliceblue[0],'BUY', 'BUY', strike_prc, base_symbol, user)
                diff = float(avg_prc) - float(entry)
                limit_prc = float(stoploss) + diff
                stoploss_order = place_stoploss_aliceblue(trading_symbol_aliceblue[0], "SELL", "SELL", strike_prc, base_symbol, limit_prc, user, broker='aliceblue')
    
    print("Listening for new messages...")
    client.run_until_disconnected()

