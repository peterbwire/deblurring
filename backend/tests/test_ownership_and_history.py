from tests.helpers import make_test_image_bytes


def test_recent_jobs_are_scoped_to_authenticated_owner(client, auth_headers, other_auth_headers):
    upload_response = client.post(
        "/upload",
        headers=auth_headers,
        files={"file": ("owned.png", make_test_image_bytes(), "image/png")},
    )
    assert upload_response.status_code == 200

    analyst_history = client.get("/auth/jobs", headers=auth_headers)
    reviewer_history = client.get("/auth/jobs", headers=other_auth_headers)

    assert analyst_history.status_code == 200
    assert reviewer_history.status_code == 200
    assert len(analyst_history.json()["items"]) == 1
    assert reviewer_history.json()["items"] == []


def test_run_status_is_not_visible_to_other_owner(client, auth_headers, other_auth_headers, monkeypatch):
    upload_response = client.post(
        "/upload",
        headers=auth_headers,
        files={"file": ("owned.png", make_test_image_bytes(), "image/png")},
    )
    job_id = upload_response.json()["job_id"]

    from app.routes import process as process_route

    monkeypatch.setattr(process_route, "submit_run", lambda *args, **kwargs: None)

    process_response = client.post(
        f"/process/{job_id}",
        headers=auth_headers,
        json={
            "denoise_strength": "medium",
            "deblur_mode": "standard",
            "sharpen_edges": True,
            "upscale": "none",
            "evidence_safe": True,
        },
    )
    assert process_response.status_code == 200
    run_id = process_response.json()["run_id"]

    owner_status = client.get(f"/process/{job_id}/{run_id}", headers=auth_headers)
    other_status = client.get(f"/process/{job_id}/{run_id}", headers=other_auth_headers)

    assert owner_status.status_code == 200
    assert other_status.status_code == 404
