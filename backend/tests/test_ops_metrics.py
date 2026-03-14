def test_ops_metrics_requires_authentication(client):
    response = client.get("/ops/metrics")

    assert response.status_code == 401


def test_ops_metrics_report_worker_capacity(client, auth_headers):
    response = client.get("/ops/metrics", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["queued_runs"] == 0
    assert payload["active_runs"] == 0
    assert payload["worker_count"] == 1
    assert payload["queue_max_size"] == 4
