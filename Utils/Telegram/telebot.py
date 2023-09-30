from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os,sys 
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')

sys.path.append(BROKERS_DIR)
import place_order as place_order
from instrument_monitor import InstrumentMonitor

env_file_path = os.path.abspath(os.path.join(BROKERS_DIR,'.env'))

# Load environment variables from .env file
load_dotenv(env_file_path)

token = os.getenv('telegram_bot_token')

mpwizard = os.path.abspath(os.path.join(CURRENT_DIR, '..','..','Strategies','MPWizard'))
sys.path.append(mpwizard)
import MPWizard_calc as mpw
# token = '807232387:AAF5OgaGJuUPV8xwDUxYFRHaOWJSU5pIAic'

UTILS_DIR = os.path.join(CURRENT_DIR, '..')

sys.path.append(UTILS_DIR)
import general_calc as gc

# Navigate to the Brokers and Utils directories relative to the current script's location

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Place Order", callback_data='Place Order'),
         InlineKeyboardButton("Place Stoploss Order", callback_data='Place Stoploss Order'),
         InlineKeyboardButton("Modify Stoploss Order", callback_data='Modify Stoploss Order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='What do you want to do?', reply_markup=reply_markup)

def action_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    action = query.data
    context.user_data['action'] = action

    if action == 'Place Order':
        start_place_order(update, context)
    elif action == 'Place Stoploss Order':
        start_stoploss_order(update, context)
    elif action == 'Modify Stoploss Order':
        start_stoploss_order(update, context)

# Starts the bot and asks the user to select the index
def start_place_order(update, context):
    keyboard = [
        [InlineKeyboardButton("NIFTY", callback_data='NIFTY'),
         InlineKeyboardButton("BANKNIFTY", callback_data='BANKNIFTY'),
         InlineKeyboardButton("FINNIFTY", callback_data='FINNIFTY')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Select the index:', reply_markup=reply_markup)

def start_stoploss_order(update, context):
    keyboard = [
        [InlineKeyboardButton("NIFTY", callback_data='NIFTY'),
         InlineKeyboardButton("BANKNIFTY", callback_data='BANKNIFTY'),
         InlineKeyboardButton("FINNIFTY", callback_data='FINNIFTY')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Select the index:', reply_markup=reply_markup)


def index_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    index = query.data
    context.user_data['index'] = index
    context.bot.send_message(chat_id=query.message.chat_id, text="Enter the strike price:")

def strike_callback(update: Update, context: CallbackContext) -> None:
    print('strike_callback')
    strike_price = update.message.text
    context.user_data['strike_price'] = int(strike_price)

    keyboard = [
        [InlineKeyboardButton("CE", callback_data='CE'),
         InlineKeyboardButton("PE", callback_data='PE')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Select the option type:', reply_markup=reply_markup)

def option_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    option_type = query.data
    context.user_data['option_type'] = option_type

    if context.user_data['action'] == 'Place Order':
        keyboard = [
            [InlineKeyboardButton("BUY", callback_data='BUY'),
             InlineKeyboardButton("SELL", callback_data='SELL')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=query.message.chat_id, text="Select the trade type:", reply_markup=reply_markup)
    elif context.user_data['action'] == 'Place Stoploss Order':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Enter the limit price:")
    elif context.user_data['action'] == 'Modify Stoploss Order':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Enter the limit price:")

def limit_callback(update: Update, context: CallbackContext) -> None:
    print('limit_callback')
    limit_price = update.message.text
    context.user_data['limit_price'] = float(limit_price)
    context.user_data['trigger_price'] = float(limit_price) + 0.5
    keyboard = [
        [InlineKeyboardButton("BUY", callback_data='BUY'),
         InlineKeyboardButton("SELL", callback_data='SELL')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Select the trade type:', reply_markup=reply_markup)
    # context.bot.send_message(chat_id=update.effective_chat.id, text='Enter the trigger price:')

def trade_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    monitor = InstrumentMonitor()
    trade_type = query.data

    order_details = {
    "base_symbol": context.user_data['index'],
    "option_type": context.user_data['option_type'],
    "strike_prc": context.user_data['strike_price'],
    "transcation": trade_type
    }

    order_details['stoploss_points'] = mpw.get_weekday_price_ref(order_details['base_symbol'])
    if context.user_data['action'] == 'Place Order':
        place_order.place_order_for_broker("MPWizard", order_details, monitor=monitor)



    if context.user_data['action'] == 'Modify Stoploss Order':
        order_details['limit_prc'] = context.user_data['limit_price']
        order_details['trigger_price'] = context.user_data['trigger_price']
        order_details['strategy'] = 'MPWizard'

        place_order.modify_orders(order_details=order_details)


        # place_stoploss_order(index, strike_price, option_type, limit_price, trigger_price, trade_type)
    #     for broker,user in users_to_trade:
    #         print(broker)
    #         if broker == 'zerodha':
    #             place_stoploss_zerodha(trading_symbol_list[0], trade_type, trade_type, strike_price, index, limit_price, user, broker='zerodha')

    #         elif broker == 'aliceblue':
    #             place_stoploss_aliceblue(trading_symbol_aliceblue[0], trade_type, trade_type, strike_price, index,limit_price, user, broker='aliceblue')

    # # else:
    #     for broker,user in users_to_trade:
    #         if broker == 'zerodha':
    #             place_zerodha_order(trading_symbol_list[0], trade_type, trade_type, strike_price, index, user, broker='zerodha')

    #         elif broker == 'aliceblue':
    #             place_aliceblue_order(trading_symbol_aliceblue[0], trade_type, trade_type, strike_price, index, user, broker='aliceblue')


    reply_text = f"You selected:\nIndex: {context.user_data['index']}\nStrike Price: {context.user_data['strike_price']}\nOption Type: {context.user_data['option_type']}\nTrade Type: {trade_type}"
    
    if context.user_data['action'] == 'Place Stoploss Order':
        reply_text += f"\nLimit Price: {order_details['limit_prc']}\nTrigger Price: {order_details['trigger_price']}"
    if context.user_data['action'] == 'Modify Stoploss Order':
        reply_text += f"\nLimit Price: {order_details['limit_prc']}\nTrigger Price: {order_details['trigger_price']}"
    
    context.bot.send_message(chat_id=query.message.chat_id, text=reply_text)

def main() -> None:
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    
    dispatcher.add_handler(CallbackQueryHandler(action_callback, pattern='^(Place Order|Place Stoploss Order|Modify Stoploss Order)$'))
    dispatcher.add_handler(CallbackQueryHandler(index_callback, pattern='^(NIFTY|BANKNIFTY|FINNIFTY)$'))
    dispatcher.add_handler(CallbackQueryHandler(option_callback, pattern='^(CE|PE)$'))
    # dispatcher.add_handler(CallbackQueryHandler(trigger_callback, pattern='^(BUY|SELL)$'))
    dispatcher.add_handler(CallbackQueryHandler(trade_callback, pattern='^(BUY|SELL)$'))

    dispatcher.add_handler(MessageHandler(Filters.regex(r"[1-9]\d{4,}"), strike_callback))  # Only accept digits
    dispatcher.add_handler(MessageHandler(Filters.regex(r"(1*(?:[1-9][0-9]?|200))"), limit_callback))  # Only accept digits and dots
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    print('Starting bot...')
    main()