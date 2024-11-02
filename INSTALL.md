
# 🚀 DollarBot Installation and Setup

## Prerequisites
1. **Telegram Desktop App**  
   Download and install from [here](https://desktop.telegram.org/).  
   Create a Telegram account or log in.

2. **OpenAI API Key**
   You need to generate a GPT API key through the OpenAI website to enable the chat function.
   Obtain an OpenAI API key from [OpenAI](https://platform.openai.com/signup).
   
---

## Installation

### MacOS / Ubuntu Users
1. **Clone the Repository**  
   Open a terminal and run:
   ```bash
   git clone https://github.com/KomachiZ/DollarBot/tree/project2
   ```
2. **Run Setup Script**  
   In the project directory, run:
   ```bash
   chmod a+x setup.sh
   bash setup.sh
   ```

### Windows Users
   To run the setup script, use a UNIX-like platform, such as **Cygwin** or **WSL**.
   Once set up, follow the steps in the MacOS/Ubuntu section above.

---

## Running DollarBot

### Bot Setup on Telegram
1. **Create a Bot**  
   Open Telegram, search for **BotFather**, and type `/newbot`.  
   Follow the on-screen instructions to name your bot and assign a unique username ending with “bot” (e.g., `dollarbot_<your_nickname>`).  
   Save the token BotFather provides for later use.

2. **Start DollarBot**  
   In the project directory, give permission and execute the script:
   ```bash
   chmod a+x run.sh
   bash run.sh       # for MacOS / Unix
   ./run.sh          # for Windows
   ```
   When prompted, paste your API token. A successful launch will display "TeleBot: Started polling."

3. **Start Interacting**  
   In Telegram, search for your bot using its unique username. Type `/start` or `menu` to begin using DollarBot!

---

## Run DollarBot on System Startup
To launch DollarBot at startup, add `.run_forever.sh` to your `.bashrc` file. [Learn more about `.bashrc` here](https://example-link.com).

--- 

You're all set! Enjoy tracking your expenses with DollarBot.
