import random
from typing import Dict, Any, List
from src.data.in_memory_store import db
import logging

logger = logging.getLogger(__name__)

def get_balance(customer_id: str) -> float:
    logger.info(f"Fetching balance for customerId: {customer_id}")
    return db.customer_balances.get(customer_id, 0.0)

def get_risk_signals(customer_id: str, amount: float) -> Dict[str, Any]:
    logger.info(f"Fetching risk signals for customerId: {customer_id}")
    if "123" in customer_id:
        return {"recent_disputes": 0, "device_change": False}
    if amount > 1000:
        return {"recent_disputes": 1, "device_change": True}
    return {"recent_disputes": random.randint(0, 3), "device_change": random.choice([True, False])}

def create_case(customer_id: str, reasons: List[str]) -> str:
    case_id = f"case_{random.randint(1000, 9999)}"
    logger.info(f"Created case {case_id} for customerId: {customer_id} due to: {reasons}")
    return case_id

def reserve_balance(customer_id: str, amount: float) -> bool:
    """Atomically reserves balance, fulfilling concurrency safety"""
    lock = db.get_balance_lock(customer_id)
    with lock:
        current_balance = db.customer_balances.get(customer_id, 0.0)
        if current_balance >= amount:
            db.customer_balances[customer_id] = current_balance - amount
            logger.info(f"Reserved ${amount} for {customer_id}. New balance: ${db.customer_balances[customer_id]}")
            return True
        else:
            logger.warning(f"Failed to reserve ${amount} for {customer_id}. Insufficient funds.")
            return False