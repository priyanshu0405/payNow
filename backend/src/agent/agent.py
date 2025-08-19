from typing import List, Tuple, Dict, Any, Callable
from .tools import get_balance, get_risk_signals, create_case, reserve_balance
from src.models.payment import AgentTraceStep, Decision
import logging

logger = logging.getLogger(__name__)

class PaymentAgent:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.trace: List[AgentTraceStep] = []

    def _add_trace(self, step: str, detail: str):
        self.trace.append(AgentTraceStep(step=step, detail=detail))

    def _call_tool_with_retry(self, tool: Callable, *args, **kwargs) -> Any:
        """Calls a tool with a simple retry mechanism"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                result = tool(*args, **kwargs)
                self._add_trace(f"tool:{tool.__name__}", f"Success. Result: {result}")
                return result
            except Exception as e:
                logger.error(f"Tool {tool.__name__} failed on attempt {attempt+1}: {e}")
                if attempt == max_retries:
                    self._add_trace(f"tool:{tool.__name__}", f"Failed after {max_retries+1} attempts.")
                    raise
        return None

    def _evaluate_rules(self, amount: float, balance: float, risk_signals: Dict[str, Any]) -> Tuple[Decision, List[str]]:
        reasons = []
        if amount > balance:
            return Decision.BLOCK, ["insufficient_funds"]

        if risk_signals.get("recent_disputes", 0) > 1:
            reasons.append("recent_disputes")
        if amount > 1000:
            reasons.append("amount_above_daily_threshold")
        if risk_signals.get("device_change", False):
            reasons.append("unrecognized_device")

        if reasons:
            return Decision.REVIEW, reasons

        return Decision.ALLOW, []

    def run(self, customer_id: str, amount: float) -> Tuple[Decision, List[str], List[AgentTraceStep]]:
        self._add_trace("plan", "Check balance, assess risk, and execute decision.")

        balance = self._call_tool_with_retry(get_balance, customer_id=customer_id)
        if balance is None:
            return Decision.BLOCK, ["internal_error_balance_check"], self.trace

        risk_signals = self._call_tool_with_retry(get_risk_signals, customer_id=customer_id, amount=amount)
        if risk_signals is None:
            return Decision.BLOCK, ["internal_error_risk_check"], self.trace

        decision, reasons = self._evaluate_rules(amount, balance, risk_signals)
        self._add_trace("decision", f"Determined decision: {decision} with reasons: {reasons}")

        if decision == Decision.ALLOW:
            success = self._call_tool_with_retry(reserve_balance, customer_id=customer_id, amount=amount)
            if not success:
                return Decision.BLOCK, ["insufficient_funds_on_reserve"], self.trace
        elif decision in [Decision.REVIEW, Decision.BLOCK]:
            self._call_tool_with_retry(create_case, customer_id=customer_id, reasons=reasons)

        return decision, reasons, self.trace