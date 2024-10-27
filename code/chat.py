
"""
File: chat.py
Author: Haojie Zhou
Date: Oct 27 2024
Description: ChatGPT integration module for DollarBot with financial advisory capabilities
"""

import helper
import openai
from telebot import types
from concurrent.futures import ThreadPoolExecutor
import logging
from jproperties import Properties
from datetime import datetime, timedelta
configs = Properties()

with open("user.properties", "rb") as read_prop:
    configs.load(read_prop)
openai_key_token = str(configs.get("openai_key").data)
#Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatGPTHandler:
    def __init__(self):
        self.openai = openai
        self.openai.api_key = openai_key_token
        self.conversations = {}
        self.user_data = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.last_activity = {}  
        self.TIMEOUT_MINUTES = 2  
        
        self.SYSTEM_PROMPT = """You are a financial advisor bot analyzing the user's DollarBot data.
        
        Current Financial Status:
        {financial_status}
        
        Your role is to:
        1. Provide clear financial insights
        2. Suggest practical budget improvements
        3. Answer questions about spending patterns
        4. Give actionable financial advice
        
        Keep responses concise and specific to the user's data."""

    def load_user_data(self, chat_id):
        """Load and process user's financial data"""
        logger.info(f"Loading data for user {chat_id}")
        try:
            # Get user data
            history = helper.getUserHistory(chat_id)
            budget = helper.getCategoryBudget(chat_id)
            overall_budget = helper.getOverallBudget(chat_id)
            
            # Initialize data structure
            financial_data = {
                "total_spent": 0,
                "transactions": [],
                "category_totals": {},
                "budget_info": budget if budget else {},
                "overall_budget": overall_budget if overall_budget else 0
            }

            # Process history if available
            if history:
                for record in history:
                    try:
                        date, category, amount = record.split(',')
                        amount = float(amount)
                        
                        financial_data["transactions"].append({
                            "date": date,
                            "category": category,
                            "amount": amount
                        })
                        
                        if category not in financial_data["category_totals"]:
                            financial_data["category_totals"][category] = 0
                        financial_data["category_totals"][category] += amount
                        financial_data["total_spent"] += amount
                    except Exception as e:
                        logger.error(f"Error processing record: {record}, Error: {str(e)}")
                        continue

            self.user_data[chat_id] = financial_data
            logger.info(f"Data loaded successfully for user {chat_id}")
            logger.debug(f"User data: {financial_data}")
            return True
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}")
            return False

    def format_financial_status(self, chat_id):
        """Format financial data for GPT prompt with detailed transaction history"""
        data = self.user_data.get(chat_id, {})
        status_lines = []

        # First, show all transactions in chronological order
        if data.get("transactions"):
            status_lines.append("Transaction History (Chronological Order):")
            sorted_transactions = sorted(
                data["transactions"], 
                key=lambda x: datetime.strptime(x["date"], helper.getDateFormat())
            )
            for t in sorted_transactions:
                status_lines.append(
                    f"- Date: {t['date']}, Category: {t['category']}, Amount: ${t['amount']:.2f}"
                )
            status_lines.append("")  # Add spacing

        # Then add summary information
        status_lines.append("Financial Summary:")
        total_spent = data.get("total_spent", 0)
        overall_budget = data.get("overall_budget", 0)
        status_lines.append(f"Total Spent: ${total_spent:.2f}")
        status_lines.append(f"Overall Budget: ${overall_budget}")
        remaining_budget = float(overall_budget) - total_spent
        status_lines.append(f"Remaining Budget: ${remaining_budget:.2f}")
        
        # Category breakdown
        if data.get("category_totals"):
            status_lines.append("\nCategory Analysis:")
            for category, amount in data["category_totals"].items():
                budget_amount = float(data.get("budget_info", {}).get(category, 0))
                category_remaining = budget_amount - amount
                percentage = (amount / budget_amount * 100) if budget_amount > 0 else 0
                status_lines.append(
                    f"- {category}:\n"
                    f"  Spent: ${amount:.2f}\n"
                    f"  Budget: ${budget_amount:.2f}\n"
                    f"  Remaining: ${category_remaining:.2f}\n"
                    f"  Budget Usage: {percentage:.1f}%"
                )

        return "\n".join(status_lines)

    def check_timeout(self, chat_id):
        """Check if the conversation has timed out"""
        if chat_id not in self.last_activity:
            return False
        
        time_difference = datetime.now() - self.last_activity[chat_id]
        return time_difference > timedelta(minutes=self.TIMEOUT_MINUTES)

    def handle_message(self, message, bot):
        """Handle user messages with timeout check"""
        chat_id = message.chat.id
        
        # Check for timeout
        if self.check_timeout(chat_id):
            bot.send_message(chat_id, "Chat session timed out due to inactivity. Start new chat with /chat")
            self.cleanup(chat_id)
            return
            
        # Update last activity time
        self.last_activity[chat_id] = datetime.now()
        
        # Rest of the handler remains the same
        logger.info(f"Handling message from user {chat_id}: {message.text}")

        if message.text.lower() == '/end':
            bot.send_message(chat_id, "Chat session ended. Start new chat with /chat")
            self.cleanup(chat_id)
            return

        try:
            self.conversations[chat_id].append({
                "role": "user",
                "content": message.text
            })

            def get_chatgpt_response():
                return openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.conversations[chat_id],
                    temperature=0.7
                )

            response = self.executor.submit(get_chatgpt_response).result()
            assistant_message = response['choices'][0]['message']['content']
            
            self.conversations[chat_id].append({
                "role": "assistant",
                "content": assistant_message
            })

            msg = bot.send_message(chat_id, assistant_message)
            bot.register_next_step_handler(msg, self.handle_message, bot)

        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}")
            bot.send_message(chat_id, f"Sorry, I encountered an error. Please try again.")
            bot.register_next_step_handler(message, self.handle_message, bot)

    def run(self, message, bot):
        """Start chat session with timeout tracking"""
        chat_id = message.chat.id
        logger.info(f"Starting chat session for user {chat_id}")
        
        # Initialize last activity time
        self.last_activity[chat_id] = datetime.now()
        
        # Rest of the run method remains the same
        bot.send_message(chat_id, "Analyzing your financial data...")
        if not self.load_user_data(chat_id):
            bot.send_message(chat_id, "Sorry, I couldn't load your financial data. Please try again later.")
            return

        self.conversations[chat_id] = [{
            "role": "system",
            "content": self.SYSTEM_PROMPT.format(
                financial_status=self.format_financial_status(chat_id)
            )
        }]
        logger.debug(f"System prompt: {self.conversations[chat_id][0]}")

        msg = bot.send_message(
            chat_id,
            "I've analyzed your financial data. What would you like to know? (Type /end to finish)"
        )
        bot.register_next_step_handler(msg, self.handle_message, bot)

    def cleanup(self, chat_id):
        """Clean up session data including timeout tracking"""
        logger.info(f"Cleaning up session for user {chat_id}")
        self.conversations.pop(chat_id, None)
        self.user_data.pop(chat_id, None)
        self.last_activity.pop(chat_id, None)

# Create handler instance
chat_handler = ChatGPTHandler()

def run(message, bot):
    """Entry point"""
    chat_handler.run(message, bot)