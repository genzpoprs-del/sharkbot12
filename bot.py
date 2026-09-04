"""Telegram bot handlers and factory methods for SharkBot."""

import io
import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai
from PIL import Image

try:
    from .prompts import SHARKBOT_SYSTEM_PROMPT
    from .risk_manager import RiskManager
except ImportError:
    from prompts import SHARKBOT_SYSTEM_PROMPT
    from risk_manager import RiskManager

load_dotenv()
logger = logging.getLogger(__name__)

user_sessions: Dict[int, RiskManager] = {}


def get_rm(user_id: int, initial_balance: float = 1500.0) -> RiskManager:
    """Retrieves or instantiates a RiskManager session for a Telegram user ID."""
    if user_id not in user_sessions:
        user_sessions[user_id] = RiskManager(balance=initial_balance)
    return user_sessions[user_id]


def create_gemini_model(
    api_key: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    system_instruction: str = SHARKBOT_SYSTEM_PROMPT,
) -> genai.GenerativeModel:
    """Configures and returns a Google Gemini GenerativeModel instance."""
    resolved_key = api_key or os.getenv("GEMINI_API_KEY")
    if not resolved_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable or argument.")
    genai.configure(api_key=resolved_key)
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets user and displays core control commands."""
    user = update.effective_user
    if not user or not update.message:
        return
    rm = get_rm(user.id)
    msg = (
        f"Welcome {user.first_name}!\n"
        f"Account: SharkFunded Bolt $1,500\n"
        f"Balance: ${rm.balance:,.2f}\n"
        f"Daily Loss Left: ${rm.daily_loss_left:,.2f}\n"
        f"Profit Target: ${rm.profit_target:,.2f}\n\n"
        f"Commands:\n"
        f"/signal - Get a trade signal\n"
        f"/balance - Account status\n"
        f"/log - Log trade (e.g., /log XAUUSD BUY 15)\n"
        f"/reset - Reset for new day\n"
        f"/rules - Trading rules\n\n"
        f"Send any chart screenshot for AI analysis!"
    )
    await update.message.reply_text(msg)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Returns current account status and daily limits."""
    if not update.effective_user or not update.message:
        return
    rm = get_rm(update.effective_user.id)
    await update.message.reply_text(rm.get_report())


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prints prop firm compliance rules."""
    if not update.message:
        return
    rules = (
        "SHARKBOT RULES\n"
        "Risk: 1% per trade = $15\n"
        "Min RR: 1:2\n"
        "Sessions: London 2-5 AM EST | NY 7-10 AM EST\n"
        "No trading: News, weekends, dead zones\n\n"
        "STOP if:\n"
        "- 2 losses in a row\n"
        "- Daily loss hits $45 (75% of limit)\n"
        "- Max drawdown $120 reached\n\n"
        "Targets:\n"
        "- Daily loss limit: $60\n"
        "- Max drawdown: $120\n"
        "- Profit target: $120 (8%)"
    )
    await update.message.reply_text(rules)


async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates an entry setup suggestion using Gemini."""
    if not update.effective_user or not update.message:
        return
    rm = get_rm(update.effective_user.id)
    can_trade, msg = rm.can_trade()
    if not can_trade:
        await update.message.reply_text(f"🛑 Trading Disabled: {msg}")
        return

    user_request = " ".join(context.args) if context.args else "XAUUSD (Gold) - find me an A+ setup right now"
    prompt = (
        f"User is asking for a signal on: {user_request}\n\n"
        f"Current account status:\n"
        f"- Balance: ${rm.balance:,.2f}\n"
        f"- Daily P&L: ${rm.daily_pnl:+,.2f}\n"
        f"- Daily loss left: ${rm.daily_loss_left:,.2f}\n\n"
        f"Give the signal using the exact format from your instructions."
    )

    try:
        await update.message.reply_text("Analyzing market setup...")
        model = context.bot_data.get("gemini_model") or create_gemini_model()
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as exc:
        logger.error("Signal error: %s", exc)
        await update.message.reply_text(f"Error generating signal: {str(exc)}")


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs trade results and recalculates parameters."""
    if not update.effective_user or not update.message:
        return
    rm = get_rm(update.effective_user.id)
    try:
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "Usage: /log PAIR DIRECTION PNL [RR]\n"
                "Example: /log XAUUSD BUY 22.50\n"
                "Example: /log EURUSD SELL -15.00"
            )
            return

        pair = context.args[0].upper()
        direction = context.args[1].upper()
        pnl = float(context.args[2])
        rr = float(context.args[3]) if len(context.args) >= 4 else 2.0

        rm.log_trade(pair, direction, pnl, rr)
        await update.message.reply_text(
            f"✅ Trade logged:\n"
            f"Pair: {pair} | Direction: {direction}\n"
            f"P&L: ${pnl:+,.2f}\n\n"
            f"{rm.get_report()}"
        )
    except ValueError:
        await update.message.reply_text("Invalid numeric values. Example: /log XAUUSD BUY 15.00")
    except Exception as exc:
        logger.error("Log error: %s", exc)
        await update.message.reply_text(f"Error logging trade: {str(exc)}")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually resets the daily tracking metrics."""
    if not update.effective_user or not update.message:
        return
    rm = get_rm(update.effective_user.id)
    rm.force_reset()
    await update.message.reply_text("🔄 Daily metrics reset:\n\n" + rm.get_report())


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes uploaded chart screenshots using multimodal prompt."""
    if not update.effective_user or not update.message or not update.message.photo:
        return
    rm = get_rm(update.effective_user.id)
    can_trade, msg = rm.can_trade()
    if not can_trade:
        await update.message.reply_text(f"🛑 Trading Disabled: {msg}")
        return

    try:
        await update.message.reply_text("📥 Downloading and analyzing chart...")
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))

        prompt = [
            image,
            (
                "Analyze this trading chart. Evaluate market structure, liquidity sweeps, and fair value gaps. "
                f"Account: Balance ${rm.balance:,.2f}, Max daily loss remaining ${rm.daily_loss_left:,.2f}. "
                "Produce an entry signal if an A+ setup is visible, or state NO TRADE."
            ),
        ]

        model = context.bot_data.get("gemini_model") or create_gemini_model()
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as exc:
        logger.error("Photo handler error: %s", exc)
        await update.message.reply_text(f"Failed to analyze image: {str(exc)}")


def build_application(
    telegram_token: Optional[str] = None,
    gemini_key: Optional[str] = None
) -> Application:
    """Constructs and returns the configured python-telegram-bot Application."""
    token = telegram_token or os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("Missing TELEGRAM_TOKEN.")

    model = create_gemini_model(gemini_key)

    app = Application.builder().token(token).build()
    app.bot_data["gemini_model"] = model

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("rules", rules_command))
    app.add_handler(CommandHandler("log", log_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    return app


def main() -> None:
    """Runs the polling loop when executed directly as a script."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger.info("Initializing SharkBot...")
    application = build_application()
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
