"""Risk management module for tracking daily drawdowns, PnL, and limits."""

from datetime import date
from typing import Tuple, Dict, Any, List


class RiskManager:
    """Manages trade history, drawdown constraints, and daily rules."""

    def __init__(self, balance: float = 1500.0) -> None:
        self.starting_balance = balance
        self.balance = balance
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.consecutive_losses = 0
        self.trade_log: List[Dict[str, Any]] = []
        self.today = date.today()
        self.daily_loss_limit = balance * 0.04
        self.max_drawdown = balance * 0.08
        self.profit_target = balance * 0.08
        self.risk_per_trade = balance * 0.01
        self.daily_loss_left = self.daily_loss_limit

    def reset_daily(self) -> None:
        """Resets daily performance metrics if a new calendar day has started."""
        if date.today() != self.today:
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.wins_today = 0
            self.losses_today = 0
            self.consecutive_losses = 0
            self.daily_loss_left = self.daily_loss_limit
            self.today = date.today()

    def force_reset(self) -> None:
        """Manually resets daily statistics upon explicit user request."""
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.consecutive_losses = 0
        self.daily_loss_left = self.daily_loss_limit
        self.today = date.today()

    def log_trade(self, pair: str, direction: str, pnl: float, rr: float = 2.0) -> None:
        """Records completed trade and recalculates running balances."""
        self.reset_daily()
        self.balance += pnl
        self.daily_pnl += pnl
        self.total_pnl += pnl
        self.trades_today += 1
        self.daily_loss_left = self.daily_loss_limit - abs(min(self.daily_pnl, 0.0))

        if pnl > 0:
            self.wins_today += 1
            self.consecutive_losses = 0
        else:
            self.losses_today += 1
            self.consecutive_losses += 1

        self.trade_log.append({
            "pair": pair,
            "direction": direction,
            "pnl": pnl,
            "rr": rr,
            "balance_after": self.balance
        })

    def can_trade(self) -> Tuple[bool, str]:
        """Evaluates whether current drawdown parameters permit trade entry."""
        self.reset_daily()
        if self.daily_loss_left <= 15:
            return False, "Daily loss limit reached (75% used). Stop trading."
        if self.consecutive_losses >= 2:
            return False, "2 consecutive losses. Stop for the day."
        if abs(self.daily_pnl) >= self.daily_loss_limit:
            return False, "Max daily loss hit. Stop trading."
        if -self.total_pnl >= self.max_drawdown:
            return False, "Max drawdown breached. Account at risk."
        if self.total_pnl >= self.profit_target:
            return False, "Profit target hit! Consider stopping."
        return True, "Trading allowed"

    def get_status(self) -> Dict[str, Any]:
        """Returns structured dictionary of account metrics."""
        self.reset_daily()
        progress = (self.total_pnl / self.profit_target) * 100 if self.profit_target > 0 else 0
        return {
            "balance": self.balance,
            "daily_pnl": self.daily_pnl,
            "total_pnl": self.total_pnl,
            "daily_loss_left": self.daily_loss_left,
            "progress": max(0.0, progress),
            "trades_today": self.trades_today,
            "wins_today": self.wins_today,
            "losses_today": self.losses_today,
            "consecutive_losses": self.consecutive_losses,
            "win_rate": (self.wins_today / self.trades_today * 100) if self.trades_today > 0 else 0
        }

    def get_report(self) -> str:
        """Formats the current status into a clean summary message."""
        s = self.get_status()
        _, msg = self.can_trade()
        return (
            f"ACCOUNT STATUS\n"
            f"Balance: ${s['balance']:,.2f}\n"
            f"Daily P&L: ${s['daily_pnl']:+,.2f}\n"
            f"Daily Loss Left: ${s['daily_loss_left']:,.2f}\n"
            f"Total P&L: ${s['total_pnl']:+,.2f}\n"
            f"Target Progress: {s['progress']:.1f}%\n"
            f"Trades Today: {s['trades_today']} (W:{s['wins_today']} / L:{s['losses_today']})\n"
            f"Win Rate: {s['win_rate']:.0f}%\n"
            f"Consecutive Losses: {s['consecutive_losses']}\n"
            f"Status: {msg}"
        )
