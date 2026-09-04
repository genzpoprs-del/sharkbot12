"""SharkBot Package: Trading assistant and risk management engine."""

from .prompts import SHARKBOT_SYSTEM_PROMPT
from .risk_manager import RiskManager
from .bot import build_application, get_rm, create_gemini_model

__all__ = [
    "SHARKBOT_SYSTEM_PROMPT",
    "RiskManager",
    "build_application",
    "get_rm",
    "create_gemini_model",
]
