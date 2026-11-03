from fastapi.testclient import TestClient

from app.core.config import settings
from main import app


def _login(client: TestClient) -> dict:
    login = client.post("/api/v1/auth/wx-login", json={"code": "demo"})
    assert login.status_code == 200
    body = login.json()
    assert body["code"] == 0
    return {"Authorization": f"Bearer {body['data']['access_token']}"}


def test_demo_login_and_menu_smoke():
    with TestClient(app) as client:
        headers = _login(client)

        response = client.get("/api/v1/menu/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 12
        assert len(data["data"]["items"]) == 12


def test_order_pay_and_pickup_flow():
    payload = {
        "store_id": 1,
        "mode": "pickup",
        "items": [
            {
                "product_id": 3,
                "ice": "少冰",
                "sugar": "五分糖",
                "topping_ids": [],
                "count": 1,
            }
        ],
    }
    with TestClient(app) as client:
        headers = _login(client)

        preview = client.post("/api/v1/orders/price-preview", json=payload, headers=headers)
        assert preview.status_code == 200
        assert preview.json()["code"] == 0

        create_headers = {**headers, "Idempotency-Key": "api-e2e-1"}
        created = client.post("/api/v1/orders", json=payload, headers=create_headers)
        assert created.status_code == 200
        order = created.json()["data"]
        order_no = order["out_trade_no"]
        assert order["state"] == "pending_pay"

        repeated = client.post("/api/v1/orders", json=payload, headers=create_headers)
        assert repeated.status_code == 200
        assert repeated.json()["data"]["out_trade_no"] == order_no

        prepay = client.post(
            "/api/v1/payments/wechat/prepay",
            json={"out_trade_no": order_no},
            headers=headers,
        )
        assert prepay.status_code == 200
        assert prepay.json()["code"] == 0

        notify = client.post(
            "/api/v1/payments/wechat/notify",
            json={"out_trade_no": order_no, "transaction_id": "E2E-TRADE"},
        )
        assert notify.status_code == 200
        assert notify.json()["data"]["state"] == "making"

        detail = client.get(f"/api/v1/orders/{order_no}", headers=headers)
        pick_code = detail.json()["data"]["pick_code"]
        assert pick_code

        original_pin = settings.staff_pin
        settings.staff_pin = "test-pin"
        try:
            lookup = client.post(
                "/api/v1/staff/pickup/lookup",
                json={"code": pick_code, "pin": "test-pin"},
            )
            assert lookup.status_code == 200
            assert lookup.json()["data"]["state"] == "making"

            complete = client.post(
                "/api/v1/staff/pickup/complete",
                json={"code": pick_code, "pin": "test-pin"},
            )
            assert complete.status_code == 200
            assert complete.json()["data"]["state"] == "completed"
        finally:
            settings.staff_pin = original_pin
