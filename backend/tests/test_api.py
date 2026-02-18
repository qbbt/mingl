from datetime import datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _create_entity(name: str) -> int:
    created = client.post(
        "/entities",
        json={"name": name, "entity_type": "generic", "contributor_type": "manual", "weight": 1.0},
    )
    if created.status_code == 200:
        return created.json()["id"]
    if created.status_code == 409:
        entities = client.get("/entities").json()
        for e in entities:
            if e["name"] == name:
                return e["id"]
    raise AssertionError(f"unable to create/find entity {name}")


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_graph_indicator_and_topn_flow() -> None:
    a = _create_entity(f"MEAL-{datetime.utcnow().timestamp()}")
    b = _create_entity(f"TRADE-{datetime.utcnow().timestamp()}")

    now = datetime.utcnow()
    for i in range(10):
        t = now - timedelta(minutes=10 - i)
        client.post(
            "/observations",
            json={
                "entity_id": a,
                "timestamp": t.isoformat(),
                "value": 400 + i * 50,
                "metric_name": "calories",
                "source_url": f"https://example.local/meal/{i}.jpg",
            },
        )
        client.post(
            "/observations",
            json={
                "entity_id": b,
                "timestamp": t.isoformat(),
                "value": 1 + (i // 3),
                "metric_name": "trade_count",
            },
        )

    graph = client.get(f"/graph/series?entity_id={a}&metric_name=calories&limit=100")
    assert graph.status_code == 200
    assert len(graph.json()) >= 10

    ind = client.get(f"/indicators/sma?entity_id={a}&metric_name=calories&window=3")
    assert ind.status_code == 200
    assert ind.json()["indicator"] == "sma"

    pair = client.get(f"/correlations/pair?entity_a_id={a}&entity_b_id={b}&lookback_points=10")
    assert pair.status_code == 200
    assert "correlation" in pair.json()

    top = client.get(f"/relationships/top?entity_id={a}&top_n=3")
    assert top.status_code == 200


def test_orders_notifications_and_demo_seed() -> None:
    seed = client.post("/demo/seed")
    assert seed.status_code == 200

    flow = client.post("/demo/meal-trade-flow")
    assert flow.status_code == 200

    order = client.post("/orders/paper", json={"symbol": "AAPL", "side": "BUY", "quantity": 1})
    assert order.status_code == 200
    assert order.json()["status"] == "paper_filled"

    process = client.post("/notifications/outbox/process?limit=5")
    assert process.status_code == 200
    assert "attempted" in process.json()


def test_analytics_and_status_routes() -> None:
    seed = client.post("/demo/meal-trade-flow")
    assert seed.status_code == 200
    payload = seed.json()
    meal_id = payload["meal_entity_id"]
    trade_id = payload["trade_entity_id"]

    status = client.get("/status")
    assert status.status_code == 200
    assert status.json()["version"] == "v1.5-optimizer"

    wave = client.get(f"/analytics/wave/{meal_id}?metric_name=calories")
    assert wave.status_code == 200
    assert "series" in wave.json()

    lag = client.get(
        f"/analytics/lag_sweep?entity_a_id={meal_id}&entity_b_id={trade_id}&metric_a=calories&metric_b=trade_count&max_lag_days=7"
    )
    assert lag.status_code == 200
    assert "best_lag" in lag.json()

    matrix = client.get(f"/analytics/correlations/matrix?entity_ids={meal_id},{trade_id}&metric_name=calories")
    assert matrix.status_code == 200
    assert matrix.json()["heatmap_ready"] is True

    media = client.post(
        "/analytics/media/sync",
        json={
            "media_url": "https://example.local/test.mp3",
            "current_audio_sec": 12.5,
            "entities": ["MEAL-CALORIES", "TRADES-AFTER-MEAL"],
        },
    )
    assert media.status_code == 200
    assert media.json()["status"] == "ready_for_mp3_overlay"
