from tests.helpers import make_test_image_bytes


def test_upload_requires_authentication(client):
    response = client.post(
        "/upload",
        files={"file": ("sample.png", make_test_image_bytes(), "image/png")},
    )

    assert response.status_code == 401


def test_upload_returns_owned_metadata_and_signed_preview(client, auth_headers):
    response = client.post(
        "/upload",
        headers=auth_headers,
        files={"file": ("sample.png", make_test_image_bytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["sha256"]
    assert payload["width"] == 96
    assert payload["height"] == 64
    assert "/preview/original/" in payload["original_url"]

    preview_response = client.get(payload["original_url"])
    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"].startswith("image/")
