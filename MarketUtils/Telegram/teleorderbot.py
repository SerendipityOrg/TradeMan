from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import logging
import os,sys
from dotenv import load_dotenv

DIR = os.getcwd()
sys.path.append(DIR)

import Brokers.place_order as place_order
import MarketUtils.general_calc as general_calc

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)  # Set to DEBUG to capture detailed logs
logger = logging.getLogger(__name__)

# Define states for the conversation
(ORDER_TYPE, TRANSACTION_TYPE,USER_SELECTION, BASE_INSTRUMENT, PRODUCT_TYPE, STOCK_NAME_INPUT, OPTION_TYPE, STRIKE_PRICE_SELECTION, 
 STRIKE_PRICE_INPUT, EXPIRY_SELECTION, QTY_RISK_SELECTION, QTY_RISK_INPUT, TRADE_ID_INPUT, STRATEGY_SELECTION,STRATEGY_QTY_SELECTION,
 ENTRY_EXIT_SELECTION, CONFIRMATION) = range(17)

# Token for your bot from BotFather
TOKEN = '807232387:AAF5OgaGJuUPV8xwDUxYFRHaOWJSU5pIAic'

def get_strategies_from_users():
    active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
    strategies = set()
    for user in active_users:
        strategies.update(user['qty'].keys())
    strategies.add("Extra")
    strategies.add("Stocks")

    # Convert the set to a list and sort it
    sorted_strategies = sorted(list(strategies))
    return {str(idx + 1): strategy for idx, strategy in enumerate(sorted_strategies)}


def get_strategy_qty(username,base_instrument, strategy):
    active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
    for user in active_users:
        if user['account_name'] == username and strategy in user['qty']:
            if isinstance(user['qty'][strategy], dict):
                return user['qty'][strategy].get(base_instrument)
            else:
                return user['qty'][strategy]
    return None

order_type_map = {"1": "PlaceOrder", "2": "PlaceStoploss", "3": "ModifyOrder"}
transaction_type_map = {"1": "BUY", "2": "SELL"}
base_instrument_map = {"1": "NIFTY", "2": "BANKNIFTY", "3": "FINNIFTY", "4": "Stock"}
product_type_map = {"1": "NRML", "2": "MIS", "3": "CNC"} 
option_type_map = {"1": "CE", "2": "PE", "3": "FUT", "4": "Stock"}
expiry_map = {"1": "current_week", "2": "current_month", "3": "next_week", "4": "next_month", "5": "Stock"}
entry_exit_map = {"1": "Entry", "2": "Exit"}
active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
active_users_map = {str(idx): user['account_name'] for idx, user in enumerate(active_users, 1)}
strategy_map = get_strategies_from_users()

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

    # Construct the strategy options message
    strategy_options_message = "Select strategy:\n"
    for key, strategy in strategy_map.items():
        strategy_options_message += f"{key}. {strategy}\n"

    update.message.reply_text(strategy_options_message)
    return STRATEGY_SELECTION

def strategy_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    selected_strategy = strategy_map.get(user_input, "Unknown")
    if selected_strategy == "Unknown":
        update.message.reply_text("Invalid strategy. Please try again.")
        return STRATEGY_SELECTION

    context.user_data['strategy'] = selected_strategy

    # Check if the selected strategy is "Extra" or "Stocks"
    if selected_strategy in ["Extra", "Stocks"]:
        # Show all users from active_users.json
        active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
        user_selection_message = "Please select one or more users by number (e.g., 1,3,5):\n"
        for idx, user in enumerate(active_users, 1):
            user_selection_message += f"{idx}. {user['account_name']}\n"
        user_selection_message += f"{len(active_users) + 1}. ALL USERS\n"
        context.user_data['filtered_users'] = active_users
        update.message.reply_text(user_selection_message)
        return USER_SELECTION
    else:
        # Filter active_users based on selected strategy
        active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
        filtered_users = [user for user in active_users if selected_strategy in user['qty']]
        context.user_data['filtered_users'] = filtered_users

        # Construct user selection message
        user_selection_message = "Please select one or more users by number (e.g., 1,3,5):\n"
        for idx, user in enumerate(filtered_users, 1):
            user_selection_message += f"{idx}. {user['account_name']}\n"

        user_selection_message += f"{len(filtered_users) + 1}. ALL USERS\n"
        update.message.reply_text(user_selection_message)
        return USER_SELECTION



def user_selection(update: Update, context: CallbackContext) -> int:
    user_inputs = update.message.text.split(',')
    all_users_option = str(len(context.user_data.get('filtered_users', [])) + 1)  # The option number for "All Users"
    selected_accounts = []

    for user_input in user_inputs:
        user_input = user_input.strip()
        if user_input == all_users_option:
            # If 'filtered_users' doesn't exist, use all users from active_users.json
            filtered_users = context.user_data.get('filtered_users')
            if not filtered_users:
                active_users = general_calc.read_json_file(os.path.join(DIR, "MarketUtils", "active_users.json"))
                filtered_users = active_users
            selected_accounts = [user['account_name'] for user in filtered_users]
            break  # No need to loop further as all users are selected
        else:
            try:
                selected_account = context.user_data.get('filtered_users', [])[int(user_input) - 1]['account_name']
                selected_accounts.append(selected_account)
            except (IndexError, ValueError):
                update.message.reply_text("Invalid selection: " + user_input)
                return USER_SELECTION

    context.user_data['account_name'] = selected_accounts
    # Proceed to the next step
    update.message.reply_text("Select transaction type:\n1. BUY\n2. SELL")
    return TRANSACTION_TYPE

def transaction_type(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['transaction_type'] = transaction_type_map[user_input]

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
                              "2. MIS\n"
                              "3. CNC")
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
                              "2. Risk\n"
                              "3. Strategy QTY")
    return QTY_RISK_SELECTION

def qty_risk_selection(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    context.user_data['qty_or_risk'] = user_input

    if user_input == "3":
        update.message.reply_text("Please Enter Trade ID")
        return TRADE_ID_INPUT
    elif user_input == "1" or user_input == "2":
        prompt = "Please enter the quantity:" if user_input == "1" else "Please enter the risk percentage:"
        update.message.reply_text(prompt)
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
    context.user_data['trade_id'] = user_input.upper()
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
                f"Transaction Type: {context.user_data.get('transaction_type')}\n"
               f"User: {context.user_data.get('account_name')}\n"
               f"Base Instrument: {context.user_data.get('base_instrument')}\n"
               f"Product Type: {context.user_data.get('product_type')}\n"
               f"Strike Price: {context.user_data.get('strike_price')}\n"
               f"Option Type: {context.user_data.get('option_type')}\n"
               f"Expiry: {context.user_data.get('expiry')}\n"
               f"Trade ID: {context.user_data.get('trade_id')}")
    if context.user_data.get('stock_name'):
        summary += f"\nStock Name: {context.user_data.get('stock_name').upper()}"
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
        order_details_list = []

        # Check the mode of quantity determination: manual or risk-based
        qty_or_risk = context.user_data.get('qty_or_risk')
        for account_name in context.user_data['account_name']:
            if qty_or_risk == "1":  # Manual quantity entry
                quantity = context.user_data.get('quantity')
                qty_or_risk_label = "qty"
            elif qty_or_risk == "2":  # Risk percentage
                quantity = context.user_data.get('risk_percentage')
                # Implement your logic for calculating quantity based on risk
                qty_or_risk_label = "risk_percentage"
            elif qty_or_risk == "3":  # Strategy quantity
                quantity = get_strategy_qty(account_name,context.user_data.get('base_instrument', ''), context.user_data.get('strategy', ''))
                qty_or_risk_label = "qty"
            else:
                update.message.reply_text("Invalid quantity/risk selection.")
                return ConversationHandler.END

            # Construct details for each user
            details = {
                "order_type": context.user_data.get('order_type'),
                "transaction_type": context.user_data.get('transaction_type'),
                "account_name": account_name,
                "base_instrument": context.user_data.get('base_instrument'),
                "product_type": context.user_data.get('product_type'),
                "strike_prc": context.user_data.get('strike_price'),
                "option_type": context.user_data.get('option_type'),
                "expiry": context.user_data.get('expiry'),
                qty_or_risk_label: quantity,  # User-specific quantity
                "trade_id": context.user_data.get('trade_id')
            }
            if context.user_data.get('stock_name'):
                details["stock_name"] = context.user_data.get('stock_name').upper()

            order_details_list.append(details)

        # Pass the list of details to orders_via_telegram function
        for order_details in order_details_list:
            place_order.orders_via_telegram(order_details)

        clear_user_data(context)
        update.message.reply_text("Orders placed for all selected users.")
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
        STRATEGY_SELECTION: [MessageHandler(Filters.text & ~Filters.command, strategy_selection)],
        USER_SELECTION: [MessageHandler(Filters.text & ~Filters.command, user_selection)],
        TRANSACTION_TYPE: [MessageHandler(Filters.text & ~Filters.command, transaction_type)],
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
