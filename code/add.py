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

def reload_group_data():
    return helper.load_group_data()
option = {}

# === Documentation of add.py ===

def run(message, bot):
    """
    run(message, bot): This is the main function used to implement the add feature.
    It prompts the user to decide whether to add the expense to a group or a category.
    """
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Do you want to add this expense to a group? (yes/no)")
    bot.register_next_step_handler(msg, handle_group_check, bot)

def handle_group_check(message, bot):
    """
    Handles whether the user wants to add the expense to a group or not.
    """
    chat_id = message.chat.id
    if message.text.lower() == "yes":
        msg = bot.send_message(chat_id, "Enter the group name:")
        bot.register_next_step_handler(msg, handle_group_name, bot)
    else:
        # Continue with normal expense addition flow
        helper.read_json()
        helper.read_category_json()
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
                    category_selection(message, bot, result)

def handle_group_name(message, bot):
    """
    Handles adding expenses to the specified group.
    Ensures that the group exists before proceeding to add the expense.
    """
    chat_id = message.chat.id
    group_name = message.text

    groups = helper.load_group_data()  # Reload group data to ensure it's up to date

    if group_name in groups:
        msg = bot.send_message(chat_id, "Enter the amount of the expense:")
        bot.register_next_step_handler(msg, handle_group_expense, bot, group_name)
    else:
        bot.send_message(chat_id, f"Group '{group_name}' does not exist or has been deleted. Please create a new group or choose an existing group.")

def handle_group_expense(message, bot, group_name):
    """
    Handles adding an expense to the group and calculates the new per-member share.
    """
    try:
        chat_id = message.chat.id
        expense = float(message.text)  # Validate input
        groups = helper.load_group_data()
        # Add the expense to the group's expenses and update the total spent
        groups[group_name]['expenses'].append(expense)
        groups[group_name]['total_spent'] += expense

        # Calculate the per-member share
        group_size = groups[group_name]['size']
        per_member_share = groups[group_name]['total_spent'] / group_size

        # Persist the updated group data
        helper.save_group_data(groups)

        # Notify the user that the expense has been added and show the per-member share
        bot.send_message(chat_id, f"Expense of ${expense} added to group '{group_name}'.")
        bot.send_message(chat_id, f"Each member now owes: ${per_member_share:.2f}")
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid number for the expense.")

def category_selection(msg, bot, date):
    """
    Handles the selection of expense categories when not adding to a group.
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
            bot.register_next_step_handler(msg, post_category_selection, bot, date)
    except Exception as e:
        print(e)

def post_category_selection(message, bot, date):
    """
    Processes the selected category and asks for the expense amount.
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
        message = bot.send_message(
            chat_id, "How much did you spend on {}? \n(Numeric values only)".format(str(option[chat_id])),)
        bot.register_next_step_handler(message, post_amount_input, bot, selected_category, date)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oh no! " + str(e))

def post_amount_input(message, bot, selected_category, date):
    """
    Handles the input of the expense amount and stores it.
    """
    try:
        chat_id = message.chat.id
        amount_entered = message.text
        amount_value = helper.validate_entered_amount(amount_entered)  # validate
        if amount_value == 0:  # cannot be $0 spending
            raise Exception("Spent amount has to be a non-zero number.")

        date_of_entry = date.strftime(helper.getDateFormat())
        date_str, category_str, amount_str = (
            str(date_of_entry),
            str(selected_category),
            str(amount_value),
        )
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
