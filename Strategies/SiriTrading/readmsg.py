import os
import re
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.events import NewMessage
import sys

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')
UTILS_DIR = os.path.join(CURRENT_DIR, '..','..','Utils')

sys.path.append(UTILS_DIR)
import general_calc

sys.path.append(BROKERS_DIR)
import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha

from instrument_monitor import monitor_instruments
import threading


def load_telethon_credentials():
    """Load and return Telethon credentials from .env file."""
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
    
def extract_values_from_message(message_content):
    """Extract required values from the message content and pass to place_orders."""
    order_details = {}
    message_content_lower = message_content.lower()
    
    #     # List of required keywords
    # required_keywords = ['entry','ce', 'pe']  # Add other required keywords as needed

    # # Check if all required keywords are present in the message
    # if not all(keyword in message_content_lower for keyword in required_keywords):
    #     return
    
    for keyword in telethon_crendentials['keywords']:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', message_content_lower):
            match = re.search(r'(\d{5})\s+(ce|pe)\s+(\w+)', message_content_lower)
            if match:
                order_details['Base_symbol'] = match.group(3).upper()
                order_details['strike_prc'] = match.group(1)
                order_details['option_type'] = match.group(2).upper()

            entry_match = re.search(r'entry\s*@\s*(\d+\s*-\s*\d+)', message_content_lower)  # Updated regex
            if entry_match:
                entry_value = entry_match.group(1)
                if "-" in entry_value:
                    # If entry is a range, compute the average
                    start, end = map(float, entry_value.split("-"))
                    order_details['entry'] = str((start + end) / 2)
                else:
                    order_details['entry'] = entry_value

            sl_match = re.search(r'sl\s+(\d+)', message_content_lower)
            if sl_match:
                order_details['stoploss'] = sl_match.group(1)

            target_matches = re.findall(r'target(?:\s+\d)?\s+(\d+)', message_content_lower)
            if target_matches:
                order_details['target'] = target_matches[0]
                for i, t in enumerate(target_matches[1:], 2):
                    order_details[f'target_{i}'] = t
            
            stoploss_points = float(order_details['entry']) - float(order_details['stoploss'])
            qty = int(float(telethon_crendentials['risk']) / (float(order_details['entry']) - float(order_details['stoploss'])))
            
            break
    return order_details
 
def place_order_for_broker(broker, user, order_details, qty):
    weeklyexpiry, _ = general_calc.get_expiry_dates(order_details['Base_symbol'])
    
    # Fetch tokens and trading symbols
    token, trading_symbol_list, trading_symbol_aliceblue = general_calc.get_tokens(
        order_details['Base_symbol'], 
        weeklyexpiry, 
        order_details['option_type'], 
        order_details['strike_prc']
    )
    
    if broker == 'zerodha':
        trading_symbol = trading_symbol_list
        place_order_func = zerodha.place_zerodha_order
    elif broker == 'aliceblue':
        trading_symbol = trading_symbol_aliceblue[0]
        place_order_func = aliceblue.place_aliceblue_order
    else:
        print(f"Unknown broker: {broker}")
        return

    avg_prc = place_order_func('SiriTrading', {
        'transaction_type': 'BUY',
        'tradingsymbol': trading_symbol,
        'user': user,
        'order_type': 'Market'
    }, qty=qty)
    

    limit_prc = float(avg_prc[1]) - order_details['stoploss_points']
    print(limit_prc)
    
    place_order_func('SiriTrading', {
        'transaction_type': 'SELL',
        'tradingsymbol': trading_symbol,
        'user': user,
        'order_type': 'Stoploss',
        'limit_prc': limit_prc,
    }, qty=qty)
    
    monitor_order_func = {
        'user':user,
        'broker' : broker,
        'token': trading_symbol,
        'target': order_details['target'],
        'limit_prc': limit_prc,
        'qty': qty,
        'strategy': 'Siri',
        'trade_type': 'SELL'
        
    }
    
    monitor_thread = threading.Thread(target=monitor_instruments, args=(monitor_order_func['token'],))
    monitor_thread.start()

telethon_crendentials = load_telethon_credentials()

with TelegramClient(telethon_crendentials['phone'], telethon_crendentials['api_id'], telethon_crendentials['api_hash']) as client:
    if not client.is_user_authorized():
        client.send_code_request(telethon_crendentials['phone'])
        client.sign_in(telethon_crendentials['phone'], input('Enter the code: '))

    group = client.get_entity(telethon_crendentials['group_url'])

    @client.on(NewMessage(chats=group))
    async def handler(event):
        message_content = event.message.message
        if message_content:
            order_details = extract_values_from_message(message_content)
            if order_details:
                order_details['stoploss_points'] = float(order_details['entry']) - float(order_details['stoploss'])
                raw_qty = int(float(telethon_crendentials['risk']) / order_details['stoploss_points'])
                print(order_details['Base_symbol'])
                qty = general_calc.round_qty(raw_qty,order_details['Base_symbol'])
                users_to_trade = general_calc.get_strategy_users('Siri')
                for broker, user in users_to_trade:
                    print(f"Placing order for {broker} and user {user}")
                    try:
                        place_order_for_broker(broker, user, order_details, qty)
                    except Exception as e:
                        print(f"Error placing order for {broker} and user {user}: {e}")

    print("Listening for new messages...")
    client.run_until_disconnected()