from pydantic import BaseModel, Field
from uuid import UUID

class PaymentRequest(BaseModel):
    correlationId: UUID
    amount: float = Field(..., gt=0)

class PaymentSummary(BaseModel):
    totalRequests: int
    totalAmount: float

class PaymentSummaryResponse(BaseModel):
    default: PaymentSummary
    fallback: PaymentSummary

class HealthStatus(BaseModel):
    failing: bool
    minResponseTime: int