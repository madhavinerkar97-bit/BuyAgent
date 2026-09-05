import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="BuyAgent",
    page_icon="🛍️",
    layout="wide",
)

st.title("🛍️ BuyAgent")
st.subheader("Personal Shopping Assistant with Delegated Payments")

st.write(
    "Tell BuyAgent what you want to buy. "
    "The agent searches, ranks products, "
    "and uses a limited delegated payment authorization."
)

st.header("1. What do you want to buy?")

shopping_request = st.text_area(
    "Shopping request",
    value="Find trail running shoes under $120 with heel support",
    height=100,
)

if st.button("🔎 Find Products"):

    if not shopping_request.strip():
        st.warning("Please enter a shopping request.")
        st.stop()

    try:
        parse_response = requests.post(
            f"{API_URL}/api/parse",
            json={"text": shopping_request},
            timeout=10,
        )

        parse_response.raise_for_status()
        intent = parse_response.json()

        st.session_state["intent"] = intent

        search_response = requests.post(
            f"{API_URL}/api/search",
            json=intent,
            timeout=10,
        )

        search_response.raise_for_status()
        st.session_state["products"] = search_response.json()

    except requests.RequestException as exc:
        st.error(f"Could not connect to BuyAgent API: {exc}")


if "intent" in st.session_state:

    intent = st.session_state["intent"]

    st.header("2. Detected Shopping Intent")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Product Type", intent["product_type"])

    with col2:
        budget = intent.get("budget")

        if budget is not None:
            st.metric("Budget", f"${budget:.2f}")
        else:
            st.metric("Budget", "Not specified")

    with col3:
        st.metric("Currency", intent["currency"])

    if intent["must_have"]:
        st.write(
            "**Must-have:** "
            + ", ".join(intent["must_have"])
        )

    if intent["preferred"]:
        st.write(
            "**Preferred:** "
            + ", ".join(intent["preferred"])
        )


if "products" in st.session_state:

    products = st.session_state["products"]

    st.header("3. Ranked Products")

    if not products:
        st.warning("No products were found.")
        st.stop()

    for index, item in enumerate(products):

        product = item["product"]
        score = item["score"]

        st.subheader(
            f"{index + 1}. {product['title']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write(
                f"**Price:** ${product['price']:.2f}"
            )

        with col2:
            st.write(
                f"**Shipping:** ${product['shipping']:.2f}"
            )

        with col3:
            total = product["price"] + product["shipping"]
            st.write(f"**Total:** ${total:.2f}")

        with col4:
            st.write(
                f"**Rating:** ⭐ {product['rating']}"
            )

        st.write(
            f"**Merchant:** {product['merchant']}"
        )

        st.write(
            f"**Return policy:** "
            f"{product['return_days']} days"
        )

        st.write(
            f"**Heel support:** "
            f"{'Yes' if product['heel_support'] else 'No'}"
        )

        st.write(
            f"**Agent score:** {score}"
        )

        st.write(product["description"])

        st.divider()


st.header("4. Delegated Purchase")

st.write(
    "The payment authorization is limited by a "
    "maximum amount, category, expiration, and "
    "single-use token."
)

user_id = st.text_input(
    "User ID",
    value="demo-user",
)


if "products" in st.session_state:

    products = st.session_state["products"]

    product_options = {}

    for item in products:
        product = item["product"]

        label = (
            f"{product['title']} — "
            f"${product['price'] + product['shipping']:.2f} "
            f"— {product['merchant']}"
        )

        product_options[label] = product

    selected_label = st.selectbox(
        "Choose a product",
        list(product_options.keys()),
    )

    selected_product = product_options[selected_label]

    st.write(
        f"Selected product: "
        f"**{selected_product['title']}**"
    )

    total = (
        selected_product["price"]
        + selected_product["shipping"]
    )

    st.write(f"Total cost: **${total:.2f}**")

    approval = st.checkbox(
        "I approve this purchase"
    )

    if st.button("🔐 Create Delegation & Purchase"):

        if not approval:
            st.warning(
                "Please approve the purchase first."
            )
            st.stop()

        policy = {
            "user_id": user_id,
            "max_total": 120,
            "currency": "USD",
            "allowed_merchants": [],
            "allowed_category": selected_product["category"],
            "expires_at": "1893456000",
            "single_use": True,
            "require_human_above": 120,
        }

        try:

            delegation_response = requests.post(
                f"{API_URL}/api/delegation",
                json={"policy": policy},
                timeout=10,
            )

            delegation_response.raise_for_status()

            token = delegation_response.json()[
                "delegation_token"
            ]

            purchase_response = requests.post(
                f"{API_URL}/api/purchase",
                json={
                    "user_id": user_id,
                    "product_id": selected_product["id"],
                    "delegation_token": token,
                    "approved": True,
                },
                timeout=10,
            )

            purchase_response.raise_for_status()

            purchase_data = purchase_response.json()

            st.success(
                "🎉 Purchase completed successfully!"
            )

            st.json(purchase_data)

        except requests.HTTPError as exc:

            try:
                error_data = purchase_response.json()

                st.error(
                    error_data.get(
                        "detail",
                        str(exc),
                    )
                )

            except Exception:
                st.error(str(exc))

        except requests.RequestException as exc:
            st.error(f"BuyAgent API error: {exc}")