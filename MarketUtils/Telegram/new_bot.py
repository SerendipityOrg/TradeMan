from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states for the conversation
(STRATEGY, USER_SELECTION, BASE_INSTRUMENT, STRIKE_PRICE_SELECTION, STRIKE_PRICE_INPUT,
 OPTION_TYPE, EXPIRY_SELECTION, QTY_RISK_SELECTION, QTY_RISK_INPUT, TRADE_ID_INPUT,ENTRY_EXIT_SELECTION,CONFIRMATION) = range(12)

# Token for your bot from BotFather
TOKEN = '807232387:AAF5OgaGJuUPV8xwDUxYFRHaOWJSU5pIAic'

# Handler functions
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome to the Trading Bot! Please choose a strategy by number:\n"
                              "1. Strategy One\n"
                              "2. Strategy Two\n"
                              "3. Strategy Three")
    return STRATEGY

def strategy(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['strategy'] = user_input
    update.message.reply_text("Please select a user or 'All Users':\n"
                              "1. User1\n"
                              "2. User2\n"
                              "3. All Users")
    return USER_SELECTION

def user_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    # If the input is '3', we will consider it as 'All Users'
    if user_input == "3":
        user_input = "All Users"
    context.user_data['user'] = user_input
    update.message.reply_text("Select a BaseInstrument by number:\n"
                              "1. Nifty\n"
                              "2. BankNifty\n"
                              "3. Finnifty")
    return BASE_INSTRUMENT

def base_instrument(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['base_instrument'] = user_input
    update.message.reply_text("Select Strike Price option:\n"
                              "1. ATM\n"
                              "2. Enter the strike price")
    return STRIKE_PRICE_SELECTION

def strike_price_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    if user_input == "1":
        context.user_data['strike_price'] = "ATM"
        update.message.reply_text("Select Option Type:\n"
                                  "1. CE\n"
                                  "2. PE\n"
                                  "3. FUT\n"
                                  "4. Stock")
        return OPTION_TYPE
    elif user_input == "2":
        update.message.reply_text("Please enter the strike price:")
        return STRIKE_PRICE_INPUT
    else:
        update.message.reply_text("Please select a valid option for Strike Price.")
        return STRIKE_PRICE_SELECTION

def strike_price_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['strike_price'] = user_input
    update.message.reply_text("Select Option Type:\n"
                              "1. CE\n"
                              "2. PE\n"
                              "3. FUT\n"
                              "4. Stock")
    return OPTION_TYPE

def option_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['option_type'] = user_input
    update.message.reply_text("Select Expiry:\n"
                              "1. Current week\n"
                              "2. Current Month\n"
                              "3. Next week\n"
                              "4. Next month\n"
                              "5. Stock")
    return EXPIRY_SELECTION

def expiry_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['expiry'] = user_input
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
    summary = (f"Strategy: {context.user_data.get('strategy')}\n"
               f"User: {context.user_data.get('user')}\n"
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
        summary = (f"Strategy: {context.user_data.get('strategy')}\n"
                   f"User: {context.user_data.get('user')}\n"
                   f"Base Instrument: {context.user_data.get('base_instrument')}\n"
                   f"Strike Price: {context.user_data.get('strike_price')}\n"
                   f"Option Type: {context.user_data.get('option_type')}\n"
                   f"Expiry: {context.user_data.get('expiry')}\n"
                   f"Qty/Risk: {context.user_data.get('qty_risk')}\n"
                   f"Trade ID: {context.user_data.get('trade_id')}")
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
            STRATEGY: [MessageHandler(Filters.text & ~Filters.command, strategy)],
            USER_SELECTION: [MessageHandler(Filters.text & ~Filters.command, user_selection)],
            BASE_INSTRUMENT: [MessageHandler(Filters.text & ~Filters.command, base_instrument)],
            STRIKE_PRICE_SELECTION: [MessageHandler(Filters.text & ~Filters.command, strike_price_selection)],
            STRIKE_PRICE_INPUT: [MessageHandler(Filters.text & ~Filters.command, strike_price_input)],
            OPTION_TYPE: [MessageHandler(Filters.text & ~Filters.command, option_type)],
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
