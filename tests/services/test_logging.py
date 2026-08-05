from datetime import UTC, datetime

from services.logging import timestamper


def test_timestamper_with_debug(monkeypatch, freezer):
    monkeypatch.setattr("services.logging.DEBUG", True)

    log = timestamper(None, None, {"event": "derp"})
    assert log == {
        "event": "derp",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def test_timestamper_without_debug(monkeypatch):
    monkeypatch.setattr("services.logging.DEBUG", False)

    assert timestamper(None, None, {"event": "derp"}) == {"event": "derp"}
