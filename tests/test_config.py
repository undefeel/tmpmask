from pathlib import Path

import pytest

from tmpmask.config import Config, parse_args
from tmpmask.tracker import DEFAULT_MODEL_PATH


def test_default_config():
    cfg = parse_args([])
    assert cfg == Config(
        camera=0,
        width=1280,
        height=720,
        mirror=True,
        filter="purple",
        output_dir=Path("captures"),
        model=DEFAULT_MODEL_PATH,
    )


def test_no_mirror_flag():
    cfg = parse_args(["--no-mirror"])
    assert cfg.mirror is False


def test_filter_arg():
    cfg = parse_args(["--filter", "gray"])
    assert cfg.filter == "gray"


def test_camera_negative_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--camera", "-1"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "число не может быть отрицательным: -1" in captured.err


def test_camera_not_int_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--camera", "abc"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "нужно целое число, получено «abc»" in captured.err


def test_width_zero_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--width", "0"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "число должно быть больше нуля: 0" in captured.err


def test_height_zero_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--height", "-5"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "число должно быть больше нуля: -5" in captured.err


def test_filter_unknown_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--filter", "nope"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "неизвестный фильтр «nope»" in captured.err
    assert "purple" in captured.err


def test_help_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        parse_args(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Портал фильтров" in captured.out
    assert "Номер камеры" in captured.out
