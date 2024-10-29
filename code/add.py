"""
File: add.py
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
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime

option = {}

# === Documentation of add.py ===

def run(message, bot):
    """
    run(message, bot): This is the main function used to implement the add feature.
    It prompts the user to decide whether to add the expense to a group or a category.
    """
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 2
    markup.add(types.KeyboardButton("Individual"), types.KeyboardButton("Group"))

    msg = bot.send_message(chat_id, "Do you want to add this expense to an individual or a group?", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_group_check, bot)

def handle_group_check(message, bot):
    """
    Handles whether the user wants to add the expense to a group or not based on button selection.
    """
    chat_id = message.chat.id
    choice = message.text.lower()

    if choice == "group":
        msg = bot.send_message(chat_id, "Enter the group name:")
        bot.register_next_step_handler(msg, handle_group_name, bot)
    elif choice == "individual":
        msg = bot.send_message(chat_id, "Select date")
        calendar, step = DetailedTelegramCalendar().build()
        bot.send_message(chat_id, f"Select {LSTEP[step]}", reply_markup=calendar)

        @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
        def cal(c):
            chat_id = c.message.chat.id
            result, key, step = DetailedTelegramCalendar().process(c.data)

            if not result and key:
                bot.edit_message_text(
                    f"Select {LSTEP[step]}",
                    chat_id,
                    c.message.message_id,
                    reply_markup=key,
                )
            elif result:
                data = datetime.today().date()
                if result > data:
                    bot.send_message(chat_id, "Cannot select future dates. Please try /add command again with correct dates.")
                else:
                    category_selection(message, bot, result, group_name=None)  # group_name=None means individual flow
    else:
        bot.send_message(chat_id, "Invalid choice. Please choose from the buttons.")

def handle_group_name(message, bot):
    """
    Handles adding expenses to the specified group.
    Ensures that the group exists before proceeding to add the expense.
    """
    chat_id = message.chat.id
    group_name = message.text

    groups = helper.load_group_data()

    if group_name in groups:
        # Proceed to ask for date for group expense
        msg = bot.send_message(chat_id, "Select date")
        calendar, step = DetailedTelegramCalendar().build()
        bot.send_message(chat_id, f"Select {LSTEP[step]}", reply_markup=calendar)

        @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
        def cal(c):
            chat_id = c.message.chat.id
            result, key, step = DetailedTelegramCalendar().process(c.data)

            if not result and key:
                bot.edit_message_text(
                    f"Select {LSTEP[step]}",
                    chat_id,
                    c.message.message_id,
                    reply_markup=key,
                )
            elif result:
                data = datetime.today().date()
                if result > data:
                    bot.send_message(chat_id, "Cannot select future dates. Please try /add command again with correct dates.")
                else:
                    category_selection(message, bot, result, group_name)  # group_name is passed for group flow
    else:
        bot.send_message(chat_id, f"Group '{group_name}' does not exist. Please create a new group with /group.")


def category_selection(msg, bot, date, group_name=None):
    """
    Handles the selection of expense categories for both individuals and groups.
    If group_name is None, it's an individual expense.
    """
    try:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        categories = helper.getSpendCategories()
        if not categories:
            bot.reply_to(msg, "You don't have any categories. Please add a category!!")
        else:
            for c in categories:
                markup.add(c)
            msg = bot.reply_to(msg, "Select Category", reply_markup=markup)
            bot.register_next_step_handler(msg, post_category_selection, bot, date, group_name)
    except Exception as e:
        print(e)

def post_category_selection(message, bot, date, group_name=None):
    """
    Processes the selected category and asks for the expense amount.
    Handles both individual and group flows based on the presence of group_name.
    """
    try:
        chat_id = message.chat.id
        selected_category = message.text
        if selected_category not in helper.getSpendCategories():
            bot.send_message(
                chat_id, "Invalid", reply_markup=types.ReplyKeyboardRemove()
            )
            raise Exception(
                'Sorry, I don\'t recognise this category "{}"!'.format(selected_category)
            )
        option[chat_id] = selected_category
        msg = bot.send_message(
            chat_id, "How much did you spend on {}? \n(Numeric values only)".format(str(option[chat_id])),
        )
        bot.register_next_step_handler(msg, post_amount_input, bot, selected_category, date, group_name)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oh no! " + str(e))

def post_amount_input(message, bot, selected_category, date, group_name=None):
    """
    Handles the input of the expense amount and stores it.
    Works for both individual and group expenses.
    """
    try:
        chat_id = message.chat.id
        amount_entered = message.text
        
        # Ensure the amount is converted to a float (will raise ValueError if invalid)
        amount_value = float(helper.validate_entered_amount(amount_entered))  # validate

        if amount_value == 0:  # cannot be $0 spending
            raise Exception("Spent amount has to be a non-zero number.")

        date_of_entry = date.strftime(helper.getDateFormat())
        date_str, category_str, amount_str = (
            str(date_of_entry),
            str(selected_category),
            str(amount_value),
        )

        if group_name:  # Group flow
            groups = helper.load_group_data()
            
            # Convert amount_value to a float if it isn't already
            expense_record = {"date": date_str, "category": category_str, "amount": amount_value}
            groups[group_name]['expenses'].append(expense_record)

            # Make sure 'total_spent' is a float to allow addition
            groups[group_name]['total_spent'] += amount_value

            # Calculate the per-member share
            group_size = groups[group_name]['size']
            per_member_share = groups[group_name]['total_spent'] / group_size

            # Persist the updated group data
            helper.save_group_data(groups)

            bot.send_message(chat_id, f"Expense of ${amount_value} for '{category_str}' added to group '{group_name}' on {date_str}.")
            bot.send_message(chat_id, f"Each member now owes: ${per_member_share:.2f}")

        else:  # Individual flow
            helper.write_json(
                add_user_record(
                    chat_id, "{},{},{}".format(date_str, category_str, amount_str)
                )
            )
            bot.send_message(
                chat_id,
                "The following expenditure has been recorded: You have spent ${} for {} on {}".format(
                    amount_str, category_str, date_str
                ),
            )
            helper.display_remaining_budget(message, bot)
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid number for the expense.")
    except Exception as e:
        logging.exception(str(e))
        bot.send_message(chat_id, "Oh no. " + str(e))

def add_user_record(chat_id, record_to_be_added):
    """
    Stores the expense record for the user.
    """
    user_list = helper.read_json()
    if str(chat_id) not in user_list:
        user_list[str(chat_id)] = helper.createNewUserRecord()

    user_list[str(chat_id)]["data"].append(record_to_be_added)
    return user_list
