from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import logging
import os,sys

DIR = os.getcwd()
sys.path.append(DIR)

import Brokers.place_order as place_order
import MarketUtils.general_calc as general_calc



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states for the conversation
(ORDER_TYPE, TRANSACTION_TYPE,USER_SELECTION, BASE_INSTRUMENT, PRODUCT_TYPE, STOCK_NAME_INPUT, OPTION_TYPE, STRIKE_PRICE_SELECTION, 
 STRIKE_PRICE_INPUT, EXPIRY_SELECTION, QTY_RISK_SELECTION, QTY_RISK_INPUT, TRADE_ID_INPUT, 
 ENTRY_EXIT_SELECTION, CONFIRMATION) = range(15)

# Token for your bot from BotFather
TOKEN = '807232387:AAF5OgaGJuUPV8xwDUxYFRHaOWJSU5pIAic'

order_type_map = {"1": "PlaceOrder", "2": "PlaceStoploss", "3": "ModifyOrder"}
transaction_type_map = {"1": "BUY", "2": "SELL"}
base_instrument_map = {"1": "NIFTY", "2": "BANKNIFTY", "3": "FINNIFTY", "4": "Stock"}
product_type_map = {"1": "NRML", "2": "MIS"} 
option_type_map = {"1": "CE", "2": "PE", "3": "FUT", "4": "Stock"}
expiry_map = {"1": "current_week", "2": "current_month", "3": "next_week", "4": "next_month", "5": "Stock"}
entry_exit_map = {"1": "Entry", "2": "Exit"}
active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
active_users_map = {str(idx): user['account_name'] for idx, user in enumerate(active_users, 1)}

# Handler functions
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome to the Trading Bot! Please choose the transaction:\n"
                              "1. Place Order\n"
                              "2. Place Stoploss\n"
                              "3. Modify Order")
    
    return ORDER_TYPE

def order_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['order_type'] = order_type_map[user_input]
    update.message.reply_text("Select transaction type:\n"
                              "1. BUY\n"
                              "2. SELL")
    return TRANSACTION_TYPE

def transaction_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['transaction_type'] = transaction_type_map[user_input]

    active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
    message = "Please select an account by number:\n"
    for idx, user in enumerate(active_users, 1):
        message += f"{idx}. {user['account_name']}\n"
    message += f"{len(active_users) + 1}. All Users"  # Dynamically adding 'All Users' option

    update.message.reply_text(message)
    return USER_SELECTION

def user_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text

    try:
        if user_input == str(len(active_users) + 1):  # Check if 'All Users' is selected
            selected_accounts = [user['account_name'] for user in active_users]
        else:
            selected_account = active_users[int(user_input) - 1]['account_name']
            selected_accounts = [selected_account]  # Store as a list for consistency
    except (IndexError, ValueError):
        update.message.reply_text("Invalid selection. Please try again.")
        return USER_SELECTION

    context.user_data['account_name'] = selected_accounts
    update.message.reply_text("Select a BaseInstrument by number:\n"
                              "1. NIFTY\n"
                              "2. BANKNIFTY\n"
                              "3. FINNIFTY\n"
                              "4. Stock")
    return BASE_INSTRUMENT

def base_instrument(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['base_instrument'] = base_instrument_map.get(user_input, "Unknown")
    
    if user_input == "4":  # Stock
        update.message.reply_text("Please enter the stock name:")
        return STOCK_NAME_INPUT
    else:
        update.message.reply_text("Select Product Type:\n"
                                  "1. NRML\n"
                                  "2. MIS")
        return PRODUCT_TYPE
    
def stock_name_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['stock_name'] = user_input
    logger.info(f"Stock name received: {user_input}")  # Log for debugging
    update.message.reply_text("Select Product Type:\n"
                              "1. NRML\n"
                              "2. MIS")
    return PRODUCT_TYPE

def product_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['product_type'] = product_type_map.get(user_input, "Unknown")
    logger.info(f"Product type selected: {context.user_data['product_type']}")  # Log for debugging
    update.message.reply_text("Select Option Type:\n"
                              "1. CE\n"
                              "2. PE\n"
                              "3. FUT\n"
                              "4. Stock")
    return OPTION_TYPE

def option_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['option_type'] = option_type_map.get(user_input, "Unknown")
    # If user selects CE or PE, ask for strike price
    if user_input in ["1", "2"]:  # Assuming 1 is CE and 2 is PE
        update.message.reply_text("Select Strike Price option:\n"
                                  "1. ATM\n"
                                  "2. Enter the strike price")
        return STRIKE_PRICE_SELECTION
    else:
        # For other selections, proceed to expiry selection
        update.message.reply_text("Select Expiry:\n"
                                  "1. Current week\n"
                                  "2. Current Month\n"
                                  "3. Next week\n"
                                  "4. Next month\n"
                                  "5. Stock")
        return EXPIRY_SELECTION

def strike_price_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input == "1":
        context.user_data['strike_price'] = "ATM"
        # After ATM, proceed to expiry selection
        update.message.reply_text("Select Expiry:\n"
                                  "1. Current week\n"
                                  "2. Current Month\n"
                                  "3. Next week\n"
                                  "4. Next month\n"
                                  "5. Stock")
        return EXPIRY_SELECTION
    elif user_input == "2":
        update.message.reply_text("Please enter the strike price:")
        return STRIKE_PRICE_INPUT
    else:
        update.message.reply_text("Please select a valid option for Strike Price.")
        return STRIKE_PRICE_SELECTION

def strike_price_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['strike_price'] = user_input
    # After inputting strike price, proceed to expiry selection
    update.message.reply_text("Select Expiry:\n"
                              "1. Current week\n"
                              "2. Current Month\n"
                              "3. Next week\n"
                              "4. Next month\n"
                              "5. Stock")
    return EXPIRY_SELECTION


def expiry_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['expiry'] = expiry_map[user_input]
    update.message.reply_text("Enter:\n"
                              "1. Qty\n"
                              "2. Risk")
    return QTY_RISK_SELECTION

def qty_risk_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input in ["1", "2"]:
        context.user_data['qty_or_risk'] = user_input  # Store whether the user chose quantity or risk

        if user_input == "1":
            update.message.reply_text("Please enter the quantity:")
        else:
            update.message.reply_text("Please enter the risk percentage:")
        return QTY_RISK_INPUT
    else:
        update.message.reply_text("Please select a valid option for Qty/Risk.")
        return QTY_RISK_SELECTION


def qty_risk_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text

    # Determine whether to store quantity or risk percentage based on previous selection
    if 'qty_or_risk' in context.user_data:
        if context.user_data['qty_or_risk'] == "1":
            context.user_data['quantity'] = user_input  # Store the quantity
        elif context.user_data['qty_or_risk'] == "2":
            context.user_data['risk_percentage'] = user_input  # Store the risk percentage
    else:
        # Handle the error case where 'qty_or_risk' was not set
        update.message.reply_text("An error occurred. Please start again.")
        return ConversationHandler.END

    update.message.reply_text("Please enter the trade ID:")
    return TRADE_ID_INPUT

def trade_id_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['trade_id'] = user_input
    update.message.reply_text("Please select:\n"
                              "1. Entry\n"
                              "2. Exit")
    return ENTRY_EXIT_SELECTION

def entry_exit_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    trade_id = context.user_data.get('trade_id')
    if user_input == "1":
        context.user_data['trade_id'] = f"{trade_id}_entry"
    elif user_input == "2":
        context.user_data['trade_id'] = f"{trade_id}_exit"
    else:
        update.message.reply_text("Please select a valid option for Entry/Exit.")
        return ENTRY_EXIT_SELECTION

    qty_or_risk = context.user_data.get('quantity') or context.user_data.get('risk_percentage')
    qty_or_risk_label = "Quantity" if 'quantity' in context.user_data else "Risk Percentage"
    # Compile the summary of selections
    summary = (f"Order Transaction: {context.user_data.get('order_type')}\n"
                f"Transaction Type: {context.user_data.get('transaction_type')}\n"
               f"User: {context.user_data.get('account_name')}\n"
               f"Base Instrument: {context.user_data.get('base_instrument')}\n"
               f"Product Type: {context.user_data.get('product_type')}\n"
               f"Strike Price: {context.user_data.get('strike_price')}\n"
               f"Option Type: {context.user_data.get('option_type')}\n"
               f"Expiry: {context.user_data.get('expiry')}\n"
               f"{qty_or_risk_label}: {qty_or_risk}\n" 
               f"Trade ID: {context.user_data.get('trade_id')}")
    if context.user_data.get('stock_name'):
        summary += f"\nStock Name: {context.user_data.get('stock_name')}"
    update.message.reply_text(f"Thank you! Here's the summary of your selections:\n{summary}")
    return confirmation(update, context)

def confirmation(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Do you want to place the order?\n1. Yes\n2. No")
    return CONFIRMATION

def clear_user_data(context: CallbackContext):
    context.user_data.clear()

def process_confirmation(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input == "1":
        qty_or_risk = context.user_data.get('quantity') or context.user_data.get('risk_percentage')
        qty_or_risk_label = "qty" if 'quantity' in context.user_data else "risk_percentage"

        # Construct details as a dictionary
        details = {
            "order_type": context.user_data.get('order_type'),
            "transaction_type": context.user_data.get('transaction_type'),
            "account_name": context.user_data.get('account_name'),
            "base_instrument": context.user_data.get('base_instrument'),
            "product_type": context.user_data.get('product_type'),
            "strike_prc": context.user_data.get('strike_price'),
            "option_type": context.user_data.get('option_type'),
            "expiry": context.user_data.get('expiry'),
            qty_or_risk_label: qty_or_risk,
            "trade_id": context.user_data.get('trade_id')
        }
        if context.user_data.get('stock_name'):
            details["stock_name"] = context.user_data.get('stock_name')

        # Call orders_via_telegram with the details dictionary
        place_order.orders_via_telegram(details)
        clear_user_data(context)
        # Convert details dictionary to a string for displaying in the message
        details_str = '\n'.join([f"{key}: {value}" for key, value in details.items()])
        update.message.reply_text(f"Order placed:\n{details_str}")
    elif user_input == "2":
        update.message.reply_text("Order not placed. Please start again with /start if you wish to place an order.")
    else:
        update.message.reply_text("Please select a valid option:\n1. Yes\n2. No")
        return CONFIRMATION

    return ConversationHandler.END


def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
        ORDER_TYPE: [MessageHandler(Filters.text & ~Filters.command, order_type)],
        TRANSACTION_TYPE: [MessageHandler(Filters.text & ~Filters.command, transaction_type)],
        USER_SELECTION: [MessageHandler(Filters.text & ~Filters.command, user_selection)],
        BASE_INSTRUMENT: [MessageHandler(Filters.text & ~Filters.command, base_instrument)],
        STOCK_NAME_INPUT: [MessageHandler(Filters.text & ~Filters.command, stock_name_input)],
        PRODUCT_TYPE: [MessageHandler(Filters.text & ~Filters.command, product_type)],
        OPTION_TYPE: [MessageHandler(Filters.text & ~Filters.command, option_type)],
        STRIKE_PRICE_SELECTION: [MessageHandler(Filters.text & ~Filters.command, strike_price_selection)],
        STRIKE_PRICE_INPUT: [MessageHandler(Filters.text & ~Filters.command, strike_price_input)],
        EXPIRY_SELECTION: [MessageHandler(Filters.text & ~Filters.command, expiry_selection)],
        QTY_RISK_SELECTION: [MessageHandler(Filters.text & ~Filters.command, qty_risk_selection)],
        QTY_RISK_INPUT: [MessageHandler(Filters.text & ~Filters.command, qty_risk_input)],
        TRADE_ID_INPUT: [MessageHandler(Filters.text & ~Filters.command, trade_id_input)],
        ENTRY_EXIT_SELECTION: [MessageHandler(Filters.text & ~Filters.command, entry_exit_selection)],
        CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, process_confirmation)]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
