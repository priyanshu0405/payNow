from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings
import time
import uuid

client = TestClient(app)

HEADERS = {
    "X-API-Key": settings.API_KEY,
    "Idempotency-Key": str(uuid.uuid4())
}

def test_decide_payment_allow():
    request_body = {
        "customerId": "c_123", "amount": 100.50, "currency": "USD", "payeeId": "p_789"
    }
    response = client.post("/payments/decide", json=request_body, headers={**HEADERS, "Idempotency-Key": str(uuid.uuid4())})
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "allow"

def test_decide_payment_review():
    request_body = {
        "customerId": "c_456", "amount": 1500.00, "currency": "USD", "payeeId": "p_789"
    }
    response = client.post("/payments/decide", json=request_body, headers={**HEADERS, "Idempotency-Key": str(uuid.uuid4())})
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "review"
    assert "amount_above_daily_threshold" in data["reasons"]

def test_idempotency():
    idempotency_key = str(uuid.uuid4())
    request_body = {
        "customerId": "c_123", "amount": 10.0, "currency": "USD", "payeeId": "p_456"
    }
    headers = {"X-API-Key": settings.API_KEY, "Idempotency-Key": idempotency_key}

    response1 = client.post("/payments/decide", json=request_body, headers=headers)
    assert response1.status_code == 200
    data1 = response1.json()

    response2 = client.post("/payments/decide", json=request_body, headers=headers)
    assert response2.status_code == 200
    data2 = response2.json()

    assert data1 == data2

def test_rate_limiter():
    customer_id = f"c_ratelimit_{time.time()}"
    request_body = {"customerId": customer_id, "amount": 5.0, "currency": "USD", "payeeId": "p_111"}

    for i in range(5):
        headers = {**HEADERS, "Idempotency-Key": str(uuid.uuid4())}
        response = client.post("/payments/decide", json=request_body, headers=headers)
        assert response.status_code == 200

    headers = {**HEADERS, "Idempotency-Key": str(uuid.uuid4())}
    response = client.post("/payments/decide", json=request_body, headers=headers)
    assert response.status_code == 429