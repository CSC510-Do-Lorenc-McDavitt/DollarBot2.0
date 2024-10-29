import helper
import logging
from tabulate import tabulate
from datetime import datetime
from currency import get_conversion_rate, get_supported_currencies
from telebot import types

def run(message, bot):
    """
    Main function to handle displaying history with currency and group selection.
    Prompts the user to select a currency, then asks if they want individual or group history.
    """
    chat_id = message.chat.id
    supported_currencies = get_supported_currencies()
    
    if supported_currencies:
        # Provide currency selection options
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for currency in supported_currencies:
            markup.add(currency)
        msg = bot.send_message(chat_id, "Select the currency you want the history to be displayed in:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: handle_history_type(m, bot))
    else:
        bot.send_message(chat_id, "Failed to fetch supported currencies. Please try again later.")

def handle_history_type(message, bot):
    """
    Handles whether the user wants to view individual or group history after currency selection.
    """
    chat_id = message.chat.id
    selected_currency = message.text.strip().upper()  # Get the selected currency

    # Ask if the user wants to view individual or group history
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 2
    markup.add(types.KeyboardButton("Individual"), types.KeyboardButton("Group"))
    
    msg = bot.send_message(chat_id, "Do you want to view individual or group history?", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: route_history_selection(m, bot, selected_currency))

def route_history_selection(message, bot, selected_currency):
    """
    Routes the user's choice to individual or group history display, using the selected currency.
    """
    chat_id = message.chat.id
    history_type = message.text.lower()

    if history_type == "individual":
        display_individual_history(chat_id, bot, selected_currency)
    elif history_type == "group":
        msg = bot.send_message(chat_id, "Enter the group name:")
        bot.register_next_step_handler(msg, lambda m: display_group_history(m, bot, selected_currency))
    else:
        bot.send_message(chat_id, "Invalid choice. Please choose 'Individual' or 'Group'.")

def display_individual_history(chat_id, bot, selected_currency):
    """
    Displays the individual spending history, with conversion if the selected currency is different from USD.
    """
    try:
        helper.read_json()
        user_history = helper.getUserHistory(chat_id)
        table = [["Date", "Category", "Amount"]]
        if user_history is None or len(user_history) == 0:
            bot.send_message(chat_id, "No transaction history found.")
            return

        for rec in user_history:
            values = rec.split(',')
            date, category, amount = values

            date_time = datetime.strptime(date, '%d-%b-%Y')
            current_date = datetime.now()

            if date_time <= current_date:
                original_currency = 'USD'  # Assume original currency is USD
                try:
                    if selected_currency != original_currency:
                        conversion_rate = get_conversion_rate(original_currency, selected_currency)
                        if conversion_rate:
                            converted_amount = round(float(amount) * conversion_rate, 2)
                            table.append([date, category, f"{converted_amount} {selected_currency}"])
                        else:
                            table.append([date, category, f"{amount} USD (conversion failed)"])
                    else:
                        table.append([date, category, f"{amount} USD"])
                except Exception as e:
                    bot.send_message(chat_id, f"Error converting amount: {e}")
                    return
        spend_total_str = "<pre>" + tabulate(table, headers='firstrow') + "</pre>"
        bot.send_message(chat_id, spend_total_str, parse_mode="HTML")

    except Exception as e:
        logging.exception(str(e))
        bot.send_message(chat_id, "Oops! " + str(e))

def display_group_history(message, bot, selected_currency):
    """
    Displays the spending history for a group along with the divided amount per person, with optional currency conversion.
    """
    try:
        chat_id = message.chat.id
        group_name = message.text.strip()

        groups = helper.load_group_data()
        if group_name not in groups:
            bot.send_message(chat_id, f"Group '{group_name}' does not exist.")
            return

        group_history = groups[group_name]['expenses']
        group_size = groups[group_name]['size']  # Get the group size

        if not group_history or len(group_history) == 0:
            bot.send_message(chat_id, f"No expenses found for group '{group_name}'.")
            return

        table = [["Date", "Category", "Amount", "Per Person"]]
        for expense in group_history:
            date = expense['date']
            category = expense['category']
            amount = expense['amount']

            # Calculate amount per person in selected currency
            try:
                if selected_currency != 'USD':
                    conversion_rate = get_conversion_rate('USD', selected_currency)
                    if conversion_rate:
                        converted_amount = round(amount * conversion_rate, 2)
                        divided_amount = round(converted_amount / group_size, 2)
                        table.append([date, category, f"{converted_amount} {selected_currency}", f"{divided_amount} {selected_currency}"])
                    else:
                        table.append([date, category, f"{amount} USD (conversion failed)", f"{amount / group_size} USD (conversion failed)"])
                else:
                    divided_amount = round(amount / group_size, 2)
                    table.append([date, category, f"{amount} USD", f"{divided_amount} USD"])
            except Exception as e:
                bot.send_message(chat_id, f"Error converting group expense: {e}")
                return

        history_str = "<pre>" + tabulate(table, headers='firstrow') + "</pre>"
        bot.send_message(chat_id, history_str, parse_mode="HTML")

    except Exception as e:
        logging.exception(str(e))
        bot.send_message(chat_id, "Oops! " + str(e))






