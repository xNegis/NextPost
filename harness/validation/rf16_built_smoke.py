"""Nonvisual RF-16 smoke against the disposable review Compose project only.

Run with the repository virtualenv after starting the isolated stack described by
``harness/validation/rf16-compose.override.yaml`` and project name
``nextpost-rf16-review-20261016``. It creates two accounts with real images, casts and
replays one immutable vote, verifies self-vote denial, Home ``has_voted`` marking, the
current-Private vote contract, revoked-capability denial, sign-in recovery and zero
aggregate/result exposure across a service restart. It does not claim browser, visual or
device validation.
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

PROJECT = "nextpost-rf16-review-20261016"
DOCKER = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Programs",
    "DockerDesktop",
    "resources",
    "bin",
    "docker.exe",
)
API = "http://127.0.0.1:18002/api"
FRONTEND = "http://localhost:14175"
COMPOSE = [
    DOCKER,
    "compose",
    "-p",
    PROJECT,
    "-f",
    "docker-compose.yml",
    "-f",
    "harness/validation/rf16-compose.override.yaml",
]
PASSWORD = "rf16-disposable-test-password"


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
        assert response.status == expected, (path, response.status, expected)
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(content), response.headers
        return content, response.headers

    def json(self, method, path, data=None, **kwargs):
        return self.request(method, path, data, **kwargs)[0]


def wait_ready():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with urlopen(API + "/ready", timeout=3) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(1)
    raise AssertionError("Disposable review backend did not become ready")


def publish(client, audience, label):
    session = client.json("POST", "/photo-upload-sessions", expected=201)["id"]
    images = []
    for size, color in [((64, 80), "red"), ((80, 64), "blue"), ((64, 64), "green")]:
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
            "ordered_image_ids": images,
            "question": f"RF16 {label} choice?",
            "context": f"{label} built-stack vote check",
            "audience": audience,
        },
        expected=201,
    )["id"]


def assert_private_headers(headers):
    assert headers["Cache-Control"] == "private, no-store"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-Content-Type-Options"] == "nosniff"


def feed(client):
    body, headers = client.request("GET", "/consultations/feed")
    assert_private_headers(headers)
    return body


def detail(client, consultation_id, *, expected=200):
    body, headers = client.request("GET", f"/consultations/{consultation_id}", expected=expected)
    if expected == 200:
        assert_private_headers(headers)
    return body


def my_vote(client, consultation_id, *, expected=200, token=None):
    headers = {"X-NextPost-Private-Link": token} if token else None
    body, resp_headers = client.request(
        "GET", f"/consultations/{consultation_id}/my-vote", headers=headers, expected=expected
    )
    if expected == 200:
        assert_private_headers(resp_headers)
    return body


def cast(client, consultation_id, photo_id, *, expected=200, token=None):
    headers = {"X-NextPost-Private-Link": token} if token else None
    body, resp_headers = client.request(
        "POST",
        f"/consultations/{consultation_id}/votes",
        {"photo_id": photo_id},
        headers=headers,
        expected=expected,
    )
    return body, resp_headers


def main():
    wait_ready()
    with urlopen(FRONTEND, timeout=10) as response:
        assert response.status == 200 and b'type="module"' in response.read()

    a, b, anonymous = Client(), Client(), Client()
    suffix = uuid.uuid4().hex[:8]
    b_email = f"rf16b{suffix}@example.com"
    for client, letter in [(a, "a"), (b, "b")]:
        client.json(
            "POST",
            "/accounts",
            {
                "email": f"rf16{letter}{suffix}@example.com",
                "alias": f"RF16{letter}{suffix}",
                "password": PASSWORD,
            },
            expected=201,
        )

    anonymous.json("GET", "/consultations/feed", expected=401)

    a_pub = publish(a, "public", "A public")
    b_pub = publish(b, "public", "B public")
    a_priv = publish(a, "private", "A private")

    # Home feed: newest first, both public items, private absent, has_voted false.
    b_feed = feed(b)
    assert [item["id"] for item in b_feed["items"]] == [b_pub, a_pub]
    for item in b_feed["items"]:
        assert "has_voted" in item and item["has_voted"] is False
    assert {a_priv}.isdisjoint({item["id"] for item in b_feed["items"]})

    a_detail = detail(b, a_pub)
    photo_ids = [p["id"] for p in a_detail["photos"]]
    assert len(photo_ids) == 3

    # Not voted yet.
    assert my_vote(b, a_pub) == {"status": "not_voted"}

    # Owner cannot vote on their own consultation (generic denial).
    a.json("POST", f"/consultations/{a_pub}/votes", {"photo_id": photo_ids[0]}, expected=404)
    a.json("GET", f"/consultations/{a_pub}/my-vote", expected=404)

    # Cast one immutable vote (201), exact replay (200), different option conflicts (409).
    created, headers = cast(b, a_pub, photo_ids[0], expected=201)
    assert created == {"status": "voted", "photo_id": photo_ids[0]}
    assert_private_headers(headers)

    replay, headers = cast(b, a_pub, photo_ids[0], expected=200)
    assert replay == {"status": "voted", "photo_id": photo_ids[0]}

    b.json("POST", f"/consultations/{a_pub}/votes", {"photo_id": photo_ids[1]}, expected=409)

    # Viewer-scoped status recovers the recorded own choice, with no aggregate fields.
    status = my_vote(b, a_pub)
    assert status == {"status": "voted", "photo_id": photo_ids[0]}

    # Feed marks has_voted only for the voting account, not for the owner.
    b_feed = feed(b)
    by_id = {item["id"]: item for item in b_feed["items"]}
    assert by_id[a_pub]["has_voted"] is True
    assert by_id[b_pub]["has_voted"] is False

    a_feed = feed(a)
    a_by_id = {item["id"]: item for item in a_feed["items"]}
    assert a_by_id[a_pub]["is_owner"] is True
    assert a_by_id[a_pub]["has_voted"] is False

    # Private requires the current capability; a replaced link invalidates the old one.
    token = a.json("GET", f"/consultations/{a_priv}/private-link")["token"]
    a_priv_detail = detail(b, a_priv, expected=404)
    priv_photo_ids = [p["id"] for p in detail(a, a_priv)["photos"]]
    b.json(
        "POST",
        f"/consultations/{a_priv}/votes",
        {"photo_id": priv_photo_ids[0]},
        expected=404,
    )
    created_priv, _ = cast(b, a_priv, priv_photo_ids[0], expected=201, token=token)
    assert created_priv == {"status": "voted", "photo_id": priv_photo_ids[0]}

    replaced = a.json(
        "POST",
        f"/consultations/{a_priv}/private-link/replace",
        {"expected_generation": "1"},
    )["token"]
    b.json(
        "POST",
        f"/consultations/{a_priv}/votes",
        {"photo_id": priv_photo_ids[0]},
        headers={"X-NextPost-Private-Link": token},
        expected=404,
    )
    assert my_vote(b, a_priv, expected=200, token=replaced)["status"] == "voted"

    # Sign-in recovery: a fresh client authenticating as B recovers the recorded choice.
    b2 = Client()
    b2.json(
        "POST", "/session", {"email": b_email, "password": PASSWORD}, expected=200
    )
    assert my_vote(b2, a_pub) == {"status": "voted", "photo_id": photo_ids[0]}

    # Ordinary disposable-service restart preserves the vote.
    subprocess.run(COMPOSE + ["restart", "db", "backend", "frontend"], check=True)
    wait_ready()
    assert my_vote(b, a_pub) == {"status": "voted", "photo_id": photo_ids[0]}
    b_feed = feed(b)
    assert {item["id"]: item["has_voted"] for item in b_feed["items"]}[a_pub] is True

    print(
        "PASS: built frontend served; immutable vote create/replay/conflict; self-vote denial; "
        "viewer-scoped my-vote recovery; Home has_voted marking; Private current-capability vote "
        "and revoked-link denial; sign-in recovery; restart persistence; no aggregate exposure."
    )


if __name__ == "__main__":
    main()
