"""Nonvisual RF-14 smoke against the disposable review Compose project only.

Run with the repository virtualenv after starting the isolated stack described by
``harness/validation/rf14-compose.override.yaml`` and project name
``nextpost-rf14-review-20261015``. It creates two accounts with real images, verifies
Public-only chronological discovery, own/other is_owner flags, first-photo preview
metadata, protected detail/photo reads, header privacy, Private exclusion and seeded
terminal removal across a service restart. It does not claim browser, visual, real
terminal-operation or device validation.
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

PROJECT = "nextpost-rf14-review-20261015"
DOCKER = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Programs",
    "DockerDesktop",
    "resources",
    "bin",
    "docker.exe",
)
API = "http://127.0.0.1:18001/api"
FRONTEND = "http://localhost:14174"
COMPOSE = [
    DOCKER,
    "compose",
    "-p",
    PROJECT,
    "-f",
    "docker-compose.yml",
    "-f",
    "harness/validation/rf14-compose.override.yaml",
]
PASSWORD = "rf14-disposable-test-password"


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
            "question": f"RF14 {label} choice?",
            "context": f"{label} built-stack discovery check",
            "audience": audience,
        },
        expected=201,
    )["id"]


def assert_private_headers(headers):
    assert headers["Cache-Control"] == "private, no-store"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-Content-Type-Options"] == "nosniff"


def assert_feed_item(item):
    assert set(item) == {
        "id",
        "owner_nickname",
        "question",
        "context_excerpt",
        "audience",
        "state",
        "published_at",
        "is_owner",
        "first_photo",
    }
    assert item["audience"] == "public"
    assert item["state"] == "open"
    assert item["published_at"].endswith("Z")
    assert isinstance(item["is_owner"], bool)
    assert set(item["first_photo"]) == {"id", "width", "height"}
    assert item["first_photo"]["width"] > 0 and item["first_photo"]["height"] > 0


def feed(client):
    body, headers = client.request("GET", "/consultations/feed")
    assert_private_headers(headers)
    return body


def detail(client, consultation_id, *, expected=200):
    body, headers = client.request("GET", f"/consultations/{consultation_id}", expected=expected)
    if expected == 200:
        assert_private_headers(headers)
    return body


def main():
    wait_ready()
    with urlopen(FRONTEND, timeout=10) as response:
        assert response.status == 200 and b'type="module"' in response.read()

    a, b, anonymous = Client(), Client(), Client()
    suffix = uuid.uuid4().hex[:8]
    a_email = f"rf14a{suffix}@example.com"
    for client, letter in [(a, "a"), (b, "b")]:
        client.json(
            "POST",
            "/accounts",
            {
                "email": f"rf14{letter}{suffix}@example.com",
                "alias": f"RF14{letter}{suffix}",
                "password": PASSWORD,
            },
            expected=201,
        )

    anonymous.json("GET", "/consultations/feed", expected=401)

    a_pub = publish(a, "public", "A public")
    a_priv = publish(a, "private", "A private")
    b_pub = publish(b, "public", "B public")
    b_priv = publish(b, "private", "B private")

    # Feed is newest first: B public then A public; no Private rows for anyone.
    b_feed = feed(b)
    assert [item["id"] for item in b_feed["items"]] == [b_pub, a_pub]
    assert b_feed["next_cursor"] is None
    for item in b_feed["items"]:
        assert_feed_item(item)
    by_id = {item["id"]: item for item in b_feed["items"]}
    assert by_id[a_pub]["is_owner"] is False
    assert by_id[b_pub]["is_owner"] is True
    assert by_id[a_pub]["owner_nickname"] == f"RF14a{suffix}"
    assert by_id[b_pub]["owner_nickname"] == f"RF14b{suffix}"
    assert {a_priv, b_priv}.isdisjoint({item["id"] for item in b_feed["items"]})

    # The owner also sees its own Public item and never its Private item.
    a_feed = feed(a)
    assert {item["id"] for item in a_feed["items"]} == {b_pub, a_pub}
    a_by_id = {item["id"]: item for item in a_feed["items"]}
    assert a_by_id[a_pub]["is_owner"] is True
    assert a_by_id[b_pub]["is_owner"] is False

    # First-photo preview is the lowest published ordinal, matching detail photos[0].
    a_detail = detail(b, a_pub)
    assert a_detail["question"] == "RF14 A public choice?"
    assert a_detail["context"] == "A public built-stack discovery check"
    assert a_detail["audience"] == "public"
    assert [(p["width"], p["height"]) for p in a_detail["photos"]] == [
        (80, 64),
        (64, 80),
    ]
    first_detail_photo = a_detail["photos"][0]
    assert a_by_id[a_pub]["first_photo"]["id"] == first_detail_photo["id"]
    assert a_by_id[a_pub]["first_photo"]["width"] == first_detail_photo["width"]

    # B can read the photo bytes with private headers.
    content, headers = b.request(
        "GET", f"/consultations/{a_pub}/photos/{first_detail_photo['id']}/content"
    )
    assert_private_headers(headers)
    with Image.open(io.BytesIO(content)) as image:
        assert image.size == (first_detail_photo["width"], first_detail_photo["height"])

    # Private is never discoverable; without a token the general read is denied.
    b.json("GET", f"/consultations/{a_priv}", expected=404)

    # Seed a terminal fixture (finalized) to prove feed removal and generic denial.
    subprocess.run(
        [
            DOCKER,
            "exec",
            PROJECT + "-db-1",
            "psql",
            "-U",
            "rf14",
            "-d",
            "rf14_review",
            "-c",
            f"UPDATE consultations SET state='finalized' WHERE id='{a_pub}'",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    b_feed = feed(b)
    assert [item["id"] for item in b_feed["items"]] == [b_pub]
    b.json("GET", f"/consultations/{a_pub}", expected=404)

    # Ordinary disposable-service restart preserves discovery and published photos.
    subprocess.run(COMPOSE + ["restart", "db", "backend", "frontend"], check=True)
    wait_ready()
    b_feed = feed(b)
    assert [item["id"] for item in b_feed["items"]] == [b_pub]
    b_detail = detail(b, b_pub)
    for photo in b_detail["photos"]:
        content, headers = b.request(
            "GET", f"/consultations/{b_pub}/photos/{photo['id']}/content"
        )
        assert_private_headers(headers)

    print(
        "PASS: built frontend served; Public-only newest-first discovery; own/other is_owner; "
        "first-photo preview equals detail photo 0; Private exclusion; protected detail/photo "
        "reads with private headers; seeded terminal removal; restart persistence."
    )


if __name__ == "__main__":
    main()
