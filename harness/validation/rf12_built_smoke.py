"""Nonvisual RF-12 smoke against the disposable review Compose project only.

Run with the repository virtualenv after starting the isolated stack described in
RF-12-implementation-review.md. It creates two test accounts and real images,
restarts that project's services, and seeds terminal fixtures only in its database.
It does not claim browser, visual, real terminal-operation or device validation.
"""

import io
import json
import os
import subprocess
import time
import uuid
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

from PIL import Image

PROJECT = "nextpost-rf12-review-20261015"
DOCKER = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Programs",
    "DockerDesktop",
    "resources",
    "bin",
    "docker.exe",
)
API = "http://127.0.0.1:18000/api"
COMPOSE = [
    DOCKER,
    "compose",
    "-p",
    PROJECT,
    "-f",
    "docker-compose.yml",
    "-f",
    "harness/validation/rf12-compose.override.yaml",
]
PASSWORD = "rf12-disposable-test-password"


class Client:
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, method, path, data=None, *, headers=None, expected=200, raw=None):
        body = json.dumps(data).encode() if data is not None else raw
        request_headers = {"Origin": "http://localhost:14173", **(headers or {})}
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        request = Request(API + path, data=body, headers=request_headers, method=method)
        try:
            response = self.opener.open(request, timeout=15)
        except HTTPError as error:
            response = error
        content = response.read()
        assert response.status == expected, (path, response.status, expected)
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(content), response.headers
        return content, response.headers

    def json(self, method, path, data=None, **kwargs):
        return self.request(method, path, data, **kwargs)[0]


def wait_ready():
    deadline = time.monotonic() + 60
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
    for size, color in [((64, 80), "red"), ((80, 64), "blue")]:
        image = io.BytesIO()
        Image.new("RGB", size, color).save(image, format="JPEG")
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
            "ordered_image_ids": list(reversed(images)),
            "question": f"RF12 {audience} choice?",
            "context": "Built-stack recovery check",
            "audience": audience,
        },
        expected=201,
    )["id"]


def verify_recovery(client, ids):
    listing, headers = client.request("GET", "/my-consultations?state=open")
    assert {item["id"] for item in listing["items"]} == set(ids)
    assert listing["next_cursor"] is None
    assert headers["Cache-Control"] == "private, no-store"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-Content-Type-Options"] == "nosniff"
    for consultation_id in ids:
        detail = client.json("GET", f"/my-consultations/{consultation_id}")
        assert [(photo["width"], photo["height"]) for photo in detail["photos"]] == [
            (80, 64),
            (64, 80),
        ]
        assert detail["context"] == "Built-stack recovery check"
        assert detail["published_at"].endswith("Z")
        for photo in detail["photos"]:
            content, _ = client.request(
                "GET", f"/consultations/{consultation_id}/photos/{photo['id']}/content"
            )
            with Image.open(io.BytesIO(content)) as image:
                assert image.size == (photo["width"], photo["height"])


def main():
    wait_ready()
    with urlopen("http://127.0.0.1:14173", timeout=10) as response:
        assert response.status == 200 and b'type="module"' in response.read()
    a, b, anonymous = Client(), Client(), Client()
    suffix = uuid.uuid4().hex[:8]
    email = f"rf12a{suffix}@example.com"
    for client, letter in [(a, "a"), (b, "b")]:
        client.json(
            "POST",
            "/accounts",
            {
                "email": f"rf12{letter}{suffix}@example.com",
                "alias": f"RF12{letter}{suffix}",
                "password": PASSWORD,
            },
            expected=201,
        )
    anonymous.json("GET", "/my-consultations", expected=401)
    public_id, private_id = publish(a, "public"), publish(a, "private")
    ids = [public_id, private_id]
    verify_recovery(a, ids)
    link_path = f"/consultations/{private_id}/private-link"
    link = a.json("GET", link_path)
    token_header = {"X-NextPost-Private-Link": link["token"]}
    assert b.json("GET", "/my-consultations")["items"] == []
    for consultation_id in ids:
        b.json(
            "GET",
            f"/my-consultations/{consultation_id}",
            headers=token_header,
            expected=404,
        )
    b.json("GET", f"/consultations/{public_id}")
    b.json("GET", f"/consultations/{private_id}", headers=token_header)
    disabled = a.json(
        "POST", link_path + "/disable", {"expected_generation": link["generation"]}
    )
    b.json("GET", f"/consultations/{private_id}", headers=token_header, expected=404)
    verify_recovery(a, ids)
    created = a.json(
        "POST", link_path + "/create", {"expected_generation": disabled["generation"]}
    )
    replaced = a.json(
        "POST", link_path + "/replace", {"expected_generation": created["generation"]}
    )
    b.json(
        "GET",
        f"/consultations/{private_id}",
        headers={"X-NextPost-Private-Link": created["token"]},
        expected=404,
    )
    b.json(
        "GET",
        f"/consultations/{private_id}",
        headers={"X-NextPost-Private-Link": replaced["token"]},
    )
    assert a.json("GET", "/consultation-capacity")["open_count"] == 2
    a.json("DELETE", "/session", expected=204)
    a.json("GET", "/my-consultations", expected=401)
    a.json("POST", "/session", {"email": email, "password": PASSWORD})
    verify_recovery(a, ids)
    subprocess.run(COMPOSE + ["restart", "db", "backend", "frontend"], check=True)
    wait_ready()
    verify_recovery(a, ids)
    assert a.json("GET", link_path) == replaced
    subprocess.run(
        COMPOSE + ["exec", "-T", "backend", "python", "-m", "app.cleanup"], check=True
    )
    verify_recovery(a, ids)
    # These fixtures prove projection and denial only: no terminal product operation is invoked.
    for terminal in ["finalized", "deleted", "removed"]:
        subprocess.run(
            [
                DOCKER,
                "exec",
                PROJECT + "-db-1",
                "psql",
                "-U",
                "rf12",
                "-d",
                "rf12_review",
                "-c",
                f"UPDATE consultations SET state='{terminal}' WHERE id='{public_id}'",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        listing = a.json("GET", "/my-consultations?state=finalized")
        if terminal == "finalized":
            summary = a.json("GET", f"/my-consultations/{public_id}")
            assert set(summary) == {"id", "state", "published_at"}
            assert len(listing["items"]) == 1 and set(listing["items"][0]) == set(
                summary
            )
        else:
            a.json("GET", f"/my-consultations/{public_id}", expected=404)
            assert listing["items"] == []
        a.json("GET", f"/consultations/{public_id}", expected=404)
    print(
        "PASS: built frontend served; two-account owner isolation; real ordered photos; private link disable/create/replace; login/restart recovery; cleanup preserves published photos; seeded terminal privacy."
    )


if __name__ == "__main__":
    main()
