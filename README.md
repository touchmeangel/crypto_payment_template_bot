# Telegram Crypto Payment Template

A lightweight, flexible, and high-performance Telegram bot template for crypto payments. Written in raw Python and powered entirely by pure blockchain interactions—no middlemen, no custodial wallet BS, and completely decentralized the way it was meant to be.

An open-source, sovereign alternative to centralized solutions like `@CryptoBot`.

## Features

- **Pure On-Chain Verification:** Directly scans the blockchain for payment confirmation. You own your flow.
- **Instant Notifications:** Real-time system notifications upon successful client purchases.
- **DDoS Protection:** In-built rate limiting to keep your bot responsive and secure.
- **Docker Ready:** Spin up the entire infrastructure with a single command.
- **Zero-Friction Config:** Easy customization using standard environment variables.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** or **Docker & Docker Compose**
- **pip** (Python package installer, if running natively)
- **Telegram Bot Token** (Get it from [@BotFather](https://t.me/BotFather))
- **Ngrok Credentials** (Temporary requirement for secure webhooks; support for more webhook services coming soon)

### Getting Ngrok Credentials
1. Go to [dashboard.ngrok.com](https://dashboard.ngrok.com/) and log in.
2. Navigate to the **"Your Authtoken"** section in the sidebar.
3. Copy your unique token.

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/touchmeangel/crypto_payment_template_bot.git
cd crypto_payment_template_bot
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory of the project and populate it with your credentials:

```env
# Network and Server Configuration
WEBHOOK_PATH=/tg_bot
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=3000

# Third-party Integrations
NGROK_TOKEN=your_ngrok_authtoken_here
TOKEN=your_telegram_bot_token_here

# RPC Nodes (Pure On-chain Data)
BSC_RPC=https://bsc-dataseed.binance.org/
BASE_RPC=https://mainnet.base.org

# Admin Controls
ADMIN_ID_LIST=[123456789, 987654321]
```

## Usage

### Option A: Using Docker (Recommended)
Deploy everything instantly in an isolated environment. Docker will automatically handle the networking and background processes.
```bash
docker compose up -d
```

### Option B: Using Native Python
If running locally without Docker, ensure your Ngrok tunnel or webhook router is running separately to forward requests to your `WEBAPP_PORT`.
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python run.py
```

## 🤝 Contribution

This project is built for the community. Contributions are highly encouraged, especially if you want to add support for **new chains, tokens, or custom smart contract checks**! 

Feel free to fork the repo, open an issue, or submit a Pull Request. Let's keep crypto decentralized.