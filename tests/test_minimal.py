"""Minimal pure release contracts; never touch a live service."""
from datetime import datetime, timezone
from pathlib import Path
import runpy
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "custom_components" / "rdt_client"


def _load(filename):
    return runpy.run_path(str(SOURCE / filename))


def test_completion_timestamp_is_real_and_private():
    parser = _load("download_completion.py")["most_recent_completion"]
    now = datetime(2026, 11, 25, 20, tzinfo=timezone.utc)
    result = parser(
        [{"completion_on": 1795600100, "name": "private", "hash": "secret"},
         {"state": "downloading"},
         {"completion_on": int(now.timestamp()) + 1}],
        now=now,
    )
    assert result == datetime.fromtimestamp(1795600100, tz=timezone.utc)
    assert "private" not in repr(result)
    assert parser([], now=now) is None
    assert parser([{"state": "uploading", "progress": 1}], now=now) is None
    for invalid in (0, -2, True, "1795600100", 1.2, [], {}):
        assert parser([{"completion_on": invalid}], now=now) is None
    with pytest.raises(ValueError):
        parser([None], now=now)


def test_subscription_expiry_is_not_renewal():
    m = _load("subscription.py")
    expiration = m["parse_expiration"]("2026-12-27T19:35:00+00:00")
    assert expiration == datetime(2026, 12, 27, 19, 35, tzinfo=timezone.utc)
    assert m["days_until_expiration"](expiration, now=datetime(2026, 12, 26, tzinfo=timezone.utc)) == 2
    assert m["parse_expiration"]("2026-12-27") is None


def test_download_counts_do_not_expose_names():
    summarize = _load("transfer.py")["summarize_downloads"]
    result = summarize({"dl_info_speed": 1024}, [
        {"state": "downloading", "name": "private"},
        {"state": "stalledDL", "hash": "secret"},
        {"state": "queuedDL", "save_path": "/secret"}
    ])
    assert result["downloading_count"] == 2
    assert result["queued_count"] == 1
    assert result["download_speed"] == 1024
    assert "private" not in repr(result) and "secret" not in repr(result)


def test_release_tree_omits_storage_and_download_metadata():
    modules = {p.name for p in SOURCE.iterdir() if p.is_file()}
    assert all(not x.startswith(("storage", "mount", "monitor_storage")) for x in modules)
    sensor = (SOURCE / "monitor_sensor.py").read_text()
    assert '"last_completed"' in sensor
    assert '"downloading_count"' in sensor
    assert '"download_speed"' in sensor
    assert '"available_bytes"' not in sensor
    assert '"queue_remaining_bytes"' not in sensor
