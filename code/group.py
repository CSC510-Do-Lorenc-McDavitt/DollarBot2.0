import helper
from telebot import types

groups = {}

def run(message, bot):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Enter group size:")
    bot.register_next_step_handler(msg, get_group_size, bot)

def get_group_size(message, bot):
    try:
        chat_id = message.chat.id
        group_size = int(message.text)  # Validate that it's a number
        groups[chat_id] = {"size": group_size, "members": [], "total_spent": 0}
        bot.send_message(chat_id, "Group created with size {}".format(group_size))
        msg = bot.send_message(chat_id, "Enter the amount spent:")
        bot.register_next_step_handler(msg, add_spend, bot)
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid number.")

def add_spend(message, bot):
    try:
        chat_id = message.chat.id
        amount = float(message.text)  # Validate amount
        group_info = groups.get(chat_id)
        if group_info:
            group_info["total_spent"] += amount
            per_person = group_info["total_spent"] / group_info["size"]
            bot.send_message(chat_id, "Each person needs to pay: ${:.2f}".format(per_person))
            # You can extend this to record the expense in a file/database
        else:
            bot.send_message(chat_id, "No group found. Please start by creating a group.")
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid amount.")
