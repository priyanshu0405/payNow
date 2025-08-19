from fastapi import Header, HTTPException, status

def get_idempotency_key(idempotency_key: str = Header(...)) -> str:
    """Dependency to extract and validate the Idempotency-Key from the header."""
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required.",
        )
    return idempotency_key