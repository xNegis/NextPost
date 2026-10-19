"""Nonvisual RF-18 smoke against the disposable review Compose project only.

Run with the repository virtualenv after starting the isolated stack described by
``harness/validation/rf18-compose.override.yaml`` and project name
``nextpost-rf18-review-20261018``. It creates an owner plus two voters with real images,
verifies initial zero counts, casts a tie with one untouched zero option, checks the exact
per-photo aggregate and list total, proves voters/anonymous are denied, and confirms counts
survive a service restart. It never claims browser, visual or device validation.
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

PROJECT = "nextpost-rf18-review-20261018"
DOCKER = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Programs",
    "DockerDesktop",
    "resources",
    "bin",
    "docker.exe",
)
API = "http://127.0.0.1:18003/api"
FRONTEND = "http://localhost:14176"
COMPOSE = [
    DOCKER,
    "compose",
    "-p",
    PROJECT,
    "-f",
    "docker-compose.yml",
    "-f",
    "harness/validation/rf18-compose.override.yaml",
]
PASSWORD = "rf18-disposable-test-password"


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
        assert response.status == expected, (path, response.status, expected, content[:200])
        if "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(content), response.headers
        return content, response.headers

    def json(self, method, path, data=None, **kwargs):
        return self.request(method, path, data, **kwargs)[0]


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


def assert_private_headers(headers):
    assert headers["Cache-Control"] == "private, no-store"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["X-Content-Type-Options"] == "nosniff"


def publish(client, label, count=3):
    session = client.json("POST", "/photo-upload-sessions", expected=201)["id"]
    images = []
    for index in range(count):
        image = io.BytesIO()
        Image.new("RGB", (64, 64), (200, 30 + index * 20, 30)).save(image, format="JPEG")
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
            "question": f"RF18 {label} choice?",
            "context": "aggregate smoke",
            "audience": "public",
        },
        expected=201,
    )["id"]


def detail(client, consultation_id):
    body, headers = client.request("GET", f"/consultations/{consultation_id}")
    assert_private_headers(headers)
    return body


def results(client, consultation_id, *, expected=200):
    body, headers = client.request(
        "GET", f"/my-consultations/{consultation_id}/results", expected=expected
    )
    if expected == 200:
        assert_private_headers(headers)
    return body


def my_list(client):
    body, headers = client.request("GET", "/my-consultations?state=open")
    assert_private_headers(headers)
    return body


def main():
    wait_ready()
    with urlopen(FRONTEND, timeout=10) as response:
        assert response.status == 200 and b'type="module"' in response.read()

    owner, bob, carol, anonymous = Client(), Client(), Client(), Client()
    suffix = uuid.uuid4().hex[:8]

    owner.json(
        "POST",
        "/accounts",
        {"email": f"owner{suffix}@example.com", "alias": "Owner", "password": PASSWORD},
        expected=201,
    )
    bob.json(
        "POST",
        "/accounts",
        {"email": f"bob{suffix}@example.com", "alias": "Bob", "password": PASSWORD},
        expected=201,
    )
    carol.json(
        "POST",
        "/accounts",
        {"email": f"carol{suffix}@example.com", "alias": "Carol", "password": PASSWORD},
        expected=201,
    )

    anonymous.request("GET", f"/my-consultations/{uuid.uuid4()}/results", expected=401)

    consultation_id = publish(owner, "public", count=3)
    photo_ids = [p["id"] for p in detail(owner, consultation_id)["photos"]]
    assert len(photo_ids) == 3

    # Initial zeros: every option present in order, total zero, no forbidden fields.
    initial = results(owner, consultation_id)
    assert initial["state"] == "open"
    assert initial["total_votes"] == 0
    assert [o["ordinal"] for o in initial["options"]] == [0, 1, 2]
    assert [o["vote_count"] for o in initial["options"]] == [0, 0, 0]
    for option in initial["options"]:
        assert set(option) == {"photo_id", "ordinal", "vote_count"}

    # Cast a tie on photos 0 and 1, leaving photo 2 untouched.
    bob.json("POST", f"/consultations/{consultation_id}/votes", {"photo_id": photo_ids[0]}, expected=201)
    carol.json("POST", f"/consultations/{consultation_id}/votes", {"photo_id": photo_ids[1]}, expected=201)

    aggregate = results(owner, consultation_id)
    assert aggregate["total_votes"] == 2
    counts = {o["ordinal"]: o["vote_count"] for o in aggregate["options"]}
    assert counts == {0: 1, 1: 1, 2: 0}
    assert sum(o["vote_count"] for o in aggregate["options"]) == aggregate["total_votes"]

    # List row total matches the aggregate.
    items = my_list(owner)["items"]
    assert len(items) == 1
    assert items[0]["id"] == consultation_id
    assert items[0]["total_votes"] == 2

    # Voters, other accounts and anonymous receive no aggregate.
    bob.request("GET", f"/my-consultations/{consultation_id}/results", expected=404)
    carol.request("GET", f"/my-consultations/{consultation_id}/results", expected=404)
    anonymous.request("GET", f"/my-consultations/{consultation_id}/results", expected=401)

    # Participant surfaces remain aggregate-free.
    feed, _ = bob.request("GET", "/consultations/feed")
    feed_item = feed["items"][0]
    assert "total_votes" not in feed_item
    assert set(feed_item) == {
        "id",
        "owner_nickname",
        "question",
        "context_excerpt",
        "audience",
        "state",
        "published_at",
        "is_owner",
        "has_voted",
        "first_photo",
    }
    bob_vote = bob.json("GET", f"/consultations/{consultation_id}/my-vote")
    assert set(bob_vote) == {"status", "photo_id"}

    # Ordinary disposable-service restart preserves the aggregate.
    subprocess.run(COMPOSE + ["restart", "db", "backend", "frontend"], check=True)
    wait_ready()
    aggregate_after = results(owner, consultation_id)
    assert aggregate_after["total_votes"] == 2
    assert {o["ordinal"]: o["vote_count"] for o in aggregate_after["options"]} == {0: 1, 1: 1, 2: 0}

    print(
        "PASS: built frontend served; initial zero counts; exact per-photo tie with a zero "
        "option; list total; voter/anonymous aggregate denial; participant aggregate-free "
        "surfaces; restart persistence."
    )


if __name__ == "__main__":
    main()
