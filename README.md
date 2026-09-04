# 🦈 SharkBot — AI Trading & Prop Firm Risk Manager

An institutional-grade Telegram trading assistant powered by **Google Gemini 1.5 Flash** and built with **`python-telegram-bot`**. Tailored specifically for prop firm challenges (defaulted to the SharkFunded Bolt $1,500 account), SharkBot enforces strict risk management rules, delivers Killzone liquidity sweep signals, and analyzes user-uploaded chart screenshots via multimodal vision.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Prop Firm Account Specifications](#-prop-firm-account-specifications)
- [Project Architecture](#-project-architecture)
- [Bot Commands](#-bot-commands)
- [Prerequisites](#-prerequisites)
- [Local Installation & Setup](#-local-installation--setup)
- [Importing as a Python Package](#-importing-as-a-python-package)
- [Cloud Deployment](#-cloud-deployment)
  - [Heroku](#heroku)
  - [Render](#render)
  - [Railway](#railway)
- [Security Best Practices](#-security-best-practices)
- [License](#-license)

---

## ⚡ Key Features

- **Automated Prop Risk Guardrails:** Halts trading when daily loss limits ($60 / 4%), consecutive losses (2 in a row), or total maximum drawdown ($120 / 8%) are reached.
- **Multimodal Chart Analysis:** Upload any candlestick chart screenshot directly in Telegram for instant structure, liquidity sweep, and Fair Value Gap (FVG) breakdown.
- **ICT / Smart Money Concepts Strategy:** Dedicated prompts fine-tuned for London (02:00–05:00 EST) and New York (07:00–10:00 EST) Killzones.
- **Interactive Trade Logging:** Log trades with `/log` to dynamically update win rate, consecutive loss counters, and remaining loss buffers.
- **Clean Modular Design:** Can be executed standalone or imported cleanly into other Python systems, backtesters, or dashboards without side effects.

---

## 🎯 Prop Firm Account Specifications

| Parameter | Rule / Limit | Value ($1,500 Account) |
| :--- | :--- | :--- |
| **Account Size** | Initial Balance | `$1,500.00` |
| **Max Daily Loss** | 4.0% | `$60.00` |
| **Soft Daily Circuit Breaker** | 75% of Daily Loss Limit | `$45.00` |
| **Max Trailing Drawdown** | 8.0% | `$120.00` |
| **Profit Target** | 8.0% | `$120.00` |
| **Max Risk per Trade** | 1.0% | `$15.00` |
| **Minimum Risk-to-Reward (RR)** | 1:2 | TP1: 1:2 (50% BE), TP2: 1:3 |
| **Consecutive Loss Cutoff** | Max 2 consecutive losses | Halts bot for the calendar day |
| **Killzones** | London / New York | `02:00–05:00 EST` & `07:00–10:00 EST` |

---

## 📂 Project Architecture

```text
sharkbot/
├── __init__.py           # Package exports for clean imports
├── bot.py                # Telegram handlers, factory builder, and polling loop
├── prompts.py            # System prompts & structured signal formats
├── risk_manager.py       # Core balance, PnL, and drawdown tracking logic
├── requirements.txt      # Pinned production dependencies
├── Procfile              # Worker specification for Heroku / Railway / Render
├── runtime.txt           # Python runtime version pinning
├── .env.example          # Environment variable template
└── README.md             # Project documentation
```

---

## 🤖 Bot Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `/start` | Initializes your session and prints the welcome status dashboard | `/start` |
| `/signal [query]` | Generates an ICT-compliant signal for the instrument | `/signal XAUUSD London Killzone` |
| `/balance` | Displays daily P&L, balance, remaining risk, and win rate | `/balance` |
| `/rules` | Displays SharkFunded trading rules and risk limits | `/rules` |
| `/log <PAIR> <DIR> <PNL> [RR]` | Logs a trade and updates risk thresholds | `/log EURUSD BUY 30.00 2.0` |
| `/reset` | Manually resets daily metrics for a fresh trading day | `/reset` |
| *Send Photo* | Uploading a chart screenshot triggers Gemini Multimodal analysis | *Attach image with or without caption* |

---

## 🛠 Prerequisites

- **Python 3.11+** installed on your system.
- A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather).
- A **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/sharkbot.git
cd sharkbot
```

### 2. Create and Activate a Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your actual credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
```

### 5. Run the Bot
```bash
python bot.py
```

---

## 📦 Importing as a Python Package

The codebase is engineered to be fully importable and modular without executing side-effects on import:

```python
from sharkbot import RiskManager, build_application, create_gemini_model

# 1. Use the Risk Engine in custom scripts or backtests
rm = RiskManager(balance=1500.0)
rm.log_trade(pair="XAUUSD", direction="BUY", pnl=30.0, rr=2.0)
can_trade, reason = rm.can_trade()
print(f"Can trade: {can_trade} | Status: {reason}")
print(rm.get_report())

# 2. Spin up an instance of the Telegram Application programmatically
app = build_application(
    telegram_token="YOUR_TELEGRAM_TOKEN",
    gemini_key="YOUR_GEMINI_KEY"
)
# app.run_polling()
```

---

## ☁️ Cloud Deployment

### Heroku
1. Create a new app on [Heroku](https://heroku.com).
2. Connect your GitHub repository.
3. In **Settings** → **Config Vars**, add:
   - `TELEGRAM_TOKEN` = `your_telegram_bot_token`
   - `GEMINI_API_KEY` = `your_gemini_api_key`
4. Under the **Resources** tab, disable the `web` dyno and enable the `worker: python -m bot` dyno.

### Render
1. Create a new **Background Worker** on [Render](https://render.com).
2. Connect your repository.
3. Set the following:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
4. Under **Environment Variables**, add `TELEGRAM_TOKEN` and `GEMINI_API_KEY`.

### Railway
1. Click **New Project** → **Deploy from GitHub repo** on [Railway](https://railway.app).
2. Add your environment variables (`TELEGRAM_TOKEN`, `GEMINI_API_KEY`).
3. Railway automatically detects the `Procfile` and launches the worker.

---

## 🔒 Security Best Practices

- **Never commit `.env` or credentials:** `.env` should always be included in `.gitignore`.
- **Stateless Warning:** Current session tracking resides in-memory (`user_sessions`). For multi-instance horizontal scaling, connect a persistent datastore such as Redis or PostgreSQL.
- **Rate Limits:** Google Gemini API free tiers have requests-per-minute (RPM) quotas. For high-volume production groups, monitor quota utilization.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.
