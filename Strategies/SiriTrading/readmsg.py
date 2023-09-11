import os,sys
import re
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.events import NewMessage

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')

# Import necessary modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Utils'))
import general_calc as gc

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Brokers'))

import place_order
from instrument_monitor import InstrumentMonitor

def load_telethon_credentials():
    """
    Load and return Telethon credentials from .env file.
    
    Returns:
        dict: Dictionary containing Telethon credentials.
    """
    dotenv_path = os.path.join(BROKERS_DIR, '.env')
    load_dotenv(dotenv_path)
    
    return {
        'api_id': os.getenv('telethon_api_id'),
        'api_hash': os.getenv('telethon_api_hash'),
        'phone': os.getenv('officephone'),
        'group_url': os.getenv('siri_group_link'),
        'keywords': os.getenv('indices'),
        'risk': os.getenv('siri_risk')
    }

def extract_values_from_message(message_content, keywords):
    """
    Extract required values from the message content.

    Args:
        message_content (str): Content of the message.
        keywords (str): Keywords to search for in the message.

    Returns:
        dict: Dictionary containing extracted order details or None if not found.
    """
    message_content_lower = message_content.lower()

    # Check for keywords
    if not any(keyword.lower() in message_content_lower for keyword in keywords):
        return None

    order_details = {}
    # Extract values using regular expressions
    main_match = re.search(r'(\d{5})\s+(ce|pe)\s+(\w+)', message_content_lower)
    if not main_match:
        return None  # Return None if the regex pattern doesn't match

    order_details.update({
        "transcation":"BUY",
        'strike_prc': int(main_match.group(1)),
        'option_type': main_match.group(2).upper(),
        'base_symbol': main_match.group(3).upper(),
    })

    entry_match = re.search(r'entry\s+(@\s+)?(\d+)(-\d+)?', message_content_lower)
    if entry_match:
        order_details['entry'] = entry_match.group(2)

    sl_match = re.search(r'sl\s+(\d+)', message_content_lower)
    if sl_match:
        order_details['stoploss'] = sl_match.group(1)

    target_matches = re.findall(r'target(?:\s+\d)?\s+(\d+)', message_content_lower)
    if target_matches:
        order_details['target'] = target_matches[0]

    if 'entry' in order_details and 'stoploss' in order_details:
        order_details['stoploss_points'] = float(order_details['entry']) - float(order_details['stoploss'])
        raw_qty = int(float(telethon_crendentials['risk']) / order_details['stoploss_points'])
        order_details['qty'] = gc.round_qty(raw_qty, order_details['base_symbol'])

    return order_details


if __name__ == "__main__":
    telethon_crendentials = load_telethon_credentials()
    monitor = InstrumentMonitor()

    with TelegramClient(telethon_crendentials['phone'], telethon_crendentials['api_id'], telethon_crendentials['api_hash']) as client:
        if not client.is_user_authorized():
            client.send_code_request(telethon_crendentials['phone'])
            client.sign_in(telethon_crendentials['phone'], input('Enter the code: '))

        group = client.get_entity(telethon_crendentials['group_url'])

        @client.on(NewMessage(chats=group))
        async def handler(event):
            """
            Handle new messages for specific group and execute actions based on the content.
            """
            message_content = event.message.message
            if message_content:
                keywords = telethon_crendentials.get('keywords')
                order_details = extract_values_from_message(message_content, keywords)
                if order_details:
                    place_order.place_order_for_broker("Siri", order_details, qty=order_details.get('qty'), monitor=monitor)

        print("Listening for new messages...")
        client.run_until_disconnected()
