import pytest

from tmpmask.filters import FILTER_IDS
from tmpmask.texts import filter_name, t

REQUIRED_KEYS = [
    "app.title",
    "cli.description",
    "cli.help",
    "cli.camera",
    "cli.width",
    "cli.height",
    "cli.mirror",
    "cli.output_dir",
    "cli.model",
    "cli.filter",
    "cli_errors.not_an_int",
    "cli_errors.negative",
    "cli_errors.not_positive",
    "cli_errors.unknown_filter",
    "messages.startup_hint",
    "messages.filter_switched",
    "messages.screenshot_saved",
    "messages.recording_started",
    "messages.recording_stopped",
    "messages.exit",
    "errors.camera_open",
    "errors.camera_no_frame",
    "errors.model_missing",
    "errors.output_dir",
    "errors.screenshot_failed",
    "errors.recording_failed",
]


def test_texts_keys_exist_and_non_empty():
    for key in REQUIRED_KEYS:
        val = t(
            key,
            filters="f",
            value="v",
            name="n",
            path="p",
            index=0,
            error="e",
            filter="flt",
            output_dir="od",
        )
        assert isinstance(val, str)
        assert len(val.strip()) > 0


def test_filters_keys_match_filter_ids():
    for fid in FILTER_IDS:
        name = filter_name(fid)
        assert isinstance(name, str)
        assert len(name.strip()) > 0
        assert t(f"filters.{fid}") == name


def test_t_formatting():
    msg = t("messages.filter_switched", name="X")
    assert msg == "Фильтр: X"


def test_t_missing_key_raises_key_error():
    with pytest.raises(KeyError):
        t("nonexistent.key")

    with pytest.raises(KeyError):
        t("messages")  # Table, not a string
