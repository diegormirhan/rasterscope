import argparse
import sys

import structlog

from rasterscope.ml.scenarios import build_scenarios
from rasterscope.ml.workflows import (
    evaluate_checkpoint,
    export_onnx,
    prepare_dataset,
    print_record,
    train_baseline,
    train_segmentation_model,
)
from rasterscope.settings import get_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rasterscope")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="Validate the dataset and create deterministic splits")
    subparsers.add_parser("train-baseline", help="Fit and evaluate the color-centroid baseline")
    subparsers.add_parser("build-scenarios", help="Acquire and analyze temporal Sentinel-2 scenes")
    for command in ("train", "evaluate", "export-onnx"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--model", choices=("unet", "segformer"), default="unet")
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    structlog.configure(processors=[structlog.processors.JSONRenderer()])
    arguments = build_parser().parse_args()
    config = get_config()
    if arguments.command == "prepare":
        print_record(prepare_dataset(config))
    elif arguments.command == "train-baseline":
        print_record(train_baseline(config))
    elif arguments.command == "build-scenarios":
        print_record(build_scenarios(config))
    elif arguments.command == "train":
        print_record(train_segmentation_model(config, arguments.model))
    elif arguments.command == "evaluate":
        print_record(evaluate_checkpoint(config, arguments.model))
    elif arguments.command == "export-onnx":
        print(export_onnx(config, arguments.model))


if __name__ == "__main__":
    main()
