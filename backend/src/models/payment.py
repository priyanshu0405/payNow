from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Any

class Decision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"

class PaymentRequest(BaseModel):
    customerId: str
    amount: float = Field(..., gt=0)
    currency: str
    payeeId: str

class AgentTraceStep(BaseModel):
    step: str
    detail: str

class PaymentResponse(BaseModel):
    decision: Decision
    reasons: List[str]
    agentTrace: List[AgentTraceStep]
    requestId: str