from fastapi import FastAPI, HTTPException

from backend.schemas import (
    ShoppingIntent,
    PurchaseRequest,
    PurchaseResponse,
)

from backend.services.parser import parse_shopping_request
from backend.services.catalog import (
    get_products,
    get_product_by_id,
)
from backend.services.agent import search_and_rank_products
from backend.services.delegation import (
    issue_token,
    verify_token,
    mark_used,
)
from backend.services.security import check_policy
from backend.services.payments import DemoPaymentGateway


app = FastAPI(title="BuyAgent")

payment_gateway = DemoPaymentGateway()


@app.get("/")
def home():
    return {
        "message": "BuyAgent is running!"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "buyagent"
    }


@app.post(
    "/api/parse",
    response_model=ShoppingIntent,
)
def parse_intent(request: dict):
    return parse_shopping_request(
        request["text"]
    )


@app.post("/api/search")
def search_products(
    intent: ShoppingIntent,
):
    products = get_products()

    ranked_products = search_and_rank_products(
        products,
        intent,
    )

    return ranked_products


@app.post("/api/delegation")
def create_delegation(request: dict):
    policy = request["policy"]

    token = issue_token(policy)

    return {
        "status": "created",
        "delegation_token": token,
    }


@app.post(
    "/api/purchase",
    response_model=PurchaseResponse,
)
def purchase(request: PurchaseRequest):

    # 1. Verify delegation token
    try:
        token_payload = verify_token(
            request.delegation_token
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    # 2. Verify that the token belongs
    #    to the requesting user
    if token_payload["user_id"] != request.user_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Delegation token does not "
                "belong to this user"
            ),
        )

    # 3. Find the product
    product = get_product_by_id(
        request.product_id
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    # 4. Check the delegated spending policy
    allowed, message = check_policy(
        product,
        token_payload,
        request.approved,
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=message,
        )

    # 5. Calculate total cost
    total = round(
        product.price + product.shipping,
        2,
    )

    # 6. Process simulated payment
    payment_result = payment_gateway.charge(
        amount=total,
        currency=token_payload.get(
            "currency",
            "USD",
        ),
    )

    # 7. Mark delegation token as used
    mark_used(token_payload)

    # 8. Return purchase result
    return PurchaseResponse(
        status="success",
        message=payment_result["message"],
        order_id=payment_result["transaction_id"],
        charged_total=payment_result["amount"],
        currency=payment_result["currency"],
    )