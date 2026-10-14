"""Command-line arguments and configuration."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tmpmask.filters import FILTER_IDS
from tmpmask.texts import t
from tmpmask.tracker import DEFAULT_MODEL_PATH


@dataclass(frozen=True)
class Config:
    camera: int = 0
    width: int = 1280
    height: int = 720
    mirror: bool = True
    filter: str = "purple"
    output_dir: Path = Path("captures")
    model: Path = DEFAULT_MODEL_PATH


def _int_min(min_val: int) -> Callable[[str], int]:
    def parser(val_str: str) -> int:
        try:
            val = int(val_str)
        except ValueError as err:
            raise argparse.ArgumentTypeError(t("cli_errors.not_an_int", value=val_str)) from err

        if min_val == 0 and val < 0:
            raise argparse.ArgumentTypeError(t("cli_errors.negative", value=val_str))
        if min_val > 0 and val < min_val:
            raise argparse.ArgumentTypeError(t("cli_errors.not_positive", value=val_str))
        return val

    return parser


def _filter_id(val_str: str) -> str:
    if val_str not in FILTER_IDS:
        raise argparse.ArgumentTypeError(
            t("cli_errors.unknown_filter", value=val_str, filters=", ".join(FILTER_IDS))
        )
    return val_str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tmpmask",
        description=t("cli.description"),
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help=t("cli.help"),
    )
    parser.add_argument(
        "--camera",
        type=_int_min(0),
        default=0,
        help=t("cli.camera"),
    )
    parser.add_argument(
        "--width",
        type=_int_min(1),
        default=1280,
        help=t("cli.width"),
    )
    parser.add_argument(
        "--height",
        type=_int_min(1),
        default=720,
        help=t("cli.height"),
    )
    parser.add_argument(
        "--mirror",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=t("cli.mirror"),
    )
    parser.add_argument(
        "--filter",
        type=_filter_id,
        default="purple",
        help=t("cli.filter", filters=", ".join(FILTER_IDS)),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("captures"),
        help=t("cli.output_dir"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=t("cli.model"),
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> Config:
    parser = build_parser()
    args = parser.parse_args(argv)
    return Config(
        camera=args.camera,
        width=args.width,
        height=args.height,
        mirror=args.mirror,
        filter=args.filter,
        output_dir=args.output_dir,
        model=args.model,
    )
