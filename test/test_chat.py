"""
File: test/test_chat.py
Author: Haojie Zhou
Date: Oct 27 2024
Description: Test cases for ChatGPT integration module
"""

import pytest
from unittest.mock import patch, mock_open
import builtins
import sys
import importlib
from pathlib import Path

# Mock properties content
MOCK_PROPERTIES = """api_token=your_mock_api_key
openai_key=gpt_token"""

class MockPropertiesFile:
    def __init__(self):
        self.data = MOCK_PROPERTIES.encode('utf-8')
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def read(self):
        return self.data

def mock_open_impl(*args, **kwargs):
    if str(args[0]) == "user.properties":
        return MockPropertiesFile()
    return original_open(*args, **kwargs)

# Store the original open function
original_open = builtins.open

# Apply mock at module level
mock_open_patcher = patch('builtins.open', side_effect=mock_open_impl)
mock_open_patcher.start()

# Import ChatGPTHandler after applying the mock
if 'code.chat' in sys.modules:
    importlib.reload(sys.modules['code.chat'])
from code.chat import ChatGPTHandler

import json

# Mock data for testing
MOCK_USER_HISTORY = [
    "27-Oct-2024,Food,25.50",
    "26-Oct-2024,Transport,15.00",
    "25-Oct-2024,Shopping,100.00"
]

MOCK_BUDGET = {
    "Food": "200",
    "Transport": "150",
    "Shopping": "300"
}

MOCK_OVERALL_BUDGET = "1000"

@pytest.fixture
def chat_handler_instance():
    """Create a fresh ChatGPTHandler instance for each test"""
    handler = ChatGPTHandler()
    handler.openai.api_key = "mock_key"
    return handler

# Test Initialization
def test_chat_handler_initialization():
    """Test ChatGPTHandler initialization"""
    handler = ChatGPTHandler()
    assert handler.TIMEOUT_MINUTES == 2
    assert isinstance(handler.conversations, dict)
    assert isinstance(handler.user_data, dict)
    assert isinstance(handler.last_activity, dict)

# Test Data Loading
@patch('helper.getOverallBudget')
@patch('helper.getCategoryBudget')
@patch('helper.getUserHistory')
def test_load_user_data_success(mock_get_history, mock_get_budget, mock_get_overall, chat_handler_instance):
    """Test successful data loading"""
    mock_get_overall.return_value = MOCK_OVERALL_BUDGET
    mock_get_budget.return_value = MOCK_BUDGET
    mock_get_history.return_value = MOCK_USER_HISTORY
    
    result = chat_handler_instance.load_user_data("123")
    
    
    mock_get_history.assert_called_once()
    mock_get_budget.assert_called_once()
    mock_get_overall.assert_called_once()
    
    # Verify basic assertions
    assert result == True
    assert "123" in chat_handler_instance.user_data
    
    user_data = chat_handler_instance.user_data["123"]
    
    # Verify data structure
    assert "transactions" in user_data
    assert "category_totals" in user_data
    assert "total_spent" in user_data
    
    # Verify transactions were loaded correctly
    assert len(user_data["transactions"]) == 3, f"Expected 3 transactions, got {len(user_data['transactions'])}"
    
    # Verify transaction content
    transactions = sorted(user_data["transactions"], key=lambda x: x["amount"])
    assert transactions[0]["amount"] == 15.00, "First transaction amount mismatch"
    assert transactions[1]["amount"] == 25.50, "Second transaction amount mismatch"
    assert transactions[2]["amount"] == 100.00, "Third transaction amount mismatch"
    
    # Verify category totals
    assert user_data["category_totals"]["Food"] == 25.50
    assert user_data["category_totals"]["Transport"] == 15.00
    assert user_data["category_totals"]["Shopping"] == 100.00
    
    # Verify total spent
    assert user_data["total_spent"] == 140.50

def test_load_user_data_no_history(chat_handler_instance):
    """Test data loading with no history"""
    with patch('code.helper.getUserHistory', return_value=None):
        result = chat_handler_instance.load_user_data("123")
        assert result == True
        assert chat_handler_instance.user_data["123"]["total_spent"] == 0

def test_load_user_data_invalid_record(chat_handler_instance):
    """Test data loading with invalid record"""
    with patch('code.helper.getUserHistory', return_value=["invalid,record"]):
        result = chat_handler_instance.load_user_data("123")
        assert result == True
        assert chat_handler_instance.user_data["123"]["total_spent"] == 0

# Test Financial Status Formatting
def test_format_financial_status_complete(chat_handler_instance):
    """Test financial status formatting with complete data"""
    chat_handler_instance.user_data["123"] = {
        "total_spent": 140.50,
        "transactions": [
            {"date": "27-Oct-2024", "category": "Food", "amount": 25.50},
            {"date": "26-Oct-2024", "category": "Transport", "amount": 15.00}
        ],
        "category_totals": {"Food": 25.50, "Transport": 15.00},
        "budget_info": {"Food": "200", "Transport": "150"},
        "overall_budget": "1000"
    }
    
    result = chat_handler_instance.format_financial_status("123")
    
    
    assert "Transaction History (Chronological Order):" in result
    assert "Financial Summary:" in result
    assert "Category Analysis:" in result
    assert "Food" in result and "$25.50" in result
    assert "Transport" in result and "$15.00" in result
    assert "Total Spent: $140.50" in result
    assert "Overall Budget: $1000" in result
    assert "Budget Usage:" in result
    
    # 检查详细的支出记录格式
    assert "- Date: 27-Oct-2024, Category: Food, Amount: $25.50" in result
    assert "- Date: 26-Oct-2024, Category: Transport, Amount: $15.00" in result

def test_format_financial_status_empty(chat_handler_instance):
    """Test financial status formatting with empty data"""
    chat_handler_instance.user_data["123"] = {}
    result = chat_handler_instance.format_financial_status("123")
    assert "Total Spent: $0.00" in result

# Test Timeout Functionality
def test_check_timeout_no_activity(chat_handler_instance):
    """Test timeout check with no previous activity"""
    assert chat_handler_instance.check_timeout("123") == False

def test_check_timeout_within_limit(chat_handler_instance):
    """Test timeout check within time limit"""
    chat_handler_instance.last_activity["123"] = datetime.now()
    assert chat_handler_instance.check_timeout("123") == False

def test_check_timeout_expired(chat_handler_instance):
    """Test timeout check after time limit"""
    chat_handler_instance.last_activity["123"] = datetime.now() - timedelta(minutes=3)
    assert chat_handler_instance.check_timeout("123") == True

# Test Message Handling
@patch('telebot.TeleBot')
def test_handle_message_end_command(mock_bot, chat_handler_instance):
    """Test handling of end command"""
    message = Mock()
    message.text = "/end"
    message.chat.id = "123"
    
    chat_handler_instance.handle_message(message, mock_bot)
    mock_bot.send_message.assert_called_with("123", "Chat session ended. Start new chat with /chat")

@patch('telebot.TeleBot')
def test_handle_message_timeout(mock_bot, chat_handler_instance):
    """Test handling of timed out session"""
    message = Mock()
    message.text = "Hello"
    message.chat.id = "123"
    chat_handler_instance.last_activity["123"] = datetime.now() - timedelta(minutes=3)
    
    chat_handler_instance.handle_message(message, mock_bot)
    mock_bot.send_message.assert_called_with("123", "Chat session timed out due to inactivity. Start new chat with /chat")

@patch('openai.ChatCompletion.create')
@patch('telebot.TeleBot')
def test_handle_message_successful_response(mock_bot, mock_openai, chat_handler_instance):
    """Test successful message handling and GPT response"""
    message = Mock()
    message.text = "Hello"
    message.chat.id = "123"
    chat_handler_instance.last_activity["123"] = datetime.now()
    chat_handler_instance.conversations["123"] = []
    
    mock_openai.return_value = {
        "choices": [{"message": {"content": "Hello! How can I help?"}}]
    }
    
    chat_handler_instance.handle_message(message, mock_bot)
    assert len(chat_handler_instance.conversations["123"]) == 2

@patch('telebot.TeleBot')
def test_handle_message_openai_error(mock_bot, chat_handler_instance):
    """Test handling of OpenAI API error"""
    message = Mock()
    message.text = "Hello"
    message.chat.id = "123"
    chat_handler_instance.last_activity["123"] = datetime.now()
    
    with patch('openai.ChatCompletion.create', side_effect=Exception("API Error")):
        chat_handler_instance.handle_message(message, mock_bot)
        mock_bot.send_message.assert_called_with("123", "Sorry, I encountered an error. Please try again.")

# Test Cleanup
def test_cleanup(chat_handler_instance):
    """Test session cleanup"""
    chat_id = "123"
    chat_handler_instance.conversations[chat_id] = ["test"]
    chat_handler_instance.user_data[chat_id] = {"test": "data"}
    chat_handler_instance.last_activity[chat_id] = datetime.now()
    
    chat_handler_instance.cleanup(chat_id)
    assert chat_id not in chat_handler_instance.conversations
    assert chat_id not in chat_handler_instance.user_data
    assert chat_id not in chat_handler_instance.last_activity

# Test Run Function
@patch('telebot.TeleBot')
def test_run_successful(mock_bot, chat_handler_instance):
    """Test successful chat session initialization"""
    message = Mock()
    message.chat.id = "123"
    
    with patch.object(chat_handler_instance, 'load_user_data', return_value=True):
        chat_handler_instance.run(message, mock_bot)
        assert len(mock_bot.send_message.call_args_list) == 2

@patch('telebot.TeleBot')
def test_run_data_load_failure(mock_bot, chat_handler_instance):
    """Test chat session initialization with data load failure"""
    message = Mock()
    message.chat.id = "123"
    
    with patch.object(chat_handler_instance, 'load_user_data', return_value=False):
        chat_handler_instance.run(message, mock_bot)
        mock_bot.send_message.assert_called_with("123", "Sorry, I couldn't load your financial data. Please try again later.")

# Test Integration
@patch('telebot.TeleBot')
def test_full_conversation_flow(mock_bot, chat_handler_instance):
    """Test a complete conversation flow"""
    message = Mock()
    message.chat.id = "123"
    message.text = "Hello"
    
    # Mock dependencies
    with patch('code.helper.getUserHistory', return_value=MOCK_USER_HISTORY), \
         patch('code.helper.getCategoryBudget', return_value=MOCK_BUDGET), \
         patch('code.helper.getOverallBudget', return_value=MOCK_OVERALL_BUDGET), \
         patch('openai.ChatCompletion.create') as mock_openai:
        
        # Setup mock response
        mock_openai.return_value = {
            "choices": [{"message": {"content": "Hello! I see you've spent $140.50 so far."}}]
        }
        
        # Start conversation
        chat_handler_instance.run(message, mock_bot)
        
        # Simulate user message
        chat_handler_instance.handle_message(message, mock_bot)
        
        # Verify conversation state
        assert "123" in chat_handler_instance.conversations
        assert len(chat_handler_instance.conversations["123"]) > 0


# Financial Advice Testing
@patch('openai.ChatCompletion.create')
@patch('telebot.TeleBot')
def test_financial_advice_request(mock_bot, mock_openai, chat_handler_instance):
    """Test requesting financial advice"""
    message = Mock()
    message.text = "Can you give me advice on my spending habits?"
    message.chat.id = "123"
    
    # Setup user data
    chat_handler_instance.user_data["123"] = {
        "total_spent": 140.50,
        "transactions": [
            {"date": "27-Oct-2024", "category": "Food", "amount": 25.50},
            {"date": "26-Oct-2024", "category": "Transport", "amount": 15.00}
        ],
        "category_totals": {"Food": 25.50, "Transport": 15.00},
        "budget_info": {"Food": "200", "Transport": "150"},
        "overall_budget": "1000"
    }
    chat_handler_instance.last_activity["123"] = datetime.now()
    chat_handler_instance.conversations["123"] = []
    
    # Mock GPT response
    mock_openai.return_value = {
        "choices": [{"message": {"content": "Based on your spending data..."}}]
    }
    
    chat_handler_instance.handle_message(message, mock_bot)
    assert len(chat_handler_instance.conversations["123"]) == 2
    mock_bot.send_message.assert_called_once()

# Security Testing
@patch('openai.ChatCompletion.create')
@patch('telebot.TeleBot')
def test_sensitive_information_handling(mock_bot, mock_openai, chat_handler_instance):
    """Test handling of sensitive information requests"""
    message = Mock()
    message.text = "What's my credit card number?"
    message.chat.id = "123"
    chat_handler_instance.last_activity["123"] = datetime.now()
    chat_handler_instance.conversations["123"] = [{
        "role": "system",
        "content": "You are a financial advisor bot..."
    }]
    
    mock_openai.return_value = {
        "choices": [{"message": {"content": "I cannot provide or access sensitive financial information..."}}]
    }
    
    chat_handler_instance.handle_message(message, mock_bot)
    assert len(chat_handler_instance.conversations["123"]) == 3
    mock_bot.send_message.assert_called_once()

# Long Conversation Testing
@patch('openai.ChatCompletion.create')
@patch('telebot.TeleBot')
def test_extended_conversation_context(mock_bot, mock_openai, chat_handler_instance):
    """Test handling of extended conversation with context"""
    message = Mock()
    message.chat.id = "123"
    chat_handler_instance.last_activity["123"] = datetime.now()
    chat_handler_instance.conversations["123"] = []
    
    # Simulate multiple message exchanges
    messages = [
        "How much did I spend on food?",
        "What's my biggest expense category?",
        "Any suggestions for saving money?"
    ]
    
    mock_openai.return_value = {
        "choices": [{"message": {"content": "Here's your financial analysis..."}}]
    }
    
    for msg in messages:
        message.text = msg
        chat_handler_instance.handle_message(message, mock_bot)
        
    assert len(chat_handler_instance.conversations["123"]) == len(messages) * 2
