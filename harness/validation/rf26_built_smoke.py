"""Nonvisual RF-26 smoke against the disposable review Compose project only."""

import io
import json
import time
import uuid
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

from PIL import Image

API = "http://127.0.0.1:18004/api"
FRONTEND = "http://localhost:14177"
PASSWORD = "rf26-disposable-test-password"


class Client:
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, method, path, data=None, *, headers=None, expected=200, raw=None):
        body = json.dumps(data).encode() if data is not None else raw
        request_headers = {"Origin": FRONTEND, **(headers or {})}
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        request = Request(API + path, data=body, headers=request_headers, method=method)
        try:
            response = self.opener.open(request, timeout=15)
        except HTTPError as error:
            response = error
        content = response.read()
        assert response.status == expected, (
            path,
            response.status,
            expected,
            content[:200],
        )
        if path.endswith("/entry"):
            assert response.headers["Cache-Control"] == "private, no-store"
            assert response.headers["Referrer-Policy"] == "no-referrer"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(content)
        return content

    def json(self, method, path, data=None, **kwargs):
        return self.request(method, path, data, **kwargs)


def wait_ready():
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            with urlopen(API + "/ready", timeout=3) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(1)
    raise AssertionError("Disposable review backend did not become ready")


def publish(client, audience):
    session = client.json("POST", "/photo-upload-sessions", expected=201)["id"]
    images = []
    for index in range(2):
        image = io.BytesIO()
        Image.new("RGB", (64, 64), (180, 40 + index * 30, 40)).save(
            image, format="JPEG"
        )
        boundary = uuid.uuid4().hex
        body = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="attempt_id"\r\n\r\n'
                f"{uuid.uuid4()}\r\n--{boundary}\r\n"
                'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
                "Content-Type: image/jpeg\r\n\r\n"
            ).encode()
            + image.getvalue()
            + f"\r\n--{boundary}--\r\n".encode()
        )
        uploaded = client.json(
            "POST",
            f"/photo-upload-sessions/{session}/images",
            raw=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            expected=201,
        )
        images.append(uploaded["id"])
    return client.json(
        "POST",
        "/consultations",
        {
            "session_id": session,
            "ordered_image_ids": images,
            "question": f"RF26 {audience} choice?",
            "context": "direct-entry smoke",
            "audience": audience,
        },
        expected=201,
    )["id"]


def main():
    wait_ready()
    owner, reader, anonymous = Client(), Client(), Client()
    suffix = uuid.uuid4().hex[:8]
    owner.json(
        "POST",
        "/accounts",
        {"email": f"owner{suffix}@example.com", "alias": "Owner", "password": PASSWORD},
        expected=201,
    )
    reader.json(
        "POST",
        "/accounts",
        {
            "email": f"reader{suffix}@example.com",
            "alias": "Reader",
            "password": PASSWORD,
        },
        expected=201,
    )

    public_id = publish(owner, "public")
    private_id = publish(owner, "private")
    token = owner.json("GET", f"/consultations/{private_id}/private-link")["token"]

    direct_path = f"/consultations/{public_id}"
    with urlopen(FRONTEND + direct_path, timeout=10) as response:
        assert response.status == 200 and b'type="module"' in response.read()

    anonymous.request("GET", f"/consultations/{public_id}/entry", expected=401)
    assert owner.json("GET", f"/consultations/{public_id}/entry") == {"role": "owner"}
    assert reader.json("GET", f"/consultations/{public_id}/entry") == {"role": "reader"}

    private_entry = f"/consultations/{private_id}/entry"
    reader.request("GET", private_entry, expected=404)
    reader.request(
        "GET",
        private_entry,
        headers={"X-NextPost-Private-Link": "v1.invalid"},
        expected=404,
    )
    assert reader.json(
        "GET", private_entry, headers={"X-NextPost-Private-Link": token}
    ) == {"role": "reader"}

    replacement = owner.json(
        "POST",
        f"/consultations/{private_id}/private-link/replace",
        {"expected_generation": "1"},
    )["token"]
    reader.request(
        "GET", private_entry, headers={"X-NextPost-Private-Link": token}, expected=404
    )
    assert reader.json(
        "GET", private_entry, headers={"X-NextPost-Private-Link": replacement}
    ) == {"role": "reader"}

    owner.json(
        "POST",
        f"/consultations/{private_id}/private-link/disable",
        {"expected_generation": "2"},
    )
    reader.request(
        "GET",
        private_entry,
        headers={"X-NextPost-Private-Link": replacement},
        expected=404,
    )
    assert owner.json("GET", private_entry) == {"role": "owner"}

    print(
        "PASS: built SPA direct-path fallback; anonymous denial; public owner/reader roles; "
        "forwarded Private access; missing/wrong/replaced/disabled token denial; owner access."
    )


if __name__ == "__main__":
    main()
