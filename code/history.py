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


# === Documentation of history.py ===


def run(message, bot):
    """
    Fetches, processes, and formats the user's transaction history based on their selected currency.
    """
    try:
        chat_id = message.chat.id
        selected_currency = message.text.strip().upper()

        helper.read_json()
        user_history = helper.getUserHistory(chat_id)
        if user_history is None or len(user_history) == 0:
            bot.send_message(chat_id, "No transaction history found.")
            return

        table = [["Date", "Category", "Amount"]]
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

        if len(table) > 1:
            spend_total_str = "<pre>" + tabulate(table, headers='firstrow') + "</pre>"
            bot.send_message(chat_id, spend_total_str, parse_mode="HTML")
        else:
            bot.send_message(chat_id, "No transaction history found after conversion.")

    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oops! " + str(e))




