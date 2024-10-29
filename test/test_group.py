from code import group
from unittest.mock import patch, MagicMock

@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_create_group(mock_load_group_data, mock_save_group_data):
    # Mock loading of existing groups
    mock_load_group_data.return_value = {}

    # Simulate a message object for bot interaction
    message = MagicMock()
    message.chat.id = 12345
    message.text = "3"  # Simulate user entering group size

    bot = MagicMock()

    group.groups = mock_load_group_data() 
    group.create_group(message, bot, "test_group")

    # Verify group is created
    assert "test_group" in group.groups, "'test_group' should be created in groups"
    assert group.groups["test_group"]["size"] == 3, "Group size should be 3"
    assert group.groups["test_group"]["total_spent"] == 0, "Total spent should be 0"
    assert group.groups["test_group"]["expenses"] == [], "Expenses should be an empty list"

    mock_save_group_data.assert_called_once_with(group.groups)


@patch('helper.save_group_data')
@patch('helper.load_group_data')
def test_delete_group(mock_load_group_data, mock_save_group_data):
    # Mock existing groups
    mock_load_group_data.return_value = {
        "test_group": {"size": 3, "total_spent": 100, "expenses": [{"amount": 50}]}
    }
    message = MagicMock()
    message.chat.id = 12345
    message.text = "test_group"
    bot = MagicMock()
    group.groups = mock_load_group_data() 
    group.handle_delete_group(message, bot)
    assert "test_group" not in group.groups, "'test_group' should be deleted from groups"
    mock_save_group_data.assert_called_once_with(group.groups)


@patch('helper.load_group_data')
def test_view_all_groups(mock_load_group_data):
    # Mock existing groups
    mock_load_group_data.return_value = {
        "group_one": {"size": 4, "total_spent": 200, "expenses": []},
        "group_two": {"size": 3, "total_spent": 150, "expenses": []},
    }
    message = MagicMock()
    message.chat.id = 12345
    bot = MagicMock()
    group.groups = mock_load_group_data()
    group.view_all_groups(message.chat.id, bot)
    bot.send_message.assert_called_once_with(
        12345, "Here are all the groups:\ngroup_one\ngroup_two"
    )

@patch('helper.load_group_data')
def test_create_group_with_existing_name(mock_load_group_data):
    mock_load_group_data.return_value = {
        "existing_group": {"size": 3, "total_spent": 100, "expenses": []}
    }
    message = MagicMock()
    message.chat.id = 12345
    message.text = "existing_group"
    bot = MagicMock()

    group.groups = mock_load_group_data() 
    group.handle_group_name(message, bot)
    bot.send_message.assert_called_once_with(
        12345, "Group 'existing_group' already exists. You can add expenses to it via /add."
    )

@patch('helper.load_group_data')
def test_delete_non_existing_group(mock_load_group_data):
    mock_load_group_data.return_value = {}
    message = MagicMock()
    message.chat.id = 12345
    message.text = "non_existing_group" 
    bot = MagicMock()
    group.groups = mock_load_group_data() 
    group.handle_delete_group(message, bot)
    bot.send_message.assert_called_once_with(
        12345, "Group 'non_existing_group' does not exist."
    )