"""
File: history.py
Author: Vyshnavi Adusumelli, Tejaswini Panati, Harshavardhan Bandaru
Date: October 01, 2023
Description: File contains Telegram bot message handlers and their associated functions.

Copyright (c) 2023

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import helper
import logging
from tabulate import tabulate
from datetime import datetime
from currency import get_conversion_rate
from currency import get_supported_currencies
from telebot import TeleBot, types

from telebot import types

# === Documentation of history.py ===



def run(message, bot):
    """
    Fetches, processes, and formats the user's transaction history based on their selected currency.
    Main function to handle displaying history (either individual or group).

    run(message, bot): This is the main function used to implement the delete feature.
    It takes 2 arguments for processing - message which is the message from the user, and bot which
    is the telegram bot object from the main code.py function. It calls helper.py to get the user's
    historical data and based on whether there is data available, it either prints an error message or
    displays the user's historical data.
    """
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 2
    markup.add(types.KeyboardButton("Individual"), types.KeyboardButton("Group"))
    
    msg = bot.send_message(chat_id, "Do you want to view individual or group history?", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_history_type, bot)

def handle_history_type(message, bot):
    """
    Handles whether the user wants to view individual or group history.
    """
    chat_id = message.chat.id
    history_type = message.text.lower()

    if history_type == "individual":
        display_individual_history(message, chat_id, bot)
    elif history_type == "group":
        msg = bot.send_message(chat_id, "Enter the group name:")
        bot.register_next_step_handler(msg, display_group_history, bot)
    else:
        bot.send_message(chat_id, "Invalid choice. Please choose 'individual' or 'group'.")

def display_individual_history(message, chat_id, bot):
    """
    Displays the individual spending history.
    """
    selected_currency = message.text.strip().upper()
    try:
        helper.read_json()
        user_history = helper.getUserHistory(chat_id)
        table = [["Date", "Category", "Amount"]]
        if user_history is None or len(user_history) == 0:
            raise Exception("Sorry! No spending records found!")
        else:
            for rec in user_history:
                values = rec.split(',')
                date, category, amount = values

                date_time = datetime.strptime(date, '%d-%b-%Y')
                current_date = datetime.now()
                if date_time <= current_date:
                    original_currency = 'USD'  # Assume the original currency is USD
                    try:
                        # Convert the amount if the selected currency is different
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


def display_group_history(message, bot):
    """
    Displays the spending history for a group along with the divided amount per person.
    """
    try:
        chat_id = message.chat.id
        group_name = message.text

        groups = helper.load_group_data()

        if group_name not in groups:
            raise Exception(f"Group '{group_name}' does not exist.")

        group_history = groups[group_name]['expenses']
        group_size = groups[group_name]['size']  # Get the group size

        if not group_history or len(group_history) == 0:
            raise Exception(f"No expenses found for group '{group_name}'.")

        table = [["Date", "Category", "Amount", "Per Person"]]
        for expense in group_history:
            date = expense['date']
            category = expense['category']
            amount = expense['amount']
            divided_amount = round(amount / group_size, 2)  # Calculate amount per person
            table.append([date, category, f"$ {amount}", f"$ {divided_amount}"])

        history_str = "<pre>" + tabulate(table, headers='firstrow') + "</pre>"
        bot.send_message(chat_id, history_str, parse_mode="HTML")

    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oops! " + str(e))





