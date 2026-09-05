from typing import List, Optional

from pydantic import BaseModel, Field


class ShoppingIntent(BaseModel):
    raw_text: str
    product_type: str
    budget: Optional[float] = None
    currency: str = "USD"
    must_have: List[str] = Field(default_factory=list)
    preferred: List[str] = Field(default_factory=list)
    max_delivery_days: Optional[int] = None
    allowed_merchants: List[str] = Field(default_factory=list)
    approval_required_above: Optional[float] = None


class Product(BaseModel):
    id: str
    merchant: str
    title: str
    category: str
    price: float
    shipping: float = 0
    rating: float = 0
    return_days: int = 0
    weight_grams: Optional[int] = None
    heel_support: bool = False
    stock: bool = True
    description: str = ""


class DelegationPolicy(BaseModel):
    user_id: str
    max_total: float
    currency: str = "USD"
    allowed_merchants: List[str] = Field(default_factory=list)
    allowed_category: Optional[str] = None
    expires_at: str
    single_use: bool = True
    require_human_above: Optional[float] = None


class CreateDelegationRequest(BaseModel):
    policy: DelegationPolicy


class PurchaseRequest(BaseModel):
    user_id: str
    product_id: str
    delegation_token: str
    approved: bool = False


class PurchaseResponse(BaseModel):
    status: str
    message: str
    order_id: Optional[str] = None
    charged_total: Optional[float] = None
    currency: str = "USD"