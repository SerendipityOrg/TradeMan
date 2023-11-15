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
(ORDER_TYPE, USER_SELECTION, BASE_INSTRUMENT, STOCK_NAME_INPUT, OPTION_TYPE, STRIKE_PRICE_SELECTION, 
 STRIKE_PRICE_INPUT, EXPIRY_SELECTION, QTY_RISK_SELECTION, QTY_RISK_INPUT, TRADE_ID_INPUT, 
 ENTRY_EXIT_SELECTION, CONFIRMATION) = range(13)

# Token for your bot from BotFather
TOKEN = '807232387:AAF5OgaGJuUPV8xwDUxYFRHaOWJSU5pIAic'

order_type_map = {"1": "Place Order", "2": "Place Stoploss", "3": "Modify Order"}
base_instrument_map = {"1": "Nifty", "2": "BankNifty", "3": "Finnifty", "4": "Stock"}
option_type_map = {"1": "CE", "2": "PE", "3": "FUT", "4": "Stock"}
expiry_map = {"1": "Current week", "2": "Current Month", "3": "Next week", "4": "Next month", "5": "Stock"}
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

    active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
    message = "Please select an account by number:\n"
    for idx, user in enumerate(active_users, 1):
        message += f"{idx}. {user['account_name']}\n"

    update.message.reply_text(message)
    return USER_SELECTION

def user_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text

    try:
        selected_account = active_users[int(user_input) - 1]['account_name']
    except (IndexError, ValueError):
        update.message.reply_text("Invalid selection. Please try again.")
        return USER_SELECTION

    context.user_data['account_name'] = selected_account
    update.message.reply_text("Select a BaseInstrument by number:\n"
                              "1. Nifty\n"
                              "2. BankNifty\n"
                              "3. Finnifty\n"
                              "4. Stock")
    return BASE_INSTRUMENT

def base_instrument(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input == "4":  # Assuming "4" is the option for "Stock"
        update.message.reply_text("Please enter the stock name:")
        return STOCK_NAME_INPUT
    else:
        context.user_data['base_instrument'] = base_instrument_map[user_input]
        update.message.reply_text("Select Option Type:\n"
                                  "1. CE\n"
                                  "2. PE\n"
                                  "3. FUT\n"
                                  "4. Stock")
        return OPTION_TYPE

def stock_name_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['stock_name'] = user_input
    update.message.reply_text("Select Option Type:\n"
                              "1. CE\n"
                              "2. PE\n"
                              "3. FUT\n"
                              "4. Stock")
    return OPTION_TYPE

def option_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['option_type'] = user_input
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
                                  "4. Next month")
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
                                  "4. Next month")
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
                              "4. Next month")
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
        if user_input == "1":
            update.message.reply_text("Please enter the quantity:")
        else:
            update.message.reply_text("Please enter the risk amount:")
        return QTY_RISK_INPUT
    else:
        update.message.reply_text("Please select a valid option for Qty/Risk.")
        return QTY_RISK_SELECTION

def qty_risk_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['qty_risk'] = user_input
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

    # Compile the summary of selections
    summary = (f"Order Transaction: {context.user_data.get('order_type')}\n"
               f"User: {context.user_data.get('account_name')}\n"
               f"Base Instrument: {context.user_data.get('base_instrument')}\n"
               f"Strike Price: {context.user_data.get('strike_price')}\n"
               f"Option Type: {context.user_data.get('option_type')}\n"
               f"Expiry: {context.user_data.get('expiry')}\n"
               f"Qty/Risk: {context.user_data.get('qty_risk')}\n"
               f"Trade ID: {context.user_data.get('trade_id')}")
    update.message.reply_text(f"Thank you! Here's the summary of your selections:\n{summary}")
    return confirmation(update, context)

def confirmation(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Do you want to place the order?\n1. Yes\n2. No")
    return CONFIRMATION

def process_confirmation(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input == "1":
        # If the user wants to place the order, print the summary of the order
        summary = (f"Order Transaction: {context.user_data.get('order_type')}\n"
                   f"User: {context.user_data.get('account_name')}\n"
                   f"Base Instrument: {context.user_data.get('base_instrument')}\n"
                   f"Strike Price: {context.user_data.get('strike_price')}\n"
                   f"Option Type: {context.user_data.get('option_type')}\n"
                   f"Expiry: {context.user_data.get('expiry')}\n"
                   f"Qty/Risk: {context.user_data.get('qty_risk')}\n"
                   f"Trade ID: {context.user_data.get('trade_id')}")
        place_order.orders_via_telegram(summary)
        update.message.reply_text(f"Order placed:\n{summary}")
    elif user_input == "2":
        # If the user selects no, tell them to start again
        update.message.reply_text("Order not placed. Please start again with /start if you wish to place an order.")
    else:
        # If the user inputs anything else, prompt them again
        update.message.reply_text("Please select a valid option:\n1. Yes\n2. No")
        return CONFIRMATION
    
    # This ends the conversation no matter what the user chooses.
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
        USER_SELECTION: [MessageHandler(Filters.text & ~Filters.command, user_selection)],
        BASE_INSTRUMENT: [MessageHandler(Filters.text & ~Filters.command, base_instrument)],
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
