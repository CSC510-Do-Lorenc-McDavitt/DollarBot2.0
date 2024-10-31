"""
File: test_group.py
Author: Yumo Shen, Jiewen Liu, Haojie Zhou
Date: October 28, 2024
Description: File contains Telegram bot message handlers and their associated functions.

Copyright (c) 2024

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

import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from telebot import types

code_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code'))
sys.path.insert(0, code_directory)
import group
import add
import history

# Define global group data to be used across multiple test cases
global_groups = {
    "test_group": {"size": 3, "total_spent": 100, "expenses": []},
    "existing_group": {"size": 3, "total_spent": 150, "expenses": [{"amount": 50}]}
}

# Helper function to reset the global group data before each test
def reset_groups():
    group.groups = global_groups.copy()

@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_create_group(mock_load_group_data, mock_save_group_data):
    # Use global group data
    reset_groups()
    mock_load_group_data.return_value = group.groups

    # Simulate a message object for bot interaction
    message = MagicMock()
    message.chat.id = 12345
    message.text = "3"  # Simulate user entering group size

    bot = MagicMock()

    group.create_group(message, bot, "new_test_group")

    # Verify group is created
    assert "new_test_group" in group.groups, "'new_test_group' should be created in groups"
    assert group.groups["new_test_group"]["size"] == 3, "Group size should be 3"
    assert group.groups["new_test_group"]["total_spent"] == 0, "Total spent should be 0"
    assert group.groups["new_test_group"]["expenses"] == [], "Expenses should be an empty list"

    mock_save_group_data.assert_called_once_with(group.groups)


@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_delete_group(mock_load_group_data, mock_save_group_data):
    reset_groups()
    mock_load_group_data.return_value = group.groups

    message = MagicMock()
    message.chat.id = 12345
    message.text = "existing_group"  # This is the group we're deleting
    bot = MagicMock()

    group.handle_delete_group(message, bot)
    assert "existing_group" not in group.groups, "'existing_group' should be deleted from groups"
    mock_save_group_data.assert_called_once_with(group.groups)


@patch('helper.load_group_data')
def test_view_all_groups(mock_load_group_data):
    reset_groups()
    mock_load_group_data.return_value = group.groups

    message = MagicMock()
    message.chat.id = 12345
    bot = MagicMock()

    group.view_all_groups(message.chat.id, bot)
    bot.send_message.assert_called_once_with(
        12345, "Here are all the groups:\ntest_group\nexisting_group"
    )


@patch('helper.load_group_data')
def test_create_group_with_existing_name(mock_load_group_data):
    reset_groups()
    mock_load_group_data.return_value = group.groups

    message = MagicMock()
    message.chat.id = 12345
    message.text = "existing_group"
    bot = MagicMock()

    group.handle_group_name(message, bot)
    bot.send_message.assert_called_once_with(
        12345, "Group 'existing_group' already exists. You can add expenses to it via /add."
    )


@patch('helper.load_group_data')
def test_delete_non_existing_group(mock_load_group_data):
    reset_groups()
    mock_load_group_data.return_value = {}

    message = MagicMock()
    message.chat.id = 12345
    message.text = "non_existing_group"
    bot = MagicMock()

    group.handle_delete_group(message, bot)
    bot.send_message.assert_called_once_with(
        12345, "Group 'non_existing_group' does not exist."
    )


@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_add_expense_to_group(mock_load_group_data, mock_save_group_data):
    reset_groups()
    mock_load_group_data.return_value = group.groups

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "50"  # Simulate the user entering expense amount
    bot = MagicMock()
    valid_date = datetime.today().date()
    add.post_amount_input(message, bot, "Food", valid_date, group_name="test_group")

    assert len(group.groups["test_group"]["expenses"]) == 1, "The group should have 1 expense"
    assert group.groups["test_group"]["total_spent"] == 150, "Total spent should be updated to 150"
    assert group.groups["test_group"]["expenses"][0]["amount"] == 50, "The added expense should be 50"
    mock_save_group_data.assert_called_once_with(group.groups)

@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_add_expense_to_non_existing_group(mock_load_group_data, mock_save_group_data):
    """
    Test adding an expense to a non-existing group, but the group name is checked first.
    """
    reset_groups()
    mock_load_group_data.return_value = group.groups

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "non_existing_group" 
    bot = MagicMock()
    add.handle_group_name(message, bot)
    bot.send_message.assert_called_with(
        12345, "Group 'non_existing_group' does not exist. Please create a new group with /group."
    )

    mock_save_group_data.assert_not_called()

@patch('helper.load_group_data')
def test_invalid_group_name(mock_load_group_data):
    """
    Test adding an expense with an invalid (empty) group name.
    """
    reset_groups()
    mock_load_group_data.return_value = group.groups
    message = MagicMock()
    message.chat.id = 12345
    message.text = ""  # Empty group name
    bot = MagicMock()
    add.handle_group_name(message, bot)
    bot.send_message.assert_called_with(12345, "Group '' does not exist. Please create a new group with /group.")

@patch('helper.getSpendCategories')
@patch('helper.load_group_data')
def test_invalid_category_selection(mock_load_group_data, mock_getSpendCategories):
    """
    Test selecting an invalid category.
    """
    reset_groups()
    mock_load_group_data.return_value = group.groups
    mock_getSpendCategories.return_value = ["Food", "Transport"]
    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "InvalidCategory"  # Invalid category selection
    bot = MagicMock()
    valid_date = datetime.today().date()
    add.post_category_selection(message, bot, valid_date, group_name="test_group")
    # We can also assert that the bot doesn't proceed to asking for an amount after invalid selection
    assert bot.send_message.call_count == 1, "Bot should only send the 'Invalid' message and stop."

@patch('helper.load_group_data')
def test_invalid_expense_amount(mock_load_group_data):
    """
    Test adding an invalid (zero) expense amount.
    """
    reset_groups()
    mock_load_group_data.return_value = group.groups

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "0"  # Invalid amount
    bot = MagicMock()

    # Call post_amount_input and simulate invalid input
    valid_date = datetime.today().date()
    add.post_amount_input(message, bot, "Food", valid_date, group_name="test_group")

    # Ensure the bot sends an error message for invalid amount
    bot.send_message.assert_called_with(12345, "Oh no. Spent amount has to be a non-zero number.")

@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_add_expense_to_existing_group(mock_load_group_data, mock_save_group_data):
    """
    Test adding an expense to an existing group.
    """
    reset_groups()
    
    # Mock existing group data
    mock_load_group_data.return_value = {
        "test_group": {"size": 3, "total_spent": 100, "expenses": []}
    }

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "50"  # User enters the expense amount
    bot = MagicMock()

    # Call post_amount_input in add.py
    valid_date = datetime.today().date()
    add.post_amount_input(message, bot, "Food", valid_date, group_name="test_group")

    # Verify that the expense was added and total spent updated
    assert group.groups["test_group"]["total_spent"] == 150, "Total spent should be updated to 150"
    assert len(group.groups["test_group"]["expenses"]) == 1, "There should be 1 expense in the group"

    # Ensure the bot sends the correct message
    bot.send_message.assert_any_call(
        12345, "Expense of $50.0 for 'Food' added to group 'test_group' on {}.".format(valid_date.strftime("%d-%b-%Y"))
    )
    bot.send_message.assert_any_call(
        12345, "Each member now owes: $50.00"
    )

@patch('helper.load_group_data')
@patch('currency.get_conversion_rate')
def test_display_group_history(mock_get_conversion_rate, mock_load_group_data):
    """
    Test retrieving and displaying group history for a valid group with expenses.
    """
    # Mock group data with expenses
    mock_load_group_data.return_value = {
        "test_group": {
            "size": 3,
            "expenses": [
                {"date": "12-Oct-2024", "category": "Food", "amount": 150},
                {"date": "13-Oct-2024", "category": "Transport", "amount": 75}
            ]
        }
    }
    mock_get_conversion_rate.return_value = 1  # Assume USD to USD conversion

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "test_group"  # Valid group name
    bot = MagicMock()

    # Call display_group_history function in history.py
    history.display_group_history(message, bot, "USD")

    # Assert the correct group history is sent
    bot.send_message.assert_called()
    bot.send_message.assert_any_call(
        12345,
        "<pre>Date         Category    Amount    Per Person\n"
        "-----------  ----------  --------  ------------\n"
        "12-Oct-2024  Food        150 USD   50.0 USD\n"
        "13-Oct-2024  Transport   75 USD    25.0 USD</pre>",
        parse_mode="HTML"
    )

@patch('helper.load_group_data')
def test_display_group_history_no_expenses(mock_load_group_data):
    """
    Test displaying group history when no expenses exist.
    """
    # Mock group data with no expenses
    mock_load_group_data.return_value = {
        "test_group": {
            "size": 3,
            "expenses": []
        }
    }

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "test_group"  # Valid group name
    bot = MagicMock()

    # Call display_group_history function in history.py
    history.display_group_history(message, bot, "USD")

    # Ensure the bot sends a message saying there are no expenses
    bot.send_message.assert_called_once_with(12345, "No expenses found for group 'test_group'.")

@patch('helper.load_group_data')
def test_display_group_history_non_existing_group(mock_load_group_data):
    """
    Test displaying group history for a non-existing group.
    """
    # Mock no groups existing
    mock_load_group_data.return_value = {}

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "non_existing_group"  # Invalid group name
    bot = MagicMock()

    # Call display_group_history function in history.py
    history.display_group_history(message, bot, "USD")

    # Ensure the bot sends a message saying the group does not exist
    bot.send_message.assert_called_once_with(12345, "Group 'non_existing_group' does not exist.")

@patch('helper.load_group_data')
@patch('currency.get_conversion_rate')
def test_display_group_history_with_conversion(mock_get_conversion_rate, mock_load_group_data):
    """
    Test displaying group history with currency conversion.
    """
    # Mock group data with expenses
    mock_load_group_data.return_value = {
        "test_group": {
            "size": 4,
            "expenses": [
                {"date": "12-Oct-2024", "category": "Food", "amount": 100}
            ]
        }
    }

    # Simulate bot and message objects
    message = MagicMock()
    message.chat.id = 12345
    message.text = "test_group"  # Valid group name
    bot = MagicMock()

    # Call display_group_history function in history.py
    history.display_group_history(message, bot, "EUR")

    # Ensure the bot sends the correctly converted amounts
    bot.send_message.assert_called()
    bot.send_message.assert_any_call(
        12345,
        "<pre>Date         Category    Amount     Per Person\n"
        "-----------  ----------  ---------  ------------\n"
        "12-Oct-2024  Food        92.18 EUR  23.05 EUR</pre>",
        parse_mode="HTML"
    )

@patch('helper.load_group_data')
@patch('currency.get_conversion_rate')
def test_display_group_history_conversion_failed(mock_get_conversion_rate, mock_load_group_data):
    """
    Test displaying group history with failed currency conversion.
    """
    mock_load_group_data.return_value = {
        "test_group": {
            "size": 4,
            "expenses": [
                {"date": "12-Oct-2024", "category": "Food", "amount": 100}
            ]
        }
    }
    mock_get_conversion_rate.return_value = None
    message = MagicMock()
    message.chat.id = 12345
    message.text = "test_group"
    bot = MagicMock()

    history.display_group_history(message, bot, "ABC")

    bot.send_message.assert_called()
    bot.send_message.assert_any_call(
        12345,
        "<pre>Date         Category    Amount                       Per Person\n"
        "-----------  ----------  ---------------------------  ----------------------------\n"
        "12-Oct-2024  Food        100 USD (conversion failed)  25.0 USD (conversion failed)</pre>",
        parse_mode="HTML"
    )
    