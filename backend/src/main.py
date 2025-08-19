import time
import uuid
from fastapi import FastAPI, Depends, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from src.models.payment import PaymentRequest, PaymentResponse, Decision
from src.core.security import get_api_key
from src.core.dependencies import get_idempotency_key
from src.agent.agent import PaymentAgent
from src.utils.logger import setup_logging, request_id_var, logger
from src.data.in_memory_store import db, TokenBucket

setup_logging()
app = FastAPI()

# Allow CORS for the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


METRICS = {
    "total_requests": 0,
    "decision_counts": {"allow": 0, "review": 0, "block": 0},
    "latencies": []
}

RATE_LIMIT_CAPACITY = 5
RATE_LIMIT_REFILL_RATE = 5.0

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    start_time = time.monotonic()
    response = await call_next(request)
    process_time = (time.monotonic() - start_time) * 1000

    if request.url.path == "/payments/decide":
        METRICS["latencies"].append(process_time)
        METRICS["total_requests"] += 1

    response.headers["X-Request-Id"] = request_id
    return response

@app.post(
    "/payments/decide",
    response_model=PaymentResponse,
    dependencies=[Depends(get_api_key)]
)
async def decide_payment(
    request: PaymentRequest,
    idempotency_key: str = Depends(get_idempotency_key)
):
    logger.info(f"Request received: Body: {request.model_dump()}")

    customer_id = request.customerId
    if customer_id not in db.rate_limit_buckets:
        db.rate_limit_buckets[customer_id] = TokenBucket(
            RATE_LIMIT_CAPACITY, RATE_LIMIT_REFILL_RATE
        )

    bucket = db.rate_limit_buckets[customer_id]
    if not bucket.consume():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this customer.",
        )

    if idempotency_key in db.idempotency_requests:
        status_code, stored_response = db.idempotency_requests[idempotency_key]
        logger.info(f"Returning idempotent response for key: {idempotency_key}")
        return JSONResponse(content=stored_response, status_code=status_code)

    request_id = request_id_var.get()

    agent = PaymentAgent(request_id=request_id)
    decision, reasons, trace = agent.run(
        customer_id=request.customerId,
        amount=request.amount
    )

    response_data = PaymentResponse(
        decision=decision,
        reasons=reasons,
        agentTrace=trace,
        requestId=request_id
    )

    METRICS["decision_counts"][decision.value] += 1

    db.idempotency_requests[idempotency_key] = (status.HTTP_200_OK, response_data.model_dump())

    return response_data

@app.get("/metrics")
async def get_metrics():
    latencies = sorted(METRICS["latencies"])
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    return {
        "total_requests": METRICS["total_requests"],
        "decision_counts": METRICS["decision_counts"],
        "p95_latency_ms": round(p95, 2)
    }